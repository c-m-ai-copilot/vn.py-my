import sys
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QDateTime
from vnpy.trader.object import ContractData, TickData
from vnpy.trader.constant import Exchange, Product
from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from ui.futures_chart import FuturesChart

class TestFuturesChart(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 创建QApplication实例
        cls.app = QApplication(sys.argv)
        
        # 创建引擎
        cls.event_engine = EventEngine()
        cls.main_engine = MainEngine(cls.event_engine)
        
        # 创建模拟合约
        cls.contract = ContractData(
            symbol="rb2405",
            exchange=Exchange.SHFE,
            name="螺纹钢2405",
            product=Product.FUTURES,
            size=10,
            pricetick=1.0,
            gateway_name="CTP"
        )
        
    def setUp(self):
        # 创建图表实例
        self.chart = FuturesChart(
            self.main_engine,
            self.event_engine,
            self.contract
        )
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.chart.contract.symbol, "rb2405")
        self.assertEqual(self.chart.current_chart_type, "分时图")
        self.assertEqual(len(self.chart.price_data), 0)
        
    def test_process_tick(self):
        """测试行情数据处理"""
        # 创建模拟行情
        tick = TickData(
            symbol="rb2405",
            exchange=Exchange.SHFE,
            datetime=QDateTime.currentDateTime().toPyDateTime(),
            name="螺纹钢2405",
            last_price=4000.0,
            volume=100,
            open_interest=0,
            gateway_name="CTP"
        )
        
        # 发送行情事件
        event = Event("tick", tick)
        self.chart.process_tick_event(event)
        
        # 验证数据是否正确添加
        self.assertEqual(len(self.chart.price_data), 1)
        self.assertEqual(self.chart.price_data[-1], 4000.0)
        self.assertEqual(self.chart.volume_data[-1], 100)
        
    def test_chart_type_switch(self):
        """测试图表类型切换"""
        # 切换到K线图
        self.chart.switch_chart_type("K线图")
        self.assertEqual(self.chart.current_chart_type, "K线图")
        self.assertTrue(self.chart.period_combo.isEnabled())
        
        # 切换回分时图
        self.chart.switch_chart_type("分时图")
        self.assertEqual(self.chart.current_chart_type, "分时图")
        self.assertFalse(self.chart.period_combo.isEnabled())
        
    def test_indicators(self):
        """测试技术指标"""
        # 添加模拟数据
        prices = [4000.0, 4010.0, 4020.0, 4030.0, 4040.0]
        for price in prices:
            tick = TickData(
                symbol="rb2405",
                exchange=Exchange.SHFE,
                datetime=QDateTime.currentDateTime().toPyDateTime(),
                name="螺纹钢2405",
                last_price=price,
                volume=100,
                open_interest=0,
                gateway_name="CTP"
            )
            event = Event("tick", tick)
            self.chart.process_tick_event(event)
            
        # 测试MA指标
        self.chart.add_ma_indicator(period=5)
        self.assertIn(5, self.chart.indicators['MA']['series'])
        
        # 测试MACD指标
        self.chart.add_macd_indicator()
        self.assertIn('macd', self.chart.indicators['MACD']['series'])
        
    def test_data_export(self):
        """测试数据导出"""
        # 添加模拟数据
        prices = [4000.0, 4010.0, 4020.0]
        for price in prices:
            tick = TickData(
                symbol="rb2405",
                exchange=Exchange.SHFE,
                datetime=QDateTime.currentDateTime().toPyDateTime(),
                name="螺纹钢2405",
                last_price=price,
                volume=100,
                open_interest=0,
                gateway_name="CTP"
            )
            event = Event("tick", tick)
            self.chart.process_tick_event(event)
            
        # TODO: 测试导出功能
        # 需要模拟文件对话框选择
        
    def tearDown(self):
        self.chart.close()
        
    @classmethod
    def tearDownClass(cls):
        cls.main_engine.close()
        cls.app.quit()

if __name__ == '__main__':
    unittest.main() 