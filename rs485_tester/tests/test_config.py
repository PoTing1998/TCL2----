# -*- coding: utf-8 -*-
"""
測試配置文件
"""
import sys
import os

# 添加專案根目錄到路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 測試常數
TEST_TIMEOUT = 5.0
TEST_RETRY_COUNT = 3
MOCK_SERIAL_PORTS = [("COM1", "Test Port 1"), ("COM3", "Test Port 2")]
MOCK_HOST = "127.0.0.1"
MOCK_PORT = 8080