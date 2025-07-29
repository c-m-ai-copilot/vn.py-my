import sys
import time
from datetime import datetime, time
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.constant import Exchange
from ui.login_dialog import LoginDialog
from ui.market_monitor import MarketMonitor
from config.log_manager import log_manager

class MarketTester(QWidget):
    def __init__(self, app: QApplication):
        super().__init__()
        
        self.app = app
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        
        # 添加CTP网关
        from vnpy_ctp import CtpGateway
        self.main_engine.add_gateway(CtpGateway)
        
        # 创建登录对话框，使用self作为父窗口
        self.login_dialog = LoginDialog(self)
        self.login_dialog.main_engine = self.main_engine  # 设置主引擎
        
        # 创建市场监控
        self.market_monitor = MarketMonitor(
            self.main_engine,
            self.event_engine
        )
        
        # 连接信号
        self.market_monitor.signal_login.connect(self.on_login_success)
        
        # 初始化标志
        self.login_clicked = False
        
    def on_login_success(self):
        """登录成功回调"""
        log_manager.log("登录成功")
        QTimer.singleShot(2000, self.show_market)
        
    def run_test(self):
        """运行测试"""
        try:
            log_manager.log("开始测试...")
            
            # 显示登录对话框
            self.login_dialog.load_settings()  # 加载默认配置
            self.login_dialog.show()
            log_manager.log("已显示登录对话框")
            
            # 等待登录对话框完全显示
            QTimer.singleShot(2000, self.test_login)
            
            # 运行应用
            return self.app.exec_()
            
        except Exception as e:
            log_manager.log(f"测试运行失败：{str(e)}")
            return 1
            
    def test_login(self):
        """测试登录"""
        try:
            if self.login_clicked:
                return
                
            log_manager.log("准备点击登录按钮...")
            
            # 确保登录对话框可见
            if not self.login_dialog.isVisible():
                log_manager.log("登录对话框未显示")
                self.app.quit()
                return
                
            # 点击连接按钮
            connect_button = self.login_dialog.connect_button
            if connect_button and connect_button.isEnabled():
                QTest.mouseClick(connect_button, Qt.LeftButton)
                self.login_clicked = True
                log_manager.log("已点击登录按钮")
            else:
                log_manager.log("登录按钮未找到或未启用")
                self.app.quit()
            
        except Exception as e:
            log_manager.log(f"登录测试失败：{str(e)}")
            self.app.quit()
            
    def show_market(self):
        """显示市场监控"""
        try:
            # 显示市场监控
            self.market_monitor.show()
            log_manager.log("已显示市场监控")
            
            # 等待5秒后搜索合约
            QTimer.singleShot(5000, self.test_search)
            
        except Exception as e:
            log_manager.log(f"显示市场监控失败：{str(e)}")
            self.app.quit()
            
    def test_search(self):
        """测试搜索功能"""
        try:
            # 输入搜索文本
            self.market_monitor.search_line.setText("rb")
            log_manager.log("已输入搜索文本：rb")
            QTest.qWait(1000)
            
            # 等待5秒后退出
            QTimer.singleShot(5000, self.app.quit)
            
        except Exception as e:
            log_manager.log(f"搜索测试失败：{str(e)}")
            self.app.quit()

def main():
    """主函数"""
    # 先创建QApplication
    app = QApplication(sys.argv)
    
    # 创建测试器
    tester = MarketTester(app)
    sys.exit(tester.run_test())

if __name__ == "__main__":
    main() 