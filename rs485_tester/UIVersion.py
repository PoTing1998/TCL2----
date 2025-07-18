import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
from serial_utils import RS485Tester, list_available_ports
from log_exporter import LogToExcelExporter
import datetime
import sys
import io
import threading
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class RS485GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RS485 測試工具 GUI 版")
        self.root.geometry("800x700")
        
        # 常用指令預設值
        self.common_commands = {
            "查詢狀態": "01 03 00 00 00 01 84 0A",
            "讀取資料": "01 04 00 00 00 02 71 CB",
            "寫入暫存器": "01 06 00 00 00 01 48 0A",
            "強制單線圈": "01 05 00 00 FF 00 8C 3A",
            "預設測試": "01 03 00 00 00 0A C5 CD",
            "螢幕開啟": "01 06 00 01 00 01 49 0A",
            "螢幕關閉": "01 06 00 01 00 00 48 0A"
        }
        
        self.tester = None
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 連線設定區域
        connection_frame = ttk.LabelFrame(main_frame, text="連線設定", padding=10)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # COM Port 選擇
        port_frame = ttk.Frame(connection_frame)
        port_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(port_frame, text="COM Port:").pack(side=tk.LEFT)
        self.port_combo = ttk.Combobox(port_frame, width=30, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(port_frame, text="🔄 重新整理", command=self.refresh_ports).pack(side=tk.LEFT, padx=(10, 0))
        
        # 波特率選擇
        baudrate_frame = ttk.Frame(connection_frame)
        baudrate_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(baudrate_frame, text="波特率:").pack(side=tk.LEFT)
        self.baudrate_combo = ttk.Combobox(baudrate_frame, width=15, state="readonly")
        self.baudrate_combo['values'] = ['9600', '19200', '38400', '57600', '115200']
        self.baudrate_combo.set('9600')
        self.baudrate_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 連線按鈕
        self.connect_button = ttk.Button(baudrate_frame, text="🔌 連線", command=self.connect)
        self.connect_button.pack(side=tk.LEFT, padx=(20, 0))
        
        self.disconnect_button = ttk.Button(baudrate_frame, text="🔌 中斷連線", command=self.disconnect)
        self.disconnect_button.pack(side=tk.LEFT, padx=(10, 0))
        self.disconnect_button.config(state=tk.DISABLED)
        
        # 常用指令區域
        command_frame = ttk.LabelFrame(main_frame, text="常用指令", padding=10)
        command_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 常用指令按鈕
        buttons_frame = ttk.Frame(command_frame)
        buttons_frame.pack(fill=tk.X)
        
        for i, (name, cmd) in enumerate(self.common_commands.items()):
            btn = ttk.Button(buttons_frame, text=name, 
                        command=lambda c=cmd: self.insert_command(c))
            btn.pack(side=tk.LEFT, padx=(0, 5))
            if i == 2:  # 換行
                buttons_frame = ttk.Frame(command_frame)
                buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 自訂指令輸入區域
        input_frame = ttk.LabelFrame(main_frame, text="指令輸入", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 指令輸入框
        hex_frame = ttk.Frame(input_frame)
        hex_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(hex_frame, text="十六進位指令:").pack(side=tk.LEFT)
        self.hex_entry = ttk.Entry(hex_frame, width=50)
        self.hex_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        self.hex_entry.bind('<Return>', lambda e: self.send_command())
        
        # 發送按鈕
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)
        
        self.send_button = ttk.Button(button_frame, text="📤 送出指令", command=self.send_command)
        self.send_button.pack(side=tk.LEFT)
        self.send_button.config(state=tk.DISABLED)
        
        ttk.Button(button_frame, text="🧹 清除輸入", command=self.clear_input).pack(side=tk.LEFT, padx=(10, 0))
        
        # 紀錄顯示區域
        log_frame = ttk.LabelFrame(main_frame, text="通訊紀錄", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 紀錄文字區域
        self.log_box = scrolledtext.ScrolledText(log_frame, width=70, height=15, wrap=tk.WORD)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        
        # 功能按鈕區域
        function_frame = ttk.Frame(main_frame)
        function_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(function_frame, text="🧹 清除紀錄", command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(function_frame, text="💾 儲存為 TXT", command=self.save_log_to_txt).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(function_frame, text="📊 匯出 Excel", command=self.export_log_to_excel).pack(side=tk.LEFT, padx=(10, 0))
        
        # 自動滾動選項
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(function_frame, text="自動滾動", variable=self.auto_scroll_var).pack(side=tk.RIGHT)
        
        # 狀態列
        self.setup_status_bar()
        
        # 初始化
        self.refresh_ports()
        self.update_status("未連線", "red")
        
    def setup_status_bar(self):
        """設定狀態列"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 狀態標籤
        self.status_label = ttk.Label(self.status_frame, text="狀態: 未連線", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 分隔線
        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 連線資訊
        self.connection_info_label = ttk.Label(self.status_frame, text="")
        self.connection_info_label.pack(side=tk.LEFT)
        
        # 時間標籤
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 更新時間
        self.update_time()
        
    def update_time(self):
        """更新時間顯示"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def update_status(self, status, color="black", connection_info=""):
        """更新狀態列"""
        self.status_label.config(text=f"狀態: {status}", foreground=color)
        self.connection_info_label.config(text=connection_info)
        
    def refresh_ports(self):
        """重新整理 COM Port 列表"""
        try:
            ports = list_available_ports()
            self.ports = ports
            port_list = [f"{dev} ({desc})" for dev, desc in ports]
            self.port_combo['values'] = port_list
            if port_list:
                self.port_combo.set(port_list[0])
            self.update_status("已更新端口列表", "blue")
        except Exception as e:
            messagebox.showerror("錯誤", f"更新端口列表失敗: {e}")
            self.update_status("更新端口列表失敗", "red")
            
    def insert_command(self, command):
        """插入常用指令到輸入框"""
        self.hex_entry.delete(0, tk.END)
        self.hex_entry.insert(0, command)
        self.hex_entry.focus()
        
    def clear_input(self):
        """清除輸入框"""
        self.hex_entry.delete(0, tk.END)
        
    def connect(self):
        """連線到 COM Port"""
        selection = self.port_combo.get()
        if not selection:
            messagebox.showwarning("警告", "請先選擇 COM Port")
            return
            
        port = selection.split(' ')[0]
        baudrate = int(self.baudrate_combo.get())
        
        try:
            self.update_status("連線中...", "orange")
            
            # 自動產生 log 檔名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            clean_name = port.replace('/', '_').replace('\\', '_')
            log_path = os.path.join(log_dir, f"log_{clean_name}_{timestamp}.log")

            self.tester = RS485Tester(port=port, baudrate=baudrate, log_file=log_path)
            
            # 更新 UI 狀態
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            
            connection_info = f"端口: {port} | 波特率: {baudrate}"
            self.update_status("已連線", "green", connection_info)
            
            self.add_log(f"✅ 成功連接到 {port} (波特率: {baudrate})")
            
        except Exception as e:
            self.update_status("連線失敗", "red")
            messagebox.showerror("連線失敗", str(e))

    def disconnect(self):
        """中斷連線"""
        if self.tester:
            try:
                self.tester.close()
                self.tester = None
                
                # 更新 UI 狀態
                self.connect_button.config(state=tk.NORMAL)
                self.disconnect_button.config(state=tk.DISABLED)
                self.send_button.config(state=tk.DISABLED)
                
                self.update_status("未連線", "red")
                self.add_log("❎ 已中斷 COM Port 連線")
                
            except Exception as e:
                messagebox.showerror("錯誤", f"中斷連線失敗：{e}")
        else:
            messagebox.showinfo("提示", "目前尚未連線任何 COM Port")

    def send_command(self):
        """發送指令"""
        if not self.tester:
            messagebox.showwarning("警告", "請先連線到 COM Port")
            return
            
        hex_cmd = self.hex_entry.get().strip()
        if not hex_cmd:
            messagebox.showwarning("警告", "請輸入指令")
            return
            
        try:
            self.update_status("發送中...", "orange", self.connection_info_label.cget("text"))
            
            # 在新執行緒中執行以避免 GUI 凍結
            threading.Thread(target=self._send_command_thread, args=(hex_cmd,), daemon=True).start()
            
        except Exception as e:
            self.add_log(f"❌ 傳送失敗：{e}")
            self.update_status("傳送失敗", "red", self.connection_info_label.cget("text"))
            
    def _send_command_thread(self, hex_cmd):
        """在背景執行緒中發送指令"""
        try:
            self.tester.send_hex(hex_cmd.replace(" ", ""))
            response = self.tester.receive_response()
            
            # 在主執行緒中更新 GUI
            self.root.after(0, self._update_gui_after_send, hex_cmd, response)
            
        except Exception as e:
            self.root.after(0, self._update_gui_after_send, hex_cmd, f"錯誤: {e}")
            
    def _update_gui_after_send(self, hex_cmd, response):
        """發送完成後更新 GUI"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.add_log(f"[{timestamp}] ➡️ 發送: {hex_cmd}")
        self.add_log(f"[{timestamp}] ⬅️ 接收: {response}")
        self.add_log("-" * 50)
        
        connection_info = self.connection_info_label.cget("text")
        if "錯誤" in response:
            self.update_status("傳送失敗", "red", connection_info)
        else:
            self.update_status("已連線", "green", connection_info)

    def add_log(self, message):
        """添加日誌訊息"""
        self.log_box.insert(tk.END, message + "\n")
        
        # 自動滾動到底部
        if self.auto_scroll_var.get():
            self.log_box.see(tk.END)

    def clear_log(self):
        """清除日誌"""
        self.log_box.delete('1.0', tk.END)

    def save_log_to_txt(self):
        """儲存日誌為 TXT 檔案"""
        content = self.log_box.get('1.0', tk.END).strip()
        if not content:
            messagebox.showinfo("提示", "沒有內容可儲存。")
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"RS485_log_{timestamp}.txt"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialvalue=default_filename
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("成功", f"紀錄已儲存到：{file_path}")
                self.update_status("日誌已儲存", "blue", self.connection_info_label.cget("text"))
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存失敗：{e}")

    def export_log_to_excel(self):
        """匯出日誌為 Excel 檔案"""
        if not self.tester or not hasattr(self.tester, "log_file"):
            messagebox.showwarning("警告", "目前沒有日誌檔案可匯出。")
            return
            
        try:
            self.update_status("匯出中...", "orange", self.connection_info_label.cget("text"))
            exporter = LogToExcelExporter(log_file_path=self.tester.log_file)
            excel_path = exporter.export_to_excel()
            messagebox.showinfo("成功", f"已匯出 Excel 至：\n{excel_path}")
            self.update_status("Excel 已匯出", "blue", self.connection_info_label.cget("text"))
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗：{e}")
            self.update_status("匯出失敗", "red", self.connection_info_label.cget("text"))


if __name__ == "__main__":
    root = tk.Tk()
    app = RS485GuiApp(root)
    root.mainloop()