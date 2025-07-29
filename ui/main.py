# main.py
# This file contains the UI code using PyQt5

from PyQt5 import QtWidgets, QtCore, QtGui
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_LOG
from vnpy.event import Event
from ui.trading_component import SimpleTradingComponent
from ui.gateway_manager import GatewayManager
import os
from tests.mock_data.mock_launcher import is_mock_enabled

if is_mock_enabled():
    from tests.mock_data.mock_engine import MockEngine as CtpGateway
    print("使用Mock数据模式")
else:
    from vnpy_ctp import CtpGateway  # 导入CTP网关
    print("使用真实CTP网关")
from ui.market_monitor import MarketMonitor  # 导入行情监控组件
from ui.position_monitor import PositionMonitor  # 导入持仓监控组件
from ui.account_monitor import AccountMonitor  # 添加导入
from ui.widgets.futures_chart import FuturesChartWindow  # 使用 widgets 目录下的版本
from config.log_manager import log_manager  # 添加导入
import logging  # 添加日志控制
from ui.order_monitor import OrderMonitor  # 添加导入
from ui.trade_monitor import TradeMonitor  # 添加导入
from ui.risk_manager import RiskManager
# from config.risk_engine import RiskEngine
from ui.notification_manager import NotificationManager
# from config.notification_engine import NotificationEngine
from ui.strategy_manager import StrategyManager
from ui.performance_analytics import PerformanceAnalytics
from config.data_persistence_engine import DataPersistenceEngine
# from config.strategy_engine import StrategyEngine

class MainWindow(QtWidgets.QMainWindow):
    # 添加信号
    signal_log = QtCore.pyqtSignal(str)
    
    def __init__(self) -> None:
        super().__init__()
        print("[DEBUG] MainWindow.__init__ 开始")
        
        # 设置CTP日志级别为ERROR，只显示错误信息
        logging.getLogger("vnpy.api.ctp").setLevel(logging.ERROR)
        
        print("[DEBUG] 创建事件引擎...")
        # 创建事件引擎
        self.event_engine = EventEngine()
        print("[DEBUG] 事件引擎创建完成")
        
        print("[DEBUG] 创建主引擎...")
        # 创建主引擎，并传入事件引擎
        self.main_engine = MainEngine(self.event_engine)
        print("[DEBUG] 主引擎创建完成")
        
        print("[DEBUG] 添加CTP网关...")
        # 添加CTP网关
        self.main_engine.add_gateway(CtpGateway)
        print("[DEBUG] CTP网关添加完成")
        
        print("[DEBUG] 初始化通知引擎...")
        # 添加通知引擎
        from config.notification_engine import NotificationEngine
        self.notification_engine = NotificationEngine(self.main_engine, self.event_engine)
        self.notification_engine.init_engine()
        print("[DEBUG] 通知引擎初始化完成")
        
        print("[DEBUG] 初始化策略引擎...")
        # 添加策略引擎
        from config.strategy_engine import StrategyEngine
        self.strategy_engine = StrategyEngine(self.main_engine, self.event_engine)
        self.strategy_engine.init_engine()
        print("[DEBUG] 策略引擎初始化完成")
        
        print("[DEBUG] 初始化数据持久化引擎...")
        # 添加数据持久化引擎
        self.persistence_engine = DataPersistenceEngine(self.main_engine, self.event_engine)
        print("[DEBUG] 数据持久化引擎初始化完成")
        
        print("[DEBUG] 开始初始化UI...")
        # 初始化UI
        self.init_ui()
        print("[DEBUG] UI初始化完成")
        
        # 连接信号到日志更新函数
        self.signal_log.connect(self.update_log)
        
        print("[DEBUG] 注册日志事件...")
        # 注册所有日志事件
        self.event_engine.register(EVENT_LOG, self.process_log_event)
        print("[DEBUG] 日志事件注册完成")
        
        print("[DEBUG] 设置窗口大小...")
        # 设置固定窗口大小
        self.resize(1800, 1000)
        print("[DEBUG] 窗口大小设置完成")
        
        print("[DEBUG] 显示登录对话框...")
        # 显示登录对话框
        self.show_login_dialog()
        
        print("[DEBUG] 确保窗口大小...")
        # 确保窗口大小设置不被覆盖
        self.resize(1800, 1000)
        print("[DEBUG] 窗口大小最终确认")
        print("[DEBUG] 登录对话框显示完成")
        
        print("[DEBUG] 注册日志处理器...")
        # 注册日志处理器
        log_manager.register_handler(self.signal_log.emit)
        print("[DEBUG] 日志处理器注册完成")
        
        print("[DEBUG] 初始化图表窗口字典...")
# 添加图表字典，用于存储已创建的图表
        self.chart_windows = {}
        self.risk_manager_window = None
        self.notification_manager_window = None
        self.strategy_manager_window = None
        self.performance_analytics_window = None
        
    def init_ui(self) -> None:
        self.setWindowTitle("交易系统")
        
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局为垂直布局
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(1)
        
        # 上部区域 - 水平布局
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(1)
        
        # 左侧交易组件
        self.trading_widget = SimpleTradingComponent(self.main_engine, self.event_engine)
        self.trading_widget.setMinimumWidth(300)
        top_layout.addWidget(self.trading_widget)
        
        # 右侧区域 - 垂直布局
        right_top_layout = QtWidgets.QVBoxLayout()
        right_top_layout.setSpacing(1)
        
        # 添加一个按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        performance_btn = QtWidgets.QPushButton("业绩分析")
        performance_btn.clicked.connect(self.show_performance_analytics)
        button_layout.addWidget(performance_btn)
        
        risk_button = QtWidgets.QPushButton("风险管理")
        risk_button.clicked.connect(self.show_risk_manager)
        button_layout.addWidget(risk_button)

        notification_button = QtWidgets.QPushButton("通知管理")
        notification_button.clicked.connect(self.show_notification_manager)
        button_layout.addWidget(notification_button)

        strategy_button = QtWidgets.QPushButton("策略管理")
        strategy_button.clicked.connect(self.show_strategy_manager)
        button_layout.addWidget(strategy_button)

        button_layout.addStretch()
        right_top_layout.addLayout(button_layout)
        
        # 行情监控 - 根据是否mock模式选择正确的网关名称
        gateway_name = "MockCTP" if is_mock_enabled() else "CTP"
        self.market_monitor = MarketMonitor(
            main_engine=self.main_engine,
            event_engine=self.event_engine,
            gateway_name=gateway_name,
            trading_widget=self.trading_widget
        )
        right_top_layout.addWidget(self.market_monitor)
        
        # 委托区域
        orders_group = QtWidgets.QGroupBox("委托")
        orders_layout = QtWidgets.QVBoxLayout()
        orders_layout.setSpacing(0)
        orders_layout.setContentsMargins(2, 4, 2, 2)
        
        # 创建一个包装器widget来控制表格大小
        orders_wrapper = QtWidgets.QWidget()
        orders_wrapper_layout = QtWidgets.QHBoxLayout()
        orders_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        orders_wrapper_layout.setSpacing(0)
        
        self.orders_monitor = OrderMonitor(self.main_engine, self.event_engine)
        orders_wrapper_layout.addWidget(self.orders_monitor)
        
        orders_wrapper.setLayout(orders_wrapper_layout)
        orders_layout.addWidget(orders_wrapper)
        orders_group.setLayout(orders_layout)
        right_top_layout.addWidget(orders_group)
        
        # 设置委托区域的样式
        orders_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 2px;
                margin-top: 8px;  /* 将margin-top从12改为8 */
                font-size: 12px;
                padding-top: 4px;  /* 将padding-top从8改为4 */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                background: white;
            }
        """)
        
        # 成交区域
        trades_group = QtWidgets.QGroupBox("成交")
        trades_layout = QtWidgets.QVBoxLayout()
        trades_layout.setSpacing(0)
        trades_layout.setContentsMargins(2, 4, 2, 2)
        self.trades_monitor = TradeMonitor(self.main_engine, self.event_engine)  # 使用新的组件
        trades_layout.addWidget(self.trades_monitor)
        trades_group.setLayout(trades_layout)
        right_top_layout.addWidget(trades_group)
        
        # 将右侧��局添加到上部布局
        right_top_widget = QtWidgets.QWidget()
        right_top_widget.setLayout(right_top_layout)
        top_layout.addWidget(right_top_widget, stretch=4)
        
        # 将上部布局添加到主布局
        main_layout.addLayout(top_layout)
        
        # 底部区域 - 水平布局
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setSpacing(1)
        
        # 日志区域
        log_group = QtWidgets.QGroupBox("日志")
        log_layout = QtWidgets.QVBoxLayout()
        log_layout.setSpacing(0)
        log_layout.setContentsMargins(2, 4, 2, 2)
        
        # 创建日志显示区域
        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setReadOnly(True)
        self.log_monitor.setStyleSheet("""
            QTextEdit {
                border: none;
                font-family: Microsoft YaHei;
                font-size: 12px;
            }
        """)
        log_layout.addWidget(self.log_monitor)
        log_group.setLayout(log_layout)
        
        # 资金区域
        account_group = QtWidgets.QGroupBox("资金")
        account_layout = QtWidgets.QVBoxLayout()
        account_layout.setSpacing(0)
        account_layout.setContentsMargins(2, 4, 2, 2)
        account_monitor = AccountMonitor(self.main_engine, self.event_engine)
        account_layout.addWidget(account_monitor)
        account_group.setLayout(account_layout)
        
        # 持仓区域
        position_group = QtWidgets.QGroupBox("持仓")
        position_layout = QtWidgets.QVBoxLayout()
        position_layout.setSpacing(0)
        position_layout.setContentsMargins(2, 4, 2, 2)
        position_monitor = PositionMonitor(self.main_engine, self.event_engine)
        position_layout.addWidget(position_monitor)
        position_group.setLayout(position_layout)
        
        # 设置底部组件样式
        style = """
            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 2px;
                margin-top: 8px;  /* 调整标题上方边距 */
                font-size: 12px;
                padding-top: 4px;  /* 调整标题与边框的距离 */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                background: white;  /* 添加白色背景 */
            }
        """
        log_group.setStyleSheet(style)
        account_group.setStyleSheet(style)
        position_group.setStyleSheet(style)
        
        # 添加到底部布局，使用相同的stretch因子确保宽度一致
        bottom_layout.addWidget(log_group, stretch=1)
        bottom_layout.addWidget(account_group, stretch=1)
        bottom_layout.addWidget(position_group, stretch=1)
        
        # 设置底部区域的固定高度
        bottom_widget = QtWidgets.QWidget()
        bottom_widget.setLayout(bottom_layout)
        bottom_widget.setFixedHeight(200)  # 设置固定高度
        
        # 将底部区域添加到主布局
        main_layout.addWidget(bottom_widget)
        
        # 设置主布局
        central_widget.setLayout(main_layout)
        
        # 设置最小边距
        main_layout.setContentsMargins(1, 1, 1, 1)
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                margin-top: 5px;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QTableWidget {
                border: none;
                font-size: 12px;
            }
            QTextEdit {
                border: none;
                font-size: 12px;
            }
        """)
        
    def process_log_event(self, event: Event) -> None:
        """处理日志事件"""
        log = event.data
        msg = f"{log.time}\t{log.msg}"
        # 发送信号而不是直接更新
        self.signal_log.emit(msg)
        
    def update_log(self, msg: str) -> None:
        """更新日志显示"""
        self.log_monitor.append(msg)
        # 滚到底部
        self.log_monitor.moveCursor(QtGui.QTextCursor.End)
        
    def closeEvent(self, event) -> None:
        """关闭窗口时关闭主引擎"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "退出",
            "确认退出程序？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.main_engine.close()
            event.accept()
        else:
            event.ignore()
        
    def show_login_dialog(self) -> None:
        """显示登录对话框"""
        from ui.login_dialog import LoginDialog
        dialog = LoginDialog(self)
        
        # 计算居中位置
        screen = QtWidgets.QApplication.desktop().screenGeometry()
        size = dialog.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        
        # 移动到居中位置
        dialog.move(x, y)
        
        # 显示对话框
        if dialog.exec_() == dialog.Accepted:
            settings = dialog.get_settings()
            # 连接CTP
            gateway_name = "CTP"
            self.main_engine.connect(settings, gateway_name)
            # 添加登录日志
            self.signal_log.emit("正在连接交易服器...")
        
    def copy_log(self) -> None:
        """复制日志到剪贴板"""
        log_text = self.log_monitor.toPlainText()
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(log_text)
        
        # 显示提示
        QtWidgets.QToolTip.showText(
            QtGui.QCursor.pos(),
            "日志已复制到剪贴板",
            self,
            QtCore.QRect(),
            1500  # 显示1.5秒
        )

    def on_contract_selected(self, contract):
        """处理合约选中件，显示期货图表"""
        try:
            vt_symbol = contract.vt_symbol
            print(f"准备显示表：{vt_symbol}")
            
            # 如果图表窗口已存在，则显示并激活
            if vt_symbol in self.chart_windows:
                chart_window = self.chart_windows[vt_symbol]
                if chart_window.isVisible():
                    chart_window.activateWindow()
                    return
                else:
                    # 如果窗口存在但不可见，说明可能已被关闭，需要重新创建
                    del self.chart_windows[vt_symbol]
            
            # 创建新的图表窗口
            print(f"创建新的图表窗口：{vt_symbol}")
            chart_window = FuturesChartWindow(  # 使用新的窗口类
                main_engine=self.main_engine,
                event_engine=self.event_engine,
                contract=contract
            )
            
            # 调整窗口大小
            chart_window.resize(1200, 800)
            
            # 算主窗口���心点
            center = self.geometry().center()
            
            # 计算图表窗口的位置使其居中显示
            chart_geometry = chart_window.frameGeometry()
            chart_geometry.moveCenter(center)
            chart_window.move(chart_geometry.topLeft())
            
            # 存图表窗口引用
            self.chart_windows[vt_symbol] = chart_window
            
            # 显示图表窗口
            chart_window.show()
            chart_window.activateWindow()
            
            print(f"显示期货图表：{vt_symbol}")
            
        except Exception as e:
            print(f"显示期货图表失败：{str(e)}")
            import traceback
            print(f"错误详情：{traceback.format_exc()}")

    def show_risk_manager(self):
        """显示风险管理窗口"""
        if self.risk_manager_window is None:
            self.risk_manager_window = RiskManager(self.main_engine, self.event_engine)
        self.risk_manager_window.show()

    def show_notification_manager(self):
        """显示通知管理窗口"""
        if self.notification_manager_window is None:
            self.notification_manager_window = NotificationManager(self.main_engine, self.event_engine)
        self.notification_manager_window.show()

    def show_strategy_manager(self):
        """显示策略管理窗口"""
        if self.strategy_manager_window is None:
            self.strategy_manager_window = StrategyManager(self.main_engine, self.event_engine, self.strategy_engine)
        self.strategy_manager_window.show()

    def show_performance_analytics(self):
        """显示业绩分析窗口"""
        if self.performance_analytics_window is None:
            self.performance_analytics_window = PerformanceAnalytics(self.main_engine, self.event_engine)
        self.performance_analytics_window.show()

if __name__ == "__main__":
    print("[DEBUG] 应用程序启动...")
    app = QtWidgets.QApplication([])
    print("[DEBUG] QApplication 创建完成")
    
    try:
        print("[DEBUG] 开始创建主窗口...")
        window = MainWindow()
        print("[DEBUG] 主窗口创建完成")
        
        print("[DEBUG] 显示主窗口...")
        window.show()
        # 确保窗口大小设置不被覆盖
        window.resize(1800, 1000)
        print("[DEBUG] 主窗口已显示，大小已设置")
        
        print("[DEBUG] 进入事件循环...")
        app.exec_()
        print("[DEBUG] 事件循环结束")
    except Exception as e:
        print(f"[ERROR] 应用程序异常: {str(e)}")
        import traceback
        print(f"[ERROR] 错误详情: {traceback.format_exc()}")
        raise
