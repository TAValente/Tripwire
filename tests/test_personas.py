import unittest

from tripwire.personas import PERSONAS, persona_prompt_section, render_personas


class PersonaTests(unittest.TestCase):
    def test_personas_include_expected_names(self):
        names = {persona.name for persona in PERSONAS}

        self.assertEqual(names, {"Engineer", "Product Manager", "Economics Watchdog"})

    def test_render_personas_is_human_readable(self):
        rendered = render_personas()

        self.assertIn("Tripwire personas", rendered)
        self.assertIn("Runs when:", rendered)

    def test_persona_prompt_section_guides_model_selection(self):
        section = persona_prompt_section()

        self.assertIn("Use this persona when:", section)
        self.assertIn("Avoid:", section)


if __name__ == "__main__":
    unittest.main()
