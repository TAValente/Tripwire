import json
import unittest

from tripwire.github import PullRequest
from tripwire.ui import json_bytes, pr_to_json


class UiTests(unittest.TestCase):
    def test_json_bytes_preserves_text(self):
        payload = {"ok": True, "output": "Ready"}

        self.assertEqual(json.loads(json_bytes(payload).decode("utf-8")), payload)

    def test_pr_to_json_renders_pull_request(self):
        pr = PullRequest(
            repo="TAValente/TrainingTweaks",
            number=7,
            title="Add app state",
            body="",
            url="https://github.com/TAValente/TrainingTweaks/pull/7",
            author="TAValente",
            head_ref="state",
            base_ref="main",
            additions=228,
            deletions=67,
            changed_files=13,
        )

        self.assertEqual(
            pr_to_json(pr),
            {
                "repo": "TAValente/TrainingTweaks",
                "number": 7,
                "title": "Add app state",
                "url": "https://github.com/TAValente/TrainingTweaks/pull/7",
                "author": "TAValente",
                "head_ref": "state",
                "base_ref": "main",
                "additions": 228,
                "deletions": 67,
                "changed_files": 13,
            },
        )


if __name__ == "__main__":
    unittest.main()
