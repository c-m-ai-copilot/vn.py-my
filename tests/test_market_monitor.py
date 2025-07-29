import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import TickData, ContractData
from vnpy.trader.constant import Exchange
from vnpy_ctp import CtpGateway  # 添加CTP网关导入
from ui.market_monitor import MarketMonitor

class TestMarketMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
        cls.event_engine = EventEngine()
        cls.main_engine = MainEngine(cls.event_engine)
        
        # 添加CTP网关
        cls.main_engine.add_gateway(CtpGateway)
        
    def setUp(self):
        self.market_monitor = MarketMonitor(
            self.main_engine,
            self.event_engine
        )
        
    def test_column_widths(self):
        """测试列宽设置"""
        # 测试合约表格列宽
        self.assertEqual(self.market_monitor.contract_table.columnWidth(7), 50)  # 最小数量列
        
        # 测试行情表格列宽
        self.assertEqual(self.market_monitor.tick_table.columnWidth(5), 50)  # 买量列
        self.assertEqual(self.market_monitor.tick_table.columnWidth(7), 50)  # 卖量列
        
    def test_table_style(self):
        """测试表格样式"""
        # 测试字体大小
        style = self.market_monitor.styleSheet()
        self.assertIn("font-size: 12px", style)
        
        # 测试表格选择模式
        self.assertEqual(
            self.market_monitor.contract_table.selectionBehavior(),
            self.market_monitor.contract_table.SelectRows
        )
        
    def test_contract_filter(self):
        """测试合约过滤功能"""
        # 模拟合约数据
        contract = ContractData(
            symbol="rb2405",
            exchange=Exchange.SHFE,
            name="螺纹钢2405",
            product=None,
            size=10,
            pricetick=1.0,
            gateway_name="CTP"
        )
        
        # 添加合约到表格
        self.market_monitor.contracts[contract.vt_symbol] = contract
        self.market_monitor.contract_table.setRowCount(1)
        self.market_monitor.contract_table.setItem(0, 0, 
            QTableWidgetItem(contract.vt_symbol))
        
        # 测试过滤
        self.market_monitor.search_line.setText("rb")
        self.assertFalse(
            self.market_monitor.contract_table.isRowHidden(0)
        )
        
        self.market_monitor.search_line.setText("xxx")
        self.assertTrue(
            self.market_monitor.contract_table.isRowHidden(0)
        )
        
    def test_tick_update(self):
        """测试行情更新"""
        # 模拟Tick数据
        tick = TickData(
            symbol="rb2405",
            exchange=Exchange.SHFE,
            datetime=datetime.now(),
            name="螺纹钢2405",
            last_price=4000.0,
            volume=100,
            open_interest=0,
            gateway_name="CTP"
        )
        
        # 更新行情
        self.market_monitor.process_tick_event(Event("tick", tick))
        
        # 验证表格更新
        self.assertEqual(
            self.market_monitor.tick_table.item(0, 1).text(),
            "4000.00"
        )
        
    def test_chart_signal(self):
        """测试图表信号"""
        signal_received = False
        
        def on_contract_selected(contract):
            nonlocal signal_received
            signal_received = True
            
        self.market_monitor.contract_selected.connect(on_contract_selected)
        
        # 模拟点击合约
        contract = ContractData(
            symbol="rb2405",
            exchange=Exchange.SHFE,
            name="螺纹钢2405",
            product=None,
            size=10,
            pricetick=1.0,
            gateway_name="CTP"
        )
        self.market_monitor.show_chart(contract)
        
        self.assertTrue(signal_received)
        
    def tearDown(self):
        self.market_monitor.close()
        
    @classmethod
    def tearDownClass(cls):
        cls.main_engine.close()
        cls.app.quit()

if __name__ == "__main__":
    unittest.main() 