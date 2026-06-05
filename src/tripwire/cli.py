from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .doctrine import load_doctrine, render_doctrine_completeness
from .doctor import render_doctor
from .evaluation import render_eval_results, run_eval
from .git import GitError, base_diff, repository_context, staged_diff, working_tree_diff
from .github import GitHubError, fetch_pr, fetch_pr_review_input, fetch_project_scan_input
from .interactive import InteractiveError, choose_pr, choose_repository, prompt_concerns
from .heuristics import local_findings
from .models import ReviewInput, ReviewMode
from .personas import render_personas
from .reviewer import review as run_review
from .storage import LocalStore, StorageError, create_store


def configure_console_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


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
    scan_parser = subparsers.add_parser(
        "scan",
        parents=[review_options],
        help="Run a project scan for longer-running drift and doctrine conflicts.",
    )
    scan_parser.add_argument("repo", nargs="?", help="Optional GitHub repository in OWNER/NAME form.")
    subparsers.add_parser("doctrine", help="Check local doctrine completeness and suggest missing docs.")
    subparsers.add_parser("doctor", parents=[ai_options], help="Check whether Tripwire review dependencies are ready.")
    ui_parser = subparsers.add_parser("ui", parents=[ai_options], help="Run the local Tripwire control panel.")
    ui_parser.add_argument("--host", default="127.0.0.1", help="Host for the local UI. Defaults to 127.0.0.1.")
    ui_parser.add_argument("--port", type=int, default=8787, help="Port for the local UI. Defaults to 8787.")
    ui_parser.add_argument("--default-repo", default="", help="Optional OWNER/REPO value to prefill.")
    ui_parser.add_argument("--open", action="store_true", help="Open the local UI in the default browser.")
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
    elif args.command == "scan":
        if args.repo:
            return fetch_project_scan_input(args.repo)
        diff = ""
        source = "Project scan"
        mode = ReviewMode.PROJECT_SCAN
    else:
        raise SystemExit(f"Unknown command: {args.command}")

    return ReviewInput(
        mode=mode,
        diff=diff,
        doctrine=doctrine,
        repository_context=context,
        source_description=source,
    )


def mark_missing_target_doctrine(review_input: ReviewInput) -> ReviewInput:
    if review_input.doctrine:
        return review_input
    return ReviewInput(
        mode=review_input.mode,
        diff=review_input.diff,
        doctrine=(),
        repository_context=review_input.repository_context
        + "\n\nDoctrine source: none found on the target repository PR base branch.",
        source_description=review_input.source_description,
        user_concerns=review_input.user_concerns,
        missing_target_doctrine=True,
    )


def attach_review_feedback(root: Path, repo: str, review_input: ReviewInput) -> ReviewInput:
    db_path = os.environ.get("TRIPWIRE_DB_PATH")
    store = LocalStore(db_path or root / ".tripwire" / "tripwire.db")
    try:
        outcomes = store.recent_review_outcomes(repo, limit=5)
    finally:
        store.close()
    if not outcomes:
        return review_input

    lines = [
        "",
        "",
        "Prior Tripwire feedback for this repository:",
        "Use this only to calibrate judgment. Do not repeat findings that were explicitly marked false_positive unless the new diff materially changes the evidence.",
    ]
    for outcome in outcomes:
        note = f" Note: {outcome['outcome_note']}" if outcome["outcome_note"] else ""
        state = outcome["outcome_state"] or "inferred_observation"
        inferred = f" Inferred signal: {outcome['inferred_signal']}." if outcome["inferred_signal"] else ""
        lines.append(
            f"- PR #{outcome['pr_number']} {outcome['pr_title']}: {state}.{inferred}{note}"
        )

    return ReviewInput(
        mode=review_input.mode,
        diff=review_input.diff,
        doctrine=review_input.doctrine,
        repository_context=review_input.repository_context + "\n".join(lines),
        source_description=review_input.source_description,
        user_concerns=review_input.user_concerns,
        missing_target_doctrine=review_input.missing_target_doctrine,
    )


def output_has_mistake(output: str) -> bool:
    text = output.strip()
    if not text or text.startswith("No high-confidence strategic findings detected."):
        return False
    if "Mistakes to Correct" not in text:
        return False
    mistakes_section = text.split("Mistakes to Correct", 1)[1].split("Concrete Improvers", 1)[0]
    return "Title:" in mistakes_section


def output_has_suppressed_finding(output: str) -> bool:
    return "Suppressed Finding" in output and "Title:" in output.split("Suppressed Finding", 1)[1]


def infer_previous_review_signals(
    store: LocalStore,
    pull_request_id: str,
    *,
    current_review_run_id: str,
    current_head_sha: str,
    current_output: str,
) -> None:
    if not current_head_sha:
        return
    current_has_mistake = output_has_mistake(current_output)
    for previous in store.previous_pr_review_runs(
        pull_request_id,
        exclude_run_id=current_review_run_id,
    ):
        diff_summary = previous.get("diff_summary")
        previous_head_sha = ""
        if isinstance(diff_summary, dict):
            previous_head_sha = str(diff_summary.get("head_sha") or "")
        if not previous_head_sha or previous_head_sha == current_head_sha:
            continue
        previous_output = str(previous.get("output_text") or "")
        if output_has_suppressed_finding(previous_output):
            signal = (
                "pr_updated_after_suppressed_finding_now_finding"
                if current_has_mistake
                else "pr_updated_after_suppressed_finding_no_current_finding"
            )
        elif output_has_mistake(previous_output) and not current_has_mistake:
            signal = "pr_updated_after_finding_no_current_finding"
        else:
            continue
        store.set_review_run_inferred_signal(str(previous["id"]), signal)


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
            "head_sha": pr.head_sha,
            "source_description": review_input.source_description,
        },
        output_text=output,
        inferred_signal="review_stored_no_feedback",
    )
    if isinstance(store, LocalStore):
        infer_previous_review_signals(
            store,
            pull_request_id,
            current_review_run_id=review_run_id,
            current_head_sha=pr.head_sha,
            current_output=output,
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
    configure_console_output()
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

    if args.command == "doctrine":
        print(render_doctrine_completeness(root))
        return 0

    if args.command == "doctor":
        output, ready = render_doctor(root, provider=args.provider, model=args.model)
        print(output)
        return 0 if ready else 1

    if args.command == "ui":
        from .ui import serve_ui

        return serve_ui(args)

    if args.command == "memory":
        if args.memory_command == "stats":
            print(render_memory_stats(root))
            return 0
        raise SystemExit(f"Unknown memory command: {args.memory_command}")

    if args.command == "review-pr":
        try:
            review_input = fetch_pr_review_input(args.repo, args.number, concerns=args.concerns)
            review_input = mark_missing_target_doctrine(review_input)
            review_input = attach_review_feedback(root, args.repo, review_input)
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
            review_input = mark_missing_target_doctrine(review_input)
            review_input = attach_review_feedback(root, selected_repo.name_with_owner, review_input)
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
    except (GitError, GitHubError) as exc:
        print(f"Tripwire could not read the requested review target: {exc}", file=sys.stderr)
        return 2
    return 0
