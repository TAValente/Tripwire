import unittest
from unittest.mock import patch

from tripwire.github import GitHubError, PullRequest, build_pr_review_input, gh_executable, run_gh
from tripwire.models import DoctrineDocument


class GitHubReviewInputTests(unittest.TestCase):
    def test_build_pr_review_input_includes_metadata_and_concerns(self):
        pr = PullRequest(
            repo="TAValente/Tripwire",
            number=12,
            title="Add review-pr command",
            body="Adds direct GitHub PR review.",
            url="https://github.com/TAValente/Tripwire/pull/12",
            author="TAValente",
            head_ref="feature",
            base_ref="main",
            additions=10,
            deletions=2,
            changed_files=3,
        )

        review_input = build_pr_review_input(
            pr,
            "+from fastapi import FastAPI",
            (DoctrineDocument("docs/principles.md", "Challenge assumptions."),),
            concerns="Watch model costs.",
        )

        self.assertIn("Pull request: #12", review_input.repository_context)
        self.assertIn("Add review-pr command", review_input.source_description)
        self.assertEqual(review_input.user_concerns, "Watch model costs.")
        self.assertEqual(review_input.doctrine[0].path, "docs/principles.md")

    @patch("tripwire.github.shutil.which", return_value=None)
    @patch("tripwire.github.Path.exists", return_value=False)
    def test_run_gh_reports_missing_cli_cleanly(self, _exists, _which):
        with self.assertRaises(GitHubError) as context:
            run_gh(["pr", "view", "1"])

        self.assertIn("GitHub CLI (`gh`) was not found", str(context.exception))
        self.assertIn("gh auth login", str(context.exception))

    @patch("tripwire.github.shutil.which", return_value=None)
    @patch("tripwire.github.Path.exists", return_value=True)
    def test_gh_executable_falls_back_to_standard_windows_path(self, _exists, _which):
        self.assertEqual(gh_executable(), "C:\\Program Files\\GitHub CLI\\gh.exe")


if __name__ == "__main__":
    unittest.main()
