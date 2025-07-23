# -*- coding: utf-8 -*-
"""
最小化版本的 UIVersion，移除所有不必要的依賴
"""

# 只導入絕對必要的模組
import sys
import os

# 確保編碼正確
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """主函數"""
    try:
        # 只在需要時導入 GUI 模組
        import tkinter as tk
        from UIVersion import EnhancedRS485GuiApp
        
        # 創建並運行應用程式
        root = tk.Tk()
        app = EnhancedRS485GuiApp(root)
        root.mainloop()
        
    except ImportError as e:
        print(f"導入錯誤: {e}")
        print("請確保所有必要的模組都已安裝：")
        print("pip install pyserial openpyxl")
        sys.exit(1)
    except Exception as e:
        print(f"應用程式錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()