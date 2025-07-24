# -*- coding: utf-8 -*-
"""
測試定時按鈕功能
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加rs485_tester目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rs485_tester'))

def test_timer_button():
    """測試定時按鈕的基本功能"""
    root = tk.Tk()
    root.title("定時按鈕測試")
    root.geometry("400x200")
    
    # 模擬按鈕狀態
    button_state = {"is_active": False}
    
    def toggle_button():
        if button_state["is_active"]:
            button_state["is_active"] = False
            timer_button.config(text="⏰ 開始定時")
            status_label.config(text="狀態: 已停止")
        else:
            button_state["is_active"] = True
            timer_button.config(text="⏹️ 停止定時")
            status_label.config(text="狀態: 運行中")
    
    # 創建UI
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="定時按鈕功能測試", font=("Arial", 14)).pack(pady=10)
    
    timer_button = ttk.Button(frame, text="⏰ 開始定時", command=toggle_button)
    timer_button.pack(pady=10)
    
    status_label = ttk.Label(frame, text="狀態: 已停止", font=("Arial", 12))
    status_label.pack(pady=10)
    
    # 測試說明
    instruction = """
測試說明：
1. 點擊「⏰ 開始定時」按鈕
2. 按鈕應該變成「⏹️ 停止定時」
3. 再次點擊應該變回「⏰ 開始定時」
4. 狀態標籤會顯示當前狀態
    """
    
    ttk.Label(frame, text=instruction, justify=tk.LEFT).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print("開始測試定時按鈕功能...")
    test_timer_button()