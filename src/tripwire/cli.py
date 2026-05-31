from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .doctrine import load_doctrine
from .evaluation import render_eval_results, run_eval
from .git import GitError, base_diff, repository_context, staged_diff, working_tree_diff
from .github import GitHubError, fetch_pr, fetch_pr_review_input
from .interactive import InteractiveError, choose_pr, choose_repository, prompt_concerns
from .heuristics import local_findings
from .models import ReviewInput, ReviewMode
from .personas import render_personas
from .reviewer import review as run_review
from .storage import LocalStore, StorageError, create_store


def build_parser() -> argparse.ArgumentParser:
    ai_options = argparse.ArgumentParser(add_help=False)
    ai_options.add_argument("--provider", choices=["ollama", "openai"], default=None, help="AI provider to use.")
    ai_options.add_argument("--model", default=None, help="AI model to use. Ollama defaults to llama3.1.")

    review_options = argparse.ArgumentParser(add_help=False, parents=[ai_options])
    review_options.add_argument("--prompt-only", action="store_true", help="Print the assembled review prompt without calling AI.")

    pr_review_options = argparse.ArgumentParser(add_help=False, parents=[review_options])
    pr_review_options.add_argument("--store", action="store_true", help="Store GitHub PR review output locally, or in Supabase when TRIPWIRE_STORE=supabase.")

    parser = argparse.ArgumentParser(
        prog="tripwire",
        description="Review code changes for strategic drift, contradictions, and hidden costs.",
    )
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser(
        "review",
        parents=[review_options],
        help="Review the current diff, staged diff, or branch against a base.",
    )
    review_parser.add_argument("base", nargs="?", help="Base ref for branch comparison, for example main.")
    review_parser.add_argument("--staged", action="store_true", help="Review staged changes.")

    pr_parser = subparsers.add_parser(
        "review-pr",
        parents=[pr_review_options],
        help="Review a GitHub pull request directly by repository and PR number.",
    )
    pr_parser.add_argument("repo", help="GitHub repository in OWNER/NAME form.")
    pr_parser.add_argument("number", type=int, help="Pull request number.")
    pr_parser.add_argument("--concerns", default="", help="Extra concerns or context to include in the review.")

    subparsers.add_parser(
        "github",
        parents=[pr_review_options],
        help="Interactively choose a GitHub repository and open pull request to review.",
    )

    subparsers.add_parser("paranoid", parents=[review_options], help="Run paranoid review mode on the current diff.")
    subparsers.add_parser("architecture", parents=[review_options], help="Run repository-wide architecture analysis.")
    subparsers.add_parser("personas", help="Explain Tripwire's reviewer personas.")
    memory_parser = subparsers.add_parser("memory", help="Inspect local Tripwire memory.")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", required=True)
    memory_subparsers.add_parser("stats", help="Show local memory database path, size, and row counts.")
    eval_parser = subparsers.add_parser(
        "eval",
        parents=[ai_options],
        help="Run Tripwire against fixture diffs and score expected findings.",
    )
    eval_parser.add_argument("--fixtures", default="eval/fixtures", help="Directory containing eval fixture JSON files.")
    eval_parser.add_argument("--show-output", action="store_true", help="Print each review output after its score.")
    return parser


def make_review_input(args: argparse.Namespace) -> ReviewInput:
    root = Path(args.root).resolve()
    doctrine = load_doctrine(root)
    context = repository_context(root)

    if args.command == "review":
        if args.staged and args.base:
            raise SystemExit("Use either --staged or a base ref, not both.")
        if args.staged:
            diff = staged_diff(root)
            source = "Staged git diff"
        elif args.base:
            diff = base_diff(root, args.base)
            source = f"Git diff from {args.base}...HEAD"
        else:
            diff = working_tree_diff(root)
            source = "Working tree git diff"
        mode = ReviewMode.STANDARD
    elif args.command == "paranoid":
        diff = working_tree_diff(root)
        source = "Working tree git diff"
        mode = ReviewMode.PARANOID
    elif args.command == "architecture":
        diff = ""
        source = "Repository-wide architecture analysis"
        mode = ReviewMode.ARCHITECTURE
    else:
        raise SystemExit(f"Unknown command: {args.command}")

    return ReviewInput(
        mode=mode,
        diff=diff,
        doctrine=doctrine,
        repository_context=context,
        source_description=source,
    )


def with_local_doctrine_fallback(review_input: ReviewInput, root: Path) -> ReviewInput:
    if review_input.doctrine:
        return review_input
    local_doctrine = load_doctrine(root)
    return ReviewInput(
        mode=review_input.mode,
        diff=review_input.diff,
        doctrine=local_doctrine,
        repository_context=review_input.repository_context
        + "\n\nDoctrine source: generic local Tripwire doctrine fallback. The target repository did not expose Tripwire doctrine docs on the PR base branch.",
        source_description=review_input.source_description,
        user_concerns=review_input.user_concerns,
    )


def store_pr_review(
    repo: str,
    number: int,
    review_input: ReviewInput,
    output: str,
    *,
    provider: str | None,
    model: str | None,
    trigger: str,
) -> str:
    pr = fetch_pr(repo, number)
    store = create_store()
    project_id = store.upsert_project(repo, default_branch=pr.base_ref, doctrine=review_input.doctrine)
    pull_request_id = store.upsert_pull_request(project_id, pr)
    review_run_id = store.create_review_run(
        pull_request_id,
        trigger=trigger,
        provider=provider,
        model=model,
        user_concerns=review_input.user_concerns,
        doctrine=review_input.doctrine,
        diff_summary={
            "changed_files": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "source_description": review_input.source_description,
        },
        output_text=output,
    )
    store.create_findings(review_run_id, local_findings(review_input))
    return review_run_id


def render_memory_stats(root: Path) -> str:
    db_path = os.environ.get("TRIPWIRE_DB_PATH")
    store = LocalStore(db_path or root / ".tripwire" / "tripwire.db")
    stats = store.stats()
    store.close()
    counts = stats["counts"]
    lines = [
        "Tripwire memory",
        "",
        f"Backend: {stats['backend']}",
        f"Path: {stats['path']}",
        f"Size: {stats['size_bytes']} bytes",
        "",
        "Rows:",
    ]
    lines.extend(f"- {table}: {count}" for table, count in counts.items())  # type: ignore[union-attr]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "eval":
        fixtures_dir = Path(args.fixtures)
        if not fixtures_dir.is_absolute():
            fixtures_dir = root / fixtures_dir
        if not fixtures_dir.exists():
            print(f"Tripwire eval fixtures directory does not exist: {fixtures_dir}", file=sys.stderr)
            return 2
        results = run_eval(root, fixtures_dir, provider=args.provider, model=args.model)
        if not results:
            print(f"Tripwire eval found no fixture JSON files in: {fixtures_dir}", file=sys.stderr)
            return 2
        print(render_eval_results(results, show_output=args.show_output))
        return 0 if all(result.passed for result in results) else 1

    if args.command == "personas":
        print(render_personas())
        return 0

    if args.command == "memory":
        if args.memory_command == "stats":
            print(render_memory_stats(root))
            return 0
        raise SystemExit(f"Unknown memory command: {args.memory_command}")

    if args.command == "review-pr":
        try:
            review_input = fetch_pr_review_input(args.repo, args.number, concerns=args.concerns)
            review_input = with_local_doctrine_fallback(review_input, root)
            output = run_review(
                review_input,
                provider=args.provider,
                model=args.model,
                prompt_only=args.prompt_only,
            )
            print(output)
            if args.store and not args.prompt_only:
                review_run_id = store_pr_review(
                    args.repo,
                    args.number,
                    review_input,
                    output,
                    provider=args.provider,
                    model=args.model,
                    trigger="manual",
                )
                print(f"\nStored Tripwire review run: {review_run_id}")
        except GitHubError as exc:
            print(f"Tripwire could not read the requested GitHub PR: {exc}", file=sys.stderr)
            return 2
        except StorageError as exc:
            print(f"Tripwire could not store the review: {exc}", file=sys.stderr)
            return 2
        return 0

    if args.command == "github":
        try:
            selected_repo = choose_repository()
            selected_pr = choose_pr(selected_repo.name_with_owner)
            concerns = prompt_concerns()
            review_input = fetch_pr_review_input(
                selected_repo.name_with_owner,
                selected_pr.number,
                concerns=concerns,
            )
            review_input = with_local_doctrine_fallback(review_input, root)
            output = run_review(
                review_input,
                provider=args.provider,
                model=args.model,
                prompt_only=args.prompt_only,
            )
            print("")
            print(output)
            if args.store and not args.prompt_only:
                review_run_id = store_pr_review(
                    selected_repo.name_with_owner,
                    selected_pr.number,
                    review_input,
                    output,
                    provider=args.provider,
                    model=args.model,
                    trigger="manual",
                )
                print(f"\nStored Tripwire review run: {review_run_id}")
        except (GitHubError, InteractiveError) as exc:
            print(f"Tripwire could not run the interactive GitHub review: {exc}", file=sys.stderr)
            return 2
        except StorageError as exc:
            print(f"Tripwire could not store the review: {exc}", file=sys.stderr)
            return 2
        return 0

    try:
        review_input = make_review_input(args)
        print(
            run_review(
                review_input,
                provider=args.provider,
                model=args.model,
                prompt_only=args.prompt_only,
            )
        )
    except GitError as exc:
        print(f"Tripwire could not read the requested git diff: {exc}", file=sys.stderr)
        return 2
    return 0
