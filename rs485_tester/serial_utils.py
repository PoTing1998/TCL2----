import serial
import serial.tools.list_ports
import datetime
import time



class RS485Tester:
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1,log_file=None):
        if not port or not port.strip():
            raise ValueError("串口名稱不能為空")
        
        if baudrate not in [9600, 19200, 38400, 57600, 115200]:
            raise ValueError(f"不支援的波特率: {baudrate}")
        
        if timeout <= 0:
            raise ValueError("逾時時間必須大於0")
        
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=timeout
            )
        except serial.SerialException as e:
            raise ConnectionError(f"無法開啟串口 {port}: {e}")
        except Exception as e:
            raise ConnectionError(f"串口初始化失敗: {e}")
        self.log_file = log_file
        if self.log_file:
            try:
                self.log_handle = open(self.log_file, 'a', encoding='utf-8')
                self._log_message(f"--- RS485 Tester Session Started on Port {port} ---")
            except (OSError, IOError) as e:
                print(f"警告: 無法開啟日誌文件 {log_file}: {e}")
                self.log_handle = None
        else:
            self.log_handle = None
    def _log_message(self , message):
        if self.log_handle:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # Milliseconds precision
            self.log_handle.write(f"[{timestamp}] {message}\n")
            self.log_handle.flush() # Ensure the message is written to the disk immediately
    
    

    def send_hex(self, hex_str):
        if not hex_str or not hex_str.strip():
            raise ValueError("十六進位字串不能為空")
        
        try:
            data = bytes.fromhex(hex_str.replace(" ", ""))
        except ValueError as e:
            raise ValueError(f"無效的十六進位字串: {e}")
        
        try:
            self.ser.write(data)
            log_message = f"[送出] {hex_str}"
            print(log_message)
            self._log_message(log_message) 
            time.sleep(0.1)  # 等待約 0.1毫秒
        except serial.SerialException as e:
            raise ConnectionError(f"發送資料失敗: {e}")
        except Exception as e:
            raise ConnectionError(f"串口寫入錯誤: {e}") 

    def receive_response(self, max_bytes=64):
        if max_bytes <= 0:
            raise ValueError("最大接收位元組數必須大於0")
        
        try:
            response = self.ser.read(max_bytes)
            if response:
                received_hex = response.hex(' ').upper()
                log_message = f"[接收] {received_hex}"
                print(log_message)
                self._log_message(log_message)
                time.sleep(0.1)  
            else:
                log_message = "[接收] 無回應（可能逾時）"
                print(log_message)
                self._log_message(log_message)
            return response  # Optionally return the response bytes for further processing
        except serial.SerialException as e:
            raise ConnectionError(f"接收資料失敗: {e}")
        except Exception as e:
            raise ConnectionError(f"串口讀取錯誤: {e}")                   
    



    def close(self):
        try:
            if hasattr(self, 'ser') and self.ser:
                self.ser.close()
        except serial.SerialException as e:
            print(f"警告: 關閉串口時發生錯誤: {e}")
        except Exception as e:
            print(f"關閉串口時發生未預期錯誤: {e}")
        
        if self.log_handle:
            try:
                self._log_message("--- RS485 Tester Session Ended ---")
                self.log_handle.close()
            except (OSError, IOError) as e:
                print(f"警告: 關閉日誌文件時發生錯誤: {e}")
            finally:
                self.log_handle = None


def list_available_ports():
    """列出可用的串口"""
    try:
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]
    except Exception as e:
        print(f"警告: 取得串口清單時發生錯誤: {e}")
        return []
