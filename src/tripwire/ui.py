from __future__ import annotations

import argparse
import json
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .cli import attach_review_feedback, mark_missing_target_doctrine, render_memory_stats, store_pr_review
from .doctor import render_doctor
from .doctrine import load_doctrine, render_doctrine_completeness, render_doctrine_sufficiency
from .github import GitHubError, fetch_pr_review_input, fetch_project_scan_input, list_open_prs, list_repositories
from .models import ReviewInput, ReviewMode
from .reviewer import review as run_review
from .storage import StorageError, VALID_OUTCOME_STATES, create_store


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tripwire</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f4;
      --panel: #ffffff;
      --line: #d7ddd2;
      --text: #1f2520;
      --muted: #667063;
      --accent: #236f5b;
      --accent-strong: #174b3f;
      --warn: #9c6120;
      --bad: #9c2f2f;
      --code: #111714;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: #fbfcf8;
    }
    .wrap {
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
    }
    .top {
      min-height: 68px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1, h2 {
      margin: 0;
      letter-spacing: 0;
    }
    h1 {
      font-size: 22px;
      line-height: 1.1;
      font-weight: 750;
    }
    h2 {
      font-size: 15px;
      font-weight: 720;
    }
    .meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
      color: var(--muted);
      font-size: 12px;
    }
    main {
      padding: 20px 0 28px;
    }
    .grid {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 16px;
      align-items: start;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .stack { display: grid; gap: 12px; }
    .row {
      display: flex;
      gap: 8px;
      align-items: end;
      flex-wrap: wrap;
    }
    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
    }
    input, textarea, select {
      width: 100%;
      min-height: 36px;
      border: 1px solid #c8d0c2;
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 8px 10px;
      font: inherit;
    }
    textarea {
      min-height: 74px;
      resize: vertical;
    }
    button {
      min-height: 36px;
      border: 1px solid #b9c5b3;
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 8px 11px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }
    button:disabled {
      cursor: wait;
      opacity: .65;
    }
    button.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(35, 111, 91, .14);
    }
    .full { flex: 1 1 100%; }
    .grow { flex: 1 1 180px; }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text);
      font-size: 13px;
      font-weight: 650;
    }
    .check input {
      width: 16px;
      min-height: 16px;
    }
    .list {
      display: grid;
      gap: 8px;
    }
    .pr {
      width: 100%;
      text-align: left;
      display: grid;
      gap: 4px;
      border-color: var(--line);
      background: #fbfcf8;
    }
    .pr.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(35, 111, 91, .12);
    }
    .pr-title {
      font-weight: 750;
      overflow-wrap: anywhere;
    }
    .pr-sub {
      color: var(--muted);
      font-size: 12px;
    }
    .history {
      display: grid;
      gap: 8px;
      max-height: 300px;
      overflow: auto;
    }
    .history-item {
      width: 100%;
      text-align: left;
      display: grid;
      gap: 4px;
      background: #fbfcf8;
      border-color: var(--line);
    }
    .history-title {
      font-weight: 750;
      overflow-wrap: anywhere;
    }
    .history-sub {
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    pre {
      margin: 0;
      min-height: 420px;
      max-height: calc(100vh - 190px);
      overflow: auto;
      background: var(--code);
      color: #eef6ee;
      border-radius: 8px;
      padding: 14px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: 13px/1.5 ui-monospace, "Cascadia Code", Consolas, monospace;
    }
    .status {
      min-height: 20px;
      color: var(--muted);
      font-size: 12px;
    }
    .status.bad { color: var(--bad); }
    .status.warn { color: var(--warn); }
    .status.good { color: var(--accent-strong); font-weight: 750; }
    .outcome {
      display: grid;
      gap: 10px;
      padding-top: 2px;
    }
    .outcome[hidden] {
      display: none;
    }
    @media (max-width: 820px) {
      .grid { grid-template-columns: 1fr; }
      .top { align-items: flex-start; flex-direction: column; padding: 16px 0; }
      .meta { justify-content: flex-start; }
      pre { max-height: none; min-height: 320px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap top">
      <h1>Tripwire</h1>
      <div class="meta">
        <span id="modelMeta"></span>
        <span>local</span>
      </div>
    </div>
  </header>
  <main class="wrap grid">
    <div class="stack">
      <section class="stack">
        <h2>Readiness</h2>
        <div class="row">
          <button id="doctorBtn" class="primary" type="button">Run Doctor</button>
          <button id="scanBtn" type="button">Project Scan</button>
          <button id="memoryBtn" type="button">Memory</button>
        </div>
        <div id="readyStatus" class="status"></div>
      </section>
      <section class="stack">
        <h2>GitHub PR</h2>
        <label>
          Repository
          <select id="repoInput"></select>
        </label>
        <div class="row">
          <button id="prsBtn" type="button">List Open PRs</button>
          <label class="grow">
            PR
            <input id="prInput" inputmode="numeric" placeholder="Number">
          </label>
        </div>
        <div id="prList" class="list"></div>
        <label>
          Concerns
          <textarea id="concernsInput"></textarea>
        </label>
        <label class="check">
          <input id="storeInput" type="checkbox" checked>
          Store locally
        </label>
        <button id="reviewBtn" class="primary" type="button">Review PR</button>
        <div id="reviewStatus" class="status"></div>
      </section>
      <section class="stack">
        <h2>Recent Reviews</h2>
        <div class="row">
          <button id="historyBtn" type="button">Refresh</button>
        </div>
        <div id="historyList" class="history"></div>
        <div id="historyStatus" class="status"></div>
      </section>
    </div>
    <section class="stack">
      <h2>Output</h2>
      <pre id="output">Ready.</pre>
      <div id="outcomePanel" class="outcome" hidden>
        <h2>Outcome</h2>
        <div class="row">
          <button type="button" data-outcome="useful">Useful</button>
          <button type="button" data-outcome="false_positive">False Positive</button>
          <button type="button" data-outcome="not_worth_blocking">Not Worth Blocking</button>
          <button type="button" data-outcome="accepted_risk">Accepted Risk</button>
          <button type="button" data-outcome="fixed_before_merge">Fixed Before Merge</button>
          <button type="button" data-outcome="needs_followup">Needs Followup</button>
        </div>
        <label>
          Note
          <textarea id="outcomeNote"></textarea>
        </label>
        <div id="outcomeStatus" class="status"></div>
      </div>
    </section>
  </main>
  <script>
    const config = __CONFIG__;
    const modelMeta = document.getElementById("modelMeta");
    const output = document.getElementById("output");
    const repoInput = document.getElementById("repoInput");
    const prInput = document.getElementById("prInput");
    const concernsInput = document.getElementById("concernsInput");
    const storeInput = document.getElementById("storeInput");
    const prList = document.getElementById("prList");
    const historyList = document.getElementById("historyList");
    const historyStatus = document.getElementById("historyStatus");
    const readyStatus = document.getElementById("readyStatus");
    const reviewStatus = document.getElementById("reviewStatus");
    const buttons = [...document.querySelectorAll("button")];
    const outcomePanel = document.getElementById("outcomePanel");
    const outcomeNote = document.getElementById("outcomeNote");
    const outcomeStatus = document.getElementById("outcomeStatus");
    let currentReviewRunId = "";
    const outcomeLabels = {
      useful: "Useful",
      false_positive: "False Positive",
      not_worth_blocking: "Not Worth Blocking",
      accepted_risk: "Accepted Risk",
      fixed_before_merge: "Fixed Before Merge",
      needs_followup: "Needs Followup"
    };

    if (config.defaultRepo) {
      const option = document.createElement("option");
      option.value = config.defaultRepo;
      option.textContent = config.defaultRepo;
      repoInput.appendChild(option);
      repoInput.value = config.defaultRepo;
    }
    modelMeta.textContent = [config.provider, config.model].filter(Boolean).join(" / ") || "local checks";

    function setBusy(isBusy) {
      buttons.forEach((button) => button.disabled = isBusy);
    }

    function show(text) {
      output.textContent = text || "";
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      return data;
    }

    document.getElementById("doctorBtn").addEventListener("click", async () => {
      readyStatus.textContent = "Checking...";
      readyStatus.className = "status";
      setBusy(true);
      try {
        const data = await api("/api/doctor");
        show(data.output);
        readyStatus.textContent = data.ready ? "Ready" : "Needs attention";
        readyStatus.className = data.ready ? "status" : "status warn";
      } catch (error) {
        readyStatus.textContent = error.message;
        readyStatus.className = "status bad";
        show(error.message);
      } finally {
        setBusy(false);
      }
    });

    async function loadRepos() {
      try {
        const data = await api("/api/repos");
        repoInput.textContent = "";
        data.repositories.forEach((repo) => {
          const option = document.createElement("option");
          option.value = repo.name_with_owner;
          option.textContent = repo.name_with_owner;
          repoInput.appendChild(option);
        });
        if (config.defaultRepo && data.repositories.some((repo) => repo.name_with_owner === config.defaultRepo)) {
          repoInput.value = config.defaultRepo;
        }
      } catch (error) {
        reviewStatus.textContent = error.message;
        reviewStatus.className = "status bad";
      }
    }

    document.getElementById("memoryBtn").addEventListener("click", async () => {
      readyStatus.textContent = "Reading memory...";
      setBusy(true);
      try {
        const data = await api("/api/memory");
        show(data.output);
        readyStatus.textContent = "Memory loaded";
        readyStatus.className = "status";
      } catch (error) {
        readyStatus.textContent = error.message;
        readyStatus.className = "status bad";
        show(error.message);
      } finally {
        setBusy(false);
      }
    });

    async function loadHistory() {
      historyStatus.textContent = "Loading...";
      historyStatus.className = "status";
      try {
        const data = await api("/api/reviews");
        historyList.textContent = "";
        if (!data.reviews.length) {
          historyList.textContent = "No stored reviews.";
        }
        data.reviews.forEach((review) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "history-item";
          const pr = review.repo && review.pr_number ? `${review.repo}#${review.pr_number}` : "Stored review";
          const outcome = review.outcome_state ? ` - ${humanize(review.outcome_state)}` : "";
          const inferred = review.inferred_signal && review.inferred_signal !== "review_stored_no_feedback" ? ` - ${humanize(review.inferred_signal)}` : "";
          const suppressed = review.has_suppressed_finding ? " - suppressed" : "";
          button.innerHTML = `<span class="history-title">${escapeHtml(pr)} ${escapeHtml(review.pr_title || "")}</span><span class="history-sub">${escapeHtml(review.summary)}${escapeHtml(outcome)}${escapeHtml(inferred)}${escapeHtml(suppressed)}</span><span class="history-sub">${escapeHtml(review.created_at)} - ${escapeHtml(review.id)}</span>`;
          button.addEventListener("click", () => openReviewRun(review.id));
          historyList.appendChild(button);
        });
        historyStatus.textContent = `${data.reviews.length} stored review${data.reviews.length === 1 ? "" : "s"}`;
      } catch (error) {
        historyStatus.textContent = error.message;
        historyStatus.className = "status bad";
      }
    }

    async function openReviewRun(id) {
      historyStatus.textContent = "Opening...";
      historyStatus.className = "status";
      setBusy(true);
      try {
        const data = await api(`/api/review-run?id=${encodeURIComponent(id)}`);
        const header = [
          `Stored review: ${data.review.repo || "unknown"}${data.review.pr_number ? "#" + data.review.pr_number : ""}`,
          `Run: ${data.review.id}`,
          `Created: ${data.review.created_at}`,
          data.review.outcome_state ? `Outcome: ${humanize(data.review.outcome_state)}` : "Outcome: none",
          data.review.inferred_signal ? `Inferred: ${data.review.inferred_signal}` : "Inferred: none",
          data.review.outcome_note ? `Note: ${data.review.outcome_note}` : ""
        ].filter(Boolean).join("\\n");
        show(`${header}\\n\\n${data.review.output}`);
        currentReviewRunId = data.review.id;
        outcomePanel.hidden = false;
        outcomeNote.value = data.review.outcome_note || "";
        outcomePanel.querySelectorAll("button[data-outcome]").forEach((button) => {
          button.classList.toggle("active", button.dataset.outcome === data.review.outcome_state);
        });
        outcomeStatus.textContent = data.review.outcome_state ? `Feedback logged: ${humanize(data.review.outcome_state)}` : "Stored review awaiting feedback";
        outcomeStatus.className = data.review.outcome_state ? "status good" : "status";
        historyStatus.textContent = "Opened";
      } catch (error) {
        historyStatus.textContent = error.message;
        historyStatus.className = "status bad";
      } finally {
        setBusy(false);
      }
    }

    document.getElementById("historyBtn").addEventListener("click", () => {
      loadHistory();
    });

    document.getElementById("scanBtn").addEventListener("click", async () => {
      const repo = repoInput.value.trim();
      readyStatus.textContent = "Scanning...";
      readyStatus.className = "status";
      show(`Running project scan${repo ? " for " + repo : ""}...`);
      setBusy(true);
      try {
        const path = repo ? `/api/scan?repo=${encodeURIComponent(repo)}` : "/api/scan";
        const data = await api(path);
        show([
          data.sourceDescription || "Project scan",
          `Doctrine docs: ${(data.doctrineDocs || []).length}`,
          data.doctrineSufficiency || "",
          "",
          data.output
        ].join("\\n"));
        readyStatus.textContent = "Scan complete";
        readyStatus.className = "status";
      } catch (error) {
        readyStatus.textContent = error.message;
        readyStatus.className = "status bad";
        show(error.message);
      } finally {
        setBusy(false);
      }
    });

    document.getElementById("prsBtn").addEventListener("click", async () => {
      const repo = repoInput.value.trim();
      prList.textContent = "";
      reviewStatus.textContent = "Loading PRs...";
      reviewStatus.className = "status";
      setBusy(true);
      try {
        const data = await api(`/api/prs?repo=${encodeURIComponent(repo)}`);
        if (!data.prs.length) {
          prList.textContent = "No open PRs.";
        }
        data.prs.forEach((pr) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "pr";
          button.innerHTML = `<span class="pr-title">#${pr.number} ${escapeHtml(pr.title)}</span><span class="pr-sub">+${pr.additions} / -${pr.deletions} · ${pr.changed_files} files · ${escapeHtml(pr.author || "unknown")}</span>`;
          button.addEventListener("click", () => {
            [...document.querySelectorAll(".pr")].forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            prInput.value = pr.number;
          });
          prList.appendChild(button);
        });
        reviewStatus.textContent = `${data.prs.length} open PR${data.prs.length === 1 ? "" : "s"}`;
      } catch (error) {
        reviewStatus.textContent = error.message;
        reviewStatus.className = "status bad";
        show(error.message);
      } finally {
        setBusy(false);
      }
    });

    document.getElementById("reviewBtn").addEventListener("click", async () => {
      reviewStatus.textContent = "Reviewing...";
      reviewStatus.className = "status";
      show("Reviewing PR...");
      setBusy(true);
      try {
        const data = await api("/api/review", {
          method: "POST",
          body: JSON.stringify({
            repo: repoInput.value.trim(),
            number: Number(prInput.value),
            concerns: concernsInput.value,
            store: storeInput.checked
          })
        });
        currentReviewRunId = data.reviewRunId || "";
        outcomePanel.hidden = !currentReviewRunId;
        outcomePanel.querySelectorAll("button[data-outcome]").forEach((button) => button.classList.remove("active"));
        outcomeNote.value = "";
        outcomeStatus.textContent = currentReviewRunId ? "Inferred: review stored, awaiting feedback" : "";
        outcomeStatus.className = "status";
        const packet = [
          `Review target: ${data.sourceDescription}`,
          `Diff size: ${data.diffBytes} bytes`,
          `Doctrine docs: ${(data.doctrineDocs || []).length}`,
          data.feedbackIncluded ? "Feedback memory: included" : "Feedback memory: none"
        ].join("\\n");
        show(packet + "\\n\\n" + data.output + (data.reviewRunId ? `\\n\\nStored Tripwire review run: ${data.reviewRunId}` : ""));
        reviewStatus.textContent = data.reviewRunId ? "Reviewed and stored" : "Reviewed";
        if (data.reviewRunId) loadHistory();
      } catch (error) {
        reviewStatus.textContent = error.message;
        reviewStatus.className = "status bad";
        show(error.message);
      } finally {
        setBusy(false);
      }
    });

    outcomePanel.addEventListener("click", async (event) => {
      const button = event.target.closest("button[data-outcome]");
      if (!button || !currentReviewRunId) return;
      outcomeStatus.textContent = "Saving...";
      outcomeStatus.className = "status";
      setBusy(true);
      try {
        const data = await api("/api/outcome", {
          method: "POST",
          body: JSON.stringify({
            reviewRunId: currentReviewRunId,
            outcome: button.dataset.outcome,
            note: outcomeNote.value
          })
        });
        outcomePanel.querySelectorAll("button[data-outcome]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        outcomeStatus.textContent = `Feedback logged: ${outcomeLabels[data.outcome] || data.outcome}`;
        outcomeStatus.className = "status good";
        show(`${output.textContent}\\n\\nFeedback logged: ${outcomeLabels[data.outcome] || data.outcome}`);
        loadHistory();
      } catch (error) {
        outcomeStatus.textContent = error.message;
        outcomeStatus.className = "status bad";
      } finally {
        setBusy(false);
      }
    });

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function humanize(value) {
      return String(value || "").replaceAll("_", " ");
    }

    loadRepos();
    loadHistory();
  </script>
</body>
</html>
"""


class UiState:
    def __init__(self, root: Path, provider: str | None, model: str | None, default_repo: str):
        self.root = root
        self.provider = provider
        self.model = model
        self.default_repo = default_repo


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object.")
    return data


def pr_to_json(pr: Any) -> dict[str, Any]:
    return {
        "repo": pr.repo,
        "number": pr.number,
        "title": pr.title,
        "url": pr.url,
        "author": pr.author,
        "head_ref": pr.head_ref,
        "base_ref": pr.base_ref,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "changed_files": pr.changed_files,
    }


def make_handler(state: UiState) -> type[BaseHTTPRequestHandler]:
    class TripwireUiHandler(BaseHTTPRequestHandler):
        server_version = "TripwireUI/0.1"

        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.send_html()
                return
            if parsed.path == "/api/doctor":
                output, ready = render_doctor(state.root, provider=state.provider, model=state.model)
                self.send_json({"ok": True, "ready": ready, "output": output})
                return
            if parsed.path == "/api/scan":
                params = parse_qs(parsed.query)
                repo = (params.get("repo") or [""])[0].strip()
                if repo:
                    try:
                        review_input = fetch_project_scan_input(repo)
                    except GitHubError as exc:
                        self.send_error_json(str(exc), HTTPStatus.BAD_GATEWAY)
                        return
                else:
                    doctrine = load_doctrine(state.root)
                    review_input = ReviewInput(
                        mode=ReviewMode.PROJECT_SCAN,
                        diff="",
                        doctrine=doctrine,
                        repository_context=render_doctrine_completeness(state.root),
                        source_description="Local project scan",
                    )
                output = run_review(review_input, provider=state.provider, model=state.model)
                self.send_json(
                    {
                        "ok": True,
                        "output": output,
                        "doctrineDocs": [document.path for document in review_input.doctrine],
                        "sourceDescription": review_input.source_description,
                        "doctrineSufficiency": render_doctrine_sufficiency(
                            review_input.doctrine,
                            source=review_input.source_description,
                        ),
                    }
                )
                return
            if parsed.path == "/api/memory":
                self.send_json({"ok": True, "output": render_memory_stats(state.root)})
                return
            if parsed.path == "/api/reviews":
                store = create_store()
                try:
                    reviews = store.recent_review_runs(limit=10)
                finally:
                    close = getattr(store, "close", None)
                    if close:
                        close()
                self.send_json({"ok": True, "reviews": reviews})
                return
            if parsed.path == "/api/review-run":
                params = parse_qs(parsed.query)
                review_run_id = (params.get("id") or [""])[0].strip()
                if not review_run_id:
                    self.send_error_json("Review run id is required.", HTTPStatus.BAD_REQUEST)
                    return
                store = create_store()
                try:
                    review = store.review_run_output(review_run_id)
                except StorageError as exc:
                    self.send_error_json(str(exc), HTTPStatus.NOT_FOUND)
                    return
                finally:
                    close = getattr(store, "close", None)
                    if close:
                        close()
                self.send_json({"ok": True, "review": review})
                return
            if parsed.path == "/api/repos":
                try:
                    repositories = [
                        {
                            "name_with_owner": repo.name_with_owner,
                            "url": repo.url,
                            "visibility": repo.visibility,
                        }
                        for repo in list_repositories(limit=100)
                    ]
                except GitHubError as exc:
                    self.send_error_json(str(exc), HTTPStatus.BAD_GATEWAY)
                    return
                self.send_json({"ok": True, "repositories": repositories})
                return
            if parsed.path == "/api/prs":
                params = parse_qs(parsed.query)
                repo = (params.get("repo") or [""])[0].strip()
                if not repo:
                    self.send_error_json("Repository is required.", HTTPStatus.BAD_REQUEST)
                    return
                try:
                    prs = [pr_to_json(pr) for pr in list_open_prs(repo)]
                except GitHubError as exc:
                    self.send_error_json(str(exc), HTTPStatus.BAD_GATEWAY)
                    return
                self.send_json({"ok": True, "prs": prs})
                return
            self.send_error_json("Not found.", HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path not in {"/api/review", "/api/outcome"}:
                self.send_error_json("Not found.", HTTPStatus.NOT_FOUND)
                return
            try:
                body = read_json_body(self)
                if parsed.path == "/api/outcome":
                    self.handle_outcome(body)
                    return
                repo = str(body.get("repo") or "").strip()
                number = int(body.get("number") or 0)
                concerns = str(body.get("concerns") or "")
                should_store = bool(body.get("store"))
                if not repo:
                    raise ValueError("Repository is required.")
                if number <= 0:
                    raise ValueError("PR number is required.")

                review_input = fetch_pr_review_input(repo, number, concerns=concerns)
                review_input = mark_missing_target_doctrine(review_input)
                review_input = attach_review_feedback(state.root, repo, review_input)
                feedback_included = "Prior Tripwire feedback for this repository:" in review_input.repository_context
                output = run_review(review_input, provider=state.provider, model=state.model)
                review_run_id = None
                if should_store:
                    review_run_id = store_pr_review(
                        repo,
                        number,
                        review_input,
                        output,
                        provider=state.provider,
                        model=state.model,
                        trigger="local-ui",
                    )
                self.send_json(
                    {
                        "ok": True,
                        "output": output,
                        "reviewRunId": review_run_id,
                        "sourceDescription": review_input.source_description,
                        "diffBytes": len(review_input.diff.encode("utf-8")),
                        "doctrineDocs": [document.path for document in review_input.doctrine],
                        "feedbackIncluded": feedback_included,
                    }
                )
            except ValueError as exc:
                self.send_error_json(str(exc), HTTPStatus.BAD_REQUEST)
            except GitHubError as exc:
                self.send_error_json(str(exc), HTTPStatus.BAD_GATEWAY)
            except StorageError as exc:
                self.send_error_json(str(exc), HTTPStatus.INTERNAL_SERVER_ERROR)

        def handle_outcome(self, body: dict[str, Any]) -> None:
            review_run_id = str(body.get("reviewRunId") or "").strip()
            outcome = str(body.get("outcome") or "").strip()
            note = str(body.get("note") or "")
            if not review_run_id:
                raise ValueError("Review run id is required.")
            if outcome not in VALID_OUTCOME_STATES:
                raise ValueError("Unknown outcome state.")
            store = create_store()
            try:
                store.set_review_run_outcome(review_run_id, outcome, note)
            finally:
                close = getattr(store, "close", None)
                if close:
                    close()
            self.send_json({"ok": True, "reviewRunId": review_run_id, "outcome": outcome})

        def send_html(self) -> None:
            config = {
                "provider": state.provider,
                "model": state.model,
                "defaultRepo": state.default_repo,
            }
            html = INDEX_HTML.replace("__CONFIG__", json.dumps(config))
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_error_json(self, message: str, status: HTTPStatus) -> None:
            self.send_json({"ok": False, "error": message}, status)

    return TripwireUiHandler


def serve_ui(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    default_repo = args.default_repo or ""
    state = UiState(root=root, provider=args.provider, model=args.model, default_repo=default_repo)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    url = f"http://{args.host}:{args.port}/"
    print(f"Tripwire local UI: {url}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTripwire local UI stopped.")
    finally:
        server.server_close()
    return 0
