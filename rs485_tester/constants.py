# -*- coding: utf-8 -*-
"""
常數定義
"""

# UI 相關常數
MAIN_WINDOW_SIZE = "1200x800"
CONNECTION_DIALOG_SIZE = "400x300"

# 時間設定
DEFAULT_TIMEOUT = 5.0
DEFAULT_INTERVAL = 1000
MIN_INTERVAL = 100
STATS_UPDATE_INTERVAL = 2000
AUTO_ANALYSIS_DELAY = 500

# 日誌設定
LOG_DIR = "logs"
MAX_RESPONSE_TIMES = 100

# 預設值
DEFAULT_BAUDRATE = 9600
DEFAULT_TCP_PORT = 502
DEFAULT_TCP_HOST = "192.168.1.100"

# 常用 Modbus 指令 (使用 {ID} 作為裝置ID變數)
COMMON_COMMANDS = {
    "查詢狀態": "{ID} 03 00 00 00 01",
    "讀取資料": "{ID} 04 00 00 00 02", 
    "寫入暫存器": "{ID} 06 00 00 00 01",
    "強制單線圈": "{ID} 05 00 00 FF 00",
    "預設測試": "{ID} 03 00 00 00 0A",
    "螢幕開啟": "{ID} 06 00 01 00 01",
    "螢幕關閉": "{ID} 06 00 01 00 00"
}

# Modbus 功能碼
MODBUS_FUNCTIONS = {
    0x01: "讀取線圈",
    0x02: "讀取離散輸入",
    0x03: "讀取保持暫存器",
    0x04: "讀取輸入暫存器",
    0x05: "寫入單一線圈",
    0x06: "寫入單一暫存器",
    0x0F: "寫入多重線圈",
    0x10: "寫入多重暫存器"
}

# 波特率選項
BAUDRATES = ['9600', '19200', '38400', '57600', '115200']

# UI 主題
THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "fg": "#000000", 
        "select_bg": "#0078D4",
        "entry_bg": "#FFFFFF",
        "frame_bg": "#F0F0F0"
    },
    "dark": {
        "bg": "#2D2D2D",
        "fg": "#FFFFFF",
        "select_bg": "#0078D4", 
        "entry_bg": "#404040",
        "frame_bg": "#3D3D3D"
    }
}