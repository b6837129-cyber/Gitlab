import unittest

from bjt import validate_and_parse

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


class TestValidation(unittest.TestCase):
    def test_valid_inputs_are_parsed(self):
        inputs, errors = validate_and_parse(VALID)
        self.assertEqual(errors, {})
        self.assertIsNotNone(inputs)
        self.assertAlmostEqual(inputs.vcc_v, 12.0)
        self.assertAlmostEqual(inputs.r1_ohm, 47000.0)
        self.assertAlmostEqual(inputs.beta, 150.0)

    def test_missing_field_reports_error(self):
        data = dict(VALID)
        del data["r1"]
        inputs, errors = validate_and_parse(data)
        self.assertIsNone(inputs)
        self.assertEqual(errors["r1"], "กรุณากรอกค่านี้")

    def test_non_numeric_reports_error(self):
        data = dict(VALID)
        data["rc"] = "abc"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["rc"], "กรุณากรอกเป็นตัวเลข")

    def test_non_finite_reports_error(self):
        for value in ("nan", "inf", "-inf"):
            data = dict(VALID)
            data["vcc"] = value
            _, errors = validate_and_parse(data)
            self.assertEqual(errors["vcc"], "กรุณากรอกเป็นตัวเลข")

    def test_zero_resistance_reports_error(self):
        data = dict(VALID)
        data["re"] = "0"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["re"], "ค่าความต้านทานต้องมากกว่า 0 Ω")

    def test_negative_resistance_reports_error(self):
        data = dict(VALID)
        data["r1"] = "-1"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["r1"], "ค่าความต้านทานต้องมากกว่า 0 Ω")

    def test_beta_below_one_reports_error(self):
        data = dict(VALID)
        data["beta"] = "0.9"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["beta"], "β ต้องมีค่าตั้งแต่ 1 ขึ้นไป")

    def test_vbe_outside_range_reports_error(self):
        for value in ("-0.1", "1.6"):
            data = dict(VALID)
            data["vbe"] = value
            _, errors = validate_and_parse(data)
            self.assertEqual(errors["vbe"], "VBE ต้องอยู่ระหว่าง 0 ถึง 1.5 V")

    def test_whitespace_is_accepted(self):
        data = dict(VALID)
        data["vcc"] = " 12 "
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.vcc_v, 12.0)

    def test_boundary_values_are_accepted(self):
        data = dict(VALID)
        data["beta"] = "1"
        data["vbe"] = "1.5"
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.beta, 1.0)
        self.assertAlmostEqual(inputs.vbe_v, 1.5)


if __name__ == "__main__":
    unittest.main()
