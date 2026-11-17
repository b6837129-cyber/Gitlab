from dataclasses import dataclass
import math
from typing import Mapping


REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")

BIAS_MODES = ("divider", "fixed", "emitter")

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias (Single Supply)",
}

MODE_REQUIRED_FIELDS = {
    "divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

MODE_RESISTANCE_FIELDS = {
    "divider": ("r1", "r2", "rc", "re"),
    "fixed": ("rb", "rc"),
    "emitter": ("rb", "rc", "re"),
}

VOLTAGE_UNITS = {"V": 1.0, "mV": 1e-3}
RESISTANCE_UNITS = {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6}
BETA_UNITS = {"—": 1.0}

UNIT_FACTORS = {
    "vcc": VOLTAGE_UNITS,
    "vbe": VOLTAGE_UNITS,
    "r1": RESISTANCE_UNITS,
    "r2": RESISTANCE_UNITS,
    "rb": RESISTANCE_UNITS,
    "rc": RESISTANCE_UNITS,
    "re": RESISTANCE_UNITS,
    "beta": BETA_UNITS,
}

DEFAULT_UNITS = {
    "vcc": "V",
    "vbe": "V",
    "r1": "Ω",
    "r2": "Ω",
    "rb": "Ω",
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


def _validate_finite_dict(data: dict) -> None:
    numeric_keys = (
        "ib_a",
        "ic_a",
        "ie_a",
        "ib_ua",
        "ic_ma",
        "ie_ma",
        "vb_v",
        "ve_v",
        "vc_v",
        "vce_v",
    )
    if not all(math.isfinite(data[k]) for k in numeric_keys):
        raise ValueError("calculation produced a non-finite result")


def _build_bias_dict(
    mode: str,
    vcc_v: float,
    rc_ohm: float,
    re_ohm: float,
    beta: float,
    vbe_v: float,
    ib_a: float,
    vth_v: float,
    rth_ohm: float,
) -> dict:
    if ib_a <= 0.0:
        result_dict = {
            "mode": mode,
            "mode_label": MODE_LABELS[mode],
            "vbb_v": vth_v,
            "rb_ohm": rth_ohm,
            "ib_a": 0.0,
            "ic_a": 0.0,
            "ie_a": 0.0,
            "ib_ua": 0.0,
            "ic_ma": 0.0,
            "ie_ma": 0.0,
            "vb_v": vth_v,
            "ve_v": 0.0,
            "vc_v": vcc_v,
            "vce_v": vcc_v,
            "region": CUTOFF,
            "warning": "Warning: IB <= 0 A (Cutoff). Forward-active model may not be valid.",
        }
        _validate_finite_dict(result_dict)
        return result_dict

    ic_a = beta * ib_a
    ie_a = (beta + 1.0) * ib_a
    ve_v = ie_a * re_ohm
    vb_v = ve_v + vbe_v
    vc_v = vcc_v - ic_a * rc_ohm
    vce_v = vc_v - ve_v

    if vce_v <= VCE_SAT_V:
        region = SATURATION
        warning = "Warning: VCE <= 0.2 V (Saturation). Forward-active model may not be valid."
    else:
        region = ACTIVE
        warning = None

    result_dict = {
        "mode": mode,
        "mode_label": MODE_LABELS[mode],
        "vbb_v": vth_v,
        "rb_ohm": rth_ohm,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "ie_a": ie_a,
        "ib_ua": ib_a * 1e6,
        "ic_ma": ic_a * 1e3,
        "ie_ma": ie_a * 1e3,
        "vb_v": vb_v,
        "ve_v": ve_v,
        "vc_v": vc_v,
        "vce_v": vce_v,
        "region": region,
        "warning": warning,
    }
    _validate_finite_dict(result_dict)
    return result_dict


def calculate_fixed_bias(
    vcc_v: float,
    rb_ohm: float,
    rc_ohm: float,
    beta: float,
    vbe_v: float,
) -> dict:
    ib_a = (vcc_v - vbe_v) / rb_ohm
    return _build_bias_dict(
        mode="fixed",
        vcc_v=vcc_v,
        rc_ohm=rc_ohm,
        re_ohm=0.0,
        beta=beta,
        vbe_v=vbe_v,
        ib_a=ib_a,
        vth_v=vcc_v,
        rth_ohm=rb_ohm,
    )


def calculate_emitter_bias(
    vcc_v: float,
    rb_ohm: float,
    rc_ohm: float,
    re_ohm: float,
    beta: float,
    vbe_v: float,
) -> dict:
    denominator = rb_ohm + (beta + 1.0) * re_ohm
    if not math.isfinite(denominator) or denominator <= 0:
        raise ValueError("calculation produced an invalid denominator")
    ib_a = (vcc_v - vbe_v) / denominator
    return _build_bias_dict(
        mode="emitter",
        vcc_v=vcc_v,
        rc_ohm=rc_ohm,
        re_ohm=re_ohm,
        beta=beta,
        vbe_v=vbe_v,
        ib_a=ib_a,
        vth_v=vcc_v,
        rth_ohm=rb_ohm,
    )


def calculate_voltage_divider(
    vcc_v: float,
    r1_ohm: float,
    r2_ohm: float,
    rc_ohm: float,
    re_ohm: float,
    beta: float,
    vbe_v: float,
) -> dict:
    vth_v = vcc_v * r2_ohm / (r1_ohm + r2_ohm)
    rth_ohm = r1_ohm * r2_ohm / (r1_ohm + r2_ohm)
    denominator = rth_ohm + (beta + 1.0) * re_ohm
    if not math.isfinite(denominator) or denominator <= 0:
        raise ValueError("calculation produced an invalid denominator")
    ib_a = (vth_v - vbe_v) / denominator
    return _build_bias_dict(
        mode="divider",
        vcc_v=vcc_v,
        rc_ohm=rc_ohm,
        re_ohm=re_ohm,
        beta=beta,
        vbe_v=vbe_v,
        ib_a=ib_a,
        vth_v=vth_v,
        rth_ohm=rth_ohm,
    )


def validate_and_parse_mode(
    raw: Mapping[str, str],
) -> tuple[dict[str, float | str] | None, dict[str, str]]:
    mode = str(raw.get("mode", "")).strip()
    if mode not in BIAS_MODES:
        return None, {"mode": "Unknown bias mode selected. Please choose a valid circuit mode."}

    required = MODE_REQUIRED_FIELDS[mode]
    resistance_fields = MODE_RESISTANCE_FIELDS[mode]
    values: dict[str, float | str] = {"mode": mode}
    errors: dict[str, str] = {}

    for field in required:
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
            errors[field] = "Please enter a finite number"
            continue
        unit = str(raw.get(f"{field}_unit", DEFAULT_UNITS[field])).strip()
        if unit not in UNIT_FACTORS[field]:
            errors[field] = "Please select a valid unit"
            continue
        values[field] = number * UNIT_FACTORS[field][unit]

    if "vcc" in values and float(values["vcc"]) <= 0:
        errors["vcc"] = "VCC must be greater than 0 V"

    for field in resistance_fields:
        if field in values and float(values[field]) <= 0:
            errors[field] = "Resistance must be greater than 0 Ω"

    if "beta" in values and float(values["beta"]) < 1:
        errors["beta"] = "β must be at least 1"

    if "vbe" in values and not (0 <= float(values["vbe"]) <= 1.5):
        errors["vbe"] = "VBE must be between 0 and 1.5 V"

    if errors:
        return None, errors

    return values, {}


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
    res = calculate_voltage_divider(
        vcc_v=inputs.vcc_v,
        r1_ohm=inputs.r1_ohm,
        r2_ohm=inputs.r2_ohm,
        rc_ohm=inputs.rc_ohm,
        re_ohm=inputs.re_ohm,
        beta=inputs.beta,
        vbe_v=inputs.vbe_v,
    )
    return BiasResult(
        vbb_v=res["vbb_v"],
        rb_ohm=res["rb_ohm"],
        ib_a=res["ib_a"],
        ic_a=res["ic_a"],
        ie_a=res["ie_a"],
        vb_v=res["vb_v"],
        vc_v=res["vc_v"],
        ve_v=res["ve_v"],
        vce_v=res["vce_v"],
        region=res["region"],
    )