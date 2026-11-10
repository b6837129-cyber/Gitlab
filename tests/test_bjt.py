import unittest

from bjt import (
    ACTIVE,
    CUTOFF,
    SATURATION,
    VCE_SAT_V,
    BiasInputs,
    analyze_bias,
    validate_and_parse,
)

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
        self.assertEqual(errors["r1"], "Please enter this value")

    def test_non_numeric_reports_error(self):
        data = dict(VALID)
        data["rc"] = "abc"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["rc"], "Please enter a number")

    def test_non_finite_reports_error(self):
        for value in ("nan", "inf", "-inf"):
            data = dict(VALID)
            data["vcc"] = value
            _, errors = validate_and_parse(data)
            self.assertEqual(errors["vcc"], "Please enter a number")

    def test_zero_resistance_reports_error(self):
        data = dict(VALID)
        data["re"] = "0"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["re"], "Resistance must be greater than 0 Ω")

    def test_negative_resistance_reports_error(self):
        data = dict(VALID)
        data["r1"] = "-1"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["r1"], "Resistance must be greater than 0 Ω")

    def test_beta_below_one_reports_error(self):
        data = dict(VALID)
        data["beta"] = "0.9"
        _, errors = validate_and_parse(data)
        self.assertEqual(errors["beta"], "β must be at least 1")

    def test_vbe_outside_range_reports_error(self):
        for value in ("-0.1", "1.6"):
            data = dict(VALID)
            data["vbe"] = value
            _, errors = validate_and_parse(data)
            self.assertEqual(errors["vbe"], "VBE must be between 0 and 1.5 V")

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

    def test_vbe_zero_is_accepted(self):
        data = dict(VALID)
        data["vbe"] = "0"
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.vbe_v, 0.0)

    def test_blank_field_reports_error(self):
        data = dict(VALID)
        data["r1"] = ""
        inputs, errors = validate_and_parse(data)
        self.assertIsNone(inputs)
        self.assertEqual(errors["r1"], "Please enter this value")

    def test_whitespace_only_field_reports_error(self):
        data = dict(VALID)
        data["beta"] = "   "
        inputs, errors = validate_and_parse(data)
        self.assertIsNone(inputs)
        self.assertEqual(errors["beta"], "Please enter this value")

    def test_kilo_ohm_unit_is_converted(self):
        data = dict(VALID)
        data.update({"r1": "100", "r1_unit": "kΩ"})
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.r1_ohm, 100000.0)

    def test_mega_ohm_unit_is_converted(self):
        data = dict(VALID)
        data.update({"r2": "1", "r2_unit": "MΩ"})
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.r2_ohm, 1_000_000.0)

    def test_millivolt_unit_is_converted(self):
        data = dict(VALID)
        data.update({"vcc": "12000", "vcc_unit": "mV"})
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.vcc_v, 12.0)

    def test_missing_unit_defaults_to_base_unit(self):
        data = dict(VALID)
        data.pop("vcc_unit", None)
        inputs, errors = validate_and_parse(data)
        self.assertEqual(errors, {})
        self.assertAlmostEqual(inputs.vcc_v, 12.0)

    def test_invalid_unit_reports_error(self):
        data = dict(VALID)
        data.update({"beta": "100", "beta_unit": "kΩ"})
        inputs, errors = validate_and_parse(data)
        self.assertIsNone(inputs)
        self.assertEqual(errors["beta"], "Please select a valid unit")


class TestAnalyzeBias(unittest.TestCase):
    def test_known_active_bias_point(self):
        result = analyze_bias(
            BiasInputs(
                vcc_v=12,
                r1_ohm=47000,
                r2_ohm=10000,
                rc_ohm=2200,
                re_ohm=1000,
                beta=150,
                vbe_v=0.7,
            )
        )
        self.assertEqual(result.region, ACTIVE)
        self.assertAlmostEqual(result.vbb_v, 2.1052631579, places=9)
        self.assertAlmostEqual(result.rb_ohm, 8245.6140351, places=6)
        self.assertAlmostEqual(result.ib_a, 8.8245014873e-6, delta=1e-12)
        self.assertAlmostEqual(result.ic_a, 1.3236752231e-3, delta=1e-12)
        self.assertAlmostEqual(result.ie_a, 1.3324997246e-3, delta=1e-12)
        self.assertAlmostEqual(result.vb_v, 2.0324997246, places=9)
        self.assertAlmostEqual(result.vc_v, 9.0879145092, places=9)
        self.assertAlmostEqual(result.ve_v, 1.3324997246, places=9)
        self.assertAlmostEqual(result.vce_v, 7.7554147846, places=9)

    def test_cutoff_when_vbb_below_vbe(self):
        result = analyze_bias(
            BiasInputs(
                vcc_v=12,
                r1_ohm=47000,
                r2_ohm=1000,
                rc_ohm=2200,
                re_ohm=1000,
                beta=150,
                vbe_v=0.7,
            )
        )
        self.assertEqual(result.region, CUTOFF)
        self.assertAlmostEqual(result.vbb_v, 0.25, places=9)
        self.assertEqual(result.ib_a, 0.0)
        self.assertEqual(result.ic_a, 0.0)
        self.assertEqual(result.ie_a, 0.0)
        self.assertAlmostEqual(result.vb_v, 0.25, places=9)
        self.assertAlmostEqual(result.vc_v, 12.0, places=9)
        self.assertEqual(result.ve_v, 0.0)
        self.assertAlmostEqual(result.vce_v, 12.0, places=9)

    def test_cutoff_when_vbe_exceeds_vcc(self):
        result = analyze_bias(
            BiasInputs(
                vcc_v=1,
                r1_ohm=47000,
                r2_ohm=10000,
                rc_ohm=2200,
                re_ohm=1000,
                beta=150,
                vbe_v=1.2,
            )
        )
        self.assertEqual(result.region, CUTOFF)
        self.assertEqual(result.ib_a, 0.0)
        self.assertEqual(result.ic_a, 0.0)

    def test_saturation_when_vce_at_or_below_threshold(self):
        result = analyze_bias(
            BiasInputs(
                vcc_v=12,
                r1_ohm=10000,
                r2_ohm=47000,
                rc_ohm=2200,
                re_ohm=1000,
                beta=150,
                vbe_v=0.7,
            )
        )
        self.assertEqual(result.region, SATURATION)
        self.assertLess(result.vce_v, VCE_SAT_V)
        self.assertAlmostEqual(result.ic_a, 8.6609011788e-3, delta=1e-12)
        self.assertAlmostEqual(result.vce_v, -15.7726231134, places=9)

    def test_beta_one_remains_active(self):
        result = analyze_bias(
            BiasInputs(
                vcc_v=12,
                r1_ohm=47000,
                r2_ohm=10000,
                rc_ohm=2200,
                re_ohm=1000,
                beta=1,
                vbe_v=0.7,
            )
        )
        self.assertEqual(result.region, ACTIVE)
        self.assertAlmostEqual(result.ic_a, 1.3715753425e-4, delta=1e-12)

    def test_non_finite_result_raises_value_error(self):
        inputs = BiasInputs(
            vcc_v=1e308,
            r1_ohm=1e308,
            r2_ohm=1e308,
            rc_ohm=1e308,
            re_ohm=1e308,
            beta=150,
            vbe_v=0.7,
        )
        with self.assertRaises(ValueError):
            analyze_bias(inputs)

    def test_extreme_beta_raises_value_error(self):
        inputs = BiasInputs(
            vcc_v=12,
            r1_ohm=100000,
            r2_ohm=22000,
            rc_ohm=2200,
            re_ohm=1000,
            beta=1e308,
            vbe_v=0.7,
        )
        with self.assertRaises(ValueError):
            analyze_bias(inputs)


if __name__ == "__main__":
    unittest.main()
