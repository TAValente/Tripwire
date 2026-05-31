import unittest

from tripwire.models import Finding


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


if __name__ == "__main__":
    unittest.main()
