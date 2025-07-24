# -*- coding: utf-8 -*-
"""
連線管理模組
"""
import socket
import datetime
import time
from collections import deque
try:
    from .constants import DEFAULT_TIMEOUT, MAX_RESPONSE_TIMES
except ImportError:
    from constants import DEFAULT_TIMEOUT, MAX_RESPONSE_TIMES


class ConnectionStats:
    """連線統計資料"""
    
    def __init__(self, name):
        self.name = name
        self.total_sent = 0
        self.total_received = 0
        self.errors = 0
        self.response_times = deque(maxlen=MAX_RESPONSE_TIMES)
        self.last_activity = None
        
    def add_transaction(self, success, response_time=None):
        """記錄一次交易"""
        self.total_sent += 1
        if success:
            self.total_received += 1
            if response_time is not None:
                self.response_times.append(response_time)
        else:
            self.errors += 1
        self.last_activity = datetime.datetime.now()
    
    def get_success_rate(self):
        """取得成功率"""
        if self.total_sent == 0:
            return 0.0
        return (self.total_received / self.total_sent) * 100
    
    def get_avg_response_time(self):
        """取得平均回應時間"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)


class TCPConnection:
    """TCP 連線管理"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self):
        """建立 TCP 連線"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(DEFAULT_TIMEOUT)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except socket.timeout:
            raise ConnectionError(f"TCP 連線逾時: {self.host}:{self.port}")
        except socket.error as e:
            raise ConnectionError(f"TCP 連線失敗: {e}")
        except Exception as e:
            raise ConnectionError(f"未知錯誤: {e}")
    
    def send_data(self, data):
        """發送資料"""
        self._ensure_connected()
        try:
            self.socket.send(data)
        except socket.error as e:
            self.connected = False
            raise ConnectionError(f"發送資料失敗: {e}")
    
    def receive_data(self, timeout=2.0):
        """接收資料"""
        self._ensure_connected()
        
        original_timeout = self.socket.gettimeout()
        self.socket.settimeout(timeout)
        
        try:
            data = self.socket.recv(1024)
            return data.hex().upper()
        except socket.timeout:
            return "回應逾時"
        except socket.error as e:
            self.connected = False
            raise ConnectionError(f"接收資料失敗: {e}")
        finally:
            self.socket.settimeout(original_timeout)
    
    def close(self):
        """關閉連線"""
        if self.socket:
            try:
                self.socket.close()
            except (AttributeError, OSError) as e:
                # 記錄關閉錯誤但不中斷流程
                print(f"警告: 關閉連線時發生錯誤: {e}")
            except Exception as e:
                print(f"關閉連線時發生未預期錯誤: {e}")
            finally:
                self.connected = False
                self.socket = None
    
    def _ensure_connected(self):
        """確保連線有效"""
        if not self.connected or not self.socket:
            raise ConnectionError("TCP 連線未建立或已中斷")


class ConnectionManager:
    """連線管理器"""
    
    def __init__(self):
        self.connections = {}
        self.connection_stats = {}
        self.auto_send_active = {}
    
    def add_connection(self, name, connection, conn_type, address):
        """新增連線"""
        if not name or not name.strip():
            raise ValueError("連線名稱不能為空")
        
        if name in self.connections:
            raise ValueError(f"連線名稱 '{name}' 已存在")
        
        if connection is None:
            raise ValueError("連線物件不能為None")
        
        if not conn_type or conn_type not in ['TCP', 'Serial']:
            raise ValueError("連線類型必須為 'TCP' 或 'Serial'")
        
        if not address or not address.strip():
            raise ValueError("連線地址不能為空")
        
        self.connections[name] = {
            'connection': connection,
            'type': conn_type,
            'address': address,
            'connected': True
        }
        self.connection_stats[name] = ConnectionStats(name)
    
    def remove_connection(self, name):
        """移除連線"""
        if name not in self.connections:
            raise ValueError(f"連線 '{name}' 不存在")
        
        # 停止自動發送
        if name in self.auto_send_active:
            self.auto_send_active[name] = False
        
        # 關閉連線
        conn_info = self.connections[name]
        try:
            if hasattr(conn_info['connection'], 'close'):
                conn_info['connection'].close()
        except (AttributeError, OSError) as e:
            print(f"警告: 關閉連線 '{name}' 時發生錯誤: {e}")
        except Exception as e:
            print(f"關閉連線 '{name}' 時發生未預期錯誤: {e}")
        
        # 清理資料
        del self.connections[name]
        if name in self.connection_stats:
            del self.connection_stats[name]
    
    def get_connection(self, name):
        """取得連線"""
        if name not in self.connections:
            raise ValueError(f"連線 '{name}' 不存在")
        return self.connections[name]
    
    def get_all_connections(self):
        """取得所有連線"""
        return self.connections.copy()
    
    def get_statistics(self, name):
        """取得連線統計"""
        return self.connection_stats.get(name)
    
    def get_all_statistics(self):
        """取得所有統計資料"""
        return self.connection_stats.copy()
    
    def set_auto_send_status(self, name, active):
        """設定自動發送狀態"""
        self.auto_send_active[name] = active
    
    def is_auto_send_active(self, name):
        """檢查自動發送是否啟用"""
        return self.auto_send_active.get(name, False)