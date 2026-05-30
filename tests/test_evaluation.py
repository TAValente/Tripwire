import tempfile
import unittest
from pathlib import Path

from tripwire.evaluation import load_cases, render_eval_results, run_eval


class EvaluationTests(unittest.TestCase):
    def test_load_cases_reads_json_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(
                """{
                  "name": "sample",
                  "mode": "standard",
                  "diff": "+from fastapi import FastAPI",
                  "must_contain": ["Scope Creep"],
                  "must_contain_any": [["Scope Creep", "Architecture Drift"]],
                  "must_not_contain": []
                }""",
                encoding="utf-8",
            )

            cases = load_cases(Path(directory))

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].name, "sample")

    def test_run_eval_scores_expected_terms(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = root / "eval" / "fixtures"
            fixtures.mkdir(parents=True)
            (fixtures / "case.json").write_text(
                """{
                  "name": "web case",
                  "mode": "standard",
                  "diff": "+from fastapi import FastAPI",
                  "must_contain": ["Scope Creep"],
                  "must_contain_any": [["Scope Creep", "Architecture Drift"]],
                  "must_not_contain": ["No high-confidence strategic findings detected"]
                }""",
                encoding="utf-8",
            )

            results = run_eval(root, fixtures)

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)
        self.assertIn("Passed 1/1", render_eval_results(results))


if __name__ == "__main__":
    unittest.main()
