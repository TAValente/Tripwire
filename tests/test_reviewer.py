import unittest

from tripwire.models import ReviewInput, ReviewMode
from tripwire.reviewer import clean_ai_output, review


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

    def test_clean_ai_output_removes_thinking_tags(self):
        output = clean_ai_output(
            "<think>private reasoning</think>\n\nMistakes to Correct\n- Title: Real issue"
        )

        self.assertEqual(output, "Mistakes to Correct\n- Title: Real issue")

    def test_clean_ai_output_discards_preamble_before_no_findings(self):
        output = clean_ai_output(
            "Thinking...\nthis looks fine\n...done thinking.\n\nNo high-confidence strategic findings detected."
        )

        self.assertEqual(output, "No high-confidence strategic findings detected.")

    def test_clean_ai_output_suppresses_non_tripwire_explanation(self):
        output = clean_ai_output(
            "</think>\n\nThis change is a useful security improvement and behaves predictably."
        )

        self.assertEqual(output, "No high-confidence strategic findings detected.")

    def test_clean_ai_output_ignores_inline_no_findings_example(self):
        output = clean_ai_output(
            "A summary says `No high-confidence strategic findings detected.` is preserved.\n\n"
            "---\n\n"
            "Mistakes to Correct\nTitle: Real issue"
        )

        self.assertEqual(output, "Mistakes to Correct\nTitle: Real issue")

    def test_clean_ai_output_prefixes_suppressed_finding_without_findings(self):
        output = clean_ai_output("Suppressed Finding\nTitle: Possible issue\nSeverity If True: 3")

        self.assertEqual(
            output,
            "No high-confidence strategic findings detected.\n\nSuppressed Finding\nTitle: Possible issue\nSeverity If True: 3",
        )


if __name__ == "__main__":
    unittest.main()
