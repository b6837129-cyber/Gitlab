# BJT DC Bias Web App — UI Redesign (English) — Design

Date: 2026-11-10
Status: Awaiting approval
Approach: A — server-rendered Flask + inline SVG, no JavaScript

## Intent

Make the existing BJT common-emitter DC bias app look like the provided
mockup: an English, three-column lab dashboard with an input panel, a
circuit diagram, and a results panel, plus an active-region card and a
"Week 2 Goal" card. The unit dropdowns in the mockup must work for real,
not just decorate the page.

## Goals

- Reproduce the mockup's layout, colours, icons, and typography closely.
- English UI text throughout, including validation and region messages.
- Functional unit dropdowns: V/mV for voltages, Ω/kΩ/MΩ for resistances.
- Inline SVG circuit whose labels reflect the current input values.
- Prefill the mockup example on GET: VCC 12 V, R1 100 kΩ, R2 22 kΩ,
  RC 2.2 kΩ, RE 1 kΩ, β 100, VBE 0.70 V. The prefill is only a default:
  every field is editable, and any valid set of values recalculates on
  submit.
- Keep the independent nodal verification requirement, styled as a
  separate card below the main dashboard.
- Keep all existing engineering behaviour and the 31 passing tests
  (updated where messages change).

## Non-goals

- No JavaScript, AC analysis, transient analysis, circuit editor, or FET.
- No change to the Thevenin calculation or the nodal verification maths.
- No new Python dependencies.

## Anti-goals

- A dropdown that does not convert its unit.
- Dropping the independent verification section to match the mockup.
- Changing numeric results to match the picture by hard-coding them.

## Approaches Considered

- **A. Server-rendered Flask + inline SVG (chosen).** Fits the existing
  architecture, testable with unittest, no new runtime complexity.
- **B. Client-side JavaScript for live updates.** Nicer interaction but
  adds a second calculation path and new failure modes.
- **C. Visual reskin only.** Fast, but the unit selects would mislead
  users and produce wrong results.

## Design

### Layout

- Light grey page background, centred content up to ~1100 px.
- Header: teal chip icon, title `Lab 02: BJT DC Bias Web App`, subtitle
  `ENG29 2121 – Common Emitter (Voltage Divider Bias)`, and a blue
  rounded badge with a code icon and
  `Computer Programming for Electrical Engineers`.
- Three cards in a responsive grid (3 columns on wide screens, 1 on
  narrow):
  1. **Input Parameters** — seven labelled rows, each with a text input
     and a unit `<select>`; teal `Calculate DC Bias` button.
  2. **Circuit: Common-Emitter Amplifier** — inline SVG showing VCC, R1,
     R2, RC, RE, Q1 (NPN, β), and ground, with live values.
  3. **DC Bias Results** — table in the mockup order (VB, VE, VC, VCE,
     IB, IC, IE) and a region card (green active / orange cutoff /
     red saturation).
- Below the grid: **Independent Verification** card with the main vs
  nodal comparison and a PASS/FAIL line.
- Bottom: **Week 2 Goal** card with the mockup's target text.

### Units and parsing

- Form sends each numeric field plus `<field>_unit`.
- Accepted units:
  - `vcc`, `vbe`: `V` (×1), `mV` (×1e-3)
  - `r1`, `r2`, `rc`, `re`: `Ω` (×1), `kΩ` (×1e3), `MΩ` (×1e6)
  - `beta`: `—` (unitless)
- A missing unit field defaults to the base unit, so existing callers and
  tests that post raw base-unit values keep working.
- Unknown or disallowed unit → field error `Please select a valid unit`.
- Parsed values are converted to base units before `BiasInputs` is built.

### English validation messages

- Blank: `Please enter this value`
- Not a number / non-finite: `Please enter a number`
- VCC ≤ 0: `VCC must be greater than 0 V`
- Resistance ≤ 0: `Resistance must be greater than 0 Ω`
- β < 1: `β must be at least 1`
- VBE outside 0–1.5: `VBE must be between 0 and 1.5 V`
- Calculation failure: `These values do not produce a valid result.`

### Results and formatting

- VB, VE, VC, VCE: 2 decimals, V.
- IB: 1 decimal, µA; IC and IE: 2 decimals, mA.
- Active card: green, check icon,
  `Active region approximation OK`, with
  `VCE = <value> V > 0.2 V (transistor in active region)`.
- Cutoff card: orange, `Transistor is in cutoff (VBB ≤ VBE)`.
- Saturation card: red, `Transistor is in saturation (VCE ≤ 0.2 V)`.
- Verification card: comparison table plus `Verification: PASS/FAIL`.

### Circuit SVG

- Static topology; dynamic text for VCC, R1, R2, RC, RE, and β.
- Values are rendered from the submitted form (or the prefilled
  defaults) so the diagram matches the results.
- Pure inline SVG, no external images.

### Files

- Modify: `bjt.py` (unit parsing + English messages)
- Modify: `app.py` (defaults, unit-aware context, results rows, region
  card text, verification card)
- Rewrite: `templates/index.html`
- Rewrite: `static/style.css`
- Modify: `tests/test_bjt.py`, `tests/test_app.py`
- Modify: `README.md` (English UI note, units, new example)

### Testing

- Unit conversion for V/mV and Ω/kΩ/MΩ; invalid unit rejected.
- Defaults render on GET; example values calculate to the mockup's
  numbers.
- English validation and calculation-error messages.
- Active, cutoff, and saturation region cards.
- SVG contains the submitted values.
- Non-finite guard from the previous review still holds.
- Verification card still shows PASS for the example.

## What is left to the builder

- Exact SVG coordinates, icon paths, spacing, and colour shades.
- Whether to use `<sub>` tags or plain labels for VCC, R1, etc.
- Minor responsive breakpoints.
