import unittest

from tripwire.github import PullRequest, build_pr_review_input
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


if __name__ == "__main__":
    unittest.main()
