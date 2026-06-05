import unittest

from tripwire.models import DoctrineDocument, ReviewInput, ReviewMode
from tripwire.prompt import build_review_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_includes_doctrine_context_and_diff(self):
        review_input = ReviewInput(
            mode=ReviewMode.STANDARD,
            diff="+import openai",
            doctrine=(DoctrineDocument("docs/principles.md", "Challenge assumptions."),),
            repository_context="Git status:\n M app.py",
            source_description="Working tree git diff",
        )

        prompt = build_review_prompt(review_input)

        self.assertIn("Challenge assumptions.", prompt)
        self.assertIn("Working tree git diff", prompt)
        self.assertIn("+import openai", prompt)
        self.assertIn("Project Understanding", prompt)
        self.assertIn("Current phase, Economics, Architecture, Roadmap/decisions", prompt)
        self.assertIn("Alignment Assessment", prompt)
        self.assertIn("Direction must be one of: better, worse, unchanged, unknown", prompt)
        self.assertIn("PR Causality", prompt)
        self.assertIn("Authoritative target: Working tree git diff", prompt)
        self.assertIn("Target Facts", prompt)
        self.assertIn("Target doctrine docs found: 1", prompt)
        self.assertIn("Target doctrine doc paths: docs/principles.md", prompt)
        self.assertIn("Diff strings inside tests, mocks, fixtures, examples, or docs are not target facts", prompt)
        self.assertIn("Repository names, project names, or example strings inside tests", prompt)
        self.assertIn("Findings", prompt)
        self.assertIn("Alignment assessment is additive, not a replacement for findings", prompt)
        self.assertIn("Emergent Concerns", prompt)
        self.assertIn("Doctrine guides judgment; it does not define every possible mistake", prompt)
        self.assertIn("Emergent concerns must cite concrete evidence", prompt)
        self.assertIn("suppress generic product-management concerns", prompt)
        self.assertIn("Suppressed / Calibration", prompt)
        self.assertIn("Confidence Limits", prompt)
        self.assertIn("Coverage supports confidence; alignment is the product output", prompt)
        self.assertIn("Every finding must pass the leverage test", prompt)
        self.assertIn("author friction without a clear project payoff", prompt)
        self.assertIn("Final answer only", prompt)
        self.assertIn("Do not output hidden reasoning", prompt)
        self.assertIn("Do not collapse the whole review to a green check", prompt)
        self.assertIn("Separate unchanged from unknown", prompt)
        self.assertIn("preserve causality", prompt)
        self.assertIn("Do not flag unused functions", prompt)
        self.assertIn("caused or materially worsened by this diff", prompt)
        self.assertIn("Evidence must cite what changed", prompt)
        self.assertIn("Do not flag AI economics merely because", prompt)
        self.assertIn("calibration question", prompt)
        self.assertIn("Do not invent one", prompt)

    def test_project_scan_prompt_prioritizes_doctrine_conflicts(self):
        review_input = ReviewInput(
            mode=ReviewMode.PROJECT_SCAN,
            diff="",
            doctrine=(DoctrineDocument("docs/current_phase.md", "Avoid hosted apps."),),
            repository_context="Tripwire doctrine completeness",
            source_description="Project scan",
        )

        prompt = build_review_prompt(review_input)

        self.assertIn("Project scan mode", prompt)
        self.assertIn("doctrine inconsistencies", prompt)
        self.assertIn("Doctrine conflict findings must cite", prompt)
        self.assertIn("Do not require a PR or diff cause", prompt)
        self.assertNotIn("caused or materially worsened by this diff", prompt)


if __name__ == "__main__":
    unittest.main()
