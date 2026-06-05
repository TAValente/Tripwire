import tempfile
import unittest
from pathlib import Path

from tripwire.doctrine import missing_doctrine_paths, render_doctrine_completeness


class DoctrineCompletenessTests(unittest.TestCase):
    def test_missing_doctrine_paths_reports_absent_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            (docs / "principles.md").write_text("Principles", encoding="utf-8")

            missing = missing_doctrine_paths(root)

        self.assertIn("docs/current_phase.md", missing)
        self.assertNotIn("docs/principles.md", missing)

    def test_render_doctrine_completeness_outputs_concrete_improver(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = render_doctrine_completeness(root)

        self.assertIn("Tripwire doctrine completeness", output)
        self.assertIn("Missing docs:", output)
        self.assertIn("Concrete Improver", output)


if __name__ == "__main__":
    unittest.main()
