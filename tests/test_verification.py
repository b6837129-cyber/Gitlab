import dataclasses
import math
import unittest

from bjt import BiasInputs, analyze_bias
from verification import verify_active


INPUTS = BiasInputs(
    vcc_v=12,
    r1_ohm=47000,
    r2_ohm=10000,
    rc_ohm=2200,
    re_ohm=1000,
    beta=150,
    vbe_v=0.7,
)


class TestVerification(unittest.TestCase):
    def test_nodal_matches_main(self):
        main = analyze_bias(INPUTS)
        result = verify_active(INPUTS, main)
        self.assertTrue(result.matches)
        for name in ("ib_a", "ic_a", "ie_a", "vb_v", "vc_v", "ve_v", "vce_v"):
            self.assertTrue(
                math.isclose(
                    getattr(result, name),
                    getattr(main, name),
                    rel_tol=1e-9,
                    abs_tol=1e-12,
                ),
                name,
            )

    def test_nodal_vb_matches_hand_value(self):
        main = analyze_bias(INPUTS)
        result = verify_active(INPUTS, main)
        self.assertAlmostEqual(result.vb_v, 2.0324997246, places=9)

    def test_mismatch_is_detected(self):
        main = analyze_bias(INPUTS)
        altered = dataclasses.replace(main, ic_a=main.ic_a * 1.01)
        result = verify_active(INPUTS, altered)
        self.assertFalse(result.matches)


if __name__ == "__main__":
    unittest.main()
