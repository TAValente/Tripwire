import unittest

from tripwire.interactive import choose, prompt_concerns


class InteractiveTests(unittest.TestCase):
    def test_choose_returns_selected_option(self):
        answers = iter(["2"])

        selected = choose(("one", "two"), "thing", str, lambda _: next(answers), lambda _: None)

        self.assertEqual(selected, "two")

    def test_prompt_concerns_returns_text(self):
        concerns = prompt_concerns(lambda _: "Watch cost.", lambda _: None)

        self.assertEqual(concerns, "Watch cost.")


if __name__ == "__main__":
    unittest.main()
