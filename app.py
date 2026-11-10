import math

from flask import Flask, render_template, request

from bjt import ACTIVE, CUTOFF, SATURATION, analyze_bias, validate_and_parse
from verification import verify_active


CALCULATION_ERROR = "These values do not produce a valid result."

DEFAULT_FORM = {
    "vcc": "12.0",
    "vcc_unit": "V",
    "r1": "100",
    "r1_unit": "kΩ",
    "r2": "22",
    "r2_unit": "kΩ",
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
    "rc": ("Ω", "kΩ", "MΩ"),
    "re": ("Ω", "kΩ", "MΩ"),
    "beta": ("—",),
}

DISPLAY_SCALES = (
    ("ib_a", 1e6),
    ("ic_a", 1e3),
    ("ie_a", 1e3),
    ("vb_v", 1.0),
    ("vc_v", 1.0),
    ("ve_v", 1.0),
    ("vce_v", 1.0),
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


def _comparison_rows(main, verification):
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
    for label, attr, scale, unit, decimals in specs:
        main_value = getattr(main, attr) * scale
        check_value = getattr(verification, attr) * scale
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


def _results_rows(result):
    return [
        {"label": "VB", "value": f"{result.vb_v:.2f}", "unit": "V"},
        {"label": "VE", "value": f"{result.ve_v:.2f}", "unit": "V"},
        {"label": "VC", "value": f"{result.vc_v:.2f}", "unit": "V"},
        {"label": "VCE", "value": f"{result.vce_v:.2f}", "unit": "V"},
        {"label": "IB", "value": f"{result.ib_a * 1e6:.1f}", "unit": "µA"},
        {"label": "IC", "value": f"{result.ic_a * 1e3:.2f}", "unit": "mA"},
        {"label": "IE", "value": f"{result.ie_a * 1e3:.2f}", "unit": "mA"},
    ]


def _region_card(result):
    if result.region == ACTIVE:
        return {
            "kind": "ok",
            "title": "Active region approximation OK",
            "detail": (
                f"VCE = {result.vce_v:.2f} V > 0.2 V "
                "(transistor in active region)"
            ),
        }
    if result.region == CUTOFF:
        return {
            "kind": "cutoff",
            "title": "Transistor is in cutoff",
            "detail": "VBB ≤ VBE, so IB ≈ 0 and the transistor is off.",
        }
    return {
        "kind": "saturation",
        "title": "Transistor is in saturation",
        "detail": "VCE ≤ 0.2 V; the linear VCE model is not valid.",
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        context = {
            "form": dict(DEFAULT_FORM),
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

        inputs, errors = validate_and_parse(request.form)
        context["form"] = request.form
        if errors:
            context["errors"] = errors
            return render_template("index.html", **context)

        try:
            result = analyze_bias(inputs)
            _require_finite(
                getattr(result, attr) * scale for attr, scale in DISPLAY_SCALES
            )

            verification = None
            comparison_rows = None
            if result.region == ACTIVE:
                verification = verify_active(inputs, result)
                _require_finite(
                    getattr(verification, attr) for attr in VERIFICATION_FIELDS
                )
                comparison_rows = _comparison_rows(result, verification)
        except (ValueError, OverflowError, ZeroDivisionError):
            context["calculation_error"] = CALCULATION_ERROR
            return render_template("index.html", **context)

        context["result"] = result
        context["region_card"] = _region_card(result)
        context["results_rows"] = _results_rows(result)
        context["verification"] = verification
        context["comparison_rows"] = comparison_rows

        return render_template("index.html", **context)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
