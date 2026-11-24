import math
import re

from flask import Flask, render_template, request

from bjt import (
    ACTIVE,
    BIAS_MODES,
    CUTOFF,
    DEFAULT_UNITS,
    MODE_LABELS,
    BiasInputs,
    BiasResult,
    calculate_emitter_bias,
    calculate_fixed_bias,
    calculate_voltage_divider,
    validate_and_parse,
    validate_and_parse_mode,
)
from spice_engine import run_ce_spice_simulation
from verification import verify_active


CALCULATION_ERROR = "These values do not produce a valid result."

DEFAULT_FORM = {
    "mode": "divider",
    "analysis_mode": "op",
    "vcc": "12.0",
    "vcc_unit": "V",
    "r1": "100",
    "r1_unit": "kΩ",
    "r2": "22",
    "r2_unit": "kΩ",
    "rb": "1",
    "rb_unit": "MΩ",
    "rc": "2.2",
    "rc_unit": "kΩ",
    "re": "1.0",
    "re_unit": "kΩ",
    "rl": "10",
    "rl_unit": "kΩ",
    "cin": "10",
    "cin_unit": "µF",
    "cout": "10",
    "cout_unit": "µF",
    "amp": "10",
    "amp_unit": "mV",
    "freq": "1",
    "freq_unit": "kHz",
    "beta": "100",
    "beta_unit": "—",
    "vbe": "0.70",
    "vbe_unit": "V",
}

UNIT_OPTIONS = {
    "vcc": ("V", "mV"),
    "vbe": ("V", "mV"),
    "r1": ("Ω", "kΩ", "MΩ"),
    "r2": ("Ω", "kΩ", "MΩ"),
    "rb": ("Ω", "kΩ", "MΩ"),
    "rc": ("Ω", "kΩ", "MΩ"),
    "re": ("Ω", "kΩ", "MΩ"),
    "rl": ("Ω", "kΩ", "MΩ"),
    "cin": ("nF", "µF", "mF"),
    "cout": ("nF", "µF", "mF"),
    "amp": ("mV", "V"),
    "freq": ("Hz", "kHz", "MHz"),
    "beta": ("—",),
}

EXTRA_UNIT_FACTORS = {
    "rl": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "cin": {"nF": 1e-9, "µF": 1e-6, "mF": 1e-3},
    "cout": {"nF": 1e-9, "µF": 1e-6, "mF": 1e-3},
    "amp": {"mV": 1e-3, "V": 1.0},
    "freq": {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6},
}

DISPLAY_KEYS = (
    "ib_ua",
    "ic_ma",
    "ie_ma",
    "vb_v",
    "vc_v",
    "ve_v",
    "vce_v",
)

VERIFICATION_FIELDS = (
    "ib_a",
    "ic_a",
    "ie_a",
    "vb_v",
    "vc_v",
    "ve_v",
    "vce_v",
)


def _require_finite(values):
    if not all(math.isfinite(value) for value in values):
        raise ValueError("calculation produced a non-finite display value")


def _comparison_rows(main_dict, verification):
    specs = (
        ("IB", "ib_a", 1e6, "µA", 4),
        ("IC", "ic_a", 1e3, "mA", 4),
        ("IE", "ie_a", 1e3, "mA", 4),
        ("VB", "vb_v", 1.0, "V", 4),
        ("VC", "vc_v", 1.0, "V", 4),
        ("VE", "ve_v", 1.0, "V", 4),
        ("VCE", "vce_v", 1.0, "V", 4),
    )
    rows = []
    for label, key, scale, unit, decimals in specs:
        main_value = main_dict[key] * scale
        check_value = getattr(verification, key) * scale
        diff = abs(main_value - check_value)
        _require_finite((main_value, check_value, diff))
        rows.append(
            {
                "label": label,
                "main": main_value,
                "check": check_value,
                "diff": diff,
                "unit": unit,
                "decimals": decimals,
            }
        )
    return rows


def _results_rows(result_dict):
    return [
        {"label": "VB", "value": f"{result_dict['vb_v']:.2f}", "unit": "V"},
        {"label": "VE", "value": f"{result_dict['ve_v']:.2f}", "unit": "V"},
        {"label": "VC", "value": f"{result_dict['vc_v']:.2f}", "unit": "V"},
        {"label": "VCE", "value": f"{result_dict['vce_v']:.2f}", "unit": "V"},
        {"label": "IB", "value": f"{result_dict['ib_ua']:.1f}", "unit": "µA"},
        {"label": "IC", "value": f"{result_dict['ic_ma']:.2f}", "unit": "mA"},
        {"label": "IE", "value": f"{result_dict['ie_ma']:.2f}", "unit": "mA"},
    ]


def _region_card(result_dict):
    region = result_dict["region"]
    if region == ACTIVE:
        return {
            "kind": "ok",
            "icon": "✓",
            "title": "Active region approximation OK",
            "detail": (
                f"VCE = {result_dict['vce_v']:.3f} V > 0.2 V "
                "(transistor in forward-active region)"
            ),
        }
    if region == CUTOFF:
        return {
            "kind": "cutoff",
            "icon": "!",
            "title": "Cutoff Warning (Model Not Valid)",
            "detail": "Transistor is in cutoff (IB ≤ 0 A); forward-active model may not be valid.",
        }
    return {
        "kind": "saturation",
        "icon": "!",
        "title": "Saturation Warning (Model Not Valid)",
        "detail": "Transistor is in saturation (VCE ≤ 0.2 V); forward-active model may not be valid.",
    }


def _parse_amplifier_extras(form_data):
    parsed = {}
    errors = {}
    defaults = {
        "rl": ("10", "kΩ"),
        "cin": ("10", "µF"),
        "cout": ("10", "µF"),
        "amp": ("10", "mV"),
        "freq": ("1", "kHz"),
    }
    for field, (def_val, def_unit) in defaults.items():
        if field not in form_data:
            raw_val = def_val
        else:
            raw_val = str(form_data.get(field, "")).strip()

        raw_unit = str(form_data.get(f"{field}_unit", def_unit)).strip()
        if not raw_val:
            errors[field] = "Please enter this value"
            continue
        try:
            num = float(raw_val)
        except ValueError:
            errors[field] = "Please enter a number"
            continue
        if not math.isfinite(num) or num <= 0.0:
            errors[field] = "Must be greater than 0"
            continue
        factors = EXTRA_UNIT_FACTORS[field]
        if raw_unit not in factors:
            errors[field] = "Invalid unit"
            continue
        parsed[field] = num * factors[raw_unit]
    return parsed, errors


def _render_safe(context):
    html = render_template("index.html", **context)
    return html.replace("nan", "N/A")


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        context = {
            "form": dict(DEFAULT_FORM),
            "mode_labels": MODE_LABELS,
            "selected_mode": "divider",
            "selected_mode_label": MODE_LABELS["divider"],
            "analysis_mode": "op",
            "errors": {},
            "result": None,
            "verification": None,
            "comparison_rows": None,
            "region_card": None,
            "calculation_error": None,
            "unit_options": UNIT_OPTIONS,
            "results_rows": None,
            "spice_result": None,
        }

        if request.method == "GET":
            return _render_safe(context)

        submitted = dict(DEFAULT_FORM)
        submitted.update(request.form.to_dict())
        for field, base_unit in DEFAULT_UNITS.items():
            if f"{field}_unit" not in request.form:
                submitted[f"{field}_unit"] = base_unit

        has_explicit_mode = "mode" in request.form
        raw_mode = str(request.form["mode"]).strip() if has_explicit_mode else "divider"
        submitted["mode"] = raw_mode

        analysis_mode = str(request.form.get("analysis_mode", "op")).strip()
        if analysis_mode not in ("op", "ac", "tran"):
            analysis_mode = "op"
        submitted["analysis_mode"] = analysis_mode

        context["form"] = submitted
        context["analysis_mode"] = analysis_mode
        context["selected_mode"] = raw_mode if raw_mode in BIAS_MODES else "invalid"
        context["selected_mode_label"] = MODE_LABELS.get(raw_mode, f"Unknown Mode ({raw_mode or 'empty'})")

        if has_explicit_mode:
            parsed, errors = validate_and_parse_mode(request.form)
        else:
            legacy_inputs, errors = validate_and_parse(request.form)
            parsed = (
                {
                    "mode": "divider",
                    "vcc": legacy_inputs.vcc_v,
                    "r1": legacy_inputs.r1_ohm,
                    "r2": legacy_inputs.r2_ohm,
                    "rc": legacy_inputs.rc_ohm,
                    "re": legacy_inputs.re_ohm,
                    "beta": legacy_inputs.beta,
                    "vbe": legacy_inputs.vbe_v,
                }
                if legacy_inputs
                else None
            )

        extra_parsed, extra_errors = ({}, {})
        if raw_mode == "divider":
            extra_parsed, extra_errors = _parse_amplifier_extras(request.form)
            errors.update(extra_errors)

        if errors:
            context["errors"] = errors
            return _render_safe(context)

        mode = parsed["mode"]
        try:
            if mode == "divider":
                result_dict = calculate_voltage_divider(
                    vcc_v=float(parsed["vcc"]),
                    r1_ohm=float(parsed["r1"]),
                    r2_ohm=float(parsed["r2"]),
                    rc_ohm=float(parsed["rc"]),
                    re_ohm=float(parsed["re"]),
                    beta=float(parsed["beta"]),
                    vbe_v=float(parsed["vbe"]),
                )
            elif mode == "fixed":
                result_dict = calculate_fixed_bias(
                    vcc_v=float(parsed["vcc"]),
                    rb_ohm=float(parsed["rb"]),
                    rc_ohm=float(parsed["rc"]),
                    beta=float(parsed["beta"]),
                    vbe_v=float(parsed["vbe"]),
                )
            elif mode == "emitter":
                result_dict = calculate_emitter_bias(
                    vcc_v=float(parsed["vcc"]),
                    rb_ohm=float(parsed["rb"]),
                    rc_ohm=float(parsed["rc"]),
                    re_ohm=float(parsed["re"]),
                    beta=float(parsed["beta"]),
                    vbe_v=float(parsed["vbe"]),
                )
            else:
                context["errors"] = {"mode": "Unknown bias mode selected."}
                return _render_safe(context)

            _require_finite(result_dict[k] for k in DISPLAY_KEYS)

            verification = None
            comparison_rows = None
            spice_result = None

            if mode == "divider":
                if result_dict["region"] == ACTIVE:
                    divider_inputs = BiasInputs(
                        vcc_v=float(parsed["vcc"]),
                        r1_ohm=float(parsed["r1"]),
                        r2_ohm=float(parsed["r2"]),
                        rc_ohm=float(parsed["rc"]),
                        re_ohm=float(parsed["re"]),
                        beta=float(parsed["beta"]),
                        vbe_v=float(parsed["vbe"]),
                    )
                    divider_result = BiasResult(
                        vbb_v=result_dict["vbb_v"],
                        rb_ohm=result_dict["rb_ohm"],
                        ib_a=result_dict["ib_a"],
                        ic_a=result_dict["ic_a"],
                        ie_a=result_dict["ie_a"],
                        vb_v=result_dict["vb_v"],
                        vc_v=result_dict["vc_v"],
                        ve_v=result_dict["ve_v"],
                        vce_v=result_dict["vce_v"],
                        region=result_dict["region"],
                    )
                    verification = verify_active(divider_inputs, divider_result)
                    _require_finite(
                        getattr(verification, attr) for attr in VERIFICATION_FIELDS
                    )
                    comparison_rows = _comparison_rows(result_dict, verification)

                spice_result = run_ce_spice_simulation(
                    analysis=analysis_mode,
                    vcc_v=float(parsed["vcc"]),
                    r1_ohm=float(parsed["r1"]),
                    r2_ohm=float(parsed["r2"]),
                    rc_ohm=float(parsed["rc"]),
                    re_ohm=float(parsed["re"]),
                    rl_ohm=float(extra_parsed["rl"]),
                    cin_f=float(extra_parsed["cin"]),
                    cout_f=float(extra_parsed["cout"]),
                    amp_v=float(extra_parsed["amp"]),
                    freq_hz=float(extra_parsed["freq"]),
                )
        except (ValueError, OverflowError, ZeroDivisionError):
            context["calculation_error"] = f"[{context['selected_mode_label']}] {CALCULATION_ERROR}"
            return _render_safe(context)

        context["result"] = result_dict
        context["region_card"] = _region_card(result_dict)
        context["results_rows"] = _results_rows(result_dict)
        context["verification"] = verification
        context["comparison_rows"] = comparison_rows
        context["spice_result"] = spice_result

        return _render_safe(context)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)