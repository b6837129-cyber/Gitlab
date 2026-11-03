def analyze_dc(voltage_v: float, resistance_ohm: float) -> dict[str, float]:
    """Calculate current and power for a DC circuit using Ohm's law."""
    if not isinstance(voltage_v, (int, float)):
        raise TypeError("voltage_v must be a number")
    if not isinstance(resistance_ohm, (int, float)):
        raise TypeError("resistance_ohm must be a number")
    if resistance_ohm <= 0:
        raise ValueError("resistance_ohm must be greater than zero")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


if __name__ == "__main__":
    try:
        voltage_v = float(input("ป้อนแรงดันไฟฟ้า (V): "))
        resistance_ohm = float(input("ป้อนความต้านทาน (Ohm): "))
        result = analyze_dc(voltage_v, resistance_ohm)

        print(f"กระแสไฟฟ้า: {result['current_a']:.2f} A")
        print(f"กำลังไฟฟ้า: {result['power_w']:.2f} W")
    except ValueError as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")