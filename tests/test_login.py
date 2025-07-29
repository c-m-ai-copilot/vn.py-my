import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import LogData
from vnpy.trader.event import EVENT_LOG
from ui.market_monitor import MarketMonitor

class TestLogin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
        cls.event_engine = EventEngine()
        cls.main_engine = MainEngine(cls.event_engine)
        
    def setUp(self):
        self.market_monitor = MarketMonitor(
            self.main_engine,
            self.event_engine
        )
        
    def test_login_process(self):
        """测试登录流程"""
        # 模拟登录成功事件
        self.market_monitor.on_login_success_event(Event(""))
        
        # 模拟行情登录成功
        self.market_monitor.on_md_login()
        
        # 模拟结算单确认
        log = LogData(
            msg="结算信息确认成功",
            gateway_name="CTP"
        )
        event = Event(EVENT_LOG, log)
        self.market_monitor.process_log_event(event)
        
        # 验证查询和订阅是否被调用
        self.assertTrue(hasattr(self.market_monitor, 'contracts'))
        
    @patch('vnpy.trader.engine.MainEngine.connect')
    def test_auto_login(self, mock_connect):
        """测试自动登录"""
        # 模拟连接函数
        mock_connect.return_value = True
        
        # 触发自动登录
        self.main_engine.connect({
            "用户名": "test",
            "密码": "test",
            "经纪商代码": "9999",
            "交易服务器": "180.168.146.187:10201",
            "行情服务器": "180.168.146.187:10211",
            "产品名称": "simnow_client_test",
            "授权编码": "0000000000000000",
        }, "CTP")
        
        # 验证连接函数是否被调用
        mock_connect.assert_called_once()
        
    def test_login_failure(self):
        """测试登录失败"""
        # 模拟登录失败的日志
        log = LogData(
            msg="用户登录失败",
            gateway_name="CTP"
        )
        event = Event(EVENT_LOG, log)
        self.market_monitor.process_log_event(event)
        
        # 验证是否有重试机制
        self.assertEqual(self.market_monitor.retry_count, 0)
        
    def test_reconnect(self):
        """测试断线重连"""
        # 模拟断线事件
        log = LogData(
            msg="行情服务器连接断开",
            gateway_name="CTP"
        )
        event = Event(EVENT_LOG, log)
        self.market_monitor.process_log_event(event)
        
        # 验证是否触发重连
        # TODO: 添加重连逻辑的验证
        
    def test_query_after_login(self):
        """测试登录后查询"""
        # 模拟登录成功
        self.market_monitor.on_md_login()
        
        # 验证是否执行了初始化查询
        # TODO: 添加查询验证
        
    def tearDown(self):
        self.market_monitor.close()
        
    @classmethod
    def tearDownClass(cls):
        cls.main_engine.close()
        cls.app.quit()

if __name__ == '__main__':
    unittest.main() 