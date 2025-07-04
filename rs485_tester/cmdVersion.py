import serial # 匯入 serial 模組以處理可能發生的串列埠錯誤
import datetime # 匯入 datetime 模組用於時間戳記
import os       # 匯入 os 模組用於路徑操作和目錄建立
from log_exporter import LogToExcelExporter

# 或傳入自訂名稱，例如 export_to_excel("my_output.xlsx")

# 從 serial_utils.py 匯入我們定義的類別和函式
from serial_utils import RS485Tester, list_available_ports

def find_real_port(user_input, ports):
    """
    Returns:
        tuple: 如果找到匹配的埠，返回 (裝置路徑, 埠描述)；否則返回 (None, None)。
    """
    # 將使用者輸入的 COM Port 名稱標準化為大寫，並移除可能的空白
    normalized_input = user_input.strip().upper()

    for port_device, port_description in ports:
        # 將找到的裝置名稱也標準化，以便進行不區分大小寫的比較
        normalized_port_device = port_device.strip().upper()

        # 1. 檢查使用者輸入是否與裝置路徑完全匹配 (例如：使用者輸入 'COM3', port_device 是 'COM3')
        if normalized_input == normalized_port_device:
            return port_device, port_description

        # 2. 檢查使用者輸入是否是裝置路徑的 basename (例如 '/dev/ttyUSB0' 的 'ttyUSB0')
        if '/' in normalized_port_device:
            # 取得路徑的最後一個部分，例如從 '/dev/ttyUSB0' 取得 'ttyUSB0'
            device_basename = normalized_port_device.split('/')[-1]
            if normalized_input == device_basename:
                return port_device, port_description
        # 3. (可選的模糊匹配) 檢查使用者輸入是否在埠描述中
        if normalized_input in port_description.upper():
            print(f"提示：您輸入的 '{user_input}' 與埠描述 '{port_description}' 部分匹配。建議輸入完整的埠名稱或序號。")
            return port_device, port_description

    return None, None # 如果沒有找到匹配的埠

def main():
    print("🔌 正在掃描可用的 COM Port...")
    ports = list_available_ports()
    
    if not ports:
        print("❌ 沒有找到任何 COM Port。請確認設備是否插好並已安裝驅動程式。")
        input("按下 Enter 鍵退出...")
        return

    print("✅ 找到以下可用 COM Port：")
    for i, (dev, desc) in enumerate(ports):
        print(f"{i+1}. {dev} （裝置描述: {desc}）") # 顯示實際的 COM port 名稱和描述

    tester = None # 初始化 tester 變數為 None，確保在 finally 塊中可被存取

    # --- 選擇並連接 COM Port ---
    while True:
        user_input = input("請輸入要使用的 COM Port 名稱（例如 COM1 或 /dev/ttyUSB0），或輸入數字選擇 (1, 2...): ").strip()

        real_port = None
        desc = None

        if user_input.isdigit():
            # 使用者輸入數字選擇
            try:
                index = int(user_input) - 1
                if 0 <= index < len(ports):
                    real_port, desc = ports[index]
                    print(f"您選擇了 {index+1}. {real_port} ({desc})")
                else:
                    print(f"⚠️ 無效的數字選擇，請輸入範圍內的數字 (1-{len(ports)})。")
                    continue
            except ValueError:
                # 不應該發生，因為已經用 isdigit() 檢查過
                pass 
        else:
            # 使用者輸入 COM Port 名稱
            real_port, desc = find_real_port(user_input, ports)
        
        if real_port is None:
            print(f"⚠️ 找不到對應 '{user_input}' 的 COM Port，請重新輸入。")
            continue

        print(f"嘗試連接 Port: {real_port} ({desc})...")

        try:
            # --- 設定日誌檔名和路徑 ---
            # 建立一個包含日期和時間的日誌檔名，避免重複
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # 將 Port 名稱中的特殊字元替換掉，以用於檔名
            clean_port_name = real_port.replace('/', '_').replace('\\', '_').replace(':', '')
            log_filename = f"rs485_log_{clean_port_name}_{timestamp_str}.log"

            # 定義日誌檔的儲存目錄，預設為程式所在目錄下的 'logs' 子資料夾
            log_directory = "logs"
            if not os.path.exists(log_directory):
                os.makedirs(log_directory) # 如果 'logs' 資料夾不存在，就建立它

            # 組合完整的日誌檔案路徑
            full_log_path = os.path.join(log_directory, log_filename)

            # 實例化 RS485Tester，並傳遞日誌檔案路徑
            tester = RS485Tester(port=real_port, baudrate=9600, log_file=full_log_path)
            print(f"✅ 成功連接到 {real_port}。")
            print(f"📝 通訊日誌將儲存到：{os.path.abspath(full_log_path)}") # 顯示絕對路徑
            break # 成功連接並初始化後跳出迴圈

        except serial.SerialException as e:
            print(f"❌ 無法開啟 Port {real_port}。錯誤訊息：{e}")
            print("👉 請確認以下事項：")
            print("   - 該 Port 沒有被其他程式佔用。")
            print("   - 裝置已正確插入電腦。")
            print("   - 裝置的驅動程式已安裝。")
            continue # 如果連接失敗，讓使用者重新輸入

        except Exception as e:
            print(f"❌ 發生未預期的錯誤：{e}")
            print("請檢查您的設定或聯繫技術支援。")
            continue

    # --- 傳送和接收十六進位指令 ---
    # 只有當 tester 物件成功建立後才進入通訊循環
    if tester:
        try:
            while True:
                hex_cmd = input("\n請輸入十六進位指令（例如 01 03 00 00 00 02 C4 0B），或輸入 'q' 離開:\n> ").strip()
                
                if hex_cmd.lower() == 'q':
                    break # 輸入 'q' 結束程式
                
                if not hex_cmd: # 避免空輸入
                    print("⚠️ 輸入不能為空，請重新輸入。")
                    continue

                # 移除使用者輸入中的所有空白，並檢查是否只包含十六進位字元
                clean_hex_cmd = "".join(hex_cmd.split())
                if not all(c in "0123456789abcdefABCDEF" for c in clean_hex_cmd.lower()):
                    print("⚠️ 輸入包含非十六進位字元。請確保只輸入 0-9 和 A-F (或 a-f)。")
                    continue
                
                # 檢查十六進位字串長度是否為偶數 (每個位元組需要兩個十六進位字元)
                if len(clean_hex_cmd) % 2 != 0:
                    print("⚠️ 十六進位字串長度必須是偶數。例如 '0102' 而非 '102'。")
                    continue

                try:
                    tester.send_hex(clean_hex_cmd)
                    tester.receive_response()
                except Exception as e:
                    print(f"❌ 傳送/接收時發生錯誤：{e}")
                    tester._log_message(f"❌ 傳送/接收時發生錯誤：{e}") # 也記錄到日誌
        finally:
            # 確保在程式結束前關閉串列埠和日誌檔案
            tester.close()
            print("✅ 程式結束。")

            # 嘗試將通訊日誌轉成 Excel
            try:
                exporter = LogToExcelExporter(log_file_path=full_log_path)
                exporter.export_to_excel()
            except Exception as e:
                print(f"❌ 匯出 Excel 發生錯誤：{e}")

    else:
        print("由於未能成功連接串列埠，程式已終止。")




if __name__ == "__main__":
    main()