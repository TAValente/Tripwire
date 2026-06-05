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
        self.assertIn("Mistakes to Correct", prompt)
        self.assertIn("Concrete Improvers", prompt)
        self.assertIn("Every finding must pass the leverage test", prompt)
        self.assertIn("author friction without a clear project payoff", prompt)
        self.assertIn("Final answer only", prompt)
        self.assertIn("Do not output hidden reasoning", prompt)
        self.assertIn("If the change is beneficial or harmless, do not summarize it", prompt)
        self.assertIn("Do not flag unused functions", prompt)
        self.assertIn("caused or materially worsened by this diff", prompt)
        self.assertIn("Evidence must cite what changed", prompt)
        self.assertIn("Do not flag AI economics merely because", prompt)

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
