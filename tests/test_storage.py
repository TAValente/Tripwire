import tempfile
import unittest
from pathlib import Path

from tripwire.models import Finding
from tripwire.github import PullRequest
from tripwire.models import DoctrineDocument
from tripwire.storage import LocalStore, review_output_summary


class StorageModelTests(unittest.TestCase):
    def test_finding_stable_key_is_stable(self):
        finding = Finding(
            title="Token Cost Increased",
            severity=3,
            confidence="High",
            category="Economics Regression",
            reviewer_persona="Economics Watchdog",
            evidence="Prompt adds static guide.",
            why_it_matters="More tokens per request.",
            acceptable_for_current_phase="Questionable",
            recommended_action="Send only selected plan guidance.",
        )

        self.assertEqual(finding.stable_key(), finding.stable_key())
        self.assertEqual(len(finding.stable_key()), 16)

    def test_local_store_persists_review_run(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalStore(Path(directory) / "tripwire.db")
            pr = PullRequest(
                repo="TAValente/Tripwire",
                number=1,
                title="Test PR",
                body="",
                url="https://github.com/TAValente/Tripwire/pull/1",
                author="TAValente",
                head_ref="feature",
                base_ref="main",
                additions=1,
                deletions=0,
                changed_files=1,
            )

            project_id = store.upsert_project(
                "TAValente/Tripwire",
                default_branch="main",
                doctrine=(DoctrineDocument("docs/principles.md", "Test"),),
            )
            pull_request_id = store.upsert_pull_request(project_id, pr)
            review_run_id = store.create_review_run(
                pull_request_id,
                trigger="manual",
                provider=None,
                model=None,
                user_concerns="",
                doctrine=(),
                diff_summary={"changed_files": 1},
                output_text="No high-confidence strategic findings detected.",
            )
            store.create_findings(review_run_id, [])
            store.set_review_run_outcome(review_run_id, "false_positive", "AI-adjacent files, no new model call.")
            stats = store.stats()
            outcome = store.connection.execute(
                "select outcome_state, outcome_note from tripwire_review_runs where id = ?",
                (review_run_id,),
            ).fetchone()
            recent_outcomes = store.recent_review_outcomes("TAValente/Tripwire")
            recent_runs = store.recent_review_runs()
            reopened = store.review_run_output(review_run_id)
            store.close()

        self.assertEqual(stats["counts"]["tripwire_projects"], 1)
        self.assertEqual(stats["counts"]["tripwire_review_runs"], 1)
        self.assertEqual(outcome[0], "false_positive")
        self.assertIn("AI-adjacent", outcome[1])
        self.assertEqual(recent_outcomes[0]["outcome_state"], "false_positive")
        self.assertEqual(recent_outcomes[0]["pr_number"], "1")
        self.assertEqual(recent_runs[0]["id"], review_run_id)
        self.assertEqual(recent_runs[0]["repo"], "TAValente/Tripwire")
        self.assertFalse(recent_runs[0]["has_suppressed_finding"])
        self.assertEqual(reopened["output"], "No high-confidence strategic findings detected.")

    def test_review_output_summary_prefers_finding_title(self):
        output = "Mistakes to Correct\n\nTitle: Real Strategic Issue\n\nWhy: It matters."

        self.assertEqual(review_output_summary(output), "Real Strategic Issue")

    def test_review_output_summary_handles_no_findings(self):
        self.assertEqual(
            review_output_summary("No high-confidence strategic findings detected.\n\nSuppressed Finding"),
            "No high-confidence strategic findings detected.",
        )


if __name__ == "__main__":
    unittest.main()
