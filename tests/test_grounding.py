import unittest

from tripwire.grounding import validate_grounding
from tripwire.models import DoctrineDocument, ReviewInput, ReviewMode


class GroundingTests(unittest.TestCase):
    def review_input(self) -> ReviewInput:
        return ReviewInput(
            mode=ReviewMode.STANDARD,
            diff="+Repository primary language: Python\n+Target doctrine docs found: 7\n",
            doctrine=(DoctrineDocument("docs/current_phase.md", "CLI-first local MVP."),),
            repository_context="GitHub repository: TAValente/Tripwire\nRepository primary language: Python",
            source_description="GitHub PR TAValente/Tripwire#5",
        )

    def test_accepts_grounded_alignment_output(self):
        output = """Project Understanding

Current phase: high
Economics: medium
Architecture: medium
Roadmap/decisions: medium
Key confidence limits: Runtime behavior not inspected.

Alignment Assessment

Priority: Local MVP
Direction: unchanged
PR Causality: unchanged
Confidence: medium
Evidence: CLI-first local MVP.

Findings

None.

Emergent Concerns

None.

Suppressed / Calibration

None.

Confidence Limits

Runtime behavior was not inspected.
"""

        self.assertTrue(validate_grounding(self.review_input(), output).ok)

    def test_rejects_alignment_without_evidence_field(self):
        output = """Project Understanding

Current phase: high
Economics: medium
Architecture: medium
Roadmap/decisions: medium
Key confidence limits: Runtime behavior not inspected.

Alignment Assessment

Priority: Scalability
Direction: worse
PR Causality: introduced
Confidence: medium

Findings

None.

Emergent Concerns

None.

Suppressed / Calibration

None.

Confidence Limits

Runtime behavior was not inspected.
"""

        result = validate_grounding(self.review_input(), output)

        self.assertFalse(result.ok)
        self.assertIn("Alignment Assessment missing field: Evidence:", result.errors)

    def test_rejects_emergent_concern_without_evidence(self):
        output = """Project Understanding

Current phase: high
Economics: medium
Architecture: medium
Roadmap/decisions: medium
Key confidence limits: Runtime behavior not inspected.

Alignment Assessment

Priority: Local MVP
Direction: unchanged
PR Causality: unchanged
Confidence: medium
Evidence: CLI-first local MVP.

Findings

None.

Emergent Concerns

The project may need enterprise onboarding.

Suppressed / Calibration

None.

Confidence Limits

Runtime behavior was not inspected.
"""

        result = validate_grounding(self.review_input(), output)

        self.assertFalse(result.ok)
        self.assertIn("Emergent Concerns must be None or include Evidence.", result.errors)


if __name__ == "__main__":
    unittest.main()
