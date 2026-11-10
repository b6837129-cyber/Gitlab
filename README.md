# BJT Common-Emitter DC Bias Calculator

## คำอธิบาย

เว็บแอปพลิเคชัน Flask สำหรับคำนวณจุดทำงานกระแสตรง (DC Operating Point) ของวงจรขยาย BJT แบบ Common-Emitter ที่ไบแอสด้วยตัวต้านทานแบบแบ่งแรงดัน ผู้ใช้กรอก VCC, R1, R2, RC, RE, β และ VBE แล้วระบบจะคำนวณ IB, IC, IE, VB, VC, VE และ VCE พร้อมหน่วย ตรวจสอบความถูกต้องของข้อมูล แจ้งย่านการทำงาน (Active / Cutoff / Saturation) และเปรียบเทียบผลกับวิธี nodal analysis ที่คำนวณแยกกัน

## ฟีเจอร์

- รับค่าอินพุต 7 ค่า: VCC, R1, R2, RC, RE, β และ VBE
- แสดงจุดทำงาน DC พร้อมหน่วย µA, mA และ V
- ตรวจสอบข้อมูลภาษาไทย เช่น ค่าติดลบ, ค่าเป็นศูนย์, ข้อความที่ไม่ใช่ตัวเลข และค่านอกช่วง
- แจ้งเตือนเมื่อทรานซิสเตอร์อยู่ในย่าน Cutoff หรือ Saturation
- ตรวจสอบผลด้วยการคำนวณอิสระแบบ nodal analysis และแสดงตารางเปรียบเทียบพร้อมผลต่าง
- มีเทสต์อัตโนมัติสำหรับการคำนวณ การตรวจสอบ และ Flask route

## วิธีติดตั้ง

ต้องใช้ Python 3.12 ขึ้นไป

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## วิธีรัน

```powershell
.\.venv\Scripts\python.exe app.py
```

เปิดเบราว์เซอร์ที่ `http://127.0.0.1:5000`

## วิธีทดสอบ

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## ตัวอย่างการใช้งาน

ค่าอินพุต:

| ปริมาณ | ค่า |
| --- | --- |
| VCC | 12 V |
| R1 | 47 kΩ |
| R2 | 10 kΩ |
| RC | 2.2 kΩ |
| RE | 1 kΩ |
| β | 150 |
| VBE | 0.7 V |

ผลลัพธ์โดยประมาณ:

| ปริมาณ | ค่า |
| --- | --- |
| IB | 8.8245 µA |
| IC | 1.3237 mA |
| IE | 1.3325 mA |
| VB | 2.0325 V |
| VC | 9.0879 V |
| VE | 1.3325 V |
| VCE | 7.7554 V |

ย่านการทำงาน: Active และผลตรวจสอบด้วย nodal analysis: ผ่าน

## โครงสร้างไฟล์

- `app.py` — Flask app factory, route และการเตรียมข้อมูลสำหรับ template
- `bjt.py` — validation, การคำนวณจุดทำงาน DC และการแยกย่านการทำงาน
- `verification.py` — การคำนวณอิสระด้วย nodal analysis และการเปรียบเทียบผล
- `templates/index.html` — หน้าเว็บภาษาไทย
- `static/style.css` — การจัดรูปแบบหน้าเว็บ
- `tests/test_bjt.py` — เทสต์ validation และการคำนวณ
- `tests/test_verification.py` — เทสต์การคำนวณอิสระ
- `tests/test_app.py` — เทสต์ Flask route และการแสดงผล
- `requirements.txt` — รายการแพ็กเกจที่ต้องใช้
- `docs/superpowers/` — เอกสาร design และ implementation plan

## หมายเหตุ

ไฟล์ `electrical.py` และ `test_electrical.py` เป็นแบบฝึกหัดเดิมเรื่องกฎของโอห์มและยังคงอยู่ใน repository นี้ แอปพลิเคชัน BJT ด้านบนเป็นงาน lab แยกต่างหาก
