# -*- coding: utf-8 -*-
"""
connection_manager.py 單元測試
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import socket
import datetime
from test_config import *

try:
    from ..connection_manager import ConnectionStats, TCPConnection, ConnectionManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from connection_manager import ConnectionStats, TCPConnection, ConnectionManager


class TestConnectionStats(unittest.TestCase):
    """ConnectionStats 測試類"""
    
    def setUp(self):
        self.stats = ConnectionStats("test_connection")
    
    def test_initial_state(self):
        """測試初始狀態"""
        self.assertEqual(self.stats.name, "test_connection")
        self.assertEqual(self.stats.total_sent, 0)
        self.assertEqual(self.stats.total_received, 0)
        self.assertEqual(self.stats.errors, 0)
        self.assertEqual(len(self.stats.response_times), 0)
        self.assertIsNone(self.stats.last_activity)
    
    def test_successful_transaction(self):
        """測試成功交易記錄"""
        response_time = 100.5
        self.stats.add_transaction(True, response_time)
        
        self.assertEqual(self.stats.total_sent, 1)
        self.assertEqual(self.stats.total_received, 1)
        self.assertEqual(self.stats.errors, 0)
        self.assertEqual(len(self.stats.response_times), 1)
        self.assertEqual(self.stats.response_times[0], response_time)
        self.assertIsNotNone(self.stats.last_activity)
    
    def test_failed_transaction(self):
        """測試失敗交易記錄"""
        self.stats.add_transaction(False)
        
        self.assertEqual(self.stats.total_sent, 1)
        self.assertEqual(self.stats.total_received, 0)
        self.assertEqual(self.stats.errors, 1)
        self.assertEqual(len(self.stats.response_times), 0)
        self.assertIsNotNone(self.stats.last_activity)
    
    def test_success_rate_calculation(self):
        """測試成功率計算"""
        # 空狀態
        self.assertEqual(self.stats.get_success_rate(), 0.0)
        
        # 全部成功
        for _ in range(5):
            self.stats.add_transaction(True, 100.0)
        self.assertEqual(self.stats.get_success_rate(), 100.0)
        
        # 部分失敗
        for _ in range(3):
            self.stats.add_transaction(False)
        expected_rate = (5 / 8) * 100  # 5成功/8總數
        self.assertEqual(self.stats.get_success_rate(), expected_rate)
    
    def test_avg_response_time_calculation(self):
        """測試平均回應時間計算"""
        # 空狀態
        self.assertEqual(self.stats.get_avg_response_time(), 0.0)
        
        # 添加回應時間
        times = [100.0, 150.0, 200.0]
        for time_val in times:
            self.stats.add_transaction(True, time_val)
        
        expected_avg = sum(times) / len(times)
        self.assertEqual(self.stats.get_avg_response_time(), expected_avg)
    
    def test_last_activity_update(self):
        """測試最後活動時間更新"""
        before_time = datetime.datetime.now()
        self.stats.add_transaction(True, 100.0)
        after_time = datetime.datetime.now()
        
        self.assertIsNotNone(self.stats.last_activity)
        self.assertGreaterEqual(self.stats.last_activity, before_time)
        self.assertLessEqual(self.stats.last_activity, after_time)


class TestTCPConnection(unittest.TestCase):
    """TCPConnection 測試類"""
    
    def setUp(self):
        self.tcp_conn = TCPConnection(MOCK_HOST, MOCK_PORT)
    
    def tearDown(self):
        if self.tcp_conn.socket:
            self.tcp_conn.close()
    
    @patch('socket.socket')
    def test_successful_connection(self, mock_socket_class):
        """測試成功連線"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        result = self.tcp_conn.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.tcp_conn.connected)
        self.assertIsNotNone(self.tcp_conn.socket)
        mock_socket.settimeout.assert_called()
        mock_socket.connect.assert_called_with((MOCK_HOST, MOCK_PORT))
    
    @patch('socket.socket')
    def test_connection_timeout(self, mock_socket_class):
        """測試連線逾時"""
        mock_socket = Mock()
        mock_socket.connect.side_effect = socket.timeout()
        mock_socket_class.return_value = mock_socket
        
        with self.assertRaises(ConnectionError) as context:
            self.tcp_conn.connect()
        
        self.assertIn("TCP 連線逾時", str(context.exception))
        self.assertFalse(self.tcp_conn.connected)
    
    @patch('socket.socket')
    def test_connection_error(self, mock_socket_class):
        """測試連線錯誤"""
        mock_socket = Mock()
        mock_socket.connect.side_effect = socket.error("Connection refused")
        mock_socket_class.return_value = mock_socket
        
        with self.assertRaises(ConnectionError) as context:
            self.tcp_conn.connect()
        
        self.assertIn("TCP 連線失敗", str(context.exception))
        self.assertFalse(self.tcp_conn.connected)
    
    @patch('socket.socket')
    def test_send_data_success(self, mock_socket_class):
        """測試成功發送資料"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # 建立連線
        self.tcp_conn.connect()
        
        # 發送資料
        test_data = b'\x01\x03\x00\x00'
        self.tcp_conn.send_data(test_data)
        
        mock_socket.send.assert_called_with(test_data)
    
    def test_send_data_without_connection(self):
        """測試未連線時發送資料"""
        test_data = b'\x01\x03\x00\x00'
        
        with self.assertRaises(ConnectionError) as context:
            self.tcp_conn.send_data(test_data)
        
        self.assertIn("TCP 連線未建立", str(context.exception))
    
    @patch('socket.socket')
    def test_receive_data_success(self, mock_socket_class):
        """測試成功接收資料"""
        mock_socket = Mock()
        mock_socket.recv.return_value = b'\x01\x03\x02\x00\x01'
        mock_socket.gettimeout.return_value = 5.0
        mock_socket_class.return_value = mock_socket
        
        # 建立連線
        self.tcp_conn.connect()
        
        # 接收資料
        result = self.tcp_conn.receive_data(timeout=2.0)
        
        self.assertEqual(result, "0103020001")
        # 驗證timeout被設置（可能被呼叫多次，所以檢查最後一次呼叫）
        timeout_calls = mock_socket.settimeout.call_args_list
        self.assertTrue(any(call[0][0] == 2.0 for call in timeout_calls))
        mock_socket.recv.assert_called_with(1024)
    
    @patch('socket.socket')
    def test_receive_data_timeout(self, mock_socket_class):
        """測試接收資料逾時"""
        mock_socket = Mock()
        mock_socket.recv.side_effect = socket.timeout()
        mock_socket.gettimeout.return_value = 5.0
        mock_socket_class.return_value = mock_socket
        
        # 建立連線
        self.tcp_conn.connect()
        
        # 接收資料
        result = self.tcp_conn.receive_data(timeout=2.0)
        
        self.assertEqual(result, "回應逾時")
    
    def test_receive_data_without_connection(self):
        """測試未連線時接收資料"""
        with self.assertRaises(ConnectionError) as context:
            self.tcp_conn.receive_data()
        
        self.assertIn("TCP 連線未建立", str(context.exception))
    
    @patch('socket.socket')
    def test_close_connection(self, mock_socket_class):
        """測試關閉連線"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # 建立連線
        self.tcp_conn.connect()
        self.assertTrue(self.tcp_conn.connected)
        
        # 關閉連線
        self.tcp_conn.close()
        
        self.assertFalse(self.tcp_conn.connected)
        self.assertIsNone(self.tcp_conn.socket)
        mock_socket.close.assert_called_once()


class TestConnectionManager(unittest.TestCase):
    """ConnectionManager 測試類"""
    
    def setUp(self):
        self.manager = ConnectionManager()
        self.mock_connection = Mock()
    
    def test_add_connection_success(self):
        """測試成功添加連線"""
        name = "test_conn"
        conn_type = "TCP"
        address = "127.0.0.1:8080"
        
        self.manager.add_connection(name, self.mock_connection, conn_type, address)
        
        self.assertIn(name, self.manager.connections)
        self.assertIn(name, self.manager.connection_stats)
        
        conn_info = self.manager.get_connection(name)
        self.assertEqual(conn_info['connection'], self.mock_connection)
        self.assertEqual(conn_info['type'], conn_type)
        self.assertEqual(conn_info['address'], address)
        self.assertTrue(conn_info['connected'])
    
    def test_add_duplicate_connection(self):
        """測試添加重複連線名稱"""
        name = "test_conn"
        
        # 添加第一個連線
        self.manager.add_connection(name, self.mock_connection, "TCP", "127.0.0.1:8080")
        
        # 嘗試添加重複名稱的連線
        with self.assertRaises(ValueError) as context:
            self.manager.add_connection(name, Mock(), "Serial", "COM1")
        
        self.assertIn("已存在", str(context.exception))
    
    def test_remove_connection_success(self):
        """測試成功移除連線"""
        name = "test_conn"
        mock_conn = Mock()
        mock_conn.close = Mock()
        
        # 添加連線
        self.manager.add_connection(name, mock_conn, "TCP", "127.0.0.1:8080")
        self.manager.set_auto_send_status(name, True)
        
        # 移除連線
        self.manager.remove_connection(name)
        
        self.assertNotIn(name, self.manager.connections)
        self.assertNotIn(name, self.manager.connection_stats)
        self.assertFalse(self.manager.is_auto_send_active(name))
        mock_conn.close.assert_called_once()
    
    def test_remove_nonexistent_connection(self):
        """測試移除不存在的連線"""
        with self.assertRaises(ValueError) as context:
            self.manager.remove_connection("nonexistent")
        
        self.assertIn("不存在", str(context.exception))
    
    def test_get_connection_success(self):
        """測試成功取得連線"""
        name = "test_conn"
        self.manager.add_connection(name, self.mock_connection, "TCP", "127.0.0.1:8080")
        
        conn_info = self.manager.get_connection(name)
        self.assertEqual(conn_info['connection'], self.mock_connection)
    
    def test_get_nonexistent_connection(self):
        """測試取得不存在的連線"""
        with self.assertRaises(ValueError) as context:
            self.manager.get_connection("nonexistent")
        
        self.assertIn("不存在", str(context.exception))
    
    def test_get_all_connections(self):
        """測試取得所有連線"""
        # 添加多個連線
        connections = [
            ("conn1", Mock(), "TCP", "127.0.0.1:8080"),
            ("conn2", Mock(), "Serial", "COM1"),
        ]
        
        for name, conn, conn_type, address in connections:
            self.manager.add_connection(name, conn, conn_type, address)
        
        all_conns = self.manager.get_all_connections()
        self.assertEqual(len(all_conns), 2)
        self.assertIn("conn1", all_conns)
        self.assertIn("conn2", all_conns)
    
    def test_auto_send_status_management(self):
        """測試自動發送狀態管理"""
        name = "test_conn"
        self.manager.add_connection(name, self.mock_connection, "TCP", "127.0.0.1:8080")
        
        # 初始狀態應為False
        self.assertFalse(self.manager.is_auto_send_active(name))
        
        # 設為True
        self.manager.set_auto_send_status(name, True)
        self.assertTrue(self.manager.is_auto_send_active(name))
        
        # 設為False
        self.manager.set_auto_send_status(name, False)
        self.assertFalse(self.manager.is_auto_send_active(name))
    
    def test_statistics_management(self):
        """測試統計資料管理"""
        name = "test_conn"
        self.manager.add_connection(name, self.mock_connection, "TCP", "127.0.0.1:8080")
        
        # 取得統計
        stats = self.manager.get_statistics(name)
        self.assertIsNotNone(stats)
        self.assertEqual(stats.name, name)
        
        # 取得所有統計
        all_stats = self.manager.get_all_statistics()
        self.assertIn(name, all_stats)
        self.assertEqual(all_stats[name], stats)


if __name__ == '__main__':
    unittest.main()