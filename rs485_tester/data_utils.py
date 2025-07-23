# -*- coding: utf-8 -*-
"""
資料處理工具類
"""
try:
    from .constants import MODBUS_FUNCTIONS
except ImportError:
    from constants import MODBUS_FUNCTIONS


class DataFormatter:
    """資料格式轉換器"""
    
    @staticmethod
    def hex_to_ascii(hex_str):
        """十六進位轉 ASCII"""
        try:
            hex_clean = hex_str.replace(" ", "")
            bytes_data = bytes.fromhex(hex_clean)
            return ''.join([chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in bytes_data])
        except ValueError:
            return "轉換錯誤: 無效的十六進位字串"
        except Exception as e:
            return f"轉換錯誤: {e}"
    
    @staticmethod
    def hex_to_decimal(hex_str):
        """十六進位轉十進位"""
        try:
            hex_clean = hex_str.replace(" ", "")
            bytes_data = bytes.fromhex(hex_clean)
            return ' '.join([str(b) for b in bytes_data])
        except ValueError:
            return "轉換錯誤: 無效的十六進位字串"
        except Exception as e:
            return f"轉換錯誤: {e}"
    
    @staticmethod
    def hex_to_binary(hex_str):
        """十六進位轉二進位"""
        try:
            hex_clean = hex_str.replace(" ", "")
            bytes_data = bytes.fromhex(hex_clean)
            return ' '.join([f'{b:08b}' for b in bytes_data])
        except ValueError:
            return "轉換錯誤: 無效的十六進位字串"
        except Exception as e:
            return f"轉換錯誤: {e}"


class ModbusPacketAnalyzer:
    """Modbus 封包分析器"""
    
    @staticmethod
    def analyze_packet(hex_str):
        """分析 Modbus 封包"""
        try:
            hex_clean = hex_str.replace(" ", "")
            if len(hex_clean) < 8:
                return "封包長度不足 (最少需要4個位元組)"
            
            bytes_data = bytes.fromhex(hex_clean)
            
            analysis = {
                "設備地址": f"{bytes_data[0]:02X} ({bytes_data[0]})",
                "功能碼": f"{bytes_data[1]:02X} ({ModbusPacketAnalyzer._get_function_name(bytes_data[1])})",
            }
            
            # 根據功能碼分析
            analysis.update(ModbusPacketAnalyzer._analyze_by_function(bytes_data))
            
            # CRC 檢查
            if len(bytes_data) >= 2:
                crc_received = (bytes_data[-1] << 8) | bytes_data[-2]
                analysis["CRC"] = f"{crc_received:04X}"
            
            return analysis
            
        except ValueError:
            return "分析錯誤: 無效的十六進位字串"
        except IndexError:
            return "分析錯誤: 封包格式不正確"
        except Exception as e:
            return f"分析錯誤: {e}"
    
    @staticmethod
    def _get_function_name(func_code):
        """取得功能碼名稱"""
        return MODBUS_FUNCTIONS.get(func_code, "未知功能")
    
    @staticmethod
    def _analyze_by_function(bytes_data):
        """根據功能碼分析封包內容"""
        analysis = {}
        func_code = bytes_data[1]
        
        if func_code in [0x03, 0x04] and len(bytes_data) >= 6:  # 讀取暫存器
            start_addr = (bytes_data[2] << 8) | bytes_data[3]
            quantity = (bytes_data[4] << 8) | bytes_data[5]
            analysis["起始位址"] = f"{start_addr:04X} ({start_addr})"
            analysis["讀取數量"] = f"{quantity}"
            
        elif func_code == 0x06 and len(bytes_data) >= 6:  # 寫入單一暫存器
            addr = (bytes_data[2] << 8) | bytes_data[3]
            value = (bytes_data[4] << 8) | bytes_data[5]
            analysis["暫存器位址"] = f"{addr:04X} ({addr})"
            analysis["寫入值"] = f"{value:04X} ({value})"
            
        return analysis