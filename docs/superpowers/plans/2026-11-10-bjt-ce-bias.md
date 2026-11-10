# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Thai-language Flask web app that calculates, validates, and independently verifies the DC operating point of a voltage-divider-biased BJT common-emitter circuit.

**Architecture:** A server-rendered Flask route accepts the seven bias values, delegates validation and calculation to `bjt.py`, and delegates the independent nodal check to `verification.py`. Jinja renders Thai errors, the operating point, a region warning, and a comparison table. Tests use the standard library `unittest` plus Flask's test client.

**Tech Stack:** Python 3.12, Flask 3.x, Jinja2, HTML/CSS, stdlib `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Python 3.12; Flask `>=3.0,<4.0`; tests use only `unittest` and Flask's test client.
- Server-rendered pages only. No JavaScript, database, authentication, or deployment code.
- UI labels and user-facing messages are Thai; engineering symbols and SI units stay standard.
- `VCE_SAT_V = 0.2` is fixed and is not an input.
- Keep `electrical.py`, `test_electrical.py`, and `git-lab-ee-clone-check/` untouched.
- Existing `.gitignore` already covers `.venv/`, `__pycache__/`, and `*.pyc`; do not add generated files to git.
- Run the full suite with `.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`.
- Do not add AC, transient, small-signal, FET, or circuit-editor behavior.

## Review Focus

These are the failure modes most likely to bite a user that the spec implies but does not spell out. Each has a test in the task that owns the code.

1. Numeric but extreme inputs such as `1e308` must not produce `nan`, a 500 response, or a fake operating point; the page must show a Thai calculation error.
2. Non-finite strings (`nan`, `inf`, `-inf`), blank fields, and whitespace-padded numbers must be handled predictably.
3. Boundary values (`VBE = 0`, `VBE = 1.5`, `beta = 1`) must be accepted and calculated without crashing.
4. Cutoff when `VBE` exceeds `VCC`, and saturation with a negative model VCE, must show the correct region warning without clamping silently.
5. Submitted values containing HTML must be escaped when the form is re-rendered after an error.

---

### Task 1: Project Setup and Input Validation

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/test_bjt.py`
- Create: `bjt.py`
- Commit: `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`, `docs/superpowers/plans/2026-11-10-bjt-ce-bias.md`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `BiasInputs` frozen dataclass with fields `vcc_v`, `r1_ohm`, `r2_ohm`, `rc_ohm`, `re_ohm`, `beta`, `vbe_v`, all `float`.
  - `validate_and_parse(raw: Mapping[str, str]) -> tuple[BiasInputs | None, dict[str, str]]`. Returns `(inputs, {})` when valid, or `(None, errors)` where `errors` is keyed by `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`.

- [ ] **Step 1: Commit the approved design and plan**

```bash
git add docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md docs/superpowers/plans/2026-11-10-bjt-ce-bias.md
git commit -m "docs: add BJT bias design and implementation plan"
```

- [ ] **Step 2: Create the environment and project skeleton**

Create `requirements.txt`:

```text
Flask>=3.0,<4.0
```

Create an empty `tests/__init__.py`. Then run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import flask; print(flask.__version__)"
```

Expected: a Flask 3.x version prints without error.

- [ ] **Step 3: Write the failing validation tests**

Add to `tests/test_bjt.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_bjt -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'bjt'`.

- [ ] **Step 5: Implement `bjt.py`**

Create `bjt.py` with:

- Imports for `dataclass`, `math`, and `Mapping`.
- `REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")` and
  `RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")`.
- The frozen `BiasInputs` dataclass exactly as defined in Interfaces.
- `validate_and_parse(raw: Mapping[str, str])` that:
  - Reads each required field with `str(raw.get(field, "")).strip()`.
  - Uses `"กรุณากรอกค่านี้"` for a blank field.
  - Converts with `float`; uses `"กรุณากรอกเป็นตัวเลข"` for a conversion
    failure or a non-finite result.
  - Applies the rules and messages from Task 1's tests: VCC `> 0`,
    resistances `> 0`, beta `>= 1`, VBE `0..1.5`.
  - Returns `(None, errors)` if any error exists, otherwise
    `(BiasInputs(...), {})`.

- [ ] **Step 6: Run the tests to verify they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_bjt -v
```

Expected: all validation tests PASS.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt bjt.py tests/__init__.py tests/test_bjt.py
git commit -m "feat: add BJT input validation"
```

---

### Task 2: Main Bias Calculation and Region Classification

**Files:**
- Modify: `bjt.py`
- Modify: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `BiasInputs` and the parsed values from Task 1.
- Produces:
  - Constants `ACTIVE = "active"`, `CUTOFF = "cutoff"`, `SATURATION = "saturation"`, `VCE_SAT_V = 0.2`.
  - `BiasResult` frozen dataclass with fields `vbb_v`, `rb_ohm`, `ib_a`, `ic_a`, `ie_a`, `vb_v`, `vc_v`, `ve_v`, `vce_v`, `region`, all `float` except `region: str`.
  - `analyze_bias(inputs: BiasInputs) -> BiasResult`.

- [ ] **Step 1: Write the failing calculation tests**

Add this import near the top of `tests/test_bjt.py` (merge it with the existing
`bjt` import if preferred), and add the class before the
`if __name__ == "__main__":` block:

```python
from bjt import ACTIVE, CUTOFF, SATURATION, VCE_SAT_V, BiasInputs, analyze_bias


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
```

- [ ] **Step 2: Run the new tests to verify they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_bjt.TestAnalyzeBias -v
```

Expected: FAIL because `ACTIVE`, `CUTOFF`, `SATURATION`, `VCE_SAT_V`, and `analyze_bias` are not defined.

- [ ] **Step 3: Implement `analyze_bias` in `bjt.py`**

Add the constants and `BiasResult` above `analyze_bias`, then implement:

- `vbb_v = vcc_v * r2_ohm / (r1_ohm + r2_ohm)`
- `rb_ohm = r1_ohm * r2_ohm / (r1_ohm + r2_ohm)`
- If `vbb_v <= vbe_v`, return cutoff with `ib_a = ic_a = ie_a = 0`, `vb_v = vbb_v`, `vc_v = vcc_v`, `ve_v = 0`, `vce_v = vcc_v`.
- Otherwise compute `ib_a`, `ic_a`, `ie_a`, `ve_v`, `vc_v`, `vb_v`, `vce_v` with the formulas in the spec.
- Construct the `BiasResult` for the cutoff or active path, then check every numeric field (`vbb_v`, `rb_ohm`, `ib_a`, `ic_a`, `ie_a`, `vb_v`, `vc_v`, `ve_v`, `vce_v`) with `math.isfinite`; if any is not finite, raise `ValueError("calculation produced a non-finite result")`.
- Set `region = SATURATION` when `vce_v <= VCE_SAT_V`, otherwise `ACTIVE`.
- Return the validated `BiasResult`.

Do not clamp a saturated or negative `vce_v`.

- [ ] **Step 4: Run the tests to verify they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_bjt -v
```

Expected: all validation and calculation tests PASS.

- [ ] **Step 5: Commit**

```bash
git add bjt.py tests/test_bjt.py
git commit -m "feat: calculate BJT DC bias point"
```

---

### Task 3: Independent Nodal Verification

**Files:**
- Create: `verification.py`
- Create: `tests/test_verification.py`

**Interfaces:**
- Consumes: `BiasInputs`, `BiasResult`, and `analyze_bias` from Tasks 1–2.
- Produces:
  - `REL_TOL = 1e-9`.
  - `VerificationResult` frozen dataclass with fields `ib_a`, `ic_a`, `ie_a`, `vb_v`, `vc_v`, `ve_v`, `vce_v`, `matches`.
  - `verify_active(inputs: BiasInputs, main: BiasResult) -> VerificationResult`.

- [ ] **Step 1: Write the failing verification tests**

Create `tests/test_verification.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_verification -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'verification'`.

- [ ] **Step 3: Implement `verification.py`**

Implement the nodal formula from the spec:

```text
VB = (VCC/R1 + VBE/((beta + 1) * RE))
     / (1/R1 + 1/R2 + 1/((beta + 1) * RE))
```

Then derive `VE`, `IE`, `IB`, `IC`, `VC`, and `VCE`. Do not call `analyze_bias` or reuse its intermediate values. Compare each quantity with `math.isclose(rel_tol=REL_TOL, abs_tol=1e-12)` and set `matches` to the conjunction.

- [ ] **Step 4: Run the tests to verify they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_verification -v
```

Expected: all verification tests PASS.

- [ ] **Step 5: Commit**

```bash
git add verification.py tests/test_verification.py
git commit -m "feat: add independent nodal verification"
```

---

### Task 4: Flask Routes and Templates

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: `validate_and_parse`, `analyze_bias`, `ACTIVE`, `CUTOFF`, `SATURATION` from `bjt.py`; `verify_active` from `verification.py`.
- Produces: `create_app() -> Flask`; module-level `app = create_app()`; route `GET/POST /`.
- Template context keys: `form`, `errors`, `result`, `verification`, `comparison_rows`, `region_label`, `warning`, `calculation_error`.
- `comparison_rows` is a list of dicts with keys `label`, `main`, `check`, `diff`, `unit`, `decimals`.

- [ ] **Step 1: Write the failing route tests**

Create `tests/test_app.py`:

```python
import unittest

from app import create_app

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('name="vcc"', text)
        self.assertIn("วงจรไบแอสแบบแบ่งแรงดัน", text)

    def test_valid_post_shows_active_result(self):
        response = self.client.post("/", data=VALID)
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("8.8245", text)
        self.assertIn("7.7554", text)
        self.assertIn("ทำงานปกติ (Active)", text)
        self.assertIn("ตรวจสอบด้วยการคำนวณอิสระ", text)
        self.assertIn("ผลตรวจสอบ: ผ่าน", text)

    def test_invalid_post_shows_thai_error(self):
        data = dict(VALID)
        data["vcc"] = "0"
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("VCC ต้องมากกว่า 0 V", text)
        self.assertNotIn("ตรวจสอบด้วยการคำนวณอิสระ", text)

    def test_cutoff_shows_warning(self):
        data = dict(VALID)
        data["r2"] = "1000"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("ตัดขาด (Cutoff)", text)
        self.assertIn("ใช้ได้เฉพาะย่าน Active", text)

    def test_saturation_shows_warning(self):
        data = dict(VALID)
        data["r1"] = "10000"
        data["r2"] = "47000"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("อิ่มตัว (Saturation)", text)
        self.assertIn("0.2 V", text)

    def test_extreme_values_show_error_not_crash(self):
        data = dict(VALID)
        data.update(
            {
                "vcc": "1e308",
                "r1": "1e308",
                "r2": "1e308",
                "rc": "1e308",
                "re": "1e308",
            }
        )
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ไม่สามารถให้ผลลัพธ์ที่ถูกต้องได้",
            response.get_data(as_text=True),
        )

    def test_submitted_html_is_escaped(self):
        data = dict(VALID)
        data["vcc"] = "<script>alert(1)</script>"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn("<script>alert(1)</script>", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `app.py` and `templates/index.html`**

`app.py` must:

- Import `Flask`, `render_template`, and `request`.
- Define `REGION_LABELS` with exactly:
  - `ACTIVE`: `"ทำงานปกติ (Active)"`
  - `CUTOFF`: `"ตัดขาด (Cutoff)"`
  - `SATURATION`: `"อิ่มตัว (Saturation)"`
- Define `WARNINGS`:
  - `CUTOFF`: `"VBB ≤ VBE: ทรานซิสเตอร์ตัดขาด (IB ≈ 0)"`
  - `SATURATION`: `"VCE ≤ 0.2 V: ทรานซิสเตอร์อิ่มตัว ค่า VCE จากแบบจำลองเชิงเส้นใช้ไม่ได้"`
  - `ACTIVE`: `None`
- Implement `_comparison_rows(main, verification)` with rows in this order and these display units/decimals:
  - `IB`: µA, 4 decimals
  - `IC`: mA, 4 decimals
  - `IE`: mA, 4 decimals
  - `VB`, `VC`, `VE`, `VCE`: V, 4 decimals
  - `diff = abs(main_value - check_value)`
- On `GET /`, render the empty form.
- On `POST /`, call `validate_and_parse(request.form)`. If errors, re-render with the submitted `form` and `errors`, no result.
- If valid, call `analyze_bias`. Catch `(ValueError, OverflowError, ZeroDivisionError)` and render `calculation_error = "ค่าที่กรอกทำให้การคำนวณไม่สามารถให้ผลลัพธ์ที่ถูกต้องได้"`.
- If region is `ACTIVE`, call `verify_active` and build `comparison_rows`.
- For cutoff or saturation, leave `verification` and `comparison_rows` as `None`.
- Use `render_template("index.html", ...)` with all context keys listed in Interfaces.
- End with `app = create_app()` and, under `if __name__ == "__main__":`,
  `app.run(host="127.0.0.1", port=5000, debug=True)`.

`templates/index.html` must:

- Include `<meta charset="utf-8">` and the Thai title.
- Render the seven inputs with `name` attributes `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`; preserve `form.get(...)` values.
- Show each field error from `errors` next to its input.
- Show the submit button labeled `คำนวณ`.
- When `calculation_error` is set, show it in a warning box.
- When `result` is set, show:
  - The region badge using `region_label` and class `badge-{{ result.region }}`.
  - The warning box when `warning` is set.
  - A `จุดทำงาน DC` table with `IB` in µA, `IC` and `IE` in mA, and `VB`, `VC`, `VE`, `VCE` in V, all to 4 decimals.
- When `verification` is set, show `ตรวจสอบด้วยการคำนวณอิสระ`, the comparison table from `comparison_rows`, and `ผลตรวจสอบ: ผ่าน` or `ผลตรวจสอบ: ไม่ผ่าน` from `verification.matches`.
- When `result` is set but `verification` is not, show `การตรวจสอบด้วยวิธี nodal ใช้ได้เฉพาะย่าน Active`.
- Do not perform engineering formulas in the template.

- [ ] **Step 4: Run the tests to verify they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: all route tests PASS.

- [ ] **Step 5: Run the full suite**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app.py templates/index.html tests/test_app.py
git commit -m "feat: add Flask web interface"
```

---

### Task 5: Styling and Visual Check

**Files:**
- Create: `static/style.css`
- Modify: `templates/index.html`

**Interfaces:**
- Consumes: the template and route from Task 4.
- Produces: a linked stylesheet and readable layout; no behavior changes.

- [ ] **Step 1: Add the stylesheet link**

In the `<head>` of `templates/index.html`, add:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

- [ ] **Step 2: Create `static/style.css`**

Use a simple readable style:

- Centered container with `max-width: 900px`, comfortable padding, and a light background.
- A white card with a subtle border and shadow.
- A responsive form grid that collapses to one column on narrow screens.
- Clear input borders, a visible focus style, and red error text.
- A result table with right-aligned numeric columns.
- Region badge colors: green for `badge-active`, gray for `badge-cutoff`, orange/red for `badge-saturation`.
- A warning box with a visible border and background.
- No animations, external fonts, or frameworks.

- [ ] **Step 3: Run the full suite**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Expected: all tests still PASS.

- [ ] **Step 4: Check the page in a browser**

Start the app:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000` and verify the active example from the spec. Check that:

- The form and results are readable at laptop width.
- The active badge is green.
- The comparison table is aligned and shows `ผ่าน`.
- No CSS 404 appears in the browser console.

- [ ] **Step 5: Commit**

```bash
git add static/style.css templates/index.html
git commit -m "style: add page styling"
```

---

### Task 6: README, End-to-End Demo, and Push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the complete app and test suite.
- Produces: Thai usage documentation, a verified localhost demo, and a pushed GitHub commit.

- [ ] **Step 1: Rewrite `README.md` in Thai**

Include these sections:

- `# BJT Common-Emitter DC Bias Calculator`
- `## คำอธิบาย` — one paragraph describing the voltage-divider bias calculator.
- `## ฟีเจอร์` — seven inputs, DC operating point, region warning, independent nodal check, Thai validation.
- `## วิธีติดตั้ง` — `python -m venv .venv`, install `requirements.txt`.
- `## วิธีรัน` — `.\.venv\Scripts\python.exe app.py`, open `http://127.0.0.1:5000`.
- `## วิธีทดสอบ` — `.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`.
- `## ตัวอย่างการใช้งาน` — the active example and expected values from the spec.
- `## โครงสร้างไฟล์` — list the app files.
- `## หมายเหตุ` — the earlier `electrical.py` and `test_electrical.py` remain as the previous Ohm's-law exercise.

- [ ] **Step 2: Run the full suite one final time**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run the end-to-end demo**

Stop any previously running Flask process, then start the app:

```powershell
.\.venv\Scripts\python.exe app.py
```

At `http://127.0.0.1:5000`, demonstrate:

1. Active: the spec example; confirm `7.7554 V` and `ผ่าน`.
2. Cutoff: set `R2 = 1000 Ω`; confirm the cutoff warning.
3. Saturation: set `R1 = 10000 Ω`, `R2 = 47000 Ω`; confirm the saturation warning.
4. Invalid: set `VCC = 0`; confirm the Thai validation error and preserved inputs.

- [ ] **Step 4: Commit the documentation**

```bash
git add README.md
git commit -m "docs: update README for BJT bias app"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```

Expected: the push succeeds and `git status` is clean.

- [ ] **Step 6: Verify the repository state**

```bash
git status --short
git log --oneline -8
```

Expected: no uncommitted changes, and the recent log contains the design, validation, calculation, verification, web interface, styling, and README commits.
