from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .doctrine import DOCTRINE_PATHS
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


@dataclass(frozen=True)
class Repository:
    name_with_owner: str
    url: str
    visibility: str


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
                "nameWithOwner,url,visibility",
            ]
        )
    )
    return tuple(
        Repository(
            name_with_owner=item.get("nameWithOwner") or "",
            url=item.get("url") or "",
            visibility=item.get("visibility") or "",
        )
        for item in data
        if item.get("nameWithOwner")
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
                "number,title,url,author,headRefName,baseRefName,additions,deletions,changedFiles",
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
                "number,title,body,url,author,headRefName,baseRefName,additions,deletions,changedFiles",
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


def build_pr_review_input(
    pr: PullRequest,
    diff: str,
    doctrine: tuple[DoctrineDocument, ...],
    *,
    concerns: str = "",
) -> ReviewInput:
    body = pr.body.strip() or "(No PR body.)"
    repository_context = "\n".join(
        [
            f"GitHub repository: {pr.repo}",
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
    return build_pr_review_input(pr, diff, doctrine, concerns=concerns)
