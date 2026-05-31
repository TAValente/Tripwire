from __future__ import annotations

from collections.abc import Callable

from .github import GitHubError, PullRequest, Repository, list_open_prs, list_repositories


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


class InteractiveError(RuntimeError):
    pass


def choose(
    options: tuple[object, ...],
    label: str,
    render: Callable[[object], str],
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> object:
    if not options:
        raise InteractiveError(f"No {label} available.")

    output_fn("")
    output_fn(f"Select {label}:")
    for index, option in enumerate(options, start=1):
        output_fn(f"{index}. {render(option)}")

    while True:
        raw = input_fn("> ").strip()
        if not raw:
            continue
        try:
            selected = int(raw)
        except ValueError:
            output_fn("Enter a number from the list.")
            continue
        if 1 <= selected <= len(options):
            return options[selected - 1]
        output_fn("Enter a number from the list.")


def choose_repository(input_fn: InputFn = input) -> Repository:
    repositories = list_repositories()
    with_prs: list[Repository] = []
    for repo in repositories:
        try:
            if list_open_prs(repo.name_with_owner):
                with_prs.append(repo)
        except GitHubError:
            continue

    choices = tuple(with_prs or repositories)
    return choose(
        choices,
        "repository",
        lambda item: f"{item.name_with_owner} ({item.visibility.lower()})",
        input_fn,
    )


def choose_pr(repo: str, input_fn: InputFn = input) -> PullRequest:
    prs = list_open_prs(repo)
    return choose(
        prs,
        "open pull request",
        lambda item: f"#{item.number} {item.title} (+{item.additions}/-{item.deletions}, {item.changed_files} files)",
        input_fn,
    )


def prompt_concerns(input_fn: InputFn = input, output_fn: OutputFn = print) -> str:
    output_fn("")
    output_fn("Add concerns or context for Tripwire. Press Enter to skip.")
    return input_fn("> ").strip()
