from dataclasses import dataclass
import math
from typing import Mapping


REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")


@dataclass(frozen=True)
class BiasInputs:
    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


def validate_and_parse(
    raw: Mapping[str, str],
) -> tuple[BiasInputs | None, dict[str, str]]:
    values: dict[str, float] = {}
    errors: dict[str, str] = {}

    for field in REQUIRED_FIELDS:
        text = str(raw.get(field, "")).strip()
        if not text:
            errors[field] = "กรุณากรอกค่านี้"
            continue
        try:
            number = float(text)
        except ValueError:
            errors[field] = "กรุณากรอกเป็นตัวเลข"
            continue
        if not math.isfinite(number):
            errors[field] = "กรุณากรอกเป็นตัวเลข"
            continue
        values[field] = number

    if "vcc" in values and values["vcc"] <= 0:
        errors["vcc"] = "VCC ต้องมากกว่า 0 V"

    for field in RESISTANCE_FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = "ค่าความต้านทานต้องมากกว่า 0 Ω"

    if "beta" in values and values["beta"] < 1:
        errors["beta"] = "β ต้องมีค่าตั้งแต่ 1 ขึ้นไป"

    if "vbe" in values and not (0 <= values["vbe"] <= 1.5):
        errors["vbe"] = "VBE ต้องอยู่ระหว่าง 0 ถึง 1.5 V"

    if errors:
        return None, errors

    return (
        BiasInputs(
            vcc_v=values["vcc"],
            r1_ohm=values["r1"],
            r2_ohm=values["r2"],
            rc_ohm=values["rc"],
            re_ohm=values["re"],
            beta=values["beta"],
            vbe_v=values["vbe"],
        ),
        {},
    )
