import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
from serial_utils import RS485Tester, list_available_ports
from log_exporter import LogToExcelExporter
import datetime
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class RS485GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RS485 測試工具 GUI 版")

        # COM Port 下拉選單
        self.port_label = ttk.Label(root, text="選擇 COM Port:")
        self.port_label.pack()
        self.port_combo = ttk.Combobox(root, width=40)
        self.port_combo.pack()
        self.refresh_ports()

        # 連線按鈕
        self.connect_button = ttk.Button(root, text="🔌 連線", command=self.connect)
        self.connect_button.pack()

        # 十六進位指令輸入
        self.hex_entry = ttk.Entry(root, width=50)
        self.hex_entry.pack()
        self.send_button = ttk.Button(root, text="📤 送出指令", command=self.send_command)
        self.send_button.pack()

        # 紀錄區塊
        self.log_box = scrolledtext.ScrolledText(root, width=70, height=15)
        self.log_box.pack()

        # 功能按鈕
        self.clear_button = ttk.Button(root, text="🧹 清除畫面", command=self.clear_log)
        self.clear_button.pack()

        self.save_txt_button = ttk.Button(root, text="💾 儲存紀錄為 .txt", command=self.save_log_to_txt)
        self.save_txt_button.pack()

        self.export_excel_button = ttk.Button(root, text="📊 匯出紀錄為 Excel", command=self.export_log_to_excel)
        self.export_excel_button.pack()

        self.disconnect_button = ttk.Button(root, text="🔌 中斷連線", command=self.disconnect)
        self.disconnect_button.pack()

        self.tester = None

    def refresh_ports(self):
        ports = list_available_ports()
        self.ports = ports
        self.port_combo['values'] = [f"{dev} ({desc})" for dev, desc in ports]

    def connect(self):
        selection = self.port_combo.get()
        if not selection:
            messagebox.showwarning("警告", "請先選擇 COM Port")
            return
        port = selection.split(' ')[0]
        try:
            # 自動產生 log 檔名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            clean_name = port.replace('/', '_').replace('\\', '_')
            log_path = os.path.join(log_dir, f"log_{clean_name}_{timestamp}.log")

            self.tester = RS485Tester(port=port, baudrate=9600, log_file=log_path)
            self.log_box.insert(tk.END, f"✅ 成功連接到 {port}\n")
        except Exception as e:
            messagebox.showerror("連線失敗", str(e))

    def send_command(self):
        hex_cmd = self.hex_entry.get().strip()
        if not hex_cmd:
            return
        try:
            self.tester.send_hex(hex_cmd.replace(" ", ""))
            response = self.tester.receive_response()
            self.log_box.insert(tk.END, f"➡️ {hex_cmd}\n⬅️ {response}\n")
        except Exception as e:
            self.log_box.insert(tk.END, f"❌ 傳送失敗：{e}\n")

    def clear_log(self):
        self.log_box.delete('1.0', tk.END)

    def save_log_to_txt(self):
        content = self.log_box.get('1.0', tk.END).strip()
        if not content:
            messagebox.showinfo("提示", "沒有內容可儲存。")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", f"紀錄已儲存到：{file_path}")

    def export_log_to_excel(self):
        if not self.tester or not hasattr(self.tester, "log_file"):
            messagebox.showwarning("警告", "目前沒有日誌檔案可匯出。")
            return
        try:
            exporter = LogToExcelExporter(log_file_path=self.tester.log_file)
            excel_path = exporter.export_to_excel()
            messagebox.showinfo("成功", f"已匯出 Excel 至：\n{excel_path}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗：{e}")

    def disconnect(self):
        if self.tester:
            try:
                self.tester.close()  # 關閉 Serial Port
                self.log_box.insert(tk.END, "❎ 已中斷 COM Port 連線\n")
                self.tester = None
            except Exception as e:
                messagebox.showerror("錯誤", f"中斷連線失敗：{e}")
        else:
            messagebox.showinfo("提示", "目前尚未連線任何 COM Port")


if __name__ == "__main__":
    root = tk.Tk()
    app = RS485GuiApp(root)
    root.mainloop()
