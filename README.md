# Lab 04: BJT Amplifier Simulator v1 (Common-Emitter DC Bias & SPICE Analysis)

## Overview

A Flask web app for the **ENG29 2121 (Computer Programming for Electrical Engineers)** lab that computes both the analytical DC operating point and real **ngspice** circuit simulations (`.op`, `.ac`, and `.tran`) of a BJT amplifier.

- **Analytical DC Bias Solver (`bjt.py` & `verification.py`)**: Supports three bias configurations (**Voltage Divider Bias**, **Fixed Bias**, and **Emitter Bias**), validates inputs with unit conversion, reports the operating region (active, cutoff, or saturation), and cross-checks voltage-divider results against an independent nodal analysis.
- **Real ngspice Simulation Engine (`spice_engine.py`)**: Executes batch simulations via `ngspice_con.exe` / `ngspice` using a `Q2N2222` BJT model for the Common-Emitter amplifier, providing real DC operating points (`.op`), small-signal Bode magnitude/phase plots (`.ac`), and time-domain input/output waveforms (`.tran`), alongside a netlist and solver log inspector.

The page is an English three-column dashboard: an input panel with unit dropdowns and SPICE mode tabs, a dynamic inline SVG circuit diagram that updates with your component values and bias mode, and a results panel that separates **Analytical** values from **Engine: ngspice** results.

## Features

- **Three Bias Modes**: Voltage Divider Bias, Fixed Bias, and Emitter Bias (Single Supply), dynamically hiding unused component fields.
- **Three Real SPICE Analysis Modes (CE Reference)**:
  - `DC (.op)`: Real SPICE node voltages ($V_B, V_E, V_C, V_{CE}$) and branch currents ($I_B, I_C$).
  - `AC (.ac)`: Frequency sweep (`10 Hz` to `10 MHz`) with midband gain (V/V and dB), $-3\text{ dB}$ cutoff frequencies ($f_L, f_H$), and an interactive Bode magnitude & phase plot.
  - `Transient (.tran)`: Time-domain sine-wave simulation showing peak $V_{in}$, peak $V_{out}$, voltage gain, $180^\circ$ phase inversion, and dual-axis waveform plots.
- **Functional Unit Dropdowns**: `V`/`mV` for voltages, `Ω`/`kΩ`/`MΩ` for resistances, `nF`/`µF`/`mF` for coupling capacitors, `Hz`/`kHz`/`MHz` for frequency, and `—` for $\beta$.
- **Provenance & Netlist Inspector**: Clearly distinguishes analytical results (`dc_bias.py`) from `ngspice` solver outputs, with an expandable panel to inspect the generated `.cir` netlist and raw `ngspice` log.
- **Input Validation & Regression Tests**: English validation messages for invalid/non-finite inputs and 43 automated unit and Flask route tests.

## Install

### 1. Install `ngspice` (Required for SPICE Simulation)

- **Windows**:
  1. Download the 64-bit Windows `ngspice` archive (e.g., `ngspice-47_64.zip`) from SourceForge.
  2. Extract it so `ngspice_con.exe` is located at `C:\Spice64\bin\ngspice_con.exe` and add `C:\Spice64\bin` to your System `PATH`.
  3. Verify in PowerShell: `ngspice_con -v`
- **macOS**: `brew install ngspice`
- **Ubuntu / Debian**: `sudo apt-get update && sudo apt-get install -y ngspice`

### 2. Install Python Dependencies

Python 3.12 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt