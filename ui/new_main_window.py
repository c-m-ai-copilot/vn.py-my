"""
New Main Window based on vn.py UI/UX design standards
Professional trading terminal with modern layout
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
import datetime
import os
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_LOG, EVENT_ACCOUNT, EVENT_POSITION
from vnpy.event import Event
from config.data_persistence_engine import DataPersistenceEngine
from ui.new_login_dialog import NewLoginDialog

# 配置PyQt5中文字体
font = QtGui.QFont()
font.setFamily("Microsoft YaHei")
font.setPointSize(9)
QtWidgets.QApplication.setFont(font)

class CloseButton(QtWidgets.QPushButton):
    """自定义关闭按钮"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("×")
        self.setFixedSize(16, 16)
        self.setStyleSheet("""
            QPushButton {
                background: #ff6b6b;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #ff5252;
            }
            QPushButton:pressed {
                background: #ff4444;
            }
        """)

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    """系统托盘图标"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QtGui.QIcon("icons/app.ico"))
        self.setToolTip("期货交易系统")
        
        # 创建托盘菜单
        menu = QtWidgets.QMenu()
        
        show_action = menu.addAction("显示主界面")
        show_action.triggered.connect(self.parent().show)
        
        hide_action = menu.addAction("隐藏主界面")
        hide_action.triggered.connect(self.parent().hide)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("退出系统")
        quit_action.triggered.connect(QtWidgets.qApp.quit)
        
        self.setContextMenu(menu)

class MenuBar(QtWidgets.QMenuBar):
    """标准化菜单栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_menus()
    
    def init_menus(self):
        """初始化菜单"""
        # 文件菜单
        file_menu = self.addMenu("文件(&F)")
        file_menu.addAction("系统设置", self.parent().show_settings)
        file_menu.addSeparator()
        file_menu.addAction("退出", QtWidgets.qApp.quit)
        
        # 视图菜单
        view_menu = self.addMenu("视图(&V)")
        view_menu.addAction("行情监控", lambda: self.parent().show_widget("market"))
        view_menu.addAction("委托管理", lambda: self.parent().show_widget("order"))
        view_menu.addAction("成交查询", lambda: self.parent().show_widget("trade"))
        view_menu.addAction("持仓管理", lambda: self.parent().show_widget("position"))
        
        # 工具菜单
        tools_menu = self.addMenu("工具(&T)")
        tools_menu.addAction("策略管理", lambda: self.parent().show_widget("strategy"))
        tools_menu.addAction("风险管理", lambda: self.parent().show_widget("risk"))
        tools_menu.addAction("业绩分析", lambda: self.parent().show_widget("performance"))
        
        # 帮助菜单
        help_menu = self.addMenu("帮助(&H)")
        help_menu.addAction("关于", self.parent().show_about)

class ToolBar(QtWidgets.QToolBar):
    """标准化工具栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(24, 24))
        self.init_tools()
    
    def init_tools(self):
        """初始化工具按钮"""
        # 连接状态
        self.connection_status = QtWidgets.QLabel("● 未连接")
        self.connection_status.setStyleSheet("color: #f5222d; font-weight: bold;")
        self.addWidget(self.connection_status)
        
        self.addSeparator()
        
        # 账户信息
        self.account_label = QtWidgets.QLabel("账户: --")
        self.account_label.setStyleSheet("font-weight: bold;")
        self.addWidget(self.account_label)
        
        self.addSeparator()
        
        # 资金信息
        self.balance_label = QtWidgets.QLabel("资金: --")
        self.balance_label.setStyleSheet("font-weight: bold;")
        self.addWidget(self.balance_label)
        
        self.addSeparator()
        
        # 时间显示
        self.time_label = QtWidgets.QLabel()
        self.time_label.setStyleSheet("font-weight: bold;")
        self.addWidget(self.time_label)
        
        # 添加弹簧
        self.addSeparator()
        
        # 功能按钮
        self.addAction("行情", lambda: self.parent().show_widget("market"))
        self.addAction("委托", lambda: self.parent().show_widget("order"))
        self.addAction("成交", lambda: self.parent().show_widget("trade"))
        self.addAction("持仓", lambda: self.parent().show_widget("position"))
    
    def update_time(self, current_time):
        """更新时间显示"""
        try:
            if hasattr(self, 'time_label'):
                self.time_label.setText(f"时间: {current_time}")
        except:
            pass
    
    def update_connection_status(self, connected, account=None):
        """更新连接状态"""
        if connected:
            self.connection_status.setText("● 已连接")
            self.connection_status.setStyleSheet("color: #52c41a; font-weight: bold;")
        else:
            self.connection_status.setText("● 未连接")
            self.connection_status.setStyleSheet("color: #f5222d; font-weight: bold;")
        
        if account:
            self.account_label.setText(f"账户: {account}")
    
    def update_balance(self, balance):
        """更新资金信息"""
        self.balance_label.setText(f"资金: ¥{balance:,.2f}")

class NavigationPanel(QtWidgets.QWidget):
    """左侧导航面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # Store reference to main window
        self.setFixedWidth(200)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 导航标题
        nav_title = QtWidgets.QLabel("功能导航")
        nav_title.setAlignment(Qt.AlignCenter)
        nav_title.setFixedHeight(40)
        nav_title.setStyleSheet("""
            QLabel {
                background-color: #001529;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        layout.addWidget(nav_title)
        
        # 导航按钮
        nav_buttons = [
            ("📊 行情监控", "market"),
            ("📋 委托管理", "order"),
            ("💰 成交查询", "trade"),
            ("📈 持仓管理", "position"),
            ("🏦 资金管理", "account"),
            ("⚙️ 策略管理", "strategy"),
            ("🛡️ 风险管理", "risk"),
            ("📊 业绩分析", "performance"),
            ("📥 日志查看", "log"),
        ]
        
        self.nav_group = QtWidgets.QButtonGroup()
        self.nav_group.setExclusive(True)
        
        for text, widget_id in nav_buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setFixedHeight(40)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #001529;
                    color: #a6adb4;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #1890ff;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #1890ff;
                    color: white;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, w=widget_id: self.main_window.show_widget(w))
            layout.addWidget(btn)
            self.nav_group.addButton(btn)
        
        layout.addStretch()
        
        # 底部状态
        status_label = QtWidgets.QLabel("vn.py 2.0")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setFixedHeight(30)
        status_label.setStyleSheet("""
            QLabel {
                background-color: #001529;
                color: #a6adb4;
                font-size: 11px;
            }
        """)
        layout.addWidget(status_label)
        
        self.setLayout(layout)
        
        # 默认选中第一个按钮
        first_btn = self.nav_group.buttons()[0]
        first_btn.setChecked(True)

class CentralWidget(QtWidgets.QWidget):
    """中央工作区"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # Store reference to main window
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签页管理
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        

        
        # 设置标签页样式
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d9d9d9;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                border: 1px solid #d9d9d9;
                padding: 8px 15px 8px 15px;
                margin-right: 2px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background: #e6f7ff;
            }

        """)
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def add_tab(self, widget, title):
        """添加标签页"""
        index = self.tab_widget.addTab(widget, title)
        self.tab_widget.setCurrentWidget(widget)
        
        # 为页签添加自定义关闭按钮
        close_button = CloseButton()
        # 使用functools.partial来正确传递索引参数
        from functools import partial
        close_button.clicked.connect(partial(self.close_tab, index))
        self.tab_widget.tabBar().setTabButton(index, QtWidgets.QTabBar.RightSide, close_button)
    
    def close_tab(self, index):
        """关闭标签页"""
        try:
            # 获取要关闭的标签页
            widget = self.tab_widget.widget(index)
            title = self.tab_widget.tabText(index)
            
            # 如果是最后一个标签页，不允许关闭
            if self.tab_widget.count() <= 1:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "提示",
                    "至少需要保留一个标签页",
                    QMessageBox.Ok
                )
                return
            
            # 对于某些重要的标签页，可以添加确认对话框
            important_tabs = ["行情监控", "委托管理", "成交记录", "持仓监控"]
            if title in important_tabs:
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "确认关闭",
                    f"确定要关闭 '{title}' 标签页吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 关闭标签页
            self.tab_widget.removeTab(index)
            
            # 如果关闭的是当前标签页，切换到前一个标签页
            if self.tab_widget.count() > 0:
                new_index = min(index, self.tab_widget.count() - 1)
                self.tab_widget.setCurrentIndex(new_index)
                
        except Exception as e:
            from config.log_manager import log_manager
            log_manager.log(f"关闭标签页时出错：{str(e)}")
    
    def get_tab_count(self):
        """获取标签页数量"""
        return self.tab_widget.count()

class NewMainWindow(QtWidgets.QMainWindow):
    """新的主窗口 - 基于vn.py设计规范"""
    
    signal_log = QtCore.pyqtSignal(Event)

    
    def __init__(self):
        super().__init__()
        print("[DEBUG] NewMainWindow.__init__ 开始")
        
        print("[DEBUG] NewMainWindow: Initializing engines...")
        # 初始化引擎
        self.init_engines()
        print("[DEBUG] NewMainWindow: Engines initialized")
        
        print("[DEBUG] NewMainWindow: Initializing UI...")
        # 初始化UI
        self.init_ui()
        print("[DEBUG] NewMainWindow: UI initialized")
        
        print("[DEBUG] NewMainWindow: Initializing system tray...")
        # 初始化系统托盘
        self.init_system_tray()
        print("[DEBUG] NewMainWindow: System tray initialized")
        
        print("[DEBUG] NewMainWindow: Connecting signals...")
        # 连接信号
        self.connect_signals()
        print("[DEBUG] NewMainWindow: Signals connected")
        
        print("[DEBUG] NewMainWindow: Showing login dialog...")
        # 显示登录对话框
        self.show_login_dialog()
        print("[DEBUG] NewMainWindow: Login dialog completed")
        
        print("[DEBUG] NewMainWindow.__init__ 完成")
    
    def init_engines(self):
        """初始化交易引擎"""
        print("[DEBUG] init_engines: 创建事件引擎...")
        self.event_engine = EventEngine()
        print("[DEBUG] init_engines: 事件引擎创建完成")
        
        print("[DEBUG] init_engines: 创建主引擎...")
        self.main_engine = MainEngine(self.event_engine)
        print("[DEBUG] init_engines: 主引擎创建完成")
        
        # 添加CTP网关
        try:
            # 强制启用mock模式进行调试
            os.environ['USE_MOCK_DATA'] = 'true'
            print("🚀 强制使用Mock数据模式（调试模式）")
            from tests.mock_data.mock_engine import MockEngine as CtpGateway
            print("[DEBUG] init_engines: 创建mock引擎...")
            # 创建mock引擎并添加到主引擎
            mock_engine = CtpGateway(self.main_engine, self.event_engine)
            self.main_engine.gateways["MockCTP"] = mock_engine
            print("[DEBUG] init_engines: Mock引擎已添加到主引擎")
            
            # 立即加载合约
            print("[DEBUG] init_engines: 获取合约列表...")
            contracts = mock_engine.get_all_contracts()
            print(f"[DEBUG] init_engines: 从Mock引擎获取合约: {len(contracts)}")
            
            # 通过事件系统发送合约，让主引擎处理
            from vnpy.event import Event
            from vnpy.trader.event import EVENT_CONTRACT
            for contract in contracts:
                event = Event(EVENT_CONTRACT, contract)
                self.event_engine.put(event)
            
            print(f"[DEBUG] init_engines: 已通过事件系统发送 {len(contracts)} 个合约")
        except ImportError as e:
            print(f"[ERROR] init_engines: CTP网关未安装: {e}")
        
        print("[DEBUG] init_engines: 添加数据持久化引擎...")
        # 添加数据持久化引擎
        self.persistence_engine = DataPersistenceEngine(self.main_engine, self.event_engine)
        print("[DEBUG] init_engines: 数据持久化引擎添加完成")
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("期货交易系统 - vn.py Terminal")
        self.setMinimumSize(1200, 700)
        self.resize(1800, 1000)
        
        # 立即设置窗口在屏幕中央（在显示之前）
        self.center_on_screen()
        
        # 设置窗口图标
        # self.setWindowIcon(QIcon("icons/app.ico"))
        
        # 创建菜单栏
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # 创建工具栏
        self.tool_bar = ToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.tool_bar)
        
        # 创建左侧导航
        self.nav_panel = NavigationPanel(self)
        
        # 创建中央工作区
        self.central_widget = CentralWidget(self)
        
        # 创建主布局
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(self.nav_panel)
        main_layout.addWidget(self.central_widget)
        
        # 设置中央部件
        central = QtWidgets.QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        # 创建状态栏
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QToolBar {
                background-color: white;
                border: 1px solid #d9d9d9;
                spacing: 5px;
            }
            QStatusBar {
                background-color: #f5f5f5;
                color: #666;
                border-top: 1px solid #d9d9d9;
            }
        """)
    
    def center_on_screen(self):
        """将窗口居中显示在屏幕上"""
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.setGeometry(window_geometry)
        print(f"center_on_screen: Centered at {window_geometry.topLeft()}")
    
    def init_system_tray(self):
        """初始化系统托盘"""
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show()
        
        # 托盘图标激活
        self.tray_icon.activated.connect(self.on_tray_activated)
    
    def connect_signals(self):
        """连接信号"""
        # 连接事件
        self.event_engine.register(EVENT_ACCOUNT, self.on_account_event)
        self.event_engine.register(EVENT_POSITION, self.on_position_event)
        
        self.signal_log.connect(self.on_log_event)
        self.event_engine.register(EVENT_LOG, self.signal_log.emit)
        
        # 创建定时器更新时间
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if hasattr(self, 'tool_bar') and self.tool_bar:
            self.tool_bar.update_time(current_time)
    
    def show_login_dialog(self):
        """显示登录对话框"""
        print("show_login_dialog: Creating dialog...")
        dialog = NewLoginDialog(self)
        dialog.setModal(True)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setWindowFlags(Qt.Dialog)
        
        print("show_login_dialog: Showing main window centered on screen...")
        # 先显示主窗口并居中在屏幕上
        self.show()
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        main_size = self.frameGeometry()
        main_x = (screen_geometry.width() - main_size.width()) // 2
        main_y = (screen_geometry.height() - main_size.height()) // 2
        self.setGeometry(main_x, main_y, main_size.width(), main_size.height())
        self.raise_()
        self.activateWindow()
        
        print("show_login_dialog: Centering dialog on main window...")
        # 居中显示在主窗口上
        dialog.adjustSize()
        dialog_geometry = dialog.frameGeometry()
        main_center = self.frameGeometry().center()
        dialog_geometry.moveCenter(main_center)
        dialog.move(dialog_geometry.topLeft())
        
        print(f"show_login_dialog: Main window center: {main_center}")
        print(f"show_login_dialog: Dialog centered at: {dialog_geometry.topLeft()}")
        
        print("show_login_dialog: Starting modal dialog...")
        result = dialog.exec_()
        print(f"show_login_dialog: Dialog result = {result}")
        
        if result == QtWidgets.QDialog.Accepted:
            settings = dialog.get_login_settings()
            print("show_login_dialog: Connecting to gateway...")
            self.connect_to_gateway(settings)
        else:
            print("show_login_dialog: User cancelled, quitting...")
            QtWidgets.qApp.quit()
    
    def connect_to_gateway(self, settings):
        """连接到网关"""
        try:
            from tests.mock_data.mock_launcher import is_mock_enabled
            if is_mock_enabled():
                gateway_name = "MockCTP"
            else:
                gateway_name = "CTP"
            print(f"[DEBUG] 开始连接到网关: {gateway_name}")
            print(f"[DEBUG] 连接设置: {settings}")
            self.main_engine.connect(settings, gateway_name)
            
            # 检查网关连接状态
            gateway = self.main_engine.get_gateway(gateway_name)
            if gateway:
                print(f"[DEBUG] 网关实例: {type(gateway)}")
                if hasattr(gateway, 'gateway') and hasattr(gateway.gateway, 'connected'):
                    print(f"[DEBUG] 网关连接状态: {gateway.gateway.connected}")
                else:
                    print("[DEBUG] 网关结构检查...")
                    print(f"[DEBUG] 网关属性: {dir(gateway)}")
            
            # 立即查询合约
            print("[DEBUG] 连接成功后立即查询合约...")
            all_contracts = list(self.main_engine.get_all_contracts())
            print(f"[DEBUG] 主引擎返回合约数量: {len(all_contracts)}")
            
            if not all_contracts:
                print("[DEBUG] 主引擎未返回合约，尝试从所有网关获取...")
                for gateway in self.main_engine.gateways.values():
                    print(f"[DEBUG] 检查网关: {gateway.gateway_name}")
                    if hasattr(gateway, 'get_all_contracts'):
                        contracts = gateway.get_all_contracts()
                        print(f"[DEBUG] 网关 {gateway.gateway_name} 返回合约: {len(contracts)}")
                        if contracts:
                            print(f"[DEBUG] 合约示例: {contracts[0].symbol}")
            
            self.tool_bar.update_connection_status(True, settings["user_id"])
            self.status_bar.showMessage("已连接到交易服务器")
            
            # 添加默认标签页
            self.show_widget("market")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "连接失败", f"连接失败: {str(e)}")
            self.tool_bar.update_connection_status(False)
    
    def show_widget(self, widget_type):
        """显示指定类型的窗口"""
        widget_map = {
            "market": self.create_market_widget,
            "order": self.create_order_widget,
            "trade": self.create_trade_widget,
            "position": self.create_position_widget,
            "account": self.create_account_widget,
            "strategy": self.create_strategy_widget,
            "risk": self.create_risk_widget,
            "performance": self.create_performance_widget,
            "log": self.create_log_widget,
        }
        
        if widget_type in widget_map:
            widget = widget_map[widget_type]()
            title_map = {
                "market": "行情监控",
                "order": "委托管理",
                "trade": "成交查询",
                "position": "持仓管理",
                "account": "资金管理",
                "strategy": "策略管理",
                "risk": "风险管理",
                "performance": "业绩分析",
                "log": "日志查看"
            }
            self.central_widget.add_tab(widget, title_map[widget_type])
    
    def create_market_widget(self):
        """创建行情监控组件"""
        from ui.market_monitor import MarketMonitor
        from ui.trading_component import SimpleTradingComponent
        from tests.mock_data.mock_launcher import is_mock_enabled

        gateway_name = "MockCTP" if is_mock_enabled() else "CTP"
        
        # 创建交易组件
        trading_component = SimpleTradingComponent(self.main_engine, self.event_engine)
        
        # 创建行情监控组件，并传入交易组件
        market_monitor = MarketMonitor(
            self.main_engine, 
            self.event_engine, 
            gateway_name=gateway_name,
            trading_widget=trading_component
        )
        
        return market_monitor
    
    def create_order_widget(self):
        """创建委托管理组件"""
        from ui.order_monitor import OrderMonitor
        return OrderMonitor(self.main_engine, self.event_engine)
    
    def create_trade_widget(self):
        """创建成交查询组件"""
        from ui.trade_monitor import TradeMonitor
        return TradeMonitor(self.main_engine, self.event_engine)
    
    def create_position_widget(self):
        """创建持仓管理组件"""
        from ui.position_monitor import PositionMonitor
        return PositionMonitor(self.main_engine, self.event_engine)
    
    def create_account_widget(self):
        """创建资金管理组件"""
        from ui.account_monitor import AccountMonitor
        return AccountMonitor(self.main_engine, self.event_engine)
    
    def create_strategy_widget(self):
        """创建策略管理组件"""
        from ui.strategy_manager import StrategyManager
        from config.strategy_engine import StrategyEngine
        strategy_engine = StrategyEngine(self.main_engine, self.event_engine)
        return StrategyManager(self.main_engine, self.event_engine, strategy_engine)
    
    def create_risk_widget(self):
        """创建风险管理组件"""
        from ui.risk_manager import RiskManager
        return RiskManager(self.main_engine, self.event_engine)
    
    def create_performance_widget(self):
        """创建业绩分析组件"""
        from ui.performance_analytics import PerformanceAnalytics
        return PerformanceAnalytics(self.main_engine, self.event_engine)
    
    def create_log_widget(self):
        """创建日志查看组件"""
        log_widget = QtWidgets.QTextEdit()
        log_widget.setReadOnly(True)
        log_widget.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #d9d9d9;
            }
        """)
        return log_widget
    
    def on_account_event(self, event):
        """处理账户事件"""
        account = event.data
        self.tool_bar.update_balance(account.balance)
    
    def on_position_event(self, event):
        """处理持仓事件"""
        pass
    
    def on_log_event(self, event):
        """处理日志事件"""
        log = event.data
        self.status_bar.showMessage(log.msg, 5000)
    
    def on_tray_activated(self, reason):
        """托盘图标激活处理"""
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def show_settings(self):
        """显示设置"""
        QtWidgets.QMessageBox.information(self, "设置", "系统设置功能开发中...")
    
    def show_about(self):
        """显示关于"""
        QtWidgets.QMessageBox.about(self, "关于", "期货交易系统 v2.0\n基于vn.py框架开发")
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认退出", "确定要退出系统吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.main_engine.close()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = NewMainWindow()
    window.show()
    sys.exit(app.exec_())