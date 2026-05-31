import unittest

from tripwire.models import ReviewInput, ReviewMode
from tripwire.reviewer import review


class ReviewerTests(unittest.TestCase):
    def test_missing_target_doctrine_outputs_concrete_improver(self):
        review_input = ReviewInput(
            mode=ReviewMode.STANDARD,
            diff="",
            doctrine=(),
            repository_context="GitHub repository: example/repo",
            source_description="GitHub PR example/repo#1",
            missing_target_doctrine=True,
        )

        output = review(review_input)

        self.assertIn("Concrete Improvers", output)
        self.assertIn("Add Minimum Project Doctrine", output)


if __name__ == "__main__":
    unittest.main()
