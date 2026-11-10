from flask import Flask, render_template, request

from bjt import ACTIVE, CUTOFF, SATURATION, analyze_bias, validate_and_parse
from verification import verify_active


REGION_LABELS = {
    ACTIVE: "ทำงานปกติ (Active)",
    CUTOFF: "ตัดขาด (Cutoff)",
    SATURATION: "อิ่มตัว (Saturation)",
}

WARNINGS = {
    ACTIVE: None,
    CUTOFF: "VBB ≤ VBE: ทรานซิสเตอร์ตัดขาด (IB ≈ 0)",
    SATURATION: (
        "VCE ≤ 0.2 V: ทรานซิสเตอร์อิ่มตัว "
        "ค่า VCE จากแบบจำลองเชิงเส้นใช้ไม่ได้"
    ),
}

CALCULATION_ERROR = "ค่าที่กรอกทำให้การคำนวณไม่สามารถให้ผลลัพธ์ที่ถูกต้องได้"


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
        rows.append(
            {
                "label": label,
                "main": main_value,
                "check": check_value,
                "diff": abs(main_value - check_value),
                "unit": unit,
                "decimals": decimals,
            }
        )
    return rows


def create_app():
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        context = {
            "form": {},
            "errors": {},
            "result": None,
            "verification": None,
            "comparison_rows": None,
            "region_label": None,
            "warning": None,
            "calculation_error": None,
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
        except (ValueError, OverflowError, ZeroDivisionError):
            context["calculation_error"] = CALCULATION_ERROR
            return render_template("index.html", **context)

        context["result"] = result
        context["region_label"] = REGION_LABELS[result.region]
        context["warning"] = WARNINGS[result.region]

        if result.region == ACTIVE:
            verification = verify_active(inputs, result)
            context["verification"] = verification
            context["comparison_rows"] = _comparison_rows(result, verification)

        return render_template("index.html", **context)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
