# -*- coding: utf-8 -*-
"""
serial_utils.py 單元測試
"""
import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import io
import datetime
from test_config import *

try:
    from ..serial_utils import RS485Tester, list_available_ports
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from serial_utils import RS485Tester, list_available_ports


class TestRS485Tester(unittest.TestCase):
    """RS485Tester 測試類"""
    
    @patch('serial_utils.serial.Serial')
    def setUp(self, mock_serial):
        """設置測試環境"""
        self.mock_serial_instance = Mock()
        mock_serial.return_value = self.mock_serial_instance
        self.test_port = "COM1"
        self.tester = RS485Tester(self.test_port)
    
    def tearDown(self):
        """清理測試環境"""
        if hasattr(self.tester, 'log_handle') and self.tester.log_handle:
            self.tester.log_handle.close()
    
    @patch('serial_utils.serial.Serial')
    def test_init_without_log_file(self, mock_serial):
        """測試不使用日誌文件的初始化"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        tester = RS485Tester("COM1", baudrate=19200, timeout=2)
        
        # 驗證串口參數
        mock_serial.assert_called_with(
            port="COM1",
            baudrate=19200,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=2
        )
        
        self.assertEqual(tester.ser, mock_serial_instance)
        self.assertIsNone(tester.log_handle)
    
    @patch('serial_utils.serial.Serial')
    @patch('builtins.open', new_callable=mock_open)
    def test_init_with_log_file(self, mock_file, mock_serial):
        """測試使用日誌文件的初始化"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        log_file = "test.log"
        tester = RS485Tester("COM1", log_file=log_file)
        
        # 驗證日誌文件被打開
        mock_file.assert_called_with(log_file, 'a', encoding='utf-8')
        self.assertIsNotNone(tester.log_handle)
    
    def test_send_hex_valid(self):
        """測試發送有效的十六進位資料"""
        hex_str = "01 03 00 00 00 01"
        expected_bytes = bytes.fromhex(hex_str)
        
        with patch('builtins.print') as mock_print, \
             patch.object(self.tester, '_log_message') as mock_log:
            
            self.tester.send_hex(hex_str)
            
            # 驗證串口寫入
            self.mock_serial_instance.write.assert_called_with(expected_bytes)
            
            # 驗證日誌記錄
            mock_print.assert_called()
            mock_log.assert_called()
    
    def test_send_hex_invalid(self):
        """測試發送無效的十六進位資料"""
        hex_str = "ZZ"
        
        with self.assertRaises(ValueError):
            self.tester.send_hex(hex_str)
    
    def test_receive_response_with_data(self):
        """測試接收有資料的回應"""
        response_bytes = b'\x01\x03\x02\x00\x01'
        self.mock_serial_instance.read.return_value = response_bytes
        
        with patch('builtins.print') as mock_print, \
             patch.object(self.tester, '_log_message') as mock_log:
            
            result = self.tester.receive_response()
            
            # 驗證回傳值
            self.assertEqual(result, response_bytes)
            
            # 驗證串口讀取
            self.mock_serial_instance.read.assert_called_with(64)
            
            # 驗證日誌記錄
            mock_print.assert_called()
            mock_log.assert_called()
    
    def test_receive_response_no_data(self):
        """測試接收無資料的回應"""
        self.mock_serial_instance.read.return_value = b''
        
        with patch('builtins.print') as mock_print, \
             patch.object(self.tester, '_log_message') as mock_log:
            
            result = self.tester.receive_response()
            
            # 驗證回傳值
            self.assertEqual(result, b'')
            
            # 驗證日誌記錄逾時訊息
            mock_log.assert_called_with("[接收] 無回應（可能逾時）")
    
    def test_receive_response_custom_max_bytes(self):
        """測試自定義最大接收位元組數"""
        response_bytes = b'\x01\x03\x02\x00\x01'
        self.mock_serial_instance.read.return_value = response_bytes
        custom_max_bytes = 128
        
        with patch('builtins.print'), \
             patch.object(self.tester, '_log_message'):
            
            self.tester.receive_response(max_bytes=custom_max_bytes)
            
            # 驗證使用自定義的最大位元組數
            self.mock_serial_instance.read.assert_called_with(custom_max_bytes)
    
    def test_close_without_log(self):
        """測試關閉不使用日誌的連線"""
        self.tester.log_handle = None
        
        self.tester.close()
        
        # 驗證串口關閉
        self.mock_serial_instance.close.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_close_with_log(self, mock_file):
        """測試關閉使用日誌的連線"""
        mock_log_handle = Mock()
        self.tester.log_handle = mock_log_handle
        
        with patch.object(self.tester, '_log_message') as mock_log:
            self.tester.close()
            
            # 驗證串口關閉
            self.mock_serial_instance.close.assert_called_once()
            
            # 驗證日誌結束訊息
            mock_log.assert_called_with("--- RS485 Tester Session Ended ---")
            
            # 驗證日誌文件關閉
            mock_log_handle.close.assert_called_once()
            self.assertIsNone(self.tester.log_handle)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_log_message(self, mock_file):
        """測試日誌訊息記錄"""
        mock_log_handle = Mock()
        self.tester.log_handle = mock_log_handle
        
        test_message = "Test message"
        
        with patch('serial_utils.datetime') as mock_datetime:
            # 模擬時間戳
            mock_now = Mock()
            mock_now.strftime.return_value = "2023-01-01 12:00:00.123456"
            mock_datetime.datetime.now.return_value = mock_now
            
            self.tester._log_message(test_message)
            
            # 驗證寫入格式（注意時間格式會被截取毫秒）
            expected_log = "[2023-01-01 12:00:00.123] Test message\n"
            mock_log_handle.write.assert_called_with(expected_log)
            mock_log_handle.flush.assert_called_once()
    
    def test_log_message_without_handle(self):
        """測試沒有日誌處理器時的日誌記錄"""
        self.tester.log_handle = None
        
        # 不應該引發異常
        self.tester._log_message("Test message")
    
    @patch('serial_utils.time.sleep')
    def test_send_hex_timing(self, mock_sleep):
        """測試發送資料的時間延遲"""
        hex_str = "01 03"
        
        with patch('builtins.print'), \
             patch.object(self.tester, '_log_message'):
            
            self.tester.send_hex(hex_str)
            
            # 驗證延遲調用
            mock_sleep.assert_called_with(0.1)
    
    @patch('serial_utils.time.sleep')
    def test_receive_response_timing(self, mock_sleep):
        """測試接收資料的時間延遲"""
        self.mock_serial_instance.read.return_value = b'\x01\x03'
        
        with patch('builtins.print'), \
             patch.object(self.tester, '_log_message'):
            
            self.tester.receive_response()
            
            # 驗證延遲調用
            mock_sleep.assert_called_with(0.1)
    
    def test_hex_formatting_in_receive(self):
        """測試接收資料的十六進位格式化"""
        response_bytes = b'\x01\x03\x02\x00\x01\x79\x84'
        self.mock_serial_instance.read.return_value = response_bytes
        
        with patch('builtins.print') as mock_print, \
             patch.object(self.tester, '_log_message') as mock_log:
            
            self.tester.receive_response()
            
            # 驗證十六進位格式化（大寫，空格分隔）
            expected_hex = "01 03 02 00 01 79 84"
            mock_log.assert_called_with(f"[接收] {expected_hex}")


class TestListAvailablePorts(unittest.TestCase):
    """list_available_ports 測試類"""
    
    @patch('serial_utils.serial.tools.list_ports.comports')
    def test_list_available_ports_with_ports(self, mock_comports):
        """測試列出可用串口（有串口）"""
        # 模擬串口資訊
        mock_port1 = Mock()
        mock_port1.device = "COM1"
        mock_port1.description = "USB Serial Port"
        
        mock_port2 = Mock()
        mock_port2.device = "COM3"
        mock_port2.description = "Bluetooth Serial Port"
        
        mock_comports.return_value = [mock_port1, mock_port2]
        
        result = list_available_ports()
        
        expected = [
            ("COM1", "USB Serial Port"),
            ("COM3", "Bluetooth Serial Port")
        ]
        
        self.assertEqual(result, expected)
    
    @patch('serial_utils.serial.tools.list_ports.comports')
    def test_list_available_ports_no_ports(self, mock_comports):
        """測試列出可用串口（無串口）"""
        mock_comports.return_value = []
        
        result = list_available_ports()
        
        self.assertEqual(result, [])
    
    @patch('serial_utils.serial.tools.list_ports.comports')
    def test_list_available_ports_with_special_characters(self, mock_comports):
        """測試包含特殊字符的串口描述"""
        mock_port = Mock()
        mock_port.device = "COM1"
        mock_port.description = "USB-to-Serial (CH340)"
        
        mock_comports.return_value = [mock_port]
        
        result = list_available_ports()
        
        expected = [("COM1", "USB-to-Serial (CH340)")]
        self.assertEqual(result, expected)


class TestRS485TesterIntegration(unittest.TestCase):
    """RS485Tester 整合測試"""
    
    @patch('serial_utils.serial.Serial')
    @patch('builtins.open', new_callable=mock_open)
    def test_complete_communication_cycle(self, mock_file, mock_serial):
        """測試完整的通訊週期"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # 模擬接收回應
        response_bytes = b'\x01\x03\x02\x00\x01\x79\x84'
        mock_serial_instance.read.return_value = response_bytes
        
        tester = RS485Tester("COM1", log_file="test.log")
        
        with patch('builtins.print'), \
             patch('serial_utils.time.sleep'):
            
            # 發送指令
            tester.send_hex("01 03 00 00 00 01 84 0A")
            
            # 接收回應
            result = tester.receive_response()
            
            # 關閉連線
            tester.close()
        
        # 驗證發送和接收
        mock_serial_instance.write.assert_called()
        mock_serial_instance.read.assert_called()
        self.assertEqual(result, response_bytes)
        
        # 驗證串口關閉
        mock_serial_instance.close.assert_called()
    
    @patch('serial_utils.serial.Serial')
    def test_error_handling_in_serial_operations(self, mock_serial):
        """測試串口操作的錯誤處理"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # 模擬串口寫入錯誤
        mock_serial_instance.write.side_effect = Exception("Serial write error")
        
        tester = RS485Tester("COM1")
        
        with self.assertRaises(Exception):
            tester.send_hex("01 03")


if __name__ == '__main__':
    # 設定測試運行時的編碼
    import sys
    import io
    
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    unittest.main(verbosity=2)