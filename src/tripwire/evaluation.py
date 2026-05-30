from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .doctrine import load_doctrine
from .models import ReviewInput, ReviewMode
from .reviewer import review


@dataclass(frozen=True)
class EvalCase:
    name: str
    mode: ReviewMode
    diff: str
    repository_context: str
    source_description: str
    must_contain: tuple[str, ...]
    must_contain_any: tuple[tuple[str, ...], ...]
    must_not_contain: tuple[str, ...]


@dataclass(frozen=True)
class EvalResult:
    case: EvalCase
    passed: bool
    missing: tuple[str, ...]
    forbidden: tuple[str, ...]
    output: str


def load_cases(fixtures_dir: Path) -> tuple[EvalCase, ...]:
    cases: list[EvalCase] = []
    for path in sorted(fixtures_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cases.append(
            EvalCase(
                name=data["name"],
                mode=ReviewMode(data.get("mode", ReviewMode.STANDARD.value)),
                diff=data["diff"],
                repository_context=data.get("repository_context", ""),
                source_description=data.get("source_description", f"Eval fixture: {path.name}"),
                must_contain=tuple(data.get("must_contain", ())),
                must_contain_any=tuple(tuple(group) for group in data.get("must_contain_any", ())),
                must_not_contain=tuple(data.get("must_not_contain", ())),
            )
        )
    return tuple(cases)


def run_eval(
    root: Path,
    fixtures_dir: Path,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[EvalResult, ...]:
    doctrine = load_doctrine(root)
    results: list[EvalResult] = []
    for case in load_cases(fixtures_dir):
        review_input = ReviewInput(
            mode=case.mode,
            diff=case.diff,
            doctrine=doctrine,
            repository_context=case.repository_context,
            source_description=case.source_description,
        )
        output = review(review_input, provider=provider, model=model)
        missing_terms = [term for term in case.must_contain if term not in output]
        missing_groups = [
            " or ".join(group)
            for group in case.must_contain_any
            if not any(term in output for term in group)
        ]
        missing = tuple([*missing_terms, *missing_groups])
        forbidden = tuple(term for term in case.must_not_contain if term in output)
        results.append(
            EvalResult(
                case=case,
                passed=not missing and not forbidden,
                missing=missing,
                forbidden=forbidden,
                output=output,
            )
        )
    return tuple(results)


def render_eval_results(results: tuple[EvalResult, ...], *, show_output: bool = False) -> str:
    passed_count = sum(1 for result in results if result.passed)
    lines = [
        "Tripwire eval",
        "",
        f"Passed {passed_count}/{len(results)} cases.",
    ]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(["", f"[{status}] {result.case.name}"])
        if result.missing:
            lines.append(f"  Missing: {', '.join(result.missing)}")
        if result.forbidden:
            lines.append(f"  Forbidden: {', '.join(result.forbidden)}")
        if show_output:
            lines.extend(["", result.output.strip()])

    return "\n".join(lines)
