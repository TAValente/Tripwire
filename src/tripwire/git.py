from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise GitError(message)
    return result.stdout


def working_tree_diff(root: Path) -> str:
    return run_git(root, "diff", "--no-ext-diff")


def staged_diff(root: Path) -> str:
    return run_git(root, "diff", "--cached", "--no-ext-diff")


def base_diff(root: Path, base: str) -> str:
    return run_git(root, "diff", "--no-ext-diff", f"{base}...HEAD")


def repository_context(root: Path) -> str:
    try:
        status = run_git(root, "status", "--short")
    except GitError as exc:
        status = f"Unavailable: {exc}"

    files = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
    )
    shown_files = files[:200]
    if len(files) > len(shown_files):
        shown_files.append(f"... {len(files) - len(shown_files)} more files")

    return "\n".join(
        [
            "Git status:",
            status.strip() or "clean or unavailable",
            "",
            "Repository files:",
            "\n".join(shown_files) or "No files discovered.",
        ]
    )
