# BJT Common-Emitter DC Bias Web App — Design

- Course: ENG29 2121
- Date: 2026-11-10
- Status: Proposed — awaiting approval
- Size: Small (one page, two calculation modules, tests)

## Intent

Build a small Flask web application that calculates the DC operating point of a
BJT common-emitter amplifier using voltage-divider bias. A student enters seven
values and receives a validated result with units, a region warning, and a
second independent calculation for comparison.

The UI is in Thai. Engineering labels and units remain in standard symbols.

## Why

This is the lab deliverable. It must show a real separation between engineering
logic, Flask routes, HTML templates, CSS, and tests, and it must demonstrate
that the calculated operating point is correct rather than merely printed.

## Goals

- Accept VCC, R1, R2, RC, RE, beta, and VBE from a web form.
- Validate every input and show useful Thai error messages.
- Calculate IB, IC, IE, VB, VC, VE, and VCE with units.
- Classify the operating region: active, cutoff, or saturation.
- Warn when the linear model is not valid.
- Compare the main result with an independently derived nodal calculation.
- Provide automated tests for the engineering logic and the Flask routes.
- Run locally at `http://127.0.0.1:5000` and commit the work to GitHub.

## Non-goals

- AC analysis, gain, frequency response, or transient analysis.
- Small-signal models, hybrid-pi parameters, or load lines.
- A schematic editor, netlist parser, or arbitrary circuit solver.
- FET, op-amp, or multi-transistor circuits.
- Database, login, user accounts, deployment, or JavaScript framework.

## Anti-goals

- Hard-coded answers or a calculator that only works for one example.
- Repeating the engineering formula inside the template.
- Silently accepting zero, negative, or non-numeric inputs.
- Reporting a saturation result as if the linear model were still valid.
- Building more UI than the lab needs.

## Constraints

- Python 3.12, Flask, and the Python standard library.
- Tests use `unittest` and Flask's test client, consistent with the existing
  `test_electrical.py`; no extra test dependency is required.
- Server-rendered pages only. No JavaScript.
- VCE(sat) is fixed at 0.2 V. It is not an input.
- The existing `electrical.py`, `test_electrical.py`, and
  `git-lab-ee-clone-check/` files are kept. The BJT app is added alongside
  them and becomes the main README deliverable.
- The application must be runnable with a local virtual environment.

## Approaches Considered

### A. Server-rendered Flask, no JavaScript (chosen)

One route handles `GET` and `POST`. The form posts back to the same page, and
Jinja renders either errors or results. Engineering logic lives in
`bjt.py`; the independent check lives in `verification.py`.

Trade-off: each calculation reloads the page. In exchange, all logic stays in
Python, there is only one source of truth, and both the calculation and the
page are easy to test.

### B. Flask JSON endpoint plus JavaScript live results

The form would update results without a reload. This adds fetch handling,
client-side state, and either duplicated formulas or extra API tests. It is
more polish than a short lab needs.

### C. Flask with WTForms

WTForms would provide form validation, but it adds a dependency and boilerplate
for seven numeric fields. A small validation function is easier to read and
test directly.

Approach A is the smallest design that meets every requirement.

## Engineering Model

### Main calculation: Thevenin equivalent

The voltage divider is replaced by:

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 || R2 = R1 * R2 / (R1 + R2)
```

Then, assuming forward-active operation:

```
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VC  = VCC - IC * RC
VB  = VBE + VE
VCE = VC - VE
```

### Independent calculation: nodal analysis

The verifier solves the base node directly instead of using the Thevenin
equivalent:

```
(VB - VCC)/R1 + VB/R2 + (VB - VBE)/((beta + 1) * RE) = 0
```

Solving for VB:

```
VB = (VCC/R1 + VBE/((beta + 1) * RE))
     / (1/R1 + 1/R2 + 1/((beta + 1) * RE))
```

Then:

```
VE  = VB - VBE
IE  = VE / RE
IB  = IE / (beta + 1)
IC  = beta * IB
VC  = VCC - IC * RC
VCE = VC - VE
```

The verifier does not call the main calculation's helper functions. It shares
only the input values, so agreement is meaningful.

The comparison is shown only for the active region. For cutoff and saturation,
the page states that the linear model is not valid instead of pretending the
two methods verified it.

### Region classification

1. **Cutoff** when `VBB <= VBE`. Set `IB = IC = IE = 0`, `VE = 0`,
   `VC = VCC`, `VCE = VCC`. Warn that the transistor is off.
2. Otherwise calculate the active-model values.
3. **Saturation** when `VCE <= 0.2 V`. Show the calculated values, warn that
   the transistor is saturated, and state that the linear-model VCE is not a
   valid prediction. Do not clamp the result silently.
4. **Active** otherwise. Show the normal result and the independent comparison.

## Validation Rules

All fields are required and must be finite numbers.

| Input | Rule | Thai message (summary) |
| --- | --- | --- |
| VCC | `> 0` | VCC ต้องมากกว่า 0 V |
| R1, R2, RC, RE | each `> 0` | ค่าความต้านทานต้องมากกว่า 0 Ω |
| beta | `>= 1` | β ต้องมีค่าตั้งแต่ 1 ขึ้นไป |
| VBE | `0 <= VBE <= 1.5` | VBE ต้องอยู่ระหว่าง 0 ถึง 1.5 V |

Validation errors are shown next to the form, with the submitted values kept so
the user can correct one field. Invalid input never reaches the calculation.

## User Interface

Single page, Thai labels, SI units:

```
BJT Common-Emitter DC Bias
วงจรไบแอสแบบแบ่งแรงดัน

VCC (V)   R1 (Ω)   R2 (Ω)
RC (Ω)    RE (Ω)   β       VBE (V)

[ คำนวณ ]

สถานะ: ทำงานปกติ (Active) / ตัดขาด (Cutoff) / อิ่มตัว (Saturation)

จุดทำงาน DC
IB  = ... µA
IC  = ... mA
IE  = ... mA
VB  = ... V
VC  = ... V
VE  = ... V
VCE = ... V

ตรวจสอบด้วยการคำนวณอิสระ
ค่า | วิธีหลัก | วิธี nodal | ผลต่าง
...
ผลตรวจสอบ: ผ่าน / ไม่ผ่าน
```

A warning box appears for cutoff, saturation, or any invalid operating point.
The page is responsive enough for a laptop browser; no animation or framework.

## File Layout

```
app.py                  Flask app factory and route
bjt.py                  Input validation, main calculation, region logic
verification.py         Independent nodal calculation and comparison
templates/index.html    Thai form, results, warnings, verification table
static/style.css        Simple readable styling
tests/test_bjt.py       Engineering and validation tests
tests/test_verification.py  Independent-calculation tests
tests/test_app.py       Flask GET/POST and error-display tests
requirements.txt        Flask
README.md               Thai/English setup and usage instructions
```

The existing `electrical.py`, `test_electrical.py`, and clone-check folder stay
untouched. The README is updated to present the BJT app and briefly mention the
earlier Ohm's-law exercise.

## Testing Plan

- Known active-bias example with hand-calculated expected values.
- Independent nodal result agrees with the main result within `1e-9` in the
  active region.
- Cutoff example: `VBB <= VBE`.
- Saturation example: `VCE <= 0.2 V`.
- Validation: non-numeric, zero, negative, beta below 1, VBE outside range.
- Flask: `GET /` returns 200 and the form; valid `POST` returns 200 with the
  operating point; invalid `POST` returns 200 with a Thai error and no result.
- Units and region label appear in the rendered HTML.

Reference example for the tests:

```
VCC=12 V, R1=47 kΩ, R2=10 kΩ, RC=2.2 kΩ, RE=1 kΩ, beta=150, VBE=0.7 V
IB  ≈ 8.8245 µA
IC  ≈ 1.32368 mA
IE  ≈ 1.33250 mA
VB  ≈ 2.03250 V
VC  ≈ 9.08791 V
VE  ≈ 1.33250 V
VCE ≈ 7.75541 V
Region: Active
```

## Demonstration and Delivery

1. Create a local `.venv` and install `requirements.txt`.
2. Run `python app.py` and open `http://127.0.0.1:5000`.
3. Demonstrate the active example, a cutoff example, a saturation example, and
   an invalid input.
4. Run the full test suite.
5. Commit the implementation, tests, and documentation to `main`, then push to
   the existing GitHub remote.

## Open Decisions Left to the Builder

- Exact CSS colors, spacing, and typography.
- Whether result numbers use fixed decimals or significant figures; the default
  is fixed decimals with units chosen for readability (µA for IB, mA for IC and
  IE, V for voltages).
- Exact Thai wording of warnings, as long as the engineering meaning is clear.
- Whether the comparison table shows absolute or relative differences; the
  default is absolute difference in the displayed unit, plus a pass/fail flag.
