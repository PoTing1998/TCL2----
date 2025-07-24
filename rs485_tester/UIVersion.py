# -*- coding: utf-8 -*-
"""
Enhanced RS485/TCP 測試工具 - 清理後的主程式
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import time
import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 導入模組
try:
    from .serial_utils import RS485Tester, list_available_ports
    from .log_exporter import LogToExcelExporter
except ImportError:
    try:
        from serial_utils import RS485Tester, list_available_ports
        from log_exporter import LogToExcelExporter
    except ImportError:
        # 模擬類別用於展示
        class RS485Tester:
            def __init__(self, port, baudrate, log_file):
                self.port = port
                self.baudrate = baudrate
                self.log_file = log_file
                self.is_connected = True
                
            def send_hex(self, hex_cmd):
                time.sleep(0.1)
                
            def receive_response(self):
                return "01 03 02 00 01 79 84"
                
            def close(self):
                self.is_connected = False
        
        def list_available_ports():
            return [("COM1", "USB Serial Port"), ("COM3", "Bluetooth Serial"), ("COM5", "Virtual Port")]
        
        class LogToExcelExporter:
            def __init__(self, log_file_path):
                self.log_file_path = log_file_path
                
            def export_to_excel(self):
                return "exported_log.xlsx"

# 導入自定義模組
try:
    from .constants import *
    from .data_utils import DataFormatter, ModbusPacketAnalyzer
    from .connection_manager import ConnectionManager, TCPConnection
    from .ui_components import ThemeManager, LogManager, StatusBar, AnalysisPanel
except ImportError:
    from constants import *
    from data_utils import DataFormatter, ModbusPacketAnalyzer
    from connection_manager import ConnectionManager, TCPConnection
    from ui_components import ThemeManager, LogManager, StatusBar, AnalysisPanel


class EnhancedRS485GuiApp:
    """Enhanced RS485/TCP 測試工具主應用程式"""
    
    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._initialize_components()
        self._setup_ui()
        self._apply_initial_theme()
        
    def _setup_window(self):
        """設定主視窗"""
        self.root.title("Enhanced RS485/TCP 測試工具")
        self.root.geometry(MAIN_WINDOW_SIZE)
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _initialize_components(self):
        """初始化組件"""
        self.connection_manager = ConnectionManager()
        self.theme_manager = ThemeManager(self.root)
        self.monitoring_active = False
        self.auto_send_threads = {}  # 追蹤自動發送線程
        
    def _setup_ui(self):
        """設定使用者介面"""
        # 建立主要筆記本容器
        main_notebook = ttk.Notebook(self.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 建立各分頁
        self.main_tab = ttk.Frame(main_notebook)
        self.monitor_tab = ttk.Frame(main_notebook)
        self.analysis_tab = ttk.Frame(main_notebook)
        
        main_notebook.add(self.main_tab, text="🔌 連線管理")
        main_notebook.add(self.monitor_tab, text="📊 即時監控")
        main_notebook.add(self.analysis_tab, text="🔍 封包分析")
        
        # 設定各分頁內容
        self._setup_main_tab()
        self._setup_monitor_tab()
        self._setup_analysis_tab()
        
        # 狀態列
        self.status_bar = StatusBar(self.root)
        
    def _setup_main_tab(self):
        """設定主要連線頁面"""
        # 工具列
        self._create_toolbar()
        
        # 連線管理區域
        self._create_connection_area()
        
        # 指令操作區域
        self._create_command_area()
        
        # 日誌顯示區域
        self._create_log_area()
        
    def _create_toolbar(self):
        """建立工具列"""
        toolbar = ttk.Frame(self.main_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="🌙 切換主題", command=self._toggle_theme).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="➕ 新增連線", command=self._add_connection).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(toolbar, text="❌ 移除連線", command=self._remove_connection).pack(side=tk.LEFT, padx=(5, 0))
        
    def _create_connection_area(self):
        """建立連線管理區域"""
        conn_frame = ttk.LabelFrame(self.main_tab, text="連線管理", padding=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 連線樹狀檢視
        columns = ("type", "address", "status", "stats")
        self.connection_tree = ttk.Treeview(conn_frame, columns=columns, show="tree headings", height=6)
        
        # 設定欄位標題
        headers = {"#0": "連線名稱", "type": "類型", "address": "地址/端口", "status": "狀態", "stats": "統計"}
        for col, title in headers.items():
            self.connection_tree.heading(col, text=title)
            
        # 設定欄寬
        widths = {"#0": 150, "type": 80, "address": 200, "status": 80, "stats": 200}
        for col, width in widths.items():
            self.connection_tree.column(col, width=width)
        
        # 綁定選擇事件
        self.connection_tree.bind("<<TreeviewSelect>>", self._on_connection_select)
            
        self.connection_tree.pack(fill=tk.X, pady=(0, 10))
        
    def _create_command_area(self):
        """建立指令操作區域"""
        cmd_frame = ttk.LabelFrame(self.main_tab, text="指令操作", padding=10)
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 常用指令按鈕
        self._create_command_buttons(cmd_frame)
        
        # 指令輸入區域
        self._create_command_input(cmd_frame)
        
        # 定時發送設定
        self._create_timer_settings(cmd_frame)
        
    def _create_command_buttons(self, parent):
        """建立常用指令按鈕"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        for i, (name, cmd) in enumerate(COMMON_COMMANDS.items()):
            btn = ttk.Button(btn_frame, text=name, command=lambda c=cmd: self._insert_command(c))
            btn.pack(side=tk.LEFT, padx=(0, 5))
            if i == 3:  # 換行
                btn_frame = ttk.Frame(parent)
                btn_frame.pack(fill=tk.X, pady=(5, 10))
                
    def _create_command_input(self, parent):
        """建立指令輸入區域"""
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X)
        
        # 裝置ID選擇器
        ttk.Label(input_frame, text="裝置ID:").pack(side=tk.LEFT)
        self.device_id_var = tk.StringVar(value="01")
        self.device_id_combo = ttk.Combobox(input_frame, textvariable=self.device_id_var, width=8, 
                                          values=[f"{i:02X}" for i in range(1, 248)], state="readonly")
        self.device_id_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(input_frame, text="指令:").pack(side=tk.LEFT)
        self.hex_entry = ttk.Entry(input_frame, width=35)
        self.hex_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        ttk.Button(input_frame, text="📤 發送", command=self._send_to_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(input_frame, text="📤 廣播", command=self._broadcast_command).pack(side=tk.LEFT, padx=(0, 5))
    
    def _insert_command(self, command_template):
        """插入指令並替換裝置ID"""
        device_id = self.device_id_var.get()
        # 替換指令模板中的 {ID} 變數
        command = command_template.replace("{ID}", device_id)
        
        # 清空現有指令並插入新指令
        self.hex_entry.delete(0, tk.END)
        self.hex_entry.insert(0, command)
    
    def _send_to_selected(self):
        """發送指令到選定的連線"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "請選擇目標連線")
            return
            
        item = selection[0]
        name = self.connection_tree.item(item)['text']
        command = self.hex_entry.get().strip()
        
        if not command:
            messagebox.showwarning("警告", "請輸入指令")
            return
            
        self._send_command_to_connection(name, command)
    
    def _broadcast_command(self):
        """廣播指令到所有連線"""
        command = self.hex_entry.get().strip()
        if not command:
            messagebox.showwarning("警告", "請輸入指令") 
            return
            
        connections = self.connection_manager.get_all_connections()
        if not connections:
            messagebox.showwarning("警告", "沒有可用的連線")
            return
            
        for name in connections.keys():
            self._send_command_to_connection(name, command)
    
    def _calculate_modbus_crc(self, data_hex):
        """計算Modbus CRC16"""
        try:
            # 移除空格並轉換為bytes
            data = bytes.fromhex(data_hex.replace(" ", ""))
            
            crc = 0xFFFF
            for byte in data:
                crc ^= byte
                for _ in range(8):
                    if crc & 0x0001:
                        crc >>= 1
                        crc ^= 0xA001
                    else:
                        crc >>= 1
            
            # CRC是小端序，先低字節後高字節
            crc_low = crc & 0xFF
            crc_high = (crc >> 8) & 0xFF
            
            return f"{crc_low:02X} {crc_high:02X}"
        except:
            return ""
    
    def _add_crc_if_needed(self, command):
        """如果需要，為指令添加CRC"""
        command = command.strip()
        if not command:
            return command
            
        # 檢查是否已經包含CRC（簡單判斷：至少6個字節）
        hex_bytes = command.replace(" ", "")
        if len(hex_bytes) >= 12:  # 至少6個字節
            return command
            
        # 為短指令自動添加CRC
        crc = self._calculate_modbus_crc(command)
        if crc:
            return f"{command} {crc}"
        return command
    
    def _send_command_to_connection(self, name, command):
        """發送指令到指定連線"""
        try:
            # 添加CRC如果需要
            command_with_crc = self._add_crc_if_needed(command)
            
            # 驗證十六進位字串
            validated_command = self._validate_hex_string(command_with_crc)
            
            conn_info = self.connection_manager.get_connection(name)
            connection = conn_info['connection']
            conn_type = conn_info['type']
            
            # 記錄發送的完整指令
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if conn_type == 'TCP':
                # TCP連線發送
                data = bytes.fromhex(validated_command.replace(" ", ""))
                connection.send_data(data)
                response = connection.receive_data()
            else:
                # Serial連線發送
                connection.send_hex(command_with_crc)
                response_bytes = connection.receive_response()
                response = response_bytes.hex(' ').upper() if response_bytes else "無回應"
            
            # 記錄交易統計
            success = response != "無回應" and response != "回應逾時"
            response_time = 100.0 if success else 0.0  # 簡化的回應時間
            
            stats = self.connection_manager.get_statistics(name)
            if stats:
                stats.add_transaction(success, response_time if success else None)
            
            # 更新日誌
            self._log_transaction(name, timestamp, command_with_crc, response, response_time)
            
        except Exception as e:
            error_msg = f"發送失敗: {e}"
            self.log_manager.add_log(error_msg, name)
            messagebox.showerror("錯誤", error_msg)
    
    def _log_transaction(self, name, timestamp, command, response, response_time):
        """記錄交易日誌"""
        # 建立日誌訊息
        log_msg = f"[{timestamp}]\n"
        log_msg += f"📤 發送: {command}\n"
        log_msg += f"📥 接收: {response}\n"
        log_msg += f"⏱️ 回應時間: {response_time:.1f}ms\n"
        log_msg += "-" * 50 + "\n"
        
        # 記錄到總覽和專屬日誌
        self.log_manager.add_log(f"[{name}] 📤 {command} → 📥 {response}", "overview")
        self.log_manager.add_log(log_msg, name)
        
        # 更新連線樹狀檢視
        self._update_connection_tree()
        
    def _create_timer_settings(self, parent):
        """建立定時發送設定"""
        timer_frame = ttk.Frame(parent)
        timer_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(timer_frame, text="定時發送:").pack(side=tk.LEFT)
        self.timer_interval = ttk.Entry(timer_frame, width=10)
        self.timer_interval.insert(0, str(DEFAULT_INTERVAL))
        self.timer_interval.pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(timer_frame, text="毫秒").pack(side=tk.LEFT)
        
        self.timer_button = ttk.Button(timer_frame, text="⏰ 開始定時", command=self._toggle_auto_send)
        self.timer_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # 強制停止按鈕（緊急用）
        self.stop_all_button = ttk.Button(timer_frame, text="🛑 全部停止", command=self._stop_all_timers)
        self.stop_all_button.pack(side=tk.LEFT, padx=(5, 0))
        
    def _create_log_area(self):
        """建立日誌顯示區域"""
        log_frame = ttk.LabelFrame(self.main_tab, text="通訊日誌", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 建立日誌管理器
        self.log_notebook = ttk.Notebook(log_frame)
        self.log_notebook.pack(fill=tk.BOTH, expand=True)
        
        self.log_manager = LogManager(self.log_notebook)
        self.log_manager.setup_log_tab("總覽", "overview")
        
    def _setup_monitor_tab(self):
        """設定監控頁面"""
        # 控制區域
        control_frame = ttk.Frame(self.monitor_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.monitor_button = ttk.Button(control_frame, text="▶️ 開始監控", command=self._toggle_monitoring)
        self.monitor_button.pack(side=tk.LEFT)
        
        ttk.Label(control_frame, text="監控間隔:").pack(side=tk.LEFT, padx=(20, 5))
        self.monitor_interval = ttk.Entry(control_frame, width=10)
        self.monitor_interval.insert(0, "5000")
        self.monitor_interval.pack(side=tk.LEFT)
        ttk.Label(control_frame, text="毫秒").pack(side=tk.LEFT)
        
        # 統計顯示區域
        self._create_statistics_area()
        
    def _create_statistics_area(self):
        """建立統計顯示區域"""
        stats_frame = ttk.LabelFrame(self.monitor_tab, text="連線統計", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 統計樹狀檢視
        stats_columns = ("sent", "received", "errors", "success_rate", "avg_time")
        self.stats_tree = ttk.Treeview(stats_frame, columns=stats_columns, show="tree headings")
        
        # 設定統計欄位標題
        stats_headers = {
            "#0": "連線", "sent": "已發送", "received": "已接收", 
            "errors": "錯誤", "success_rate": "成功率%", "avg_time": "平均回應時間(ms)"
        }
        for col, title in stats_headers.items():
            self.stats_tree.heading(col, text=title)
            self.stats_tree.column(col, width=120)
            
        self.stats_tree.pack(fill=tk.BOTH, expand=True)
        
        # 定期更新統計
        self._update_statistics()
        
    def _setup_analysis_tab(self):
        """設定分析頁面"""
        self.analysis_panel = AnalysisPanel(self.analysis_tab, self._analyze_packet)
        
    def _apply_initial_theme(self):
        """套用初始主題"""
        self.theme_manager.apply_theme(self.log_notebook)
        
    # 事件處理方法
    def _toggle_theme(self):
        """切換主題"""
        self.theme_manager.toggle_theme()
        self.theme_manager.apply_theme(self.log_notebook)
        
    def _add_connection(self):
        """新增連線"""
        dialog = ConnectionDialog(self.root, self.connection_manager, self.log_manager, self._update_connection_tree)
        
    def _remove_connection(self):
        """移除連線"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要移除的連線")
            return
            
        item = selection[0]
        name = self.connection_tree.item(item)['text']
        
        if messagebox.askyesno("確認", f"確定要移除連線 '{name}' 嗎？"):
            try:
                # 停止該連線的自動發送線程
                if name in self.auto_send_threads:
                    del self.auto_send_threads[name]
                
                self.connection_manager.remove_connection(name)
                self.log_manager.remove_log_tab(name)
                self._update_connection_tree()
                
                # 重置按鈕狀態
                self.timer_button.config(text="⏰ 開始定時")
                
                self.log_manager.add_log(f"❌ 連線 '{name}' 已移除", "overview")
            except Exception as e:
                messagebox.showerror("錯誤", f"移除連線失敗: {e}")
                
    def _update_connection_tree(self):
        """更新連線樹狀檢視"""
        # 清空現有項目
        for item in self.connection_tree.get_children():
            self.connection_tree.delete(item)
            
        # 重新載入連線
        for name, conn_info in self.connection_manager.get_all_connections().items():
            status = "🟢 連線中" if conn_info.get('connected', False) else "🔴 已中斷"
            
            stats_text = ""
            stats = self.connection_manager.get_statistics(name)
            if stats:
                stats_text = f"發送:{stats.total_sent} 成功率:{stats.get_success_rate():.1f}%"
            
            self.connection_tree.insert("", "end", text=name, values=(
                conn_info['type'],
                conn_info['address'], 
                status,
                stats_text
            ))
            
    def _insert_command(self, command):
        """插入常用指令"""
        self.hex_entry.delete(0, tk.END)
        self.hex_entry.insert(0, command)
        
    def _send_to_selected(self):
        """發送指令到選中的連線"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "請選擇目標連線")
            return
            
        item = selection[0]
        name = self.connection_tree.item(item)['text']
        command = self.hex_entry.get().strip()
        
        if not command:
            messagebox.showwarning("警告", "請輸入指令")
            return
            
        self._send_command_to_connection(name, command)
        
    def _broadcast_command(self):
        """廣播指令到所有連線"""
        command = self.hex_entry.get().strip()
        if not command:
            messagebox.showwarning("警告", "請輸入指令")
            return
            
        for name in self.connection_manager.get_all_connections().keys():
            self._send_command_to_connection(name, command)
            
    def _send_command_to_connection(self, name, command):
        """發送指令到指定連線"""
        def send_thread():
            try:
                conn_info = self.connection_manager.get_connection(name)
                start_time = time.time()
                
                if conn_info['type'] == 'Serial':
                    conn_info['connection'].send_hex(command.replace(" ", ""))
                    response = conn_info['connection'].receive_response()
                else:  # TCP
                    hex_bytes = bytes.fromhex(command.replace(" ", ""))
                    conn_info['connection'].send_data(hex_bytes)
                    response = conn_info['connection'].receive_data()
                
                response_time = (time.time() - start_time) * 1000  # 毫秒
                
                # 更新統計
                stats = self.connection_manager.get_statistics(name)
                if stats:
                    success = "錯誤" not in response and "逾時" not in response
                    stats.add_transaction(success, response_time if success else None)
                
                # 記錄到日誌
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.root.after(0, lambda: self._log_transaction(name, timestamp, command, response, response_time))
                
            except Exception as e:
                error_msg = f"發送錯誤: {e}"
                stats = self.connection_manager.get_statistics(name)
                if stats:
                    stats.add_transaction(False)
                
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.root.after(0, lambda: self._log_transaction(name, timestamp, command, error_msg, 0))
        
        threading.Thread(target=send_thread, daemon=True).start()
        
    def _log_transaction(self, name, timestamp, command, response, response_time):
        """記錄交易到日誌"""
        log_msg = f"[{timestamp}] ➡️ 發送: {command}\n"
        log_msg += f"[{timestamp}] ⬅️ 接收: {response}"
        if response_time > 0:
            log_msg += f" ({response_time:.1f}ms)"
        log_msg += "\n" + "-" * 50 + "\n"
        
        # 記錄到總覽和專屬日誌
        self.log_manager.add_log(f"[{name}] {log_msg}", "overview")
        self.log_manager.add_log(log_msg, name)
            
        # 更新連線樹狀檢視
        self._update_connection_tree()
        
    def _toggle_auto_send(self):
        """切換定時發送"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "請選擇目標連線")
            return
            
        item = selection[0]
        name = self.connection_tree.item(item)['text']
        
        
        if self.connection_manager.is_auto_send_active(name):
            # 停止定時發送
            self.connection_manager.set_auto_send_status(name, False)
            # 清理線程追蹤
            if name in self.auto_send_threads:
                del self.auto_send_threads[name]
            self.timer_button.config(text="⏰ 開始定時")
            self.log_manager.add_log("⏰ 停止定時發送", name)
        else:
            # 開始定時發送
            try:
                interval = int(self.timer_interval.get())
                if interval < MIN_INTERVAL:
                    messagebox.showwarning("警告", f"間隔時間不能小於{MIN_INTERVAL}毫秒")
                    return
                    
                command = self.hex_entry.get().strip()
                if not command:
                    messagebox.showwarning("警告", "請輸入指令")
                    return
                    
                self.connection_manager.set_auto_send_status(name, True)
                self.timer_button.config(text="⏹️ 停止定時")
                self.log_manager.add_log(f"⏰ 開始定時發送 (間隔:{interval}ms)", name)
                
                self._start_auto_send(name, command, interval)
                
            except ValueError:
                messagebox.showwarning("警告", "請輸入有效的間隔時間")
                
    def _start_auto_send(self, name, command, interval):
        """開始自動發送"""
        def auto_send_loop():
            while self.connection_manager.is_auto_send_active(name) and name in self.auto_send_threads:
                try:
                    if name in self.connection_manager.get_all_connections():
                        self._send_command_to_connection(name, command)
                    time.sleep(interval / 1000.0)
                except Exception as e:
                    self.log_manager.add_log(f"⚠️ 定時發送錯誤: {e}", name)
                    # 發生錯誤時停止自動發送
                    self.connection_manager.set_auto_send_status(name, False)
                    # 更新UI按鈕狀態
                    self.root.after(0, lambda: self._update_timer_button_state(name))
                    break
            
            # 線程結束時清理
            if name in self.auto_send_threads:
                del self.auto_send_threads[name]
                
        # 啟動線程並追蹤
        thread = threading.Thread(target=auto_send_loop, daemon=True)
        self.auto_send_threads[name] = thread
        thread.start()
    
    def _update_timer_button_state(self, name):
        """更新定時按鈕狀態"""
        selection = self.connection_tree.selection()
        if selection:
            selected_name = self.connection_tree.item(selection[0])['text']
            if selected_name == name:
                if self.connection_manager.is_auto_send_active(name):
                    self.timer_button.config(text="⏹️ 停止定時")
                else:
                    self.timer_button.config(text="⏰ 開始定時")
    
    def _on_connection_select(self, event):
        """處理連線選擇事件"""
        selection = self.connection_tree.selection()
        if selection:
            name = self.connection_tree.item(selection[0])['text']
            
            # 更新定時按鈕狀態
            if self.connection_manager.is_auto_send_active(name):
                self.timer_button.config(text="⏹️ 停止定時")
            else:
                self.timer_button.config(text="⏰ 開始定時")
            
            # 載入連線的預設裝置ID
            try:
                conn_info = self.connection_manager.get_connection(name)
                if 'default_device_id' in conn_info:
                    self.device_id_var.set(conn_info['default_device_id'])
            except:
                pass  # 如果沒有預設ID，保持當前選擇
        else:
            # 沒有選擇時禁用按鈕
            self.timer_button.config(text="⏰ 開始定時")
    
    def _stop_all_timers(self):
        """停止所有定時發送"""
        stopped_count = 0
        for name in list(self.connection_manager.get_all_connections().keys()):
            if self.connection_manager.is_auto_send_active(name):
                self.connection_manager.set_auto_send_status(name, False)
                if name in self.auto_send_threads:
                    del self.auto_send_threads[name]
                stopped_count += 1
                self.log_manager.add_log("🛑 定時發送已停止", name)
        
        # 重置按鈕狀態
        self.timer_button.config(text="⏰ 開始定時")
        
        if stopped_count > 0:
            self.log_manager.add_log(f"🛑 已停止 {stopped_count} 個定時發送", "overview")
            messagebox.showinfo("完成", f"已停止 {stopped_count} 個定時發送")
        else:
            messagebox.showinfo("提示", "目前沒有運行中的定時發送")
        
    def _toggle_monitoring(self):
        """切換監控模式"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.monitor_button.config(text="▶️ 開始監控")
            self.log_manager.add_log("📊 監控已停止", "overview")
        else:
            self.monitoring_active = True
            self.monitor_button.config(text="⏹️ 停止監控")
            self.log_manager.add_log("📊 監控已開始", "overview")
            self._start_monitoring()
            
    def _start_monitoring(self):
        """開始監控"""
        def monitor_loop():
            while self.monitoring_active:
                try:
                    interval = int(self.monitor_interval.get())
                    # 向所有連線發送查詢指令
                    query_cmd = "01 03 00 00 00 01 84 0A"  # 查詢狀態指令
                    
                    for name in list(self.connection_manager.get_all_connections().keys()):
                        if name in self.connection_manager.get_all_connections():
                            self._send_command_to_connection(name, query_cmd)
                    
                    time.sleep(interval / 1000.0)
                except (KeyError, ValueError, TypeError) as e:
                    self.log_manager.add_log(f"監控錯誤: {e}", "overview")
                    break
                except Exception as e:
                    self.log_manager.add_log(f"監控發生未預期錯誤: {e}", "overview")
                    break
                    
        if self.monitoring_active:
            threading.Thread(target=monitor_loop, daemon=True).start()
            
    def _update_statistics(self):
        """更新統計顯示"""
        # 清空統計樹狀檢視
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
            
        # 重新載入統計資料
        for name, stats in self.connection_manager.get_all_statistics().items():
            self.stats_tree.insert("", "end", text=name, values=(
                stats.total_sent,
                stats.total_received,
                stats.errors,
                f"{stats.get_success_rate():.1f}",
                f"{stats.get_avg_response_time():.1f}"
            ))
            
        # 定期更新
        self.root.after(STATS_UPDATE_INTERVAL, self._update_statistics)
    
    def _validate_interval(self, interval_str):
        """驗證間隔時間輸入"""
        try:
            interval = int(interval_str)
            if interval < MIN_INTERVAL:
                raise ValueError(f"間隔時間不能小於{MIN_INTERVAL}毫秒")
            if interval > 3600000:  # 最大1小時
                raise ValueError("間隔時間不能超過1小時")
            return interval
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("請輸入有效的數字")
            raise
    
    def _validate_hex_string(self, hex_str):
        """驗證十六進位字串輸入"""
        if not hex_str or not hex_str.strip():
            raise ValueError("指令不能為空")
        
        # 移除空格並檢查
        hex_clean = hex_str.replace(" ", "")
        if len(hex_clean) % 2 != 0:
            raise ValueError("十六進位字串長度必須為偶數")
        
        try:
            bytes.fromhex(hex_clean)
        except ValueError:
            raise ValueError("包含無效的十六進位字符")
        
        return hex_clean
    
    def _validate_tcp_address(self, host, port_str):
        """驗證TCP地址輸入"""
        if not host or not host.strip():
            raise ValueError("主機地址不能為空")
        
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError("端口號必須在1-65535之間")
            return host.strip(), port
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("請輸入有效的端口號")
            raise
        
    def _analyze_packet(self, packet):
        """分析封包"""
        if not packet:
            return
            
        # Modbus 分析
        analysis = ModbusPacketAnalyzer.analyze_packet(packet)
        
        if isinstance(analysis, dict):
            result_text = "📋 Modbus 封包分析\n" + "=" * 30 + "\n\n"
            for key, value in analysis.items():
                result_text += f"{key:12}: {value}\n"
        else:
            result_text = f"分析結果: {analysis}\n"
            
        # 格式轉換
        ascii_result = DataFormatter.hex_to_ascii(packet)
        decimal_result = DataFormatter.hex_to_decimal(packet)
        binary_result = DataFormatter.hex_to_binary(packet)
        
        # 更新分析面板
        self.analysis_panel.update_results(result_text, ascii_result, decimal_result, binary_result)
    
    def _on_closing(self):
        """處理程式關閉事件"""
        try:
            # 停止監控
            self.monitoring_active = False
            
            # 停止所有自動發送並清理線程
            for name in list(self.connection_manager.get_all_connections().keys()):
                if self.connection_manager.is_auto_send_active(name):
                    self.connection_manager.set_auto_send_status(name, False)
            
            # 清理線程追蹤
            self.auto_send_threads.clear()
            
            # 關閉所有連線
            for name in list(self.connection_manager.get_all_connections().keys()):
                try:
                    self.connection_manager.remove_connection(name)
                except Exception as e:
                    print(f"關閉連線 {name} 時發生錯誤: {e}")
                    
        except Exception as e:
            print(f"程式關閉時發生錯誤: {e}")
        finally:
            self.root.destroy()


class ConnectionDialog:
    """連線對話框"""
    
    def __init__(self, parent, connection_manager, log_manager, update_callback):
        self.parent = parent
        self.connection_manager = connection_manager
        self.log_manager = log_manager
        self.update_callback = update_callback
        self._create_dialog()
        
    def _create_dialog(self):
        """建立對話框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("新增連線")
        self.dialog.geometry(CONNECTION_DIALOG_SIZE)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_form()
        self._create_buttons()
        
    def _create_form(self):
        """建立表單"""
        # 連線名稱
        ttk.Label(self.dialog, text="連線名稱:").pack(pady=(10, 5))
        self.name_entry = ttk.Entry(self.dialog, width=30)
        self.name_entry.pack()
        
        # 連線類型
        ttk.Label(self.dialog, text="連線類型:").pack(pady=(10, 5))
        self.type_var = tk.StringVar(value="Serial")
        type_combo = ttk.Combobox(self.dialog, textvariable=self.type_var, values=["Serial", "TCP"], state="readonly")
        type_combo.pack()
        
        # 動態設定區域
        self.settings_frame = ttk.Frame(self.dialog)
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self._create_serial_settings()
        self._create_tcp_settings()
        
        self.type_var.trace('w', self._on_type_change)
        self._on_type_change()  # 初始顯示
        
    def _create_serial_settings(self):
        """建立 Serial 設定"""
        self.serial_frame = ttk.Frame(self.settings_frame)
        
        ttk.Label(self.serial_frame, text="COM Port:").pack(anchor=tk.W)
        self.port_combo = ttk.Combobox(self.serial_frame, state="readonly")
        try:
            ports = list_available_ports()
            self.port_combo['values'] = [f"{dev} ({desc})" for dev, desc in ports]
            if self.port_combo['values']:
                self.port_combo.set(self.port_combo['values'][0])
        except ImportError as e:
            messagebox.showwarning("警告", f"無法載入串口模組: {e}")
        except Exception as e:
            messagebox.showwarning("警告", f"無法取得可用串口: {e}")
        self.port_combo.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.serial_frame, text="波特率:").pack(anchor=tk.W)
        self.baud_combo = ttk.Combobox(self.serial_frame, values=BAUDRATES, state="readonly")
        self.baud_combo.set(str(DEFAULT_BAUDRATE))
        self.baud_combo.pack(fill=tk.X)
        
    def _create_tcp_settings(self):
        """建立 TCP 設定"""
        self.tcp_frame = ttk.Frame(self.settings_frame)
        
        ttk.Label(self.tcp_frame, text="IP 位址:").pack(anchor=tk.W)
        self.ip_entry = ttk.Entry(self.tcp_frame)
        self.ip_entry.insert(0, DEFAULT_TCP_HOST)
        self.ip_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.tcp_frame, text="Port:").pack(anchor=tk.W) 
        self.port_entry = ttk.Entry(self.tcp_frame)
        self.port_entry.insert(0, str(DEFAULT_TCP_PORT))
        self.port_entry.pack(fill=tk.X)
        
    def _create_buttons(self):
        """建立按鈕"""
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="建立", command=self._create_connection).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
    def _on_type_change(self, *args):
        """根據類型切換設定介面"""
        for frame in [self.serial_frame, self.tcp_frame]:
            frame.pack_forget()
            
        if self.type_var.get() == "Serial":
            self.serial_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.tcp_frame.pack(fill=tk.BOTH, expand=True)
            
    def _create_connection(self):
        """建立連線"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("警告", "請輸入連線名稱")
            return
            
        try:
            if self.type_var.get() == "Serial":
                conn, address = self._create_serial_connection(name)
            else:
                conn, address = self._create_tcp_connection()
            
            # 記錄連線
            self.connection_manager.add_connection(name, conn, self.type_var.get(), address)
            
            # 建立日誌分頁
            self.log_manager.setup_log_tab(name, name)
            
            # 更新 UI
            self.update_callback()
            
            self.log_manager.add_log(f"✅ 連線 '{name}' 建立成功", "overview")
            self.log_manager.add_log(f"✅ 連線 '{name}' 建立成功", name)
            
            self.dialog.destroy()
            messagebox.showinfo("成功", f"連線 '{name}' 建立成功")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"連線建立失敗: {e}")
            
    def _create_serial_connection(self, name):
        """建立 Serial 連線"""
        port = self.port_combo.get().split(' ')[0] if self.port_combo.get() else ""
        if not port:
            raise ValueError("請選擇 COM Port")
            
        baudrate = int(self.baud_combo.get())
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = os.path.join(LOG_DIR, f"log_{name}_{timestamp}.log")
        
        conn = RS485Tester(port=port, baudrate=baudrate, log_file=log_path)
        address = f"{port} ({baudrate})"
        
        return conn, address
        
    def _create_tcp_connection(self):
        """建立 TCP 連線"""
        host = self.ip_entry.get().strip()
        port = int(self.port_entry.get())
        if not host:
            raise ValueError("請輸入 IP 位址")
            
        conn = TCPConnection(host, port)
        conn.connect()
        address = f"{host}:{port}"
        
        return conn, address


class ConnectionDialog:
    """連線對話框"""
    
    def __init__(self, parent, connection_manager, log_manager, update_callback):
        self.connection_manager = connection_manager
        self.log_manager = log_manager
        self.update_callback = update_callback
        
        # 建立對話框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("新增連線")
        self.dialog.geometry(CONNECTION_DIALOG_SIZE)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_dialog_ui()
        
    def _create_dialog_ui(self):
        """建立對話框 UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 連線名稱
        ttk.Label(main_frame, text="連線名稱:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 預設裝置ID
        ttk.Label(main_frame, text="預設裝置ID:").pack(anchor=tk.W)
        self.device_id_var = tk.StringVar(value="01")
        device_id_frame = ttk.Frame(main_frame)
        device_id_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.device_id_combo = ttk.Combobox(device_id_frame, textvariable=self.device_id_var, 
                                          width=10, values=[f"{i:02X}" for i in range(1, 248)], 
                                          state="readonly")
        self.device_id_combo.pack(side=tk.LEFT)
        
        ttk.Label(device_id_frame, text="  (可在主界面修改)").pack(side=tk.LEFT)
        
        # 連線類型選擇
        ttk.Label(main_frame, text="連線類型:").pack(anchor=tk.W)
        self.conn_type = tk.StringVar(value="Serial")
        
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(type_frame, text="Serial (RS485)", variable=self.conn_type, 
                       value="Serial", command=self._on_type_change).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="TCP", variable=self.conn_type, 
                       value="TCP", command=self._on_type_change).pack(side=tk.LEFT, padx=(20, 0))
        
        # 設定區域
        self.settings_frame = ttk.LabelFrame(main_frame, text="連線設定", padding=10)
        self.settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 初始建立 Serial 設定
        self._create_serial_settings()
        
        # 按鈕區域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="連線", command=self._create_connection).pack(side=tk.RIGHT, padx=(0, 10))
        
    def _on_type_change(self):
        """連線類型改變時的處理"""
        # 清空設定區域
        for widget in self.settings_frame.winfo_children():
            widget.destroy()
            
        if self.conn_type.get() == "Serial":
            self._create_serial_settings()
        else:
            self._create_tcp_settings()
    
    def _create_serial_settings(self):
        """建立 Serial 設定"""
        self.serial_frame = ttk.Frame(self.settings_frame)
        self.serial_frame.pack(fill=tk.X)
        
        ttk.Label(self.serial_frame, text="COM Port:").pack(anchor=tk.W)
        self.port_combo = ttk.Combobox(self.serial_frame, state="readonly")
        
        try:
            from serial_utils import list_available_ports
            ports = list_available_ports()
            self.port_combo['values'] = [f"{dev} ({desc})" for dev, desc in ports]
            if self.port_combo['values']:
                self.port_combo.set(self.port_combo['values'][0])
        except ImportError as e:
            messagebox.showwarning("警告", f"無法載入串口模組: {e}")
        except Exception as e:
            messagebox.showwarning("警告", f"無法取得可用串口: {e}")
        
        self.port_combo.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.serial_frame, text="波特率:").pack(anchor=tk.W)
        self.baud_combo = ttk.Combobox(self.serial_frame, values=BAUDRATES, state="readonly")
        self.baud_combo.set(str(DEFAULT_BAUDRATE))
        self.baud_combo.pack(fill=tk.X)
        
    def _create_tcp_settings(self):
        """建立 TCP 設定"""
        self.tcp_frame = ttk.Frame(self.settings_frame)
        self.tcp_frame.pack(fill=tk.X)
        
        ttk.Label(self.tcp_frame, text="IP 位址:").pack(anchor=tk.W)
        self.ip_entry = ttk.Entry(self.tcp_frame)
        self.ip_entry.insert(0, DEFAULT_TCP_HOST)
        self.ip_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.tcp_frame, text="Port:").pack(anchor=tk.W)
        self.port_entry = ttk.Entry(self.tcp_frame)
        self.port_entry.insert(0, str(DEFAULT_TCP_PORT))
        self.port_entry.pack(fill=tk.X)
        
    def _create_connection(self):
        """建立連線"""
        try:
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showwarning("警告", "請輸入連線名稱")
                return
                
            if name in self.connection_manager.get_all_connections():
                messagebox.showwarning("警告", "連線名稱已存在")
                return
            
            # 根據連線類型建立連線
            if self.conn_type.get() == "Serial":
                connection, address = self._create_serial_connection(name)
                conn_type = "Serial"
            else:
                connection, address = self._create_tcp_connection()
                conn_type = "TCP"
            
            # 添加連線到管理器（包含預設裝置ID）
            self.connection_manager.add_connection(name, connection, conn_type, address)
            
            # 儲存預設裝置ID到連線資訊中
            conn_info = self.connection_manager.get_connection(name)
            conn_info['default_device_id'] = self.device_id_var.get()
            
            # 建立日誌分頁
            self.log_manager.setup_log_tab(name, name)
            
            # 更新 UI
            self.update_callback()
            
            self.log_manager.add_log(f"✅ 連線 '{name}' 建立成功 (預設ID: {self.device_id_var.get()})", "overview")
            self.log_manager.add_log(f"✅ 連線 '{name}' 建立成功", name)
            
            self.dialog.destroy()
            messagebox.showinfo("成功", f"連線 '{name}' 建立成功")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"連線建立失敗: {e}")
            
    def _create_serial_connection(self, name):
        """建立 Serial 連線"""
        port = self.port_combo.get().split(' ')[0] if self.port_combo.get() else ""
        if not port:
            raise ValueError("請選擇 COM Port")
            
        from serial_utils import RS485Tester
        baudrate = int(self.baud_combo.get())
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = os.path.join(LOG_DIR, f"log_{name}_{timestamp}.log")
        
        conn = RS485Tester(port=port, baudrate=baudrate, log_file=log_path)
        address = f"{port} ({baudrate})"
        
        return conn, address
        
    def _create_tcp_connection(self):
        """建立 TCP 連線"""
        from connection_manager import TCPConnection
        host = self.ip_entry.get().strip()
        port = int(self.port_entry.get())
        if not host:
            raise ValueError("請輸入 IP 位址")
            
        conn = TCPConnection(host, port)
        conn.connect()
        address = f"{host}:{port}"
        
        return conn, address


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedRS485GuiApp(root)
    root.mainloop()