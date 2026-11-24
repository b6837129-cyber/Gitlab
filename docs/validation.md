# Lab 03: BJT DC Bias Web App — Browser Validation & Verification

## 1. ตารางบันทึกผลการทดสอบผ่านเบราว์เซอร์ (A1–A5)

- **พารามิเตอร์ร่วมทุกกรณี:** $V_{CC} = 12\text{ V}$, $R_C = 2.2\text{ k}\Omega$, $\beta = 100$, $V_{BE} = 0.70\text{ V}$
- **เกณฑ์ความคลาดเคลื่อนที่ยอมรับได้:** $I_C \pm 0.01\text{ mA}$ และ $V_{CE} \pm 0.02\text{ V}$
- **หมายเหตุเครื่องมือทดสอบ:** **Playwright MCP = `NOT RUN`** เนื่องจากโควตาข้อความฟรีประจำวันของ OpenCode หมดระหว่างปฏิบัติการ จึงเปลี่ยนมาทดสอบด้วยตนเองผ่านเบราว์เซอร์จริง (**Manual**) ครบทั้ง 5 กรณีแทน

| กรณี | โหมดและอินพุตเฉพาะวงจร | คาดหมายก่อนรัน | เห็นจริงบนหน้าเว็บ | วิธีตรวจ | สถานะ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1 · โหมดเดิม** | **Divider:** $R_1 = 100\text{ k}\Omega, R_2 = 22\text{ k}\Omega, R_E = 1\text{ k}\Omega$ | ตรงกับ Lab 2 เดิม<br>$I_C = 1.23\text{ mA}$<br>$V_{CE} = 8.05\text{ V}$ | $I_C = 1.23\text{ mA}$<br>$V_{CE} = 8.05\text{ V}$<br>(Active region OK) | Manual | PASS |
| **A2 · Fixed** | **Fixed:** $R_B = 1\text{ M}\Omega$ (ไม่กรอก $R_E$) | ไม่ต้องกรอก $R_E$<br>$I_C = 1.13\text{ mA}$<br>$V_{CE} = 9.51\text{ V}$ | $I_C = 1.13\text{ mA}$<br>$V_{CE} = 9.51\text{ V}$<br>(Active region OK) | Manual | PASS |
| **A3 · Emitter** | **Emitter:** $R_B = 1\text{ M}\Omega, R_E = 1\text{ k}\Omega$ | ใช้ค่า $R_E$ คำนวณ<br>$I_C = 1.03\text{ mA}$<br>$V_{CE} = 8.71\text{ V}$ | $I_C = 1.03\text{ mA}$<br>$V_{CE} = 8.71\text{ V}$<br>(Active region OK) | Manual | PASS |
| **A4 · เปลี่ยนค่าเดียว** | **Emitter:** $R_B = 1\text{ M}\Omega, R_E = 2\text{ k}\Omega$ | $I_C$ **ลดลง**จาก A3<br>$I_C = 0.94\text{ mA}$<br>$V_{CE} = 8.03\text{ V}$ | $I_C = 0.94\text{ mA}$<br>$V_{CE} = 8.03\text{ V}$<br>(ลดลงจาก A3 จริง) | Manual | PASS |
| **A5 · อินพุตผิด** | **Fixed:** $R_B = 0\ \Omega$ | แจ้ง Error ให้แก้ $R_B$<br>เว็บไม่ล่ม ไม่ค้างผลเก่า | แสดงข้อความ `Resistance must be greater than 0 Ω` และไม่แสดงผลเก่า | Manual | PASS |

---

## 2. การคำนวณมืออ้างอิงอิสระ (โหมดใหม่)

### กรณี A2: Fixed Bias ($R_B = 1\text{ M}\Omega$)
- $I_B = \dfrac{V_{CC} - V_{BE}}{R_B} = \dfrac{12 - 0.70}{1 \times 10^6} = 11.30\ \mu\text{A}$
- $I_C = \beta I_B = 100 \times 11.30\ \mu\text{A} = \mathbf{1.13\text{ mA}}$
- $V_E = 0\text{ V}$ (Emitter ต่อลงกราวด์โดยตรง)
- $V_C = V_{CC} - I_C R_C = 12 - (1.13\text{ mA} \times 2.2\text{ k}\Omega) = 9.514\text{ V}$
- $V_{CE} = V_C - V_E = \mathbf{9.51\text{ V}}$

### กรณี A3: Emitter Bias ($R_B = 1\text{ M}\Omega, R_E = 1\text{ k}\Omega$)
- $I_B = \dfrac{V_{CC} - V_{BE}}{R_B + (\beta + 1)R_E} = \dfrac{12 - 0.70}{1,000,000 + (101 \times 1,000)} = \dfrac{11.30}{1,101,000} \approx 10.263\ \mu\text{A}$
- $I_C = \beta I_B = 100 \times 10.263\ \mu\text{A} = \mathbf{1.03\text{ mA}}$
- $I_E = (\beta + 1)I_B = 101 \times 10.263\ \mu\text{A} \approx 1.037\text{ mA}$
- $V_E = I_E R_E = 1.037\text{ mA} \times 1\text{ k}\Omega = 1.037\text{ V}$
- $V_C = V_{CC} - I_C R_C = 12 - (1.0263\text{ mA} \times 2.2\text{ k}\Omega) = 9.742\text{ V}$
- $V_{CE} = V_C - V_E = 9.742 - 1.037 = \mathbf{8.71\text{ V}}$

---

## 3. การแบ่งหน้าที่พัฒนาและตรวจสอบโค้ด (AI vs นักศึกษา)

- **ส่วนที่ AI สร้าง:**
  - `bjt.py`: เพิ่มฟังก์ชัน `calculate_fixed_bias()`, `calculate_emitter_bias()`, `calculate_voltage_divider()` และ `validate_and_parse_mode()` โดยคืนค่าเป็น `dict` ที่มีคีย์และหน่วยมาตรฐานเดียวกัน
  - `app.py`: เพิ่มการตรวจสอบและเลือกเรียกฟังก์ชันตามโหมดด้วยโครงสร้าง `if / elif` และส่งชื่อโหมดไปแสดงผล
  - `templates/index.html`: เพิ่มเมนูเลือกโหมด 3 แบบ ปรับการซ่อน/ปิดช่องอินพุตที่ไม่เกี่ยวข้อง และปรับแผนภาพวงจร SVG ตามโหมด
- **ส่วนที่นักศึกษาตรวจสอบ:**
  - ตรวจสอบสมการ Forward Active ใน `bjt.py` ทั้ง 3 โหมด รวมถึงเงื่อนไขแจ้งเตือน Cutoff ($I_B \le 0$) และ Saturation ($V_{CE} \le 0.2\text{ V}$)
  - ตรวจสอบจุดแปลงหน่วยใน `RESISTANCE_UNITS` (`Ω`: 1.0, `kΩ`: $10^3$, `MΩ`: $10^6$) ภายในฟังก์ชัน `validate_and_parse_mode()` ของ `bjt.py`
  - ตรวจสอบการส่งค่าโหมดและเงื่อนไข `if / elif` ใน `app.py` รวมถึงทดสอบซ้ำด้วยตนเองผ่านเบราว์เซอร์จริง

---

## 4. คำตอบคำถามปิด Lab

**คำถาม:** ถ้าตัวเลขคำนวณมือถูก แต่เปลี่ยน $R_E$ แล้วผลบนหน้าเว็บไม่เปลี่ยน จะตรวจค่าที่ส่งจากฟอร์มและค่าที่เข้าไปในฟังก์ชันอย่างไร?

**แนวทางตรวจสอบ:**
1. **ตรวจฝั่งหน้าเว็บ (`templates/index.html`):** ตรวจสอบใน Browser DevTools (Network/Elements) ว่าช่อง `<input id="re" name="re">` ไม่ได้ติดสถานะ `disabled` และค่าที่กรอกถูกส่งไปใน Payload ของคำขอ `POST` จริง
2. **ตรวจจุดรับข้อมูลและแปลงหน่วย (`app.py` และ `bjt.py`):** ตรวจสอบว่า `request.form.get("re")` และ `request.form.get("re_unit")` รับค่าใหม่เข้ามาถูกต้อง และฟังก์ชัน `validate_and_parse_mode()` แปลงหน่วยเป็นโอห์ม (`parsed["re"]`) ได้ตรงตามที่กรอก
3. **ตรวจการส่งพารามิเตอร์เข้าฟังก์ชันคำนวณ (`app.py`):** ตรวจสอบในบล็อก `elif mode == "emitter":` และ `if mode == "divider":` ว่าได้ส่งอาร์กิวเมนต์ `re_ohm=float(parsed["re"])` เข้าไปในฟังก์ชัน `calculate_emitter_bias()` หรือ `calculate_voltage_divider()` จริง ไม่ได้เผลอส่งค่าคงที่หรือส่ง `re_ohm=0.0` ของ Fixed Bias ไปแทนmarkdown
# Lab 04 Validation & Acceptance Report (B1–B8)

รายงานการตรวจสอบความถูกต้องของเว็บแอปพลิเคชัน **Lab 04: BJT Amplifier Simulator v1** บนเบราว์เซอร์จริง (`http://127.0.0.1:5000`) ร่วมกับเครื่องมือจำลองวงจร **ngspice-47** (โมเดล `Q2N2222_LAB4`)

---

## 1. ตารางผลการตรวจสอบ Browser Acceptance (B1–B8)

| รหัส | รายการตรวจสอบ (Test Case) | วิธีการตรวจสอบ (Procedure) | ผลที่เห็นจริง (Actual Result) | สถานะ |
| :--- | :--- | :--- | :--- | :---: |
| **B1** | **หน้าเริ่มต้นและการแสดงผลพื้นฐาน** | เปิด `http://127.0.0.1:5000` ด้วยวิธี `GET` | หน้าเว็บโหลดครบถ้วน แสดงฟอร์มค่าเริ่มต้น ($V_{CC}=12\text{ V}, R_1=100\text{ k}\Omega, R_2=22\text{ k}\Omega, R_C=2.2\text{ k}\Omega, R_E=1\text{ k}\Omega$) และรูปวงจร SVG ถูกต้อง | **PASS** |
| **B2** | **ความต่อเนื่องจาก Lab 3 (DC Bias 3 แบบ + Regression)** | รัน `python -m pytest tests` และทดลองคำนวณโหมด `Voltage Divider`, `Fixed Bias`, `Emitter Bias` | ผ่านชุดทดสอบอัตโนมัติครบ **43 passed**; โหมด Fixed และ Emitter ซ่อนช่องอุปกรณ์ AC ที่ไม่เกี่ยวข้อง และคำนวณจุดทำงาน DC ได้ถูกต้อง | **PASS** |
| **B3** | **การจำลอง SPICE โหมด DC (`.op`)** | เลือก `Voltage Divider Bias` + `DC (.op)` ค่าเริ่มต้น แล้วกด **Run Simulation** | สถานะขึ้น `Success (.op)` แสดงค่าจริงจาก `ngspice-47`: $V_B = 2.016\text{ V}$, $V_E = 1.364\text{ V}$, $V_C = 9.017\text{ V}$, $V_{CE} = 7.653\text{ V}$ สอดคล้องกับค่า Analytical ($V_B = 1.94\text{ V}, V_{CE} = 8.05\text{ V}$) | **PASS** |
| **B4** | **การจำลอง SPICE โหมด AC (`.ac`) และ Bode Plot** | เลือกโหมด `AC (.ac)` ($R_L = 10\text{ k}\Omega, C_{in} = 10\text{ }\mu\text{F}, C_{out} = 10\text{ }\mu\text{F}$) แล้วกด **Run Simulation** | สถานะขึ้น `Success (.ac)` แสดงอัตราขยาย Midband Gain (V/V และ dB), ความถี่ตัด $f_L, f_H$ และวาดกราฟ Bode Magnitude (dB) กับ Phase (deg) บนแกนความถี่ Log Scale ได้จริง | **PASS** |
| **B5** | **การจำลอง SPICE โหมด Transient (`.tran`)** | เลือกโหมด `Transient (.tran)` ($V_{in} = 10\text{ mV}, f = 1\text{ kHz}$) แล้วกด **Run Simulation** | สถานะขึ้น `Success (.tran)` แสดงค่า $V_{in}\text{ Peak}, V_{out}\text{ Peak}$, อัตราขยาย และวาดกราฟคลื่น $V_{in}$ เทียบกับ $V_{out}$ ที่กลับเฟส $180^\circ$ ในโดเมนเวลา | **PASS** |
| **B6** | **การตอบสนองเมื่อเปลี่ยนพารามิเตอร์แหล่งจ่าย/ตัวเก็บประจุ** | ทดลองเปลี่ยน Amplitude ใน `.tran` (เช่น $10\text{ mV} \to 20\text{ mV}$) และเปลี่ยน $C_{in}$ ใน `.ac` | ใน `.tran` ค่า $V_{out}\text{ Peak}$ เพิ่มขึ้นตามสัดส่วนอินพุต; ใน `.ac` ความถี่ตัดต่ำ $f_L$ ขยับเปลี่ยนตามค่า $C_{in}$ และตรวจสอบใน Netlist/Log พบค่าอัปเดตตรงตามที่กรอก | **PASS** |
| **B7** | **การแยกแหล่งที่มา (Provenance) และ Netlist Inspector** | ตรวจสอบป้ายกำกับผลลัพธ์และคลี่หัวข้อ `Inspect Generated Netlist & ngspice Log` | แยกตาราง `Analytical (dc_bias.py)` ออกจากกล่อง `SPICE Simulation (Engine: ngspice)` ชัดเจน และสามารถเปิดดูโค้ด `.cir` กับ Log ของ `ngspice` ได้จริง | **PASS** |
| **B8** | **การจัดการข้อผิดพลาด (Input Validation & Error Handling)** | กรอกค่าไม่ถูกต้อง (เช่น $V_{CC}=0$, ค่าติดลบ, หรือตัวอักษร) แล้วกดรัน | แสดงข้อความแจ้งเตือนภาษาอังกฤษที่ชัดเจน ไม่เกิด Server Crash (HTTP 500) และไม่ส่งค่าผิดพลาดไปรันใน `ngspice` | **PASS** |

---

## 2. แหล่งอ้างอิง ความคลาดเคลื่อน และข้อจำกัด (References, Discrepancies & Limitations)

1. **แหล่งอ้างอิง (References)**:
   - **Analytical Model (`bjt.py`)**: คำนวณด้วยแบบจำลองอุดมคติค่าคงที่ ($\beta = 100$, $V_{BE} = 0.70\text{ V}$ คงที่, ไม่คิด Early Effect)
   - **SPICE Model (`spice_engine.py`)**: ใช้สมการ Gummel-Poon ของทรานซิสเตอร์จริง `Q2N2222` (`IS=14.34f`, `BF=255.9`, `VAF=74.03`) รันบน `ngspice-47`
2. **ความคลาดเคลื่อนระหว่าง Analytical กับ SPICE (Discrepancies)**:
   - ค่าจุดทำงาน DC แตกต่างกันเล็กน้อย (เช่น $V_B = 1.94\text{ V}$ vs $2.016\text{ V}$ และ $V_{CE} = 8.05\text{ V}$ vs $7.653\text{ V}$) เนื่องจากโมเดล `Q2N2222` มีอัตราขยายกระแสจริง ($\beta \approx 200\text{–}255$) สูงกว่าค่าสมมติ $\beta = 100$ ทำให้กระแสเบส $I_B$ น้อยลง ลดผลกระทบการโหลดตัวแบ่งแรงดัน ($R_1 \parallel R_2$) และแรงดันตกคร่อม $V_{BE}$ จริงแปรผันตามสมการไดโอด ($I_C = I_S e^{V_{BE}/V_T}$)
3. **ข้อจำกัดของระบบ (Limitations)**:
   - การจำลอง AC และ Transient ของ `ngspice` ในเวอร์ชันนี้รองรับเฉพาะโครงสร้าง **Voltage Divider Common-Emitter (CE Reference)** เท่านั้น (โหมด Fixed Bias และ Emitter Bias รองรับเฉพาะการวิเคราะห์ DC Bias)
   - กราฟ `.ac` ใช้แบบจำลองเชิงเส้นสัญญาณเล็ก (Small-Signal) จึงไม่แสดงอาการขลิบสัญญาณ (Clipping) เมื่อป้อนอินพุตขนาดใหญ่ (ต้องตรวจสอบอาการ Clipping ในโหมด `.tran`)

---

## 3. บันทึกการใช้ AI และการตรวจสอบด้วยตนเอง (AI Usage & Self-Verification Log)

- **ส่วนที่ AI ช่วยสร้าง/แก้ไข**: AI ช่วยออกแบบโครงสร้างโมดูล `spice_engine.py` สำหรับสร้าง Netlist และเรียกใช้งาน `ngspice_con.exe` แบบ Batch Mode รวมถึงปรับปรุงหน้า UI ใน `templates/index.html` และ `static/style.css` เพื่อเพิ่มแท็บวิเคราะห์ `.op` / `.ac` / `.tran`, วาดกราฟ Canvas Bode/Waveform และซ่อนช่อง input ที่ไม่ใช้ในแต่ละโหมด
- **ส่วนที่นักศึกษาตรวจสอบและแก้ไขด้วยตนเอง**: นักศึกษาได้ทดสอบรันเซิร์ฟเวอร์ Flask บนเครื่องจริง (`http://127.0.0.1:5000`), ตรวจสอบความถูกต้องของวงจร SVG และหน่วยทางไฟฟ้า, รันชุดทดสอบ `pytest` จนผ่านครบทั้งหมด 43 ข้อ (`43 passed`) รวมถึงเปิดตรวจสอบ Generated Netlist และ Log ของ `ngspice` เทียบกับผลคำนวณทางทฤษฎีด้วยตนเอง