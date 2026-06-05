import tempfile
import unittest
from pathlib import Path

from tripwire.doctrine import (
    missing_doctrine_document_paths,
    missing_doctrine_paths,
    render_doctrine_completeness,
    render_doctrine_sufficiency,
)
from tripwire.models import DoctrineDocument


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

    def test_render_doctrine_sufficiency_reports_limited_review(self):
        documents = (DoctrineDocument("docs/principles.md", "Move fast."),)

        output = render_doctrine_sufficiency(documents, source="TAValente/Tangent@main")

        self.assertIn("Doctrine sufficiency", output)
        self.assertIn("Found: 1/7 doctrine docs", output)
        self.assertIn("Substantive review: limited", output)

    def test_missing_doctrine_document_paths_uses_loaded_documents(self):
        missing = missing_doctrine_document_paths(
            (DoctrineDocument("docs/current_phase.md", "MVP"),)
        )

        self.assertIn("docs/principles.md", missing)
        self.assertNotIn("docs/current_phase.md", missing)


if __name__ == "__main__":
    unittest.main()
