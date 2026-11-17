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
3. **ตรวจการส่งพารามิเตอร์เข้าฟังก์ชันคำนวณ (`app.py`):** ตรวจสอบในบล็อก `elif mode == "emitter":` และ `if mode == "divider":` ว่าได้ส่งอาร์กิวเมนต์ `re_ohm=float(parsed["re"])` เข้าไปในฟังก์ชัน `calculate_emitter_bias()` หรือ `calculate_voltage_divider()` จริง ไม่ได้เผลอส่งค่าคงที่หรือส่ง `re_ohm=0.0` ของ Fixed Bias ไปแทน