import unittest
from unittest.mock import patch

from tripwire.github import (
    GitHubError,
    PullRequest,
    Repository,
    build_pr_review_input,
    fetch_project_scan_input,
    gh_executable,
    run_gh,
    select_scan_paths,
)
from tripwire.models import DoctrineDocument, ReviewMode


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
            repository=Repository(
                name_with_owner="TAValente/Tripwire",
                url="https://github.com/TAValente/Tripwire",
                visibility="PRIVATE",
                description="Project consistency checker",
                default_branch="main",
                primary_language="Python",
            ),
        )

        self.assertIn("Pull request: #12", review_input.repository_context)
        self.assertIn("Repository primary language: Python", review_input.repository_context)
        self.assertIn("Repository description: Project consistency checker", review_input.repository_context)
        self.assertIn("Add review-pr command", review_input.source_description)
        self.assertEqual(review_input.user_concerns, "Watch model costs.")
        self.assertEqual(review_input.doctrine[0].path, "docs/principles.md")

    def test_select_scan_paths_prioritizes_doctrine_and_project_files(self):
        paths = select_scan_paths(
            (
                "src/app.py",
                "docs/principles.md",
                "README.md",
                "package.json",
                "assets/logo.png",
            ),
            limit=3,
        )

        self.assertEqual(paths, ("docs/principles.md", "README.md", "package.json"))

    @patch("tripwire.github.fetch_remote_tree_paths", return_value=("README.md", "docs/principles.md", "src/app.py"))
    @patch("tripwire.github.fetch_remote_readme", return_value=("README.md", "Tangent readme"))
    @patch(
        "tripwire.github.fetch_remote_doctrine",
        return_value=(DoctrineDocument("docs/principles.md", "Stay coherent."),),
    )
    @patch(
        "tripwire.github.fetch_repository",
        return_value=Repository(
            name_with_owner="TAValente/Tangent",
            url="https://github.com/TAValente/Tangent",
            visibility="PRIVATE",
            description="Scratchpad",
            default_branch="main",
            primary_language="TypeScript",
        ),
    )
    def test_fetch_project_scan_input_includes_remote_evidence(
        self,
        _repo,
        _doctrine,
        _readme,
        _tree,
    ):
        review_input = fetch_project_scan_input("TAValente/Tangent")

        self.assertEqual(review_input.mode, ReviewMode.PROJECT_SCAN)
        self.assertIn("GitHub repository: TAValente/Tangent", review_input.repository_context)
        self.assertIn("Doctrine sufficiency", review_input.repository_context)
        self.assertIn("Tangent readme", review_input.repository_context)
        self.assertIn("- src/app.py", review_input.repository_context)
        self.assertIn("Project scan for TAValente/Tangent@main", review_input.source_description)

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
