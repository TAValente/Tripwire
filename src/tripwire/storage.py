from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict

from .github import PullRequest
from .models import DoctrineDocument, Finding


class StorageError(RuntimeError):
    pass


class SupabaseStore:
    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = (url or os.environ.get("SUPABASE_URL") or "").rstrip("/")
        self.key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or ""
        if not self.url or not self.key:
            raise StorageError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to store Tripwire reviews.")

    def _request(self, method: str, path: str, payload: object | None = None) -> object:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.url}/rest/v1/{path}",
            data=body,
            method=method,
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation,resolution=merge-duplicates",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise StorageError(f"Supabase request failed: HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise StorageError(f"Supabase request failed: {exc}") from exc
        return json.loads(text) if text else None

    def upsert_project(
        self,
        repo: str,
        *,
        default_branch: str,
        doctrine: tuple[DoctrineDocument, ...],
    ) -> str:
        owner, name = repo.split("/", 1)
        rows = self._request(
            "POST",
            "tripwire_projects?on_conflict=github_owner,github_repo",
            [
                {
                    "github_owner": owner,
                    "github_repo": name,
                    "default_branch": default_branch,
                    "doctrine_snapshot": [asdict(document) for document in doctrine],
                }
            ],
        )
        return rows[0]["id"]  # type: ignore[index]

    def upsert_pull_request(self, project_id: str, pr: PullRequest, *, state: str = "open") -> str:
        rows = self._request(
            "POST",
            "tripwire_pull_requests?on_conflict=project_id,github_pr_number",
            [
                {
                    "project_id": project_id,
                    "github_pr_number": pr.number,
                    "title": pr.title,
                    "author_login": pr.author,
                    "base_branch": pr.base_ref,
                    "head_branch": pr.head_ref,
                    "state": state,
                    "url": pr.url,
                }
            ],
        )
        return rows[0]["id"]  # type: ignore[index]

    def create_review_run(
        self,
        pull_request_id: str,
        *,
        trigger: str,
        provider: str | None,
        model: str | None,
        user_concerns: str,
        doctrine: tuple[DoctrineDocument, ...],
        diff_summary: dict[str, object],
        output_text: str,
    ) -> str:
        rows = self._request(
            "POST",
            "tripwire_review_runs",
            [
                {
                    "pull_request_id": pull_request_id,
                    "trigger": trigger,
                    "provider": provider,
                    "model": model,
                    "user_concerns": user_concerns,
                    "doctrine_snapshot": [asdict(document) for document in doctrine],
                    "diff_summary": diff_summary,
                    "output_text": output_text,
                }
            ],
        )
        return rows[0]["id"]  # type: ignore[index]

    def create_findings(self, review_run_id: str, findings: list[Finding]) -> None:
        if not findings:
            return
        self._request(
            "POST",
            "tripwire_findings",
            [
                {
                    "review_run_id": review_run_id,
                    "stable_key": finding.stable_key(),
                    "finding_type": "mistake",
                    "title": finding.title,
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "category": finding.category,
                    "persona": finding.reviewer_persona,
                    "evidence": finding.evidence,
                    "why_it_matters": finding.why_it_matters,
                    "recommended_action": finding.recommended_action,
                    "acceptable_for_current_phase": finding.acceptable_for_current_phase,
                }
                for finding in findings
            ],
        )


def quote_filter(value: str) -> str:
    return urllib.parse.quote(value, safe="")
