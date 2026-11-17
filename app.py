import math

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
    validate_and_parse_mode,
)
from verification import verify_active


CALCULATION_ERROR = "These values do not produce a valid result."

DEFAULT_FORM = {
    "mode": "divider",
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
    "beta": ("—",),
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
            "detail": result_dict["warning"] or "IB ≤ 0 A; forward-active model may not be valid.",
        }
    return {
        "kind": "saturation",
        "icon": "!",
        "title": "Saturation Warning (Model Not Valid)",
        "detail": result_dict["warning"] or "VCE ≤ 0.2 V; forward-active model may not be valid.",
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        context = {
            "form": dict(DEFAULT_FORM),
            "mode_labels": MODE_LABELS,
            "selected_mode": "divider",
            "selected_mode_label": MODE_LABELS["divider"],
            "errors": {},
            "result": None,
            "verification": None,
            "comparison_rows": None,
            "region_card": None,
            "calculation_error": None,
            "unit_options": UNIT_OPTIONS,
            "results_rows": None,
        }

        if request.method == "GET":
            return render_template("index.html", **context)

        submitted = dict(DEFAULT_FORM)
        submitted.update(request.form.to_dict())
        for field, unit in DEFAULT_UNITS.items():
            submitted.setdefault(f"{field}_unit", unit)

        raw_mode = str(request.form.get("mode", "")).strip()
        context["form"] = submitted
        context["selected_mode"] = raw_mode if raw_mode in BIAS_MODES else "invalid"
        context["selected_mode_label"] = MODE_LABELS.get(raw_mode, f"Unknown Mode ({raw_mode or 'empty'})")

        parsed, errors = validate_and_parse_mode(request.form)
        if errors:
            context["errors"] = errors
            return render_template("index.html", **context)

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
                return render_template("index.html", **context)

            _require_finite(result_dict[k] for k in DISPLAY_KEYS)

            verification = None
            comparison_rows = None
            if mode == "divider" and result_dict["region"] == ACTIVE:
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
        except (ValueError, OverflowError, ZeroDivisionError):
            context["calculation_error"] = f"[{context['selected_mode_label']}] {CALCULATION_ERROR}"
            return render_template("index.html", **context)

        context["result"] = result_dict
        context["region_card"] = _region_card(result_dict)
        context["results_rows"] = _results_rows(result_dict)
        context["verification"] = verification
        context["comparison_rows"] = comparison_rows

        return render_template("index.html", **context)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)