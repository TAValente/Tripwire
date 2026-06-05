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
        self.assertIn("Minimum docs needed:", rendered)

    def test_persona_prompt_section_guides_model_selection(self):
        section = persona_prompt_section()

        self.assertIn("Use this persona when:", section)
        self.assertIn("Avoid:", section)

    def test_economics_watchdog_distinguishes_material_cost_from_instrumentation(self):
        economics = next(persona for persona in PERSONAS if persona.name == "Economics Watchdog")

        joined = " ".join((*economics.uses_when, *economics.avoids, *economics.example_questions))
        self.assertIn("marginal cost", joined)
        self.assertIn("bounded logging", joined)
        self.assertIn("product evaluation", joined)


if __name__ == "__main__":
    unittest.main()
