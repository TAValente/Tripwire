from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from .github import PullRequest
from .models import DoctrineDocument, Finding


class StorageError(RuntimeError):
    pass


VALID_OUTCOME_STATES = (
    "useful",
    "false_positive",
    "not_worth_blocking",
    "accepted_risk",
    "fixed_before_merge",
    "needs_followup",
)


SQLITE_SCHEMA = """
create table if not exists tripwire_projects (
  id text primary key,
  github_owner text not null,
  github_repo text not null,
  default_branch text,
  doctrine_snapshot text not null default '[]',
  created_at text not null default current_timestamp,
  updated_at text not null default current_timestamp,
  unique (github_owner, github_repo)
);

create table if not exists tripwire_pull_requests (
  id text primary key,
  project_id text not null references tripwire_projects(id) on delete cascade,
  github_pr_number integer not null,
  title text not null default '',
  author_login text not null default '',
  base_branch text not null default '',
  head_branch text not null default '',
  state text not null default 'open',
  url text not null default '',
  last_seen_head_sha text,
  created_at text not null default current_timestamp,
  updated_at text not null default current_timestamp,
  merged_at text,
  unique (project_id, github_pr_number)
);

create table if not exists tripwire_review_runs (
  id text primary key,
  pull_request_id text references tripwire_pull_requests(id) on delete cascade,
  trigger text not null default 'manual',
  provider text,
  model text,
  prompt_version text not null default 'concise-v1',
  user_concerns text not null default '',
  doctrine_snapshot text not null default '[]',
  diff_summary text not null default '{}',
  output_text text not null default '',
  inferred_signal text,
  outcome_state text,
  outcome_note text not null default '',
  created_at text not null default current_timestamp
);

create table if not exists tripwire_findings (
  id text primary key,
  review_run_id text not null references tripwire_review_runs(id) on delete cascade,
  stable_key text not null,
  finding_type text not null default 'mistake',
  title text not null,
  severity integer,
  confidence text,
  category text,
  persona text,
  evidence text not null default '',
  why_it_matters text not null default '',
  recommended_action text not null default '',
  acceptable_for_current_phase text,
  status text not null default 'open',
  value_score real,
  created_at text not null default current_timestamp,
  resolved_at text
);

create table if not exists tripwire_finding_events (
  id text primary key,
  finding_id text not null references tripwire_findings(id) on delete cascade,
  event_type text not null,
  github_comment_url text,
  evidence_snapshot text,
  rationale text,
  created_at text not null default current_timestamp
);

create table if not exists tripwire_project_memory (
  id text primary key,
  project_id text not null references tripwire_projects(id) on delete cascade,
  memory text not null default '{}',
  created_at text not null default current_timestamp,
  updated_at text not null default current_timestamp,
  unique (project_id)
);

create table if not exists tripwire_author_memory (
  id text primary key,
  author_login text not null unique,
  memory text not null default '{}',
  created_at text not null default current_timestamp,
  updated_at text not null default current_timestamp
);

create index if not exists tripwire_findings_stable_key_idx on tripwire_findings(stable_key);
create index if not exists tripwire_review_runs_created_at_idx on tripwire_review_runs(created_at desc);
"""


class LocalStore:
    def __init__(self, db_path: Path | str | None = None):
        raw_path = db_path or os.environ.get("TRIPWIRE_DB_PATH") or Path.cwd() / ".tripwire" / "tripwire.db"
        self.db_path = Path(raw_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("pragma foreign_keys = on")
        self.connection.executescript(SQLITE_SCHEMA)
        self._ensure_pull_request_columns()
        self._ensure_review_run_columns()
        self.connection.commit()

    def _ensure_pull_request_columns(self) -> None:
        existing_columns = {
            row[1]
            for row in self.connection.execute("pragma table_info(tripwire_pull_requests)").fetchall()
        }
        columns = {
            "last_seen_head_sha": "text",
            "merged_at": "text",
        }
        for column, definition in columns.items():
            if column not in existing_columns:
                self.connection.execute(f"alter table tripwire_pull_requests add column {column} {definition}")

    def _ensure_review_run_columns(self) -> None:
        existing_columns = {
            row[1]
            for row in self.connection.execute("pragma table_info(tripwire_review_runs)").fetchall()
        }
        columns = {
            "inferred_signal": "text",
            "outcome_state": "text",
            "outcome_note": "text not null default ''",
        }
        for column, definition in columns.items():
            if column not in existing_columns:
                self.connection.execute(f"alter table tripwire_review_runs add column {column} {definition}")

    def close(self) -> None:
        self.connection.close()

    def upsert_project(
        self,
        repo: str,
        *,
        default_branch: str,
        doctrine: tuple[DoctrineDocument, ...],
    ) -> str:
        owner, name = repo.split("/", 1)
        existing = self.connection.execute(
            "select id from tripwire_projects where github_owner = ? and github_repo = ?",
            (owner, name),
        ).fetchone()
        project_id = existing[0] if existing else str(uuid4())
        self.connection.execute(
            """
            insert into tripwire_projects (id, github_owner, github_repo, default_branch, doctrine_snapshot, updated_at)
            values (?, ?, ?, ?, ?, current_timestamp)
            on conflict(github_owner, github_repo) do update set
              default_branch = excluded.default_branch,
              doctrine_snapshot = excluded.doctrine_snapshot,
              updated_at = current_timestamp
            """,
            (project_id, owner, name, default_branch, json.dumps([asdict(document) for document in doctrine])),
        )
        self.connection.commit()
        return project_id

    def upsert_pull_request(self, project_id: str, pr: PullRequest, *, state: str | None = None) -> str:
        existing = self.connection.execute(
            "select id from tripwire_pull_requests where project_id = ? and github_pr_number = ?",
            (project_id, pr.number),
        ).fetchone()
        pull_request_id = existing[0] if existing else str(uuid4())
        self.connection.execute(
            """
            insert into tripwire_pull_requests (
              id, project_id, github_pr_number, title, author_login, base_branch, head_branch, state, url,
              last_seen_head_sha, merged_at, updated_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp)
            on conflict(project_id, github_pr_number) do update set
              title = excluded.title,
              author_login = excluded.author_login,
              base_branch = excluded.base_branch,
              head_branch = excluded.head_branch,
              state = excluded.state,
              url = excluded.url,
              last_seen_head_sha = excluded.last_seen_head_sha,
              merged_at = excluded.merged_at,
              updated_at = current_timestamp
            """,
            (
                pull_request_id,
                project_id,
                pr.number,
                pr.title,
                pr.author,
                pr.base_ref,
                pr.head_ref,
                state or pr.state.lower() or "open",
                pr.url,
                pr.head_sha,
                pr.merged_at,
            ),
        )
        self.connection.commit()
        return pull_request_id

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
        inferred_signal: str | None = None,
    ) -> str:
        review_run_id = str(uuid4())
        self.connection.execute(
            """
            insert into tripwire_review_runs (
              id, pull_request_id, trigger, provider, model, user_concerns, doctrine_snapshot, diff_summary,
              output_text, inferred_signal
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_run_id,
                pull_request_id,
                trigger,
                provider,
                model,
                user_concerns,
                json.dumps([asdict(document) for document in doctrine]),
                json.dumps(diff_summary),
                output_text,
                inferred_signal,
            ),
        )
        self.connection.commit()
        return review_run_id

    def set_review_run_outcome(self, review_run_id: str, outcome_state: str, outcome_note: str = "") -> None:
        result = self.connection.execute(
            """
            update tripwire_review_runs
            set outcome_state = ?,
                outcome_note = ?,
                inferred_signal = coalesce(inferred_signal, 'review_stored_no_feedback')
            where id = ?
            """,
            (outcome_state, outcome_note, review_run_id),
        )
        self.connection.commit()
        if result.rowcount == 0:
            raise StorageError(f"Unknown Tripwire review run: {review_run_id}")

    def recent_review_outcomes(self, repo: str, limit: int = 5) -> list[dict[str, str]]:
        owner, name = repo.split("/", 1)
        rows = self.connection.execute(
            """
            select
              runs.id,
              runs.outcome_state,
              runs.outcome_note,
              runs.inferred_signal,
              prs.github_pr_number,
              prs.title
            from tripwire_review_runs runs
            join tripwire_pull_requests prs on prs.id = runs.pull_request_id
            join tripwire_projects projects on projects.id = prs.project_id
            where projects.github_owner = ?
              and projects.github_repo = ?
              and (
                runs.outcome_state is not null
                or runs.inferred_signal in (
                  'pr_updated_after_finding_no_current_finding',
                  'pr_updated_after_suppressed_finding_no_current_finding',
                  'pr_updated_after_suppressed_finding_now_finding'
                )
              )
            order by runs.created_at desc
            limit ?
            """,
            (owner, name, limit),
        ).fetchall()
        return [
            {
                "id": str(row[0]),
                "outcome_state": row[1] or "",
                "outcome_note": row[2] or "",
                "inferred_signal": row[3] or "",
                "pr_number": str(row[4]),
                "pr_title": row[5] or "",
            }
            for row in rows
        ]

    def recent_review_runs(self, limit: int = 10) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            select
              runs.id,
              runs.created_at,
              runs.output_text,
              runs.outcome_state,
              runs.inferred_signal,
              runs.outcome_note,
              prs.github_pr_number,
              prs.title,
              projects.github_owner || '/' || projects.github_repo as repo
            from tripwire_review_runs runs
            left join tripwire_pull_requests prs on prs.id = runs.pull_request_id
            left join tripwire_projects projects on projects.id = prs.project_id
            order by runs.created_at desc
            limit ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": str(row[0]),
                "created_at": row[1] or "",
                "summary": review_output_summary(row[2] or ""),
                "has_suppressed_finding": "Suppressed Finding" in (row[2] or ""),
                "outcome_state": row[3] or "",
                "inferred_signal": row[4] or "",
                "outcome_note": row[5] or "",
                "pr_number": str(row[6] or ""),
                "pr_title": row[7] or "",
                "repo": row[8] or "",
            }
            for row in rows
        ]

    def previous_pr_review_runs(self, pull_request_id: str, *, exclude_run_id: str) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            select id, output_text, diff_summary, inferred_signal, outcome_state
            from tripwire_review_runs
            where pull_request_id = ?
              and id <> ?
              and outcome_state is null
            order by created_at desc
            """,
            (pull_request_id, exclude_run_id),
        ).fetchall()
        previous: list[dict[str, object]] = []
        for row in rows:
            try:
                diff_summary = json.loads(row[2] or "{}")
            except json.JSONDecodeError:
                diff_summary = {}
            previous.append(
                {
                    "id": str(row[0]),
                    "output_text": row[1] or "",
                    "diff_summary": diff_summary,
                    "inferred_signal": row[3] or "",
                    "outcome_state": row[4] or "",
                }
            )
        return previous

    def set_review_run_inferred_signal(self, review_run_id: str, inferred_signal: str) -> None:
        self.connection.execute(
            """
            update tripwire_review_runs
            set inferred_signal = ?
            where id = ?
            """,
            (inferred_signal, review_run_id),
        )
        self.connection.commit()

    def review_run_output(self, review_run_id: str) -> dict[str, str]:
        row = self.connection.execute(
            """
            select
              runs.id,
              runs.created_at,
              runs.output_text,
              runs.outcome_state,
              runs.inferred_signal,
              runs.outcome_note,
              prs.github_pr_number,
              prs.title,
              projects.github_owner || '/' || projects.github_repo as repo
            from tripwire_review_runs runs
            left join tripwire_pull_requests prs on prs.id = runs.pull_request_id
            left join tripwire_projects projects on projects.id = prs.project_id
            where runs.id = ?
            """,
            (review_run_id,),
        ).fetchone()
        if row is None:
            raise StorageError(f"Unknown Tripwire review run: {review_run_id}")
        return {
            "id": str(row[0]),
            "created_at": row[1] or "",
            "output": row[2] or "",
            "outcome_state": row[3] or "",
            "inferred_signal": row[4] or "",
            "outcome_note": row[5] or "",
            "pr_number": str(row[6] or ""),
            "pr_title": row[7] or "",
            "repo": row[8] or "",
        }

    def create_findings(self, review_run_id: str, findings: list[Finding]) -> None:
        if not findings:
            return
        self.connection.executemany(
            """
            insert into tripwire_findings (
              id, review_run_id, stable_key, finding_type, title, severity, confidence, category,
              persona, evidence, why_it_matters, recommended_action, acceptable_for_current_phase
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(uuid4()),
                    review_run_id,
                    finding.stable_key(),
                    "mistake",
                    finding.title,
                    finding.severity,
                    finding.confidence,
                    finding.category,
                    finding.reviewer_persona,
                    finding.evidence,
                    finding.why_it_matters,
                    finding.recommended_action,
                    finding.acceptable_for_current_phase,
                )
                for finding in findings
            ],
        )
        self.connection.commit()

    def stats(self) -> dict[str, object]:
        tables = (
            "tripwire_projects",
            "tripwire_pull_requests",
            "tripwire_review_runs",
            "tripwire_findings",
            "tripwire_finding_events",
            "tripwire_project_memory",
            "tripwire_author_memory",
        )
        counts = {
            table: self.connection.execute(f"select count(*) from {table}").fetchone()[0]
            for table in tables
        }
        return {
            "backend": "sqlite",
            "path": str(self.db_path),
            "size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
            "counts": counts,
        }


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
                    "last_seen_head_sha": pr.head_sha,
                    "merged_at": pr.merged_at,
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
        inferred_signal: str | None = None,
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
                    "inferred_signal": inferred_signal,
                }
            ],
        )
        return rows[0]["id"]  # type: ignore[index]

    def set_review_run_outcome(self, review_run_id: str, outcome_state: str, outcome_note: str = "") -> None:
        self._request(
            "PATCH",
            f"tripwire_review_runs?id=eq.{quote_filter(review_run_id)}",
            {
                "outcome_state": outcome_state,
                "outcome_note": outcome_note,
                "inferred_signal": "review_stored_no_feedback",
            },
        )

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

    def previous_pr_review_runs(self, pull_request_id: str, *, exclude_run_id: str) -> list[dict[str, object]]:
        return []

    def set_review_run_inferred_signal(self, review_run_id: str, inferred_signal: str) -> None:
        self._request(
            "PATCH",
            f"tripwire_review_runs?id=eq.{quote_filter(review_run_id)}",
            {"inferred_signal": inferred_signal},
        )


def quote_filter(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def review_output_summary(output: str) -> str:
    text = output.strip()
    if not text:
        return "No output stored."
    if text.startswith("No high-confidence strategic findings detected."):
        return "No high-confidence strategic findings detected."
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Title:"):
            return stripped.removeprefix("Title:").strip()
    first_line = text.splitlines()[0].strip()
    return first_line[:120]


def create_store() -> LocalStore | SupabaseStore:
    backend = os.environ.get("TRIPWIRE_STORE", "local").strip().lower()
    if backend in {"", "local", "sqlite"}:
        return LocalStore()
    if backend == "supabase":
        return SupabaseStore()
    raise StorageError("TRIPWIRE_STORE must be 'local' or 'supabase'.")
