# BJT DC Bias Web App — English Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Restyle the BJT common-emitter DC bias app into the supplied English three-column lab dashboard, with functional unit dropdowns, a live-value circuit SVG, and English validation.

**Architecture:** Keep the existing server-rendered Flask structure. `bjt.py` converts value+unit input into base units before the unchanged Thevenin calculation. `app.py` builds display rows and a region card for the template. `templates/index.html` is rewritten around a three-card grid plus a verification card and a Week 2 Goal card. `static/style.css` is rewritten to match the mockup. No JavaScript and no new dependencies.

**Tech Stack:** Python 3.12, Flask 3.x, Jinja2, inline SVG, CSS, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-redesign-design.md`

## Global Constraints

- All user-facing UI text is English.
- Internal base units stay V, Ω, A; `BiasInputs` keeps its current fields.
- Unit dropdowns are functional; a selected unit must change the parsed value.
- No JavaScript, no new dependencies, no change to the Thevenin or nodal maths.
- Do not hard-code the mockup's result numbers; compute from the inputs.
- Existing non-finite guard must keep showing an English calculation error.
- The independent nodal verification must remain visible in the UI.
- The mockup's own numbers are approximate (it ignores base current); the app shows the exact model result for the same inputs.
- The prefilled example is only a default. Every field stays editable, and any valid values recalculate on submit.

## Review Focus

1. Unit conversion is applied correctly: `100 kΩ` must become `100000 Ω`, not `100 Ω`.
2. A disallowed unit (for example `beta_unit=kΩ`) must show a field error, never compute or crash.
3. Missing unit fields from older callers must default to the base unit and still calculate.
4. Extreme or non-finite values must still show the English calculation error, never `nan`/`inf`.
5. The region card must reflect the actual region (active/cutoff/saturation), not always show green.

---

### Task 1: Unit-Aware Validation and English Messages

**Files:**
- Modify: `bjt.py`
- Modify: `tests/test_bjt.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `VOLTAGE_UNITS = {"V": 1.0, "mV": 1e-3}`
  - `RESISTANCE_UNITS = {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6}`
  - `BETA_UNITS = {"—": 1.0}`
  - `UNIT_FACTORS: dict[str, dict[str, float]]` keyed by form field.
  - `DEFAULT_UNITS: dict[str, str]` keyed by form field.
  - `validate_and_parse(raw: Mapping[str, str]) -> tuple[BiasInputs | None, dict[str, str]]` unchanged signature.

- [x] **Step 1: Write the failing unit tests**

Append to `TestValidation` in `tests/test_bjt.py`:

```python
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
```

Update the expected messages in the existing tests to English:
`Please enter this value`, `Please enter a number`, `Resistance must be greater than 0 Ω`, `β must be at least 1`, `VBE must be between 0 and 1.5 V`.

- [x] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_bjt -v`
Expected: the new unit tests fail because units are ignored, and the message assertions fail with Thai text.

- [x] **Step 3: Implement unit parsing in `bjt.py`**

Add the constants above. In `validate_and_parse`, keep the existing `math.isfinite` check on the parsed number, then read `raw.get(f"{field}_unit", DEFAULT_UNITS[field])`, strip it, and multiply by `UNIT_FACTORS[field][unit]`; on an unknown unit set `errors[field] = "Please select a valid unit"` and continue. Applying the factor after the finite check is deliberate: a finite value times `kΩ` that overflows stays a calculation error (caught by `analyze_bias`), matching the existing extreme-value test. Replace every Thai message with its English counterpart from the spec.

- [x] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_bjt -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add bjt.py tests/test_bjt.py
git commit -m "feat: parse unit selections in bias inputs"
```

---

### Task 2: Dashboard Route Context and Template

**Files:**
- Modify: `app.py`
- Rewrite: `templates/index.html`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `validate_and_parse`, `analyze_bias`, `ACTIVE`, `CUTOFF`, `SATURATION`, `verify_active`.
- Produces:
  - `DEFAULT_FORM: dict[str, str]` with the mockup example and its units.
  - `UNIT_OPTIONS: dict[str, tuple[str, ...]]` keyed by form field.
  - `_results_rows(result: BiasResult) -> list[dict[str, str]]` with keys `label`, `value`, `unit`, ordered VB, VE, VC, VCE, IB, IC, IE.
  - `_region_card(result: BiasResult) -> dict[str, str]` with keys `kind` (`ok`/`cutoff`/`saturation`), `title`, `detail`.
  - Template context keys: `form`, `errors`, `result`, `verification`, `comparison_rows`, `region_card`, `calculation_error`, `unit_options`, `results_rows`.

- [x] **Step 1: Write the failing route tests**

Replace `VALID` in `tests/test_app.py` with the mockup example plus units:

```python
VALID = {
    "vcc": "12.0", "vcc_unit": "V",
    "r1": "100", "r1_unit": "kΩ",
    "r2": "22", "r2_unit": "kΩ",
    "rc": "2.2", "rc_unit": "kΩ",
    "re": "1.0", "re_unit": "kΩ",
    "beta": "100", "beta_unit": "—",
    "vbe": "0.70", "vbe_unit": "V",
}
```

Replace the assertions of the existing tests and add:

```python
    def test_get_prefills_example(self):
        text = self.client.get("/").get_data(as_text=True)
        self.assertIn("Lab 02: BJT DC Bias Web App", text)
        self.assertIn("Computer Programming for Electrical Engineers", text)
        self.assertIn('value="12.0"', text)
        self.assertIn('name="r1_unit"', text)
        self.assertIn("kΩ", text)

    def test_valid_post_shows_active_result(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        for value in ("1.94", "1.24", "9.29", "8.05", "12.3", "1.23"):
            self.assertIn(value, text)
        self.assertIn("Active region approximation OK", text)
        self.assertIn("Independent Verification", text)
        self.assertIn("Verification: PASS", text)

    def test_invalid_post_shows_english_error(self):
        data = dict(VALID)
        data["vcc"] = "0"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("VCC must be greater than 0 V", text)
        self.assertNotIn("Independent Verification", text)

    def test_cutoff_shows_card(self):
        data = dict(VALID)
        data["r2"] = "1"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("Transistor is in cutoff", text)

    def test_saturation_shows_card(self):
        data = dict(VALID)
        data["r1"] = "22"
        data["r2"] = "100"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("Transistor is in saturation", text)

    def test_other_values_calculate(self):
        data = {
            "vcc": "9", "vcc_unit": "V",
            "r1": "47", "r1_unit": "kΩ",
            "r2": "10", "r2_unit": "kΩ",
            "rc": "1", "rc_unit": "kΩ",
            "re": "470", "re_unit": "Ω",
            "beta": "200", "beta_unit": "—",
            "vbe": "0.65", "vbe_unit": "V",
        }
        text = self.client.post("/", data=data).get_data(as_text=True)
        for value in ("1.50", "0.85", "7.19", "6.34", "9.0", "1.81", "1.82"):
            self.assertIn(value, text)
        self.assertIn("Active region approximation OK", text)

    def test_svg_contains_submitted_values(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("100 kΩ", text)
        self.assertIn("12.0 V", text)

    def test_extreme_values_show_error_not_crash(self):
        data = dict(VALID)
        data.update({"vcc": "1e308", "r1": "1e308", "r2": "1e308",
                     "rc": "1e308", "re": "1e308"})
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("These values do not produce a valid result.", text)

    def test_non_finite_verification_shows_error(self):
        data = dict(VALID)
        data.update({"r1": "5e-324", "rc": "1", "r1_unit": "Ω", "rc_unit": "Ω"})
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("These values do not produce a valid result.", text)
        self.assertNotIn("nan", text)

    def test_display_scaling_overflow_shows_error(self):
        data = dict(VALID)
        data.update({"r1": "1e-307", "r2": "1e-307", "rc": "1e-303",
                     "re": "1e-303", "beta": "1", "r1_unit": "Ω",
                     "r2_unit": "Ω", "rc_unit": "Ω", "re_unit": "Ω"})
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("These values do not produce a valid result.", text)
        self.assertNotIn("inf", text)
```

Keep `test_submitted_html_is_escaped` (still asserting `&lt;script&gt;`).

- [x] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: FAIL because the template still has the old Thai layout and no unit selects.

- [x] **Step 3: Implement the route context in `app.py`**

Add `DEFAULT_FORM`, `UNIT_OPTIONS`, `_results_rows`, and `_region_card` as specified above. Initialize the GET context with `dict(DEFAULT_FORM)`, `UNIT_OPTIONS`, and empty result fields. On success set `results_rows` and `region_card`; keep the existing finite checks and verification. Change `CALCULATION_ERROR` to `"These values do not produce a valid result."`.

- [x] **Step 4: Rewrite `templates/index.html`**

Build the mockup structure:

- Header with an inline chip SVG, `Lab 02: BJT DC Bias Web App`, the subtitle, and the blue course badge.
- Three cards: Input Parameters, Circuit, DC Bias Results.
- Input rows for `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`, each with an input and a `select` named `<field>_unit` populated from `unit_options`. Show `errors[field]` under the row. Beta's select shows `—`.
- Submit button `Calculate DC Bias`.
- Results card: if `calculation_error`, show it; elif `result`, render `results_rows` as `label | value unit` and the `region_card` with class `region-{{ region_card.kind }}`; else a placeholder.
- Circuit card: inline SVG with dynamic text from `form` for VCC, R1, R2, RC, RE, and β, using `form.get('vcc', '')` and `form.get('vcc_unit', 'V')` etc. Render the R1 text as `{{ form.get('r1', '') }} {{ form.get('r1_unit', 'Ω') }}` so the test can find `100 kΩ`.
- Verification card below the grid: keep the existing comparison table, heading `Independent Verification`, and `Verification: PASS/FAIL`.
- Week 2 Goal card with the mockup text.

- [x] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add app.py templates/index.html tests/test_app.py
git commit -m "feat: build English dashboard layout"
```

---

### Task 3: Styling to Match the Mockup

**Files:**
- Rewrite: `static/style.css`

**Interfaces:**
- Consumes: the class names from Task 2 (`app-header`, `brand`, `chip-icon`, `course-badge`, `dashboard`, `card`, `field-row`, `field-control`, `results-table`, `region-card`, `region-ok`, `region-cutoff`, `region-saturation`, `verification-card`, `goal-card`, `error`, `placeholder`).
- Produces: no behavior changes.

- [x] **Step 1: Rewrite `static/style.css`**

Match the mockup: light grey background, white cards with a thin border and soft shadow, a three-column grid that collapses to one column below ~980 px, teal accents, blue course badge, right-aligned numeric result column with a pale blue fill, green/orange/red region cards, and a pale blue Week 2 Goal card. Keep inputs and selects readable and keyboard-focusable.

- [x] **Step 2: Run the full suite**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`
Expected: PASS (CSS changes no behavior).

- [x] **Step 3: Visual check in the browser**

Start the app if it is not already running: `.venv\Scripts\python.exe app.py`, open `http://127.0.0.1:5000`, and confirm the three cards, header badge, active card, verification card, and goal card render, with no console errors. Check a narrow viewport collapses to one column.

- [x] **Step 4: Commit**

```bash
git add static/style.css
git commit -m "style: match the lab dashboard mockup"
```

---

### Task 4: README, Demo, and Merge

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the finished app and test suite.
- Produces: English usage docs, a verified localhost demo, and `main` updated on GitHub.

- [x] **Step 1: Update `README.md`**

Document the English dashboard, the unit dropdowns (V/mV, Ω/kΩ/MΩ), the mockup example inputs, the exact model results for those inputs, and the three region cards. Keep the install/run/test commands.

- [x] **Step 2: Run the full suite**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`
Expected: all tests PASS.

- [x] **Step 3: Demo the three regions and an invalid input**

Use the browser at `http://127.0.0.1:5000` to confirm active (default example), cutoff (`R2 = 1 kΩ`), saturation (`R1 = 22 kΩ`, `R2 = 100 kΩ`), and invalid (`VCC = 0`). Confirm no console errors.

- [x] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: describe the English dashboard and units"
```

- [x] **Step 5: Merge and push**

```bash
git -C "C:\Users\b6837129\Desktop\Gitlab" merge --ff-only bjt-ce-bias
git -C "C:\Users\b6837129\Desktop\Gitlab" push origin main
git push origin bjt-ce-bias
```

Verify both working trees are clean and `main` points at the final commit.
