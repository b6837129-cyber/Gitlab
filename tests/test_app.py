import unittest

from app import create_app

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('name="vcc"', text)
        self.assertIn("วงจรไบแอสแบบแบ่งแรงดัน", text)

    def test_valid_post_shows_active_result(self):
        response = self.client.post("/", data=VALID)
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("8.8245", text)
        self.assertIn("7.7554", text)
        self.assertIn("ทำงานปกติ (Active)", text)
        self.assertIn("ตรวจสอบด้วยการคำนวณอิสระ", text)
        self.assertIn("ผลตรวจสอบ: ผ่าน", text)

    def test_invalid_post_shows_thai_error(self):
        data = dict(VALID)
        data["vcc"] = "0"
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("VCC ต้องมากกว่า 0 V", text)
        self.assertNotIn("ตรวจสอบด้วยการคำนวณอิสระ", text)

    def test_cutoff_shows_warning(self):
        data = dict(VALID)
        data["r2"] = "1000"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("ตัดขาด (Cutoff)", text)
        self.assertIn("ใช้ได้เฉพาะย่าน Active", text)

    def test_saturation_shows_warning(self):
        data = dict(VALID)
        data["r1"] = "10000"
        data["r2"] = "47000"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("อิ่มตัว (Saturation)", text)
        self.assertIn("0.2 V", text)

    def test_extreme_values_show_error_not_crash(self):
        data = dict(VALID)
        data.update(
            {
                "vcc": "1e308",
                "r1": "1e308",
                "r2": "1e308",
                "rc": "1e308",
                "re": "1e308",
            }
        )
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ไม่สามารถให้ผลลัพธ์ที่ถูกต้องได้",
            response.get_data(as_text=True),
        )

    def test_submitted_html_is_escaped(self):
        data = dict(VALID)
        data["vcc"] = "<script>alert(1)</script>"
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn("<script>alert(1)</script>", text)


if __name__ == "__main__":
    unittest.main()
