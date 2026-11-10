from dataclasses import dataclass
import math

from bjt import BiasInputs, BiasResult


REL_TOL = 1e-9


@dataclass(frozen=True)
class VerificationResult:
    ib_a: float
    ic_a: float
    ie_a: float
    vb_v: float
    vc_v: float
    ve_v: float
    vce_v: float
    matches: bool


def verify_active(inputs: BiasInputs, main: BiasResult) -> VerificationResult:
    beta_plus_one_re = (inputs.beta + 1) * inputs.re_ohm
    vb_v = (
        inputs.vcc_v / inputs.r1_ohm + inputs.vbe_v / beta_plus_one_re
    ) / (
        1 / inputs.r1_ohm
        + 1 / inputs.r2_ohm
        + 1 / beta_plus_one_re
    )
    ve_v = vb_v - inputs.vbe_v
    ie_a = ve_v / inputs.re_ohm
    ib_a = ie_a / (inputs.beta + 1)
    ic_a = inputs.beta * ib_a
    vc_v = inputs.vcc_v - ic_a * inputs.rc_ohm
    vce_v = vc_v - ve_v

    matches = all(
        math.isclose(check_value, main_value, rel_tol=REL_TOL, abs_tol=1e-12)
        for check_value, main_value in (
            (ib_a, main.ib_a),
            (ic_a, main.ic_a),
            (ie_a, main.ie_a),
            (vb_v, main.vb_v),
            (vc_v, main.vc_v),
            (ve_v, main.ve_v),
            (vce_v, main.vce_v),
        )
    )

    return VerificationResult(
        ib_a=ib_a,
        ic_a=ic_a,
        ie_a=ie_a,
        vb_v=vb_v,
        vc_v=vc_v,
        ve_v=ve_v,
        vce_v=vce_v,
        matches=matches,
    )
