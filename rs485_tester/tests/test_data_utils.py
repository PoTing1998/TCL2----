# -*- coding: utf-8 -*-
"""
data_utils.py 單元測試
"""
import unittest
from test_config import *

try:
    from ..data_utils import DataFormatter, ModbusPacketAnalyzer
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data_utils import DataFormatter, ModbusPacketAnalyzer


class TestDataFormatter(unittest.TestCase):
    """DataFormatter 測試類"""
    
    def test_hex_to_ascii_valid(self):
        """測試有效的十六進位轉ASCII"""
        # 可列印字符
        result = DataFormatter.hex_to_ascii("48656C6C6F")  # "Hello"
        self.assertEqual(result, "Hello")
        
        # 包含空格的十六進位
        result = DataFormatter.hex_to_ascii("48 65 6C 6C 6F")
        self.assertEqual(result, "Hello")
        
        # 混合可列印和不可列印字符
        result = DataFormatter.hex_to_ascii("480165")  # H\x01e
        self.assertEqual(result, "H\\x01e")
    
    def test_hex_to_ascii_invalid(self):
        """測試無效的十六進位轉ASCII"""
        # 無效字符
        result = DataFormatter.hex_to_ascii("ZZ")
        self.assertIn("轉換錯誤", result)
        
        # 奇數長度的十六進位字串
        result = DataFormatter.hex_to_ascii("48656C6C6")
        self.assertIn("轉換錯誤", result)
        
        # 空字串
        result = DataFormatter.hex_to_ascii("")
        self.assertEqual(result, "")
    
    def test_hex_to_decimal_valid(self):
        """測試有效的十六進位轉十進位"""
        result = DataFormatter.hex_to_decimal("010203")
        self.assertEqual(result, "1 2 3")
        
        # 包含空格
        result = DataFormatter.hex_to_decimal("01 02 03")
        self.assertEqual(result, "1 2 3")
        
        # 大數值
        result = DataFormatter.hex_to_decimal("FF")
        self.assertEqual(result, "255")
    
    def test_hex_to_decimal_invalid(self):
        """測試無效的十六進位轉十進位"""
        result = DataFormatter.hex_to_decimal("ZZ")
        self.assertIn("轉換錯誤", result)
        
        result = DataFormatter.hex_to_decimal("0102G")
        self.assertIn("轉換錯誤", result)
    
    def test_hex_to_binary_valid(self):
        """測試有效的十六進位轉二進位"""
        result = DataFormatter.hex_to_binary("01")
        self.assertEqual(result, "00000001")
        
        result = DataFormatter.hex_to_binary("FF")
        self.assertEqual(result, "11111111")
        
        result = DataFormatter.hex_to_binary("01 02")
        self.assertEqual(result, "00000001 00000010")
    
    def test_hex_to_binary_invalid(self):
        """測試無效的十六進位轉二進位"""
        result = DataFormatter.hex_to_binary("ZZ")
        self.assertIn("轉換錯誤", result)
    
    def test_edge_cases(self):
        """測試邊界情況"""
        # 空字串
        self.assertEqual(DataFormatter.hex_to_ascii(""), "")
        self.assertEqual(DataFormatter.hex_to_decimal(""), "")
        self.assertEqual(DataFormatter.hex_to_binary(""), "")
        
        # 單一字節
        self.assertEqual(DataFormatter.hex_to_ascii("41"), "A")
        self.assertEqual(DataFormatter.hex_to_decimal("41"), "65")
        self.assertEqual(DataFormatter.hex_to_binary("41"), "01000001")


class TestModbusPacketAnalyzer(unittest.TestCase):
    """ModbusPacketAnalyzer 測試類"""
    
    def test_analyze_read_holding_registers(self):
        """測試讀取保持暫存器封包分析"""
        # 標準讀取請求: 設備地址01, 功能碼03, 起始位址0000, 數量0001
        packet = "01 03 00 00 00 01 84 0A"
        result = ModbusPacketAnalyzer.analyze_packet(packet)
        
        self.assertIsInstance(result, dict)
        self.assertIn("設備地址", result)
        self.assertIn("功能碼", result)
        self.assertIn("起始位址", result)
        self.assertIn("讀取數量", result)
        self.assertIn("CRC", result)
        
        # 檢查解析結果
        self.assertIn("01", result["設備地址"])
        self.assertIn("03", result["功能碼"])
        self.assertIn("0000", result["起始位址"])
        self.assertEqual(result["讀取數量"], "1")
    
    def test_analyze_read_input_registers(self):
        """測試讀取輸入暫存器封包分析"""
        # 設備地址01, 功能碼04, 起始位址0000, 數量0002
        packet = "01 04 00 00 00 02 71 CB"
        result = ModbusPacketAnalyzer.analyze_packet(packet)
        
        self.assertIsInstance(result, dict)
        self.assertIn("設備地址", result)
        self.assertIn("功能碼", result)
        self.assertIn("起始位址", result)
        self.assertIn("讀取數量", result)
        
        # 檢查解析結果
        self.assertIn("01", result["設備地址"])
        self.assertIn("04", result["功能碼"])
        self.assertEqual(result["讀取數量"], "2")
    
    def test_analyze_write_single_register(self):
        """測試寫入單一暫存器封包分析"""
        # 設備地址01, 功能碼06, 位址0001, 數值0123
        packet = "01 06 00 01 01 23 9A 0B"
        result = ModbusPacketAnalyzer.analyze_packet(packet)
        
        self.assertIsInstance(result, dict)
        self.assertIn("設備地址", result)
        self.assertIn("功能碼", result)
        self.assertIn("暫存器位址", result)
        self.assertIn("寫入值", result)
        
        # 檢查解析結果
        self.assertIn("01", result["設備地址"])
        self.assertIn("06", result["功能碼"])
        self.assertIn("0001", result["暫存器位址"])
        self.assertIn("0123", result["寫入值"])
    
    def test_analyze_invalid_packet_length(self):
        """測試無效封包長度"""
        # 太短的封包
        short_packet = "01 03"
        result = ModbusPacketAnalyzer.analyze_packet(short_packet)
        self.assertIsInstance(result, str)
        self.assertIn("封包長度不足", result)
    
    def test_analyze_invalid_hex_string(self):
        """測試無效的十六進位字串"""
        invalid_packet = "01 GG 00 00 00 01"
        result = ModbusPacketAnalyzer.analyze_packet(invalid_packet)
        self.assertIsInstance(result, str)
        self.assertIn("分析錯誤", result)
    
    def test_analyze_unknown_function_code(self):
        """測試未知功能碼"""
        # 使用不常見的功能碼99
        packet = "01 99 00 00 00 01 84 0A"
        result = ModbusPacketAnalyzer.analyze_packet(packet)
        
        self.assertIsInstance(result, dict)
        self.assertIn("功能碼", result)
        self.assertIn("未知功能", result["功能碼"])
    
    def test_get_function_name(self):
        """測試功能碼名稱取得"""
        # 測試已知功能碼
        self.assertNotEqual(
            ModbusPacketAnalyzer._get_function_name(0x03), 
            "未知功能"
        )
        
        # 測試未知功能碼
        self.assertEqual(
            ModbusPacketAnalyzer._get_function_name(0x99), 
            "未知功能"
        )
    
    def test_analyze_by_function_edge_cases(self):
        """測試功能碼分析的邊界情況"""
        # 測試功能碼03但封包太短
        short_data = bytes([0x01, 0x03, 0x00])
        result = ModbusPacketAnalyzer._analyze_by_function(short_data)
        self.assertIsInstance(result, dict)
        # 短封包不應該包含位址和數量資訊
        self.assertNotIn("起始位址", result)
        
        # 測試功能碼06但封包太短
        short_data = bytes([0x01, 0x06, 0x00])
        result = ModbusPacketAnalyzer._analyze_by_function(short_data)
        self.assertIsInstance(result, dict)
        self.assertNotIn("暫存器位址", result)
    
    def test_crc_calculation(self):
        """測試CRC計算"""
        # 包含CRC的完整封包
        packet = "01 03 00 00 00 01 84 0A"
        result = ModbusPacketAnalyzer.analyze_packet(packet)
        
        self.assertIn("CRC", result)
        # CRC應該是最後兩個字節的組合 (小端序)
        self.assertIn("0A84", result["CRC"])
    
    def test_response_packet_analysis(self):
        """測試回應封包分析"""
        # 讀取暫存器的回應封包: 設備地址01, 功能碼03, 資料長度02, 資料0001
        response_packet = "01 03 02 00 01 79 84"
        result = ModbusPacketAnalyzer.analyze_packet(response_packet)
        
        self.assertIsInstance(result, dict)
        self.assertIn("設備地址", result)
        self.assertIn("功能碼", result)
        self.assertIn("01", result["設備地址"])
        self.assertIn("03", result["功能碼"])
    
    def test_empty_packet(self):
        """測試空封包"""
        result = ModbusPacketAnalyzer.analyze_packet("")
        self.assertIsInstance(result, str)
        self.assertIn("封包長度不足", result)
    
    def test_packet_with_spaces(self):
        """測試包含多種空格格式的封包"""
        packets = [
            "01030000000184 0A",  # 末尾空格
            " 01 03 00 00 00 01 84 0A ",  # 前後空格
            "01  03   00 00 00 01 84 0A",  # 多重空格
        ]
        
        for packet in packets:
            result = ModbusPacketAnalyzer.analyze_packet(packet)
            self.assertIsInstance(result, dict)
            self.assertIn("設備地址", result)


if __name__ == '__main__':
    unittest.main()