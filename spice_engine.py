import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any


BJT_MODEL_NAME = "Q2N2222_LAB4"
BJT_MODEL_CARD = (
    f".model {BJT_MODEL_NAME} NPN("
    "IS=1.434E-14 XTI=3 EG=1.11 VAF=74.03 BF=255.9 NE=1.307 "
    "ISE=1.434E-14 IKF=.2847 XTB=1.5 BR=6.092 NC=2 ISC=0 IKR=0 RC=1 "
    "CJC=7.306E-12 MJC=.3416 VJC=.75 FC=.5 CJE=2.201E-11 MJE=.377 VJE=.75 "
    "TR=4.691E-8 TF=4.111E-10 ITF=.6 VTF=1.7 XTF=3 RB=10)"
)


@dataclass
class SpiceRunResult:
    ok: bool
    analysis: str
    status_text: str
    ngspice_version: str
    model_name: str
    netlist: str
    raw_log: str
    dc_op: dict[str, float] | None = None
    ac_data: dict[str, Any] | None = None
    tran_data: dict[str, Any] | None = None
    error_message: str | None = None


def find_ngspice_executable() -> str | None:
    for exe in ("ngspice_con", "ngspice_con.exe", "ngspice"):
        found = shutil.which(exe)
        if found:
            if found.lower().endswith("ngspice.exe"):
                con_path = os.path.join(os.path.dirname(found), "ngspice_con.exe")
                if os.path.isfile(con_path):
                    return con_path
            return found

    for fallback in (r"C:\Spice64\bin\ngspice_con.exe", r"C:\Spice64\bin\ngspice.exe"):
        if os.path.isfile(fallback):
            return fallback
    return None

def get_ngspice_version(exe_path: str) -> str:
    try:
        proc = subprocess.run(
            [exe_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        for line in combined.splitlines():
            if "ngspice" in line.lower():
                return line.strip().lstrip("* ").strip()
    except Exception:
        pass
    return "ngspice (detected)"


def _validate_ce_inputs(
    vcc_v: float,
    r1_ohm: float,
    r2_ohm: float,
    rc_ohm: float,
    re_ohm: float,
    rl_ohm: float,
    cin_f: float,
    cout_f: float,
    amp_v: float,
    freq_hz: float,
) -> None:
    positive_checks = {
        "VCC": vcc_v,
        "R1": r1_ohm,
        "R2": r2_ohm,
        "RC": rc_ohm,
        "RE": re_ohm,
        "RL": rl_ohm,
        "Cin": cin_f,
        "Cout": cout_f,
        "Amplitude": amp_v,
        "Frequency": freq_hz,
    }
    for name, val in positive_checks.items():
        if not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{name} must be strictly greater than 0 for SPICE simulation.")


def build_ce_netlist(
    analysis: str,
    vcc_v: float,
    r1_ohm: float,
    r2_ohm: float,
    rc_ohm: float,
    re_ohm: float,
    rl_ohm: float,
    cin_f: float,
    cout_f: float,
    amp_v: float,
    freq_hz: float,
) -> str:
    period_s = 1.0 / freq_hz
    t_stop = 4.0 * period_s
    t_step = period_s / 80.0

    if analysis == "op":
        directive_block = """.op
.control
run
print v(vb) v(ve) v(vc) v(vc,ve) i(vcc_sense) i(vb_sense)
quit
.endc"""
    elif analysis == "ac":
        directive_block = """.ac dec 25 10 10Meg
.control
run
set wr_vecnames
set wr_singlescale
wrdata ac_out.txt vm(vout) vp(vout) vm(vin_node)
quit
.endc"""
    elif analysis == "tran":
        directive_block = f""".tran {t_step:.6e} {t_stop:.6e}
.control
run
set wr_vecnames
set wr_singlescale
wrdata tran_out.txt v(vin_node) v(vout)
quit
.endc"""
    else:
        raise ValueError(f"Unsupported SPICE analysis mode: {analysis}")

    return f"""* ENG29 2121 Lab 04 - Common-Emitter Voltage Divider Amplifier
VCC vcc_src 0 DC {vcc_v:.6g}
VCC_SENSE vcc_src vcc DC 0

R1 vcc vb {r1_ohm:.6g}
R2 vb 0 {r2_ohm:.6g}
RC vcc vc {rc_ohm:.6g}
RE ve 0 {re_ohm:.6g}

VB_SENSE vb vb_q DC 0
Q1 vc vb_q ve {BJT_MODEL_NAME}

VIN vin_node 0 DC 0 AC 1 SIN(0 {amp_v:.6g} {freq_hz:.6g})
CIN vin_node vb {cin_f:.6e}
COUT vc vout {cout_f:.6e}
RL vout 0 {rl_ohm:.6g}

{BJT_MODEL_CARD}

{directive_block}
.end
"""


def _parse_op_log(log_text: str) -> dict[str, float]:
    patterns = {
        "vb_v": r"v\(vb\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "ve_v": r"v\(ve\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "vc_v": r"v\(vc\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "vce_v": r"v\(vc,ve\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "ic_sense": r"i\(vcc_sense\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "ib_sense": r"i\(vb_sense\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
    }
    parsed: dict[str, float] = {}
    for key, pat in patterns.items():
        match = re.search(pat, log_text, re.IGNORECASE)
        if not match:
            raise RuntimeError(f"Could not parse '{key}' from ngspice .op output.")
        val = float(match.group(1))
        if not math.isfinite(val):
            raise RuntimeError(f"Non-finite value parsed for '{key}'.")
        parsed[key] = val

    # Current through R1 flows from vcc to vb; total VCC current = I(RC) + I(R1)
    # Using Kirchhoff at collector & base: IC is current into collector
    ib_a = parsed["ib_sense"]
    # Exact collector current from VCC minus R1 current:
    # Since we need IC directly, compute from VC and VCC:
    return {
        "vb_v": parsed["vb_v"],
        "ve_v": parsed["ve_v"],
        "vc_v": parsed["vc_v"],
        "vce_v": parsed["vce_v"],
        "ib_a": ib_a,
        "ib_ua": ib_a * 1e6,
        "total_vcc_ma": parsed["ic_sense"] * 1e3,
    }


def _parse_wrdata_columns(file_path: str, expected_cols: int) -> list[list[float]]:
    if not os.path.isfile(file_path):
        raise RuntimeError(f"Expected ngspice output file not created: {os.path.basename(file_path)}")

    rows: list[list[float]] = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                continue
            if len(nums) >= expected_cols and all(math.isfinite(x) for x in nums[:expected_cols]):
                rows.append(nums[:expected_cols])

    if len(rows) < 5:
        raise RuntimeError("ngspice returned insufficient data points.")
    return rows


def run_ce_spice_simulation(
    analysis: str,
    vcc_v: float,
    r1_ohm: float,
    r2_ohm: float,
    rc_ohm: float,
    re_ohm: float,
    rl_ohm: float,
    cin_f: float,
    cout_f: float,
    amp_v: float,
    freq_hz: float,
) -> SpiceRunResult:
    exe_path = find_ngspice_executable()
    if not exe_path:
        return SpiceRunResult(
            ok=False,
            analysis=analysis,
            status_text="Engine Missing",
            ngspice_version="Not Found",
            model_name=BJT_MODEL_NAME,
            netlist="",
            raw_log="",
            error_message="ngspice executable was not found in PATH or C:\\Spice64\\bin\\ngspice.exe.",
        )

    version_str = get_ngspice_version(exe_path)

    try:
        _validate_ce_inputs(
            vcc_v=vcc_v,
            r1_ohm=r1_ohm,
            r2_ohm=r2_ohm,
            rc_ohm=rc_ohm,
            re_ohm=re_ohm,
            rl_ohm=rl_ohm,
            cin_f=cin_f,
            cout_f=cout_f,
            amp_v=amp_v,
            freq_hz=freq_hz,
        )
        netlist = build_ce_netlist(
            analysis=analysis,
            vcc_v=vcc_v,
            r1_ohm=r1_ohm,
            r2_ohm=r2_ohm,
            rc_ohm=rc_ohm,
            re_ohm=re_ohm,
            rl_ohm=rl_ohm,
            cin_f=cin_f,
            cout_f=cout_f,
            amp_v=amp_v,
            freq_hz=freq_hz,
        )
    except ValueError as exc:
        return SpiceRunResult(
            ok=False,
            analysis=analysis,
            status_text="Validation Error",
            ngspice_version=version_str,
            model_name=BJT_MODEL_NAME,
            netlist="",
            raw_log="",
            error_message=str(exc),
        )

    try:
        with tempfile.TemporaryDirectory(prefix="lab04_spice_") as tmpdir:
            cir_path = os.path.join(tmpdir, "circuit.cir")
            log_path = os.path.join(tmpdir, "run.log")
            with open(cir_path, "w", encoding="utf-8") as f:
                f.write(netlist)

            proc = subprocess.run(
                [exe_path, "-b", "-o", log_path, cir_path],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            log_text = ""
            if os.path.isfile(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
                    log_text = lf.read()
            combined_log = (log_text + "\n" + proc.stderr).strip()

            if proc.returncode != 0 or "simulation aborted" in combined_log.lower():
                return SpiceRunResult(
                    ok=False,
                    analysis=analysis,
                    status_text="Simulation Failed",
                    ngspice_version=version_str,
                    model_name=BJT_MODEL_NAME,
                    netlist=netlist,
                    raw_log=combined_log,
                    error_message="ngspice aborted or returned a non-zero exit code.",
                )

            if analysis == "op":
                op_vals = _parse_op_log(combined_log)
                ic_a = (vcc_v - op_vals["vc_v"]) / rc_ohm
                ie_a = op_vals["ve_v"] / re_ohm
                op_vals["ic_a"] = ic_a
                op_vals["ic_ma"] = ic_a * 1e3
                op_vals["ie_a"] = ie_a
                op_vals["ie_ma"] = ie_a * 1e3
                return SpiceRunResult(
                    ok=True,
                    analysis="op",
                    status_text="Success (.op)",
                    ngspice_version=version_str,
                    model_name=BJT_MODEL_NAME,
                    netlist=netlist,
                    raw_log=combined_log,
                    dc_op=op_vals,
                )

            if analysis == "ac":
                rows = _parse_wrdata_columns(os.path.join(tmpdir, "ac_out.txt"), 4)
                freqs = []
                gains_vv = []
                gains_db = []
                phases_deg = []
                for freq, vm_out, vp_out_rad, vm_in in rows:
                    if freq <= 0 or vm_in <= 0:
                        continue
                    gain_mag = vm_out / vm_in
                    gain_db = 20.0 * math.log10(max(gain_mag, 1e-12))
                    phase_deg = math.degrees(vp_out_rad)
                    freqs.append(freq)
                    gains_vv.append(gain_mag)
                    gains_db.append(gain_db)
                    phases_deg.append(phase_deg)

                if not freqs:
                    raise RuntimeError("No valid AC frequency points extracted.")

                mid_idx = max(range(len(gains_db)), key=lambda i: gains_db[i])
                mid_gain_db = gains_db[mid_idx]
                mid_gain_vv = gains_vv[mid_idx]
                mid_freq_hz = freqs[mid_idx]
                target_3db = mid_gain_db - 3.0

                f_low = None
                for i in range(mid_idx, 0, -1):
                    if gains_db[i] >= target_3db and gains_db[i - 1] < target_3db:
                        f_low = freqs[i]
                        break

                f_high = None
                for i in range(mid_idx, len(freqs) - 1):
                    if gains_db[i] >= target_3db and gains_db[i + 1] < target_3db:
                        f_high = freqs[i]
                        break

                return SpiceRunResult(
                    ok=True,
                    analysis="ac",
                    status_text="Success (.ac)",
                    ngspice_version=version_str,
                    model_name=BJT_MODEL_NAME,
                    netlist=netlist,
                    raw_log=combined_log,
                    ac_data={
                        "freqs_hz": freqs,
                        "gains_vv": gains_vv,
                        "gains_db": gains_db,
                        "phases_deg": phases_deg,
                        "midband_gain_db": mid_gain_db,
                        "midband_gain_vv": mid_gain_vv,
                        "midband_freq_hz": mid_freq_hz,
                        "f_low_str": f"{f_low:.1f} Hz" if f_low else "not determined in sweep range",
                        "f_high_str": f"{f_high / 1e3:.2f} kHz" if f_high else "not determined in sweep range",
                    },
                )

            if analysis == "tran":
                rows = _parse_wrdata_columns(os.path.join(tmpdir, "tran_out.txt"), 3)
                times_ms = [r[0] * 1e3 for r in rows]
                vin_mv = [r[1] * 1e3 for r in rows]
                vout_v = [r[2] for r in rows]

                vin_peak_mv = max(abs(x) for x in vin_mv)
                vout_peak_v = max(abs(x) for x in vout_v)
                measured_gain = (vout_peak_v * 1e3) / vin_peak_mv if vin_peak_mv > 0 else 0.0

                # Check phase inversion using correlation of Vin and Vout
                dot = sum(vi * vo for vi, vo in zip(vin_mv, vout_v))
                phase_relation = "Inverted (~180° out of phase)" if dot < 0 else "In-phase (~0°)"

                return SpiceRunResult(
                    ok=True,
                    analysis="tran",
                    status_text="Success (.tran)",
                    ngspice_version=version_str,
                    model_name=BJT_MODEL_NAME,
                    netlist=netlist,
                    raw_log=combined_log,
                    tran_data={
                        "times_ms": times_ms,
                        "vin_mv": vin_mv,
                        "vout_v": vout_v,
                        "vin_peak_mv": vin_peak_mv,
                        "vout_peak_v": vout_peak_v,
                        "measured_gain": measured_gain,
                        "phase_relation": phase_relation,
                        "freq_hz": freq_hz,
                    },
                )

    except subprocess.TimeoutExpired:
        return SpiceRunResult(
            ok=False,
            analysis=analysis,
            status_text="Timeout",
            ngspice_version=version_str,
            model_name=BJT_MODEL_NAME,
            netlist=netlist,
            raw_log="",
            error_message="ngspice execution timed out after 10 seconds.",
        )
    except Exception as exc:
        return SpiceRunResult(
            ok=False,
            analysis=analysis,
            status_text="Parse / Runtime Error",
            ngspice_version=version_str,
            model_name=BJT_MODEL_NAME,
            netlist=netlist,
            raw_log="",
            error_message=str(exc),
        )

    return SpiceRunResult(
        ok=False,
        analysis=analysis,
        status_text="Unknown Error",
        ngspice_version=version_str,
        model_name=BJT_MODEL_NAME,
        netlist="",
        raw_log="",
        error_message="Unexpected execution path.",
    )