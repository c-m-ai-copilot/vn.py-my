from typing import Dict
from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_LOG
from vnpy.event import Event
from vnpy.trader.utility import load_json
from vnpy_ctp import CtpGateway
from datetime import datetime, time

from config import log_manager

class GatewayManager(QtWidgets.QWidget):
    """网关管理组件"""
    
    # 添加信号
    signal_log = QtCore.pyqtSignal(str)
    signal_login_success = QtCore.pyqtSignal()  # 添加登录成功信号
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super().__init__()
        
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.gateway_name: str = "CTP"  # 默认使用CTP
        
        self.init_ui()
        self.load_settings()
        self.register_event()
        
        # 连接信号到更新日志的槽
        self.signal_log.connect(self.update_log)
    
    def init_ui(self) -> None:
        self.setWindowTitle("交易接口")
        self.setFixedWidth(300)
        
        self.setStyleSheet("""
            QWidget {
                font-family: Microsoft YaHei;
                font-size: 12px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QLabel {
                font-weight: bold;
            }
        """)
        
        # CTP接口配置
        form = QtWidgets.QFormLayout()
        
        self.userid_line = QtWidgets.QLineEdit()
        self.password_line = QtWidgets.QLineEdit()
        self.password_line.setEchoMode(QtWidgets.QLineEdit.Password)
        
        self.brokerid_line = QtWidgets.QLineEdit()
        self.td_address_line = QtWidgets.QLineEdit()
        self.md_address_line = QtWidgets.QLineEdit()
        self.appid_line = QtWidgets.QLineEdit()
        self.auth_code_line = QtWidgets.QLineEdit()
        
        form.addRow("用户名", self.userid_line)
        form.addRow("密码", self.password_line)
        form.addRow("经纪商代码", self.brokerid_line)
        form.addRow("交易服务器", self.td_address_line)
        form.addRow("行情服务器", self.md_address_line)
        form.addRow("产品名称", self.appid_line)
        form.addRow("授权编码", self.auth_code_line)
        
        # 连接和断开按钮
        button_layout = QtWidgets.QHBoxLayout()
        connect_button = QtWidgets.QPushButton("连接")
        disconnect_button = QtWidgets.QPushButton("断开")
        
        connect_button.clicked.connect(self.connect)
        disconnect_button.clicked.connect(self.disconnect)
        
        button_layout.addWidget(connect_button)
        button_layout.addWidget(disconnect_button)
        
        # 添加日志显示区域
        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setReadOnly(True)
        self.log_monitor.setMaximumHeight(200)
        self.log_monitor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                background-color: #f9f9f9;
            }
        """)
        
        # 主布局
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(button_layout)
        vbox.addWidget(QtWidgets.QLabel("连接日志"))
        vbox.addWidget(self.log_monitor)
        self.setLayout(vbox)
        
    def load_settings(self) -> None:
        """加载默认配置"""
        self.userid_line.setText("233998")
        self.password_line.setText("3621191@qazWSX")
        self.brokerid_line.setText("9999")
        
        # 根据当前时间选择合适的服务器地址
        current_time = datetime.now().time()
        is_trading_day = self.is_trading_day()  # 需要实现这个方法
        
        # 交易日：16:00～次日09:00；非交易日：16:00～次日12:00
        if (time(16, 0) <= current_time or current_time <= time(9, 0)) or \
           (not is_trading_day and time(16, 0) <= current_time <= time(12, 0)):
            # 使用7x24看穿式前置（新地址）
            self.td_address_line.setText("182.254.243.31:40001")
            self.md_address_line.setText("182.254.243.31:40011")
            self.signal_log.emit("使用7x24看穿式前置地址")
        else:
            # 使用普通地址（新地址）
            self.td_address_line.setText("182.254.243.31:30001")
            self.md_address_line.setText("182.254.243.31:30011")
            self.signal_log.emit("使用普通地址")
        
        self.appid_line.setText("simnow_client_test")
        self.auth_code_line.setText("0000000000000000")
    
    def is_trading_day(self) -> bool:
        """判断是否为交易日"""
        current_date = datetime.now()
        weekday = current_date.weekday()
        
        # 简单判断：周一至周五为交易日
        # 实际使用时可能需要考虑节假日
        return weekday < 5
    
    def register_event(self) -> None:
        """注册事件监听"""
        self.event_engine.register(EVENT_LOG, self.process_log_event)
        
        # CTP特定事件
        self.event_engine.register(f"{self.gateway_name}.connect", self.process_connect_event)
        self.event_engine.register(f"{self.gateway_name}.error", self.process_error_event)
        
        # 添加更多事件监听
        self.event_engine.register(f"trade.{self.gateway_name}", self.process_trade_event)
        self.event_engine.register(f"position.{self.gateway_name}", self.process_position_event)
        self.event_engine.register(f"account.{self.gateway_name}", self.process_account_event)
        self.event_engine.register(f"contract.{self.gateway_name}", self.process_contract_event)
    
    def process_log_event(self, event: Event) -> None:
        """处理日志事件"""
        log = event.data
        msg = log.msg
        
        # 发送信号而不是直接更新
        self.signal_log.emit(f"{log.time}\t{msg}")
        
        # 检测登录成功
        if "交易服务器登录成功" in msg:
            print("检测到交易服务器登录成功")
            # 发送登录成功事件
            login_event = Event("LOGIN", None)
            self.event_engine.put(login_event)
            log_manager.console_log("已发送登录成功事件")
    
    def process_error_event(self, event: Event) -> None:
        """处理错误事件"""
        error = event.data
        self.signal_log.emit(f"错误信息：{error.msg}")
        # 记录更细的错误信息
        if hasattr(error, 'error_id'):
            self.signal_log.emit(f"错误ID：{error.error_id}")
            self.signal_log.emit(f"错误详情：{error}")
            # CTP错误码3表示登录失败
            if error.error_id == 3:
                self.signal_log.emit("登录失败，可能是账号密码错误")
                self._retry_count = 5  # 停止重试
    
    def process_trade_event(self, event: Event) -> None:
        """处理成交事件"""
        self.signal_log.emit("收到成交数据")
    
    def process_position_event(self, event: Event) -> None:
        """处理持仓事件"""
        self.signal_log.emit("收到持仓数据")
    
    def process_account_event(self, event: Event) -> None:
        """处理账户事件"""
        self.signal_log.emit("收到账户数据")
    
    def process_contract_event(self, event: Event) -> None:
        """处理合约事件"""
        self.signal_log.emit("收到合约数据")
    
    def process_status_event(self, event: Event) -> None:
        """处理状态事件"""
        msg = f"接口状态更新：{event.data}"
        self.signal_log.emit(msg)
    
    def process_connected_event(self, event: Event) -> None:
        """处理连接成功事件"""
        self.signal_log.emit("接口已连接到服务器")
    
    def process_disconnected_event(self, event: Event) -> None:
        """处理断开连接事件"""
        self.signal_log.emit("接口已断开连接")
    
    def process_login_event(self, event: Event) -> None:
        """处理登录事件"""
        print(f"收到登录事件: type={event.type_}")  # 打印事件类型
        self.signal_log.emit("收到登录事件")
        gateway = self.main_engine.gateways.get(self.gateway_name)
        print(f"process_login_event gateway: {gateway}")    
        
        if gateway:
            td_api = gateway.td_api
            self.signal_log.emit(f"交易接口实际登录状态: {td_api.login_status}")
            print(f"process_login_event td_api.login_status: {td_api.login_status}")    
            
            if td_api.login_status:
                self._retry_count = 0
                self.signal_log.emit("登录成功！")
                log_manager.log("交易系统登录成功")
                log_manager.console_log("交易系统登录成功")
                print("process_login_event login_status: True")
                
                # 发送登录成功事件
                login_event = Event("LOGIN", None)
                self.event_engine.put(login_event)
                log_manager.console_log("已发送登录成功事件")
                print("已发送登录成功事件")
                
                # 等待一下再查询
                QtCore.QTimer.singleShot(1000, lambda: self.start_query(gateway))
    
    def start_query(self, gateway) -> None:
        """开始查询"""
        # 立即查询账户和持仓信息
        self.signal_log.emit("开始查询账户和持仓信息...")
        
        # 立即查询
        gateway.query_account()
        gateway.query_position()
        
        # 1秒后再次查询确保数据完整
        QtCore.QTimer.singleShot(1000, lambda: gateway.query_account())
        QtCore.QTimer.singleShot(1000, lambda: gateway.query_position())
    
    def process_connect_event(self, event: Event) -> None:
        """处理连接事件"""
        self.signal_log.emit("收到连接事件")
    
    def update_log(self, msg: str) -> None:
        """更新日志显示"""
        self.log_monitor.append(msg)
    
    def connect(self) -> None:
        """连接特定接口"""
        settings = {
            "用户名": self.userid_line.text(),
            "密码": self.password_line.text(),
            "经纪商代码": self.brokerid_line.text(),
            "交易服务器": self.td_address_line.text(),
            "行情服务器": self.md_address_line.text(),
            "产品名称": self.appid_line.text(),
            "授权编码": self.auth_code_line.text(),
        }
        
        try:
            # 清空之前的日志
            self.log_monitor.clear()
            
            self.signal_log.emit("正在连接CTP接口...")
            self.signal_log.emit("=== 详细连接参数 ===")
            for key, value in settings.items():
                # 密码用*号代替
                #if key == "密码":
                #    self.signal_log.emit(f"{key}: {'*' * len(value)}")
                #else:
                self.signal_log.emit(f"{key}: {value}")
            self.signal_log.emit("==================")
            
            # 连接前检查网关是否已存在
            if self.gateway_name in self.main_engine.gateways:
                self.signal_log.emit(f"网关 {self.gateway_name} 已加载")
                gateway = self.main_engine.gateways.get(self.gateway_name)
                
                # 检查网关状态
                if gateway:
                    td_api = gateway.td_api
                    md_api = gateway.md_api
                    self.signal_log.emit("=== 网关状态 ===")
                    self.signal_log.emit(f"交易接口状: {td_api.connect_status}")
                    self.signal_log.emit(f"行情接口状态: {md_api.connect_status}")
                    self.signal_log.emit(f"登录状态: {td_api.login_status}")
                    # 打印更多网关信息
                    self.signal_log.emit(f"交易接口类型: {type(td_api)}")
                    self.signal_log.emit(f"行情接口类型: {type(md_api)}")
                    self.signal_log.emit("===============")
            else:
                self.signal_log.emit(f"网关 {self.gateway_name} 未找到，请检查配置")
                return
                
            self.signal_log.emit("始连接...")
            self.main_engine.connect(settings, self.gateway_name)
            self.signal_log.emit("已发送连接请求，等待接口响应...")
            
            # 启动定时器检查连接状态
            QtCore.QTimer.singleShot(2000, self.check_connection_status)
            
        except Exception as e:
            self.signal_log.emit(f"连接出错: {str(e)}")
            import traceback
            self.signal_log.emit(f"详细错误: {traceback.format_exc()}")
    
    def check_connection_status(self) -> None:
        """检查连接状态"""
        try:
            gateway = self.main_engine.gateways.get(self.gateway_name)
            if gateway:
                td_api = getattr(gateway, 'td_api', None)
                md_api = getattr(gateway, 'md_api', None)
                
                if not td_api or not md_api:
                    self.signal_log.emit("错误：交易接口或行情接口未初始化")
                    return

                self.signal_log.emit("=== 连接状态检查 ===")
                td_connected = getattr(td_api, 'connect_status', False)
                md_connected = getattr(md_api, 'connect_status', False)
                td_logged_in = getattr(td_api, 'login_status', False)
                
                print(f"检查连接状态: td_connected={td_connected}, md_connected={md_connected}, td_logged_in={td_logged_in}")
                
                if td_connected and md_connected and td_logged_in:
                    self.signal_log.emit("连接和登录成功！")
                    # 发送登录成功事件
                    login_event = Event(f"{self.gateway_name}.login", None)
                    self.event_engine.put(login_event)
                    print("发送CTP登录事件")
                    
                    # 发送通用登录事件
                    general_login_event = Event("LOGIN", None)
                    self.event_engine.put(general_login_event)
                    print("已发送通用登录事件")
        except Exception as e:
            self.signal_log.emit(f"状态检查出错: {str(e)}")
            import traceback
            self.signal_log.emit(f"详细错误信息: {traceback.format_exc()}")
    
    def disconnect(self) -> None:
        """断开接口"""
        self.signal_log.emit("正在断开CTP接口...")
        self.main_engine.close(self.gateway_name) 