import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow
from vnpy.trader.constant import Exchange
from ui.market_monitor import MarketMonitor
from ui.futures_chart import FuturesChart
from config.log_manager import log_manager

class ChartTester:
    """图表测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        # 确保只有一个 QApplication 实例
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
            
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        self.main_window = MainWindow(self.main_engine, self.event_engine)
        
        # 测试合约信息
        self.test_symbol = "rb2405"
        self.test_exchange = Exchange.SHFE
        
        # 连接超时设置
        self.login_timeout = 5000  # 登录超���时间(毫秒)
        self.query_timeout = 2000  # 查询超时时间
        self.chart_timeout = 2000  # 图表显示超时时间
        
        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_timeout)
        self.start_time = None
        
    def run(self):
        """运行测试"""
        try:
            # 显示主窗口
            self.main_window.showMaximized()
            
            # 启动测试流程
            QTimer.singleShot(0, self.start_test)
            
            # 运行应用
            return self.app.exec_()
            
        except Exception as e:
            log_manager.log(f"测试运行失败：{str(e)}")
            return 1
            
    def start_test(self):
        """开始测试流程"""
        try:
            log_manager.log("开始自动化测试...")
            
            # 查找市场监控组件
            self.market_monitor = self.find_market_monitor()
            if not self.market_monitor:
                self.quit_test("未找到市场监控组件")
                return
                
            # 搜索测试合约
            self.market_monitor.search_line.setText(self.test_symbol)
            log_manager.log(f"搜索合约：{self.test_symbol}")
            
            # 等待合约显示
            QTimer.singleShot(self.query_timeout, self.check_contract)
            
        except Exception as e:
            self.quit_test(f"启动测试失败：{str(e)}")
            
    def check_contract(self):
        """检查合约是否显示"""
        try:
            contract_table = self.market_monitor.contract_table
            if contract_table.rowCount() > 0:
                # 查找目标合约
                found = False
                for row in range(contract_table.rowCount()):
                    symbol_item = contract_table.item(row, 1)  # 合约代码列
                    if symbol_item and symbol_item.text() == self.test_symbol:
                        # 选中并点击合约
                        contract_table.selectRow(row)
                        QTest.mouseClick(contract_table.viewport(), Qt.LeftButton)
                        log_manager.log(f"已点击合约：{self.test_symbol}")
                        found = True
                        break
                        
                if not found:
                    self.quit_test(f"未找到目标合约：{self.test_symbol}")
                    return
                    
                # 等待图表显示
                QTimer.singleShot(self.chart_timeout, self.test_chart)
            else:
                self.quit_test("合约列表为空")
                
        except Exception as e:
            self.quit_test(f"检查合约失败：{str(e)}")
            
    def test_chart(self):
        """测试图表功能"""
        try:
            # 查找图表窗口
            futures_chart = self.find_futures_chart()
            if not futures_chart:
                self.quit_test("未找到图表窗口")
                return
                
            log_manager.log("图表已显示，开始测试图表功能...")
            
            # 测试切换图表类型
            futures_chart.kline_button.click()
            log_manager.log("已切换到K线图")
            
            # 测试周期切换
            futures_chart.period_combo.setCurrentText("5分钟")
            log_manager.log("已切换到5分钟周期")
            
            # 测试技术指标
            futures_chart.indicator_combo.setCurrentText("MA")
            log_manager.log("已添加MA指标")
            
            # 测试指标参数设置
            futures_chart.indicator_setting.click()
            log_manager.log("已打开指标参数设置")
            
            # 测试指标功能
            futures_chart.indicator_combo.setCurrentText("MA")
            log_manager.log("已切换到MA指标")
            
            # 修改MA参数
            futures_chart.indicators['MA']['periods'] = [3, 6, 9]
            futures_chart.on_indicator_changed("MA")
            log_manager.log("已修改MA参数")
            
            # 切换到MACD
            futures_chart.indicator_combo.setCurrentText("MACD")
            log_manager.log("已切换到MACD指标")
            
            # 修改MACD参数
            futures_chart.indicators['MACD']['params'].update({
                'fast': 6,
                'slow': 13,
                'signal': 4
            })
            futures_chart.on_indicator_changed("MACD")
            log_manager.log("已修改MACD参数")
            
            # 等待一段时间后结束测试
            QTimer.singleShot(5000, lambda: self.quit_test("测试完成"))
            
        except Exception as e:
            self.quit_test(f"测试图表功能失败：{str(e)}")
            
    def find_market_monitor(self) -> MarketMonitor:
        """查找市场监控组件"""
        for widget in self.app.allWidgets():
            if isinstance(widget, MarketMonitor):
                return widget
        return None
        
    def find_futures_chart(self) -> FuturesChart:
        """查找期货图表组件"""
        for widget in self.app.allWidgets():
            if isinstance(widget, FuturesChart):
                return widget
        return None
        
    def check_timeout(self):
        """检查超时"""
        if self.start_time and (time.time() - self.start_time > 30):  # 30秒超时
            self.quit_test("测试超时")
            
    def quit_test(self, reason: str):
        """退出测试"""
        log_manager.log(f"退出测试：{reason}")
        self.timer.stop()
        self.app.quit()

def main():
    """主函数"""
    # 设置工作目录
    os.chdir(str(Path(__file__).parent.parent))
    
    # 运行测试
    tester = ChartTester()
    sys.exit(tester.run())

if __name__ == "__main__":
    main() 