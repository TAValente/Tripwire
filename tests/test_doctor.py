import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tripwire.doctor import check_ai, check_github_auth, render_doctor


class DoctorTests(unittest.TestCase):
    @patch("tripwire.doctor.gh_executable", return_value=None)
    def test_github_auth_reports_missing_cli(self, _gh):
        check = check_github_auth()

        self.assertEqual(check.status, "FAIL")
        self.assertIn("install GitHub CLI", check.detail)

    @patch.dict("os.environ", {}, clear=True)
    def test_check_ai_warns_when_no_provider_configured(self):
        check = check_ai()

        self.assertEqual(check.status, "WARN")
        self.assertIn("no AI provider", check.detail)

    @patch("tripwire.doctor.check_github_cli")
    @patch("tripwire.doctor.check_github_auth")
    @patch("tripwire.doctor.check_ai")
    def test_render_doctor_reports_not_ready_on_failure(self, ai, auth, cli):
        cli.return_value = type("Check", (), {"name": "GitHub CLI", "status": "OK", "detail": "gh"})()
        auth.return_value = type("Check", (), {"name": "GitHub auth", "status": "FAIL", "detail": "not authenticated"})()
        ai.return_value = type("Check", (), {"name": "AI provider", "status": "OK", "detail": "ollama"})()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output, ready = render_doctor(root)

        self.assertFalse(ready)
        self.assertIn("[FAIL] GitHub auth", output)


if __name__ == "__main__":
    unittest.main()
