import unittest

from tripwire.heuristics import local_findings
from tripwire.models import DoctrineDocument, ReviewInput, ReviewMode


TRIPWIRE_PHASE_DOCTRINE = DoctrineDocument(
    "docs/current_phase.md",
    "Tripwire is in MVP validation. Acceptable: command-line interface. Avoid: dashboards, web interfaces, databases.",
)


def make_input(diff: str, doctrine: tuple[DoctrineDocument, ...] = (TRIPWIRE_PHASE_DOCTRINE,)) -> ReviewInput:
    return ReviewInput(
        mode=ReviewMode.STANDARD,
        diff=diff,
        doctrine=doctrine,
        repository_context="",
        source_description="Working tree git diff",
    )


class HeuristicTests(unittest.TestCase):
    def test_flags_web_surface_as_scope_creep(self):
        findings = local_findings(make_input("+from fastapi import FastAPI"))

        self.assertTrue(findings)
        self.assertEqual(findings[0].category, "Scope Creep")

    def test_does_not_apply_tripwire_scope_rule_without_supporting_doctrine(self):
        doctrine = (
            DoctrineDocument(
                "docs/architecture.md",
                "This project is a web decision-support app built with Next.js.",
            ),
        )

        self.assertEqual(local_findings(make_input("+import { NextRequest } from 'next/server'", doctrine)), [])

    def test_ignores_empty_diff(self):
        self.assertEqual(local_findings(make_input("")), [])

    def test_doctrine_update_can_justify_local_ui_surface(self):
        diff = "\n".join(
            [
                "+- a simple local control panel that wraps common commands",
                "+Tripwire should feel like an out-of-the-box local project helper after setup.",
                "+from http.server import ThreadingHTTPServer",
            ]
        )

        self.assertEqual(local_findings(make_input(diff)), [])

    def test_doctrine_update_can_justify_local_storage(self):
        diff = "\n".join(
            [
                "+- lightweight local storage when it directly improves review quality",
                "+Local memory and evaluation storage are acceptable.",
                "+sqlite3.connect(path)",
            ]
        )

        self.assertEqual(local_findings(make_input(diff)), [])


if __name__ == "__main__":
    unittest.main()
