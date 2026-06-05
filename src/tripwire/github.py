from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .doctrine import DOCTRINE_PATHS, render_doctrine_sufficiency
from .models import DoctrineDocument, ReviewInput, ReviewMode


class GitHubError(RuntimeError):
    pass


def gh_executable() -> str | None:
    path = shutil.which("gh")
    if path:
        return path
    common_windows_path = Path("C:/Program Files/GitHub CLI/gh.exe")
    if common_windows_path.exists():
        return str(common_windows_path)
    return None


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    title: str
    body: str
    url: str
    author: str
    head_ref: str
    base_ref: str
    additions: int
    deletions: int
    changed_files: int
    head_sha: str = ""
    state: str = ""
    merged_at: str = ""


@dataclass(frozen=True)
class Repository:
    name_with_owner: str
    url: str
    visibility: str
    description: str = ""
    default_branch: str = ""
    primary_language: str = ""


def run_gh(args: list[str]) -> str:
    executable = gh_executable()
    if executable is None:
        raise GitHubError(
            "GitHub CLI (`gh`) was not found on PATH. Install GitHub CLI, authenticate with `gh auth login`, "
            "then rerun the command."
        )
    result = subprocess.run(
        [executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise GitHubError(message)
    return result.stdout


def list_repositories(limit: int = 50) -> tuple[Repository, ...]:
    data = json.loads(
        run_gh(
            [
                "repo",
                "list",
                "--limit",
                str(limit),
                "--json",
                "nameWithOwner,url,visibility,description,defaultBranchRef,primaryLanguage",
            ]
        )
    )
    return tuple(
        Repository(
            name_with_owner=item.get("nameWithOwner") or "",
            url=item.get("url") or "",
            visibility=item.get("visibility") or "",
            description=item.get("description") or "",
            default_branch=(item.get("defaultBranchRef") or {}).get("name") or "",
            primary_language=(item.get("primaryLanguage") or {}).get("name") or "",
        )
        for item in data
        if item.get("nameWithOwner")
    )


def fetch_repository(repo: str) -> Repository:
    data = json.loads(
        run_gh(
            [
                "repo",
                "view",
                repo,
                "--json",
                "nameWithOwner,url,visibility,description,defaultBranchRef,primaryLanguage",
            ]
        )
    )
    return Repository(
        name_with_owner=data.get("nameWithOwner") or repo,
        url=data.get("url") or "",
        visibility=data.get("visibility") or "",
        description=data.get("description") or "",
        default_branch=(data.get("defaultBranchRef") or {}).get("name") or "main",
        primary_language=(data.get("primaryLanguage") or {}).get("name") or "",
    )


def list_open_prs(repo: str) -> tuple[PullRequest, ...]:
    data = json.loads(
        run_gh(
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--json",
                "number,title,url,author,headRefName,baseRefName,headRefOid,state,mergedAt,additions,deletions,changedFiles",
            ]
        )
    )
    prs: list[PullRequest] = []
    for item in data:
        author = item.get("author") or {}
        prs.append(
            PullRequest(
                repo=repo,
                number=int(item.get("number") or 0),
                title=item.get("title") or "",
                body="",
                url=item.get("url") or "",
                author=author.get("login") or "",
                head_ref=item.get("headRefName") or "",
                base_ref=item.get("baseRefName") or "",
                head_sha=item.get("headRefOid") or "",
                state=item.get("state") or "open",
                merged_at=item.get("mergedAt") or "",
                additions=int(item.get("additions") or 0),
                deletions=int(item.get("deletions") or 0),
                changed_files=int(item.get("changedFiles") or 0),
            )
        )
    return tuple(prs)


def fetch_pr(repo: str, number: int) -> PullRequest:
    data = json.loads(
        run_gh(
            [
                "pr",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                "number,title,body,url,author,headRefName,baseRefName,headRefOid,state,mergedAt,additions,deletions,changedFiles",
            ]
        )
    )
    author = data.get("author") or {}
    return PullRequest(
        repo=repo,
        number=int(data.get("number", number)),
        title=data.get("title") or "",
        body=data.get("body") or "",
        url=data.get("url") or "",
        author=author.get("login") or "",
        head_ref=data.get("headRefName") or "",
        base_ref=data.get("baseRefName") or "",
        head_sha=data.get("headRefOid") or "",
        state=data.get("state") or "",
        merged_at=data.get("mergedAt") or "",
        additions=int(data.get("additions") or 0),
        deletions=int(data.get("deletions") or 0),
        changed_files=int(data.get("changedFiles") or 0),
    )


def fetch_pr_diff(repo: str, number: int) -> str:
    return run_gh(["pr", "diff", str(number), "--repo", repo, "--patch"])


def fetch_remote_doctrine(repo: str, ref: str) -> tuple[DoctrineDocument, ...]:
    documents: list[DoctrineDocument] = []
    for path in DOCTRINE_PATHS:
        try:
            content = run_gh(
                [
                    "api",
                    "-H",
                    "Accept: application/vnd.github.raw",
                    f"/repos/{repo}/contents/{path}?ref={ref}",
                ]
            )
        except GitHubError:
            continue
        if content.strip():
            documents.append(DoctrineDocument(path=path, content=content.strip()))
    return tuple(documents)


def fetch_remote_text(repo: str, ref: str, path: str) -> str:
    return run_gh(
        [
            "api",
            "-H",
            "Accept: application/vnd.github.raw",
            f"/repos/{repo}/contents/{path}?ref={ref}",
        ]
    )


def fetch_remote_readme(repo: str, ref: str) -> tuple[str, str]:
    for path in ("README.md", "README.mdx", "README"):
        try:
            content = fetch_remote_text(repo, ref, path).strip()
        except GitHubError:
            continue
        if content:
            return path, content
    return "", ""


def fetch_remote_tree_paths(repo: str, ref: str) -> tuple[str, ...]:
    data = json.loads(run_gh(["api", f"/repos/{repo}/git/trees/{ref}?recursive=1"]))
    tree = data.get("tree") or []
    paths = [
        item.get("path") or ""
        for item in tree
        if item.get("type") == "blob" and item.get("path")
    ]
    return tuple(sorted(paths))


def select_scan_paths(paths: tuple[str, ...], limit: int = 80) -> tuple[str, ...]:
    priority_names = {
        "README.md",
        "README.mdx",
        "pyproject.toml",
        "package.json",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "Dockerfile",
    }
    selected: list[str] = []
    for path in paths:
        if path in priority_names or path.startswith("docs/") or path.startswith(".github/"):
            selected.append(path)
    for path in paths:
        if len(selected) >= limit:
            break
        if path not in selected and not path.startswith(".git/"):
            selected.append(path)
    return tuple(selected[:limit])


def build_pr_review_input(
    pr: PullRequest,
    diff: str,
    doctrine: tuple[DoctrineDocument, ...],
    *,
    concerns: str = "",
    repository: Repository | None = None,
) -> ReviewInput:
    body = pr.body.strip() or "(No PR body.)"
    repository_context = "\n".join(
        [
            f"GitHub repository: {pr.repo}",
            f"Repository URL: {repository.url if repository else pr.url.rsplit('/pull/', 1)[0]}",
            f"Repository visibility: {repository.visibility if repository else 'unknown'}",
            f"Repository default branch: {repository.default_branch if repository else pr.base_ref}",
            f"Repository primary language: {repository.primary_language if repository else 'unknown'}",
            f"Repository description: {(repository.description if repository else '') or '(none)'}",
            f"Pull request: #{pr.number}",
            f"URL: {pr.url}",
            f"Author: {pr.author or 'unknown'}",
            f"Base branch: {pr.base_ref}",
            f"Head branch: {pr.head_ref}",
            f"Changed files: {pr.changed_files}",
            f"Additions: {pr.additions}",
            f"Deletions: {pr.deletions}",
            "",
            "PR title:",
            pr.title,
            "",
            "PR body:",
            body,
        ]
    )
    return ReviewInput(
        mode=ReviewMode.STANDARD,
        diff=diff,
        doctrine=doctrine,
        repository_context=repository_context,
        source_description=f"GitHub PR {pr.repo}#{pr.number}: {pr.title}",
        user_concerns=concerns,
    )


def fetch_pr_review_input(repo: str, number: int, *, concerns: str = "") -> ReviewInput:
    pr = fetch_pr(repo, number)
    diff = fetch_pr_diff(repo, number)
    doctrine = fetch_remote_doctrine(repo, pr.base_ref)
    try:
        repository = fetch_repository(repo)
    except GitHubError:
        repository = None
    return build_pr_review_input(pr, diff, doctrine, concerns=concerns, repository=repository)


def fetch_project_scan_input(repo: str) -> ReviewInput:
    repository = fetch_repository(repo)
    ref = repository.default_branch or "main"
    doctrine = fetch_remote_doctrine(repo, ref)
    readme_path, readme = fetch_remote_readme(repo, ref)
    try:
        paths = select_scan_paths(fetch_remote_tree_paths(repo, ref))
    except GitHubError:
        paths = ()

    readme_excerpt = readme[:5000]
    context_lines = [
        f"GitHub repository: {repository.name_with_owner}",
        f"URL: {repository.url}",
        f"Visibility: {repository.visibility or 'unknown'}",
        f"Default branch: {ref}",
        f"Primary language: {repository.primary_language or 'unknown'}",
        f"Description: {repository.description or '(none)'}",
        "",
        render_doctrine_sufficiency(doctrine, source=f"{repository.name_with_owner}@{ref}"),
    ]
    if readme_excerpt:
        context_lines.extend(["", f"Repository README excerpt ({readme_path}):", readme_excerpt])
    else:
        context_lines.extend(["", "Repository README excerpt: none found."])
    if paths:
        context_lines.extend(["", "Visible repository files sampled for scan:"])
        context_lines.extend(f"- {path}" for path in paths)
    else:
        context_lines.extend(["", "Visible repository files sampled for scan: unavailable."])

    return ReviewInput(
        mode=ReviewMode.PROJECT_SCAN,
        diff="",
        doctrine=doctrine,
        repository_context="\n".join(context_lines),
        source_description=f"Project scan for {repository.name_with_owner}@{ref}",
        missing_target_doctrine=not doctrine,
    )
