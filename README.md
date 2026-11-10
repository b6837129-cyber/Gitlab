# BJT Common-Emitter DC Bias Calculator

## Overview

A Flask web app for the ENG29 2121 lab that computes the DC operating point of
a common-emitter amplifier with voltage-divider bias. Enter VCC, R1, R2, RC,
RE, β and VBE, and the app calculates IB, IC, IE, VB, VC, VE and VCE with
units, validates the input, reports the operating region (active, cutoff or
saturation), and compares the result against an independent nodal analysis.

The page is an English three-column dashboard: an input panel with unit
dropdowns, a circuit diagram whose labels follow the values you enter, and a
results panel with a region card. The independent verification table and the
Week 2 goal sit below the main dashboard.

## Features

- Seven inputs: VCC, R1, R2, RC, RE, β and VBE.
- Functional unit dropdowns: `V`/`mV` for voltages, `Ω`/`kΩ`/`MΩ` for
  resistances, and a unitless `—` for β. Values are converted to base units
  before the calculation.
- The form opens with the example values from the lab mockup, but every field
  is editable and any valid set of values recalculates on submit.
- DC operating point shown with µA, mA and V units.
- English validation messages for blank, non-numeric, non-finite, zero or
  negative values, β < 1, and VBE outside 0–1.5 V.
- A region card that reports active, cutoff or saturation, with its own colour
  for each.
- Independent nodal analysis with a comparison table and a PASS/FAIL line.
- Inline SVG circuit diagram, no JavaScript and no extra runtime dependencies.
- Automated tests for the calculation, validation and Flask routes.

## Install

Python 3.12 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000`.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## Example

The default values follow the lab mockup:

| Quantity | Value |
| --- | --- |
| VCC | 12 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RC | 2.2 kΩ |
| RE | 1 kΩ |
| β | 100 |
| VBE | 0.70 V |

Results from the app's exact model (it accounts for base current, so the
numbers differ slightly from the approximate values in the mockup):

| Quantity | Value |
| --- | --- |
| VB | 1.94 V |
| VE | 1.24 V |
| VC | 9.29 V |
| VCE | 8.05 V |
| IB | 12.3 µA |
| IC | 1.23 mA |
| IE | 1.24 mA |

Operating region: active, and the independent nodal verification passes.

Changing any field recalculates with the new values. For example, 9 V, 47 kΩ,
10 kΩ, 1 kΩ, 470 Ω, β = 200 and VBE = 0.65 V gives VB 1.50 V, VE 0.85 V,
VC 7.19 V, VCE 6.34 V, IB 9.0 µA, IC 1.81 mA and IE 1.82 mA.

## File layout

- `app.py` — Flask app factory, route, default form values and view helpers
- `bjt.py` — unit-aware validation, DC operating point calculation and region
  classification
- `verification.py` — independent nodal analysis and result comparison
- `templates/index.html` — English dashboard template with the inline SVG
  circuit
- `static/style.css` — dashboard styling
- `tests/test_bjt.py` — validation and calculation tests
- `tests/test_verification.py` — independent verification tests
- `tests/test_app.py` — Flask route and rendering tests
- `requirements.txt` — runtime dependencies
- `docs/superpowers/` — design and implementation plan documents

## Notes

`electrical.py` and `test_electrical.py` are an earlier Ohm's law exercise and
remain in the repository. The BJT app above is a separate lab project.
