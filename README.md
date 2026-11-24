# Lab 04: BJT Amplifier Simulator v1 (ENG29 2121)

เว็บแอปพลิเคชันจำลองวงจรทรานซิสเตอร์ BJT (Common-Emitter Amplifier และ DC Bias 3 รูปแบบ) พัฒนาด้วย Python (Flask) ร่วมกับโปรแกรมจำลองวงจรจริง **ngspice** สำหรับรายวิชา **ENG29 2121 Computer Programming for Electrical Engineers**

## คุณสมบัติหลัก (Features)
- **DC Bias Analytical Solver (`bjt.py` & `verification.py`)**: คำนวณจุดทำงาน DC Operating Point สำหรับวงจร 3 รูปแบบ ได้แก่ **Voltage Divider Bias**, **Fixed Bias**, และ **Emitter Bias** พร้อมระบบตรวจสอบอิสระ (Independent Nodal Verification) และแจ้งเตือนสถานะ Active / Cutoff / Saturation
- **Real SPICE Simulation (`spice_engine.py` + `ngspice`)**:
  - **DC Operating Point (`.op`)**: จำลองแรงดันและกระแส DC จริงด้วยโมเดลทรานซิสเตอร์ `Q2N2222`
  - **AC Small-Signal Analysis (`.ac`)**: วิเคราะห์การตอบสนองความถี่ หาอัตราขยาย Midband Gain (V/V, dB), ความถี่ตัดต่ำ/สูง ($f_L, f_H$) และแสดงกราฟ **Bode Magnitude & Phase**
  - **Transient Analysis (`.tran`)**: จำลองรูปคลื่นสัญญาณอินพุต $V_{in}(t)$ และเอาต์พุต $V_{out}(t)$ ในโดเมนเวลา พร้อมแสดงการกลับเฟส $180^\circ$
- **Provenance & Netlist Inspector**: แยกป้ายกำกับชัดเจนระหว่างค่าคำนวณทางทฤษฎี (`Analytical`) และค่าจากโปรแกรมจำลองจริง (`Engine: ngspice`) พร้อมขอดู Netlist (`.cir`) และ Log การรันจริงได้

---

## การติดตั้ง (Installation)

### 1. ติดตั้ง ngspice (จำเป็นสำหรับการจำลอง SPICE)
- **Windows**:
  1. ดาวน์โหลด `ngspice` สำหรับ Windows (เช่น `ngspice-47_64.zip`) จาก [SourceForge ngspice](https://sourceforge.net/projects/ngspice/files/)
  2. แตกไฟล์ไว้ที่ `C:\Spice64` (ให้มีไฟล์ `C:\Spice64\bin\ngspice_con.exe`) และเพิ่ม `C:\Spice64\bin` ลงใน System `PATH`
  3. ทดสอบใน Terminal: `ngspice_con -v`
- **macOS (Homebrew)**: `brew install ngspice`
- **Ubuntu / Debian**: `sudo apt-get update && sudo apt-get install -y ngspice`

### 2. ติดตั้ง Python Dependencies
```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt