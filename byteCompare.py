import re

def clean_hex_string(raw):
    """過濾掉非十六進位與空白字元"""
    return re.sub(r'[^0-9a-fA-F ]+', '', raw)

def hex_string_to_bytes(hex_string):
    """轉成 bytes"""
    cleaned = clean_hex_string(hex_string)
    return bytes.fromhex(cleaned)

def compare_hex_data(hex1, hex2):
    """比對兩段 hex 並印出差異"""
    data1 = hex_string_to_bytes(hex1)
    data2 = hex_string_to_bytes(hex2)

    max_len = max(len(data1), len(data2))
    print("====== 差異位置比對開始 ======")
    for i in range(max_len):
        b1 = data1[i] if i < len(data1) else None
        b2 = data2[i] if i < len(data2) else None
        if b1 != b2:
            s1 = f"{b1:02X}" if b1 is not None else "None"
            s2 = f"{b2:02X}" if b2 is not None else "None"
            print(f"差異位置: {i:04X} | 第一段: {s1} | 第二段: {s2}")
    print("====== 比對完成 ======")

# === 比對byteArray ===
hex1 = """
AA 55 40 01 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF 76 26 04 00 FF FF FF FF
68 26 04 00 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
04 00 00 00 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
F6 26 04 00 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
26
"""

hex2 = """
AA 55 40 01 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF 76 26 04 00 FF FF FF FF
68 26 04 00 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
04 00 00 00 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
F6 26 04 00 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
26
"""

hex3 = """55 AA 01 17 41 01 00 02 02 """
hex4 = """55 AA 01 03 41 01 00 02 02  """

# === 執行 ===
compare_hex_data(hex3, hex4)  

