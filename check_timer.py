# -*- coding: utf-8 -*-
"""
檢查定時功能的程式碼
"""
import os
import sys

# 添加路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rs485_tester'))

def check_timer_functionality():
    """檢查定時功能的程式碼結構"""
    try:
        with open('rs485_tester/UIVersion.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("=== 定時按鈕相關程式碼檢查 ===\n")
        
        # 檢查按鈕創建
        if 'timer_button' in content:
            print("✅ 找到定時按鈕變量")
        else:
            print("❌ 沒有找到定時按鈕變量")
        
        # 檢查按鈕創建代碼
        if 'ttk.Button(timer_frame, text="⏰ 開始定時"' in content:
            print("✅ 找到按鈕創建代碼")
        else:
            print("❌ 沒有找到按鈕創建代碼")
            
        # 檢查切換函數
        if '_toggle_auto_send' in content:
            print("✅ 找到切換功能函數")
        else:
            print("❌ 沒有找到切換功能函數")
        
        # 檢查按鈕狀態更新
        if 'timer_button.config(text="⏹️ 停止定時")' in content:
            print("✅ 找到停止狀態更新代碼")
        else:
            print("❌ 沒有找到停止狀態更新代碼")
            
        if 'timer_button.config(text="⏰ 開始定時")' in content:
            print("✅ 找到開始狀態更新代碼")
        else:
            print("❌ 沒有找到開始狀態更新代碼")
        
        print("\n=== 程式碼片段 ===")
        
        # 提取相關程式碼片段
        lines = content.split('\n')
        in_toggle_function = False
        for i, line in enumerate(lines):
            if '_toggle_auto_send' in line and 'def' in line:
                print(f"\n找到切換函數 (行 {i+1}):")
                # 打印函數的前20行
                for j in range(i, min(i+25, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('    ') and j > i:
                        break
                    print(f"{j+1:3d}: {lines[j]}")
                break
                
    except Exception as e:
        print(f"檢查時發生錯誤: {e}")

if __name__ == "__main__":
    check_timer_functionality()