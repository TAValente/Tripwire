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


if __name__ == "__main__":
    unittest.main()
