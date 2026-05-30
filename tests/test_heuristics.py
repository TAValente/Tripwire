import unittest

from tripwire.heuristics import local_findings
from tripwire.models import ReviewInput, ReviewMode


def make_input(diff: str) -> ReviewInput:
    return ReviewInput(
        mode=ReviewMode.STANDARD,
        diff=diff,
        doctrine=(),
        repository_context="",
        source_description="Working tree git diff",
    )


class HeuristicTests(unittest.TestCase):
    def test_flags_web_surface_as_scope_creep(self):
        findings = local_findings(make_input("+from fastapi import FastAPI"))

        self.assertTrue(findings)
        self.assertEqual(findings[0].category, "Scope Creep")


    def test_ignores_empty_diff(self):
        self.assertEqual(local_findings(make_input("")), [])


if __name__ == "__main__":
    unittest.main()
