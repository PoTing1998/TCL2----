import serial
import serial.tools.list_ports
import datetime
import time



class RS485Tester:
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1,log_file=None):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout
        )
        self.log_file = log_file
        if self.log_file:
            self.log_handle = open(self.log_file , 'a' , encoding='utf-8')
            self._log_message(f"--- RS485 Tester Session Started on Port {port} ---")
        else:
            self.log_handle = None
    def _log_message(self , message):
        if self.log_handle:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # Milliseconds precision
            self.log_handle.write(f"[{timestamp}] {message}\n")
            self.log_handle.flush() # Ensure the message is written to the disk immediately
    
    

    def send_hex(self, hex_str):
        data = bytes.fromhex(hex_str)
        self.ser.write(data)
        log_message = f"[送出] {hex_str}"
        print(log_message)
        self._log_message(log_message) 
        time.sleep(0.1) #等待約 0.1毫秒 

    def receive_response(self, max_bytes=64):
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
        return response # Optionally return the response bytes for further processing                   
    



    def close(self):
        self.ser.close()
        if self.log_handle:
            self._log_message("--- RS485 Tester Session Ended ---")
            self.log_handle.close()
            self.log_handle = None


def list_available_ports():
    
    ports = serial.tools.list_ports.comports()
    return [(port.device, port.description) for port in ports]
