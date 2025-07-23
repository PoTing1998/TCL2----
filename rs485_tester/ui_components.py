# -*- coding: utf-8 -*-
"""
UI 組件模組
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
try:
    from .constants import THEMES, AUTO_ANALYSIS_DELAY
except ImportError:
    from constants import THEMES, AUTO_ANALYSIS_DELAY


class ThemeManager:
    """主題管理器"""
    
    def __init__(self, root):
        self.root = root
        self.current_theme = "light"
        
    def apply_theme(self, log_notebook=None):
        """套用主題"""
        theme = THEMES[self.current_theme]
        
        # 設定 ttk 樣式
        style = ttk.Style()
        if self.current_theme == "dark":
            style.theme_use('clam')
            style.configure("TFrame", background=theme["bg"])
            style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
            style.configure("TButton", background=theme["frame_bg"], foreground=theme["fg"])
            style.configure("TEntry", background=theme["entry_bg"], foreground=theme["fg"])
            style.configure("TCombobox", background=theme["entry_bg"], foreground=theme["fg"])
        else:
            style.theme_use('default')
            
        # 更新主視窗背景
        self.root.configure(bg=theme["bg"])
        
        # 更新文字區域顏色
        if log_notebook:
            self._update_scrolled_texts(log_notebook, theme)

    def _update_scrolled_texts(self, log_notebook, theme):
        """更新 ScrolledText 組件顏色"""
        for tab_id in log_notebook.tabs():
            tab_widget = log_notebook.nametowidget(tab_id)
            for child in tab_widget.winfo_children():
                if isinstance(child, scrolledtext.ScrolledText):
                    child.configure(bg=theme["entry_bg"], fg=theme["fg"])
        
    def toggle_theme(self):
        """切換主題"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"


class LogManager:
    """日誌管理器"""
    
    def __init__(self, log_notebook):
        self.log_notebook = log_notebook
        self.log_boxes = {}
        
    def setup_log_tab(self, name, tab_id):
        """設定日誌分頁"""
        frame = ttk.Frame(self.log_notebook)
        self.log_notebook.add(frame, text=name)
        
        log_box = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        log_box.pack(fill=tk.BOTH, expand=True)
        
        self.log_boxes[tab_id] = log_box
        return log_box
        
    def add_log(self, message, tab_id):
        """添加日誌訊息到指定分頁"""
        if tab_id in self.log_boxes:
            log_box = self.log_boxes[tab_id]
            log_box.insert(tk.END, message + "\n")
            log_box.see(tk.END)
    
    def remove_log_tab(self, name):
        """移除日誌分頁"""
        for tab_id in self.log_notebook.tabs():
            if self.log_notebook.tab(tab_id, "text") == name:
                self.log_notebook.forget(tab_id)
                break
        
        if name in self.log_boxes:
            del self.log_boxes[name]


class StatusBar:
    """狀態列組件"""
    
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.update_time()
        
    def setup_ui(self):
        """設定狀態列 UI"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="準備就緒")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side=tk.RIGHT, padx=10)
        
    def update_time(self):
        """更新時間顯示"""
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def set_status(self, message):
        """設定狀態訊息"""
        self.status_label.config(text=message)


class AnalysisPanel:
    """分析面板組件"""
    
    def __init__(self, parent, on_analyze_callback):
        self.parent = parent
        self.on_analyze_callback = on_analyze_callback
        self.setup_ui()
        
    def setup_ui(self):
        """設定分析面板 UI"""
        # 輸入區域
        input_frame = ttk.LabelFrame(self.parent, text="封包輸入", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="十六進位封包:").pack(anchor=tk.W)
        self.analysis_entry = ttk.Entry(input_frame, width=80)
        self.analysis_entry.pack(fill=tk.X, pady=(5, 10))
        self.analysis_entry.bind('<KeyRelease>', self._on_input_change)
        
        ttk.Button(input_frame, text="🔍 分析封包", command=self.analyze_packet).pack()
        
        # 分析結果顯示
        result_frame = ttk.LabelFrame(self.parent, text="分析結果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 建立筆記本用於不同格式顯示
        analysis_notebook = ttk.Notebook(result_frame)
        analysis_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Modbus 分析頁面
        modbus_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(modbus_frame, text="📋 Modbus 分析")
        
        self.modbus_result = scrolledtext.ScrolledText(modbus_frame, height=10)
        self.modbus_result.pack(fill=tk.BOTH, expand=True)
        
        # 格式轉換頁面
        format_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(format_frame, text="🔄 格式轉換")
        
        self._setup_format_displays(format_frame)
        
    def _setup_format_displays(self, parent):
        """設定格式顯示區域"""
        # ASCII 顯示
        ttk.Label(parent, text="ASCII:").pack(anchor=tk.W)
        self.ascii_result = scrolledtext.ScrolledText(parent, height=4)
        self.ascii_result.pack(fill=tk.X, pady=(0, 10))
        
        # 十進位顯示  
        ttk.Label(parent, text="十進位:").pack(anchor=tk.W)
        self.decimal_result = scrolledtext.ScrolledText(parent, height=4)
        self.decimal_result.pack(fill=tk.X, pady=(0, 10))
        
        # 二進位顯示
        ttk.Label(parent, text="二進位:").pack(anchor=tk.W)
        self.binary_result = scrolledtext.ScrolledText(parent, height=4)
        self.binary_result.pack(fill=tk.X)
        
    def analyze_packet(self):
        """分析封包"""
        packet = self.analysis_entry.get().strip()
        if packet and self.on_analyze_callback:
            self.on_analyze_callback(packet)
            
    def _on_input_change(self, event):
        """當輸入改變時自動分析"""
        from .constants import AUTO_ANALYSIS_DELAY
        self.parent.after(AUTO_ANALYSIS_DELAY, self.analyze_packet)
        
    def update_results(self, modbus_result, ascii_result, decimal_result, binary_result):
        """更新分析結果"""
        self.modbus_result.delete('1.0', tk.END)
        self.ascii_result.delete('1.0', tk.END)
        self.decimal_result.delete('1.0', tk.END) 
        self.binary_result.delete('1.0', tk.END)
        
        self.modbus_result.insert(tk.END, modbus_result)
        self.ascii_result.insert(tk.END, ascii_result)
        self.decimal_result.insert(tk.END, decimal_result)
        self.binary_result.insert(tk.END, binary_result)