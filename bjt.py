from dataclasses import dataclass
import math
from typing import Mapping


REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")

VOLTAGE_UNITS = {"V": 1.0, "mV": 1e-3}
RESISTANCE_UNITS = {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6}
BETA_UNITS = {"—": 1.0}

UNIT_FACTORS = {
    "vcc": VOLTAGE_UNITS,
    "vbe": VOLTAGE_UNITS,
    "r1": RESISTANCE_UNITS,
    "r2": RESISTANCE_UNITS,
    "rc": RESISTANCE_UNITS,
    "re": RESISTANCE_UNITS,
    "beta": BETA_UNITS,
}

DEFAULT_UNITS = {
    "vcc": "V",
    "vbe": "V",
    "r1": "Ω",
    "r2": "Ω",
    "rc": "Ω",
    "re": "Ω",
    "beta": "—",
}


ACTIVE = "active"
CUTOFF = "cutoff"
SATURATION = "saturation"
VCE_SAT_V = 0.2


@dataclass(frozen=True)
class BiasInputs:
    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class BiasResult:
    vbb_v: float
    rb_ohm: float
    ib_a: float
    ic_a: float
    ie_a: float
    vb_v: float
    vc_v: float
    ve_v: float
    vce_v: float
    region: str


def validate_and_parse(
    raw: Mapping[str, str],
) -> tuple[BiasInputs | None, dict[str, str]]:
    values: dict[str, float] = {}
    errors: dict[str, str] = {}

    for field in REQUIRED_FIELDS:
        text = str(raw.get(field, "")).strip()
        if not text:
            errors[field] = "Please enter this value"
            continue
        try:
            number = float(text)
        except ValueError:
            errors[field] = "Please enter a number"
            continue
        if not math.isfinite(number):
            errors[field] = "Please enter a number"
            continue
        unit = str(raw.get(f"{field}_unit", DEFAULT_UNITS[field])).strip()
        if unit not in UNIT_FACTORS[field]:
            errors[field] = "Please select a valid unit"
            continue
        values[field] = number * UNIT_FACTORS[field][unit]

    if "vcc" in values and values["vcc"] <= 0:
        errors["vcc"] = "VCC must be greater than 0 V"

    for field in RESISTANCE_FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = "Resistance must be greater than 0 Ω"

    if "beta" in values and values["beta"] < 1:
        errors["beta"] = "β must be at least 1"

    if "vbe" in values and not (0 <= values["vbe"] <= 1.5):
        errors["vbe"] = "VBE must be between 0 and 1.5 V"

    if errors:
        return None, errors

    return (
        BiasInputs(
            vcc_v=values["vcc"],
            r1_ohm=values["r1"],
            r2_ohm=values["r2"],
            rc_ohm=values["rc"],
            re_ohm=values["re"],
            beta=values["beta"],
            vbe_v=values["vbe"],
        ),
        {},
    )


def analyze_bias(inputs: BiasInputs) -> BiasResult:
    vbb_v = inputs.vcc_v * inputs.r2_ohm / (inputs.r1_ohm + inputs.r2_ohm)
    rb_ohm = inputs.r1_ohm * inputs.r2_ohm / (inputs.r1_ohm + inputs.r2_ohm)

    if vbb_v <= inputs.vbe_v:
        result = BiasResult(
            vbb_v=vbb_v,
            rb_ohm=rb_ohm,
            ib_a=0.0,
            ic_a=0.0,
            ie_a=0.0,
            vb_v=vbb_v,
            vc_v=inputs.vcc_v,
            ve_v=0.0,
            vce_v=inputs.vcc_v,
            region=CUTOFF,
        )
    else:
        ib_a = (vbb_v - inputs.vbe_v) / (
            rb_ohm + (inputs.beta + 1) * inputs.re_ohm
        )
        ic_a = inputs.beta * ib_a
        ie_a = (inputs.beta + 1) * ib_a
        ve_v = ie_a * inputs.re_ohm
        vc_v = inputs.vcc_v - ic_a * inputs.rc_ohm
        vb_v = inputs.vbe_v + ve_v
        vce_v = vc_v - ve_v
        region = SATURATION if vce_v <= VCE_SAT_V else ACTIVE
        result = BiasResult(
            vbb_v=vbb_v,
            rb_ohm=rb_ohm,
            ib_a=ib_a,
            ic_a=ic_a,
            ie_a=ie_a,
            vb_v=vb_v,
            vc_v=vc_v,
            ve_v=ve_v,
            vce_v=vce_v,
            region=region,
        )

    numeric_values = (
        result.vbb_v,
        result.rb_ohm,
        result.ib_a,
        result.ic_a,
        result.ie_a,
        result.vb_v,
        result.vc_v,
        result.ve_v,
        result.vce_v,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError("calculation produced a non-finite result")

    return result
