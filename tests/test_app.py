import unittest

from app import create_app

VALID = {
    "vcc": "12.0", "vcc_unit": "V",
    "r1": "100", "r1_unit": "kΩ",
    "r2": "22", "r2_unit": "kΩ",
    "rc": "2.2", "rc_unit": "kΩ",
    "re": "1.0", "re_unit": "kΩ",
    "beta": "100", "beta_unit": "—",
    "vbe": "0.70", "vbe_unit": "V",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_prefills_example(self):
        text = self.client.get("/").get_data(as_text=True)
        self.assertIn("Lab 02: BJT DC Bias Web App", text)
        self.assertIn("Computer Programming for Electrical Engineers", text)
        self.assertIn('value="12.0"', text)
        self.assertIn('name="r1_unit"', text)
        self.assertIn("kΩ", text)

    def test_valid_post_shows_active_result(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        for value in ("1.94", "1.24", "9.29", "8.05", "12.3", "1.23"):
            self.assertIn(value, text)
        self.assertIn("Active region approximation OK", text)
        self.assertIn("Independent Verification", text)
        self.assertIn("Verification: PASS", text)

    def test_invalid_post_shows_english_error(self):
        data = dict(VALID)
        data["vcc"] = "0"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("VCC must be greater than 0 V", text)
        self.assertNotIn("Independent Verification", text)

    def test_cutoff_shows_card(self):
        data = dict(VALID)
        data["r2"] = "1"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("Transistor is in cutoff", text)

    def test_saturation_shows_card(self):
        data = dict(VALID)
        data["r1"] = "22"
        data["r2"] = "100"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("Transistor is in saturation", text)

    def test_other_values_calculate(self):
        data = {
            "vcc": "9", "vcc_unit": "V",
            "r1": "47", "r1_unit": "kΩ",
            "r2": "10", "r2_unit": "kΩ",
            "rc": "1", "rc_unit": "kΩ",
            "re": "470", "re_unit": "Ω",
            "beta": "200", "beta_unit": "—",
            "vbe": "0.65", "vbe_unit": "V",
        }
        text = self.client.post("/", data=data).get_data(as_text=True)
        for value in ("1.50", "0.85", "7.19", "6.34", "9.0", "1.81", "1.82"):
            self.assertIn(value, text)
        self.assertIn("Active region approximation OK", text)

    def test_svg_contains_submitted_values(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("100 kΩ", text)
        self.assertIn("12.0 V", text)

    def test_extreme_values_show_error_not_crash(self):
        data = dict(VALID)
        data.update(
            {
                "vcc": "1e308",
                "r1": "1e308",
                "r2": "1e308",
                "rc": "1e308",
                "re": "1e308",
            }
        )
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("These values do not produce a valid result.", text)

    def test_non_finite_verification_shows_error(self):
        data = dict(VALID)
        data.update({"r1": "5e-324", "rc": "1", "r1_unit": "Ω", "rc_unit": "Ω"})
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("These values do not produce a valid result.", text)
        self.assertNotIn("nan", text)

    def test_display_scaling_overflow_shows_error(self):
        data = dict(VALID)
        data.update(
            {
                "r1": "1e-307",
                "r2": "1e-307",
                "rc": "1e-303",
                "re": "1e-303",
                "beta": "1",
                "r1_unit": "Ω",
                "r2_unit": "Ω",
                "rc_unit": "Ω",
                "re_unit": "Ω",
            }
        )
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("These values do not produce a valid result.", text)
        self.assertNotIn("inf", text)

    def test_submitted_html_is_escaped(self):
        data = dict(VALID)
        data["vcc"] = "<script>alert(1)</script>"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn("<script>alert(1)</script>", text)


if __name__ == "__main__":
    unittest.main()
