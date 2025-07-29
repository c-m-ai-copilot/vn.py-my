from typing import Dict, List
from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT, EVENT_LOG
from vnpy.trader.object import TickData, ContractData, SubscribeRequest
from vnpy.trader.constant import Exchange, Direction
from vnpy.event import Event
from config.subscribed_symbols import subscribed_symbols
from config.tick_manager import tick_manager
from config.log_manager import log_manager
from ui.account_monitor import AccountMonitor
from ui.position_monitor import PositionMonitor
from ui.widgets.futures_chart import FuturesChartWindow  # 添加这行导入
import csv
from functools import partial

class MarketMonitor(QtWidgets.QWidget):
    """行情监控组件"""
    
    signal_tick = QtCore.pyqtSignal(Event)
    signal_login = QtCore.pyqtSignal()  # 添加登录信号
    signal_md_login = QtCore.pyqtSignal()  # 添加行情登录信号
    signal_query = QtCore.pyqtSignal()  # 添加查询信号
    contract_selected = QtCore.pyqtSignal(object)  # 添加合约选中信号
    
    def __init__(
        self, 
        main_engine: MainEngine, 
        event_engine: EventEngine, 
        gateway_name: str = "CTP",
        trading_widget = None  # 添加交易组件参数
    ) -> None:
        super().__init__()
        
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.gateway_name = gateway_name
        self.trading_widget = trading_widget  # 保存交易组件引用
        self.contracts: Dict[str, ContractData] = {}
        self.retry_count = 0
        self.trading_widget = trading_widget  # 保存交易组件引用
        
        # 初始化UI
        self.init_ui()
        self.register_event()
        
        # 连接信号
        self.signal_query.connect(self.do_query_contracts)
        
        # 添加定时器定期更新行情
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_tick_table)
        self.timer.start(2000)  # 改为2秒更新一次
        
        # 注册日志处理器，确保日志能显示在控制台
        log_manager.register_handler(self.console_log_handler)
    
    def console_log_handler(self, msg: str) -> None:
        """控制台日志处理器"""
        # print(f"[MarketMonitor] {msg}")
        pass

    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle("行情监控")
        
        # 创建主布局 - 水平分割：左侧交易组件，右侧行情区域
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setSpacing(2)
        
        # 左侧交易组件区域
        if self.trading_widget:
            left_container = QtWidgets.QWidget()
            left_container.setFixedWidth(320)  # 固定宽度
            left_container.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    border-right: 1px solid #dee2e6;
                }
            """)
            
            left_layout = QtWidgets.QVBoxLayout(left_container)
            left_layout.setContentsMargins(5, 5, 5, 5)
            left_layout.addWidget(self.trading_widget)
            
            main_layout.addWidget(left_container, stretch=3)  # 左侧占30%空间
        else:
            # 如果没有交易组件，创建一个空的占位区域
            placeholder = QtWidgets.QWidget()
            placeholder.setFixedWidth(320)
            placeholder.setStyleSheet("background-color: #f8f9fa; border-right: 1px solid #dee2e6;")
            main_layout.addWidget(placeholder, stretch=3)
        
        # 右侧行情区域 - 垂直分割：上方合约查询，下方订阅行情
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setSpacing(1)
        
        # 创建合约查询面板
        query_panel = QtWidgets.QWidget()
        query_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
            }
        """)
        query_panel.setFixedHeight(50)
        
        query_layout = QtWidgets.QHBoxLayout(query_panel)
        query_layout.setContentsMargins(10, 5, 10, 5)
        
        # 添加查询按钮
        query_button = QtWidgets.QPushButton("查询合约")
        query_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        query_button.clicked.connect(self.query_contracts)
        query_layout.addWidget(query_button)
        
        # 添加刷新按钮
        refresh_button = QtWidgets.QPushButton("刷新")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
            QPushButton:pressed {
                background-color: #155724;
            }
        """)
        refresh_button.clicked.connect(self.do_query_contracts)
        query_layout.addWidget(refresh_button)
        
        # 添加搜索框
        search_label = QtWidgets.QLabel("合约筛选:")
        search_label.setStyleSheet("font-weight: bold; color: #333;")
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("输入合约代码或名称进行筛选")
        self.search_line.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        self.search_line.textChanged.connect(self.filter_contracts)
        query_layout.addWidget(search_label)
        query_layout.addWidget(self.search_line)
        
        # 添加弹性空间
        query_layout.addStretch()
        
        right_layout.addWidget(query_panel)
        
        # 创建合约表格标题
        contract_title = QtWidgets.QLabel("合约查询")
        contract_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 5px;
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-bottom: none;
            }
        """)
        right_layout.addWidget(contract_title)
        
        # 创建合约查询表格
        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(9)  # 增加到9列
        self.contract_table.setHorizontalHeaderLabels([
            "合约代码", "代码", "交易所", "名称",
            "合约类型", "合约乘数", "价格单位", "最小下单量",
            "订阅"  # 新增订阅列
        ])
        self.contract_table.cellDoubleClicked.connect(self.on_contract_clicked)
        
        # 设置列宽
        header = self.contract_table.horizontalHeader()
        header.setStretchLastSection(False)  # 关闭后一列自动拉伸

        # 设置各列的宽度
        column_widths = {
            0: 150,  # 合约代码 (vt_symbol)
            1: 120,  # 代码 (symbol)
            2: 100,  # 交易所
            3: 150,  # 名称
            4: 100,  # 合约类型
            5: 100,  # 合约乘数
            6: 100,  # 价格单位
            7: 100,  # 最小下单量
            8: 60    # 订阅按钮 - 减小宽度
        }

        # 应用列宽设置
        for col, width in column_widths.items():
            self.contract_table.setColumnWidth(col, width)
            if col == 8:  # 订阅列固定宽度
                header.setSectionResizeMode(col, QtWidgets.QHeaderView.Fixed)
            else:  # 其他列可调整
                header.setSectionResizeMode(col, QtWidgets.QHeaderView.Interactive)

        # 设置表格的最小宽度，确保能显示所有列
        min_width = sum(column_widths.values()) + 50  # 加50是为了留一些边距
        self.contract_table.setMinimumWidth(min_width)
        
        # 设置合约表格属性
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.contract_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        
        # 添加合约表格到右侧布局
        right_layout.addWidget(self.contract_table)
        
        # 创建订阅行情表格标题
        tick_title = QtWidgets.QLabel("订阅合约行情")
        tick_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 5px;
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-bottom: none;
            }
        """)
        right_layout.addWidget(tick_title)
        
        # 创建行情表格
        self.tick_table = QtWidgets.QTableWidget()
        self.tick_table.setColumnCount(17)  # 增加到17列
        self.tick_table.setHorizontalHeaderLabels([
            "代码", "交易所", "名称", "最新价", 
            "成交量", "开盘价", "最高价", "最低价",
            "买价", "买量", "卖价", "卖量", 
            "时间", "接口", "K线图", "快速下单", "退订"  # 修改最后一列的名称为"退订"
        ])
        
        # 设置行情表格属性
        self.tick_table.verticalHeader().setVisible(False)
        self.tick_table.setEditTriggers(self.tick_table.NoEditTriggers)
        self.tick_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tick_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tick_table.cellDoubleClicked.connect(self.on_tick_clicked)  # 添加双击事件
        
        # 设置行情表格列宽
        self.tick_table.setColumnWidth(0, 80)   # 代码
        self.tick_table.setColumnWidth(1, 60)   # 交易所
        self.tick_table.setColumnWidth(2, 80)   # 名称
        self.tick_table.setColumnWidth(3, 80)   # 最新价
        self.tick_table.setColumnWidth(4, 80)   # 成交量
        self.tick_table.setColumnWidth(5, 80)   # 开盘价
        self.tick_table.setColumnWidth(6, 80)   # 最高价
        self.tick_table.setColumnWidth(7, 80)   # 最低价
        self.tick_table.setColumnWidth(8, 80)   # 买价
        self.tick_table.setColumnWidth(9, 60)   # 买量
        self.tick_table.setColumnWidth(10, 80)  # 卖价
        self.tick_table.setColumnWidth(11, 60)  # 卖量
        self.tick_table.setColumnWidth(12, 100) # 时间
        self.tick_table.setColumnWidth(13, 60)  # 接口
        self.tick_table.setColumnWidth(14, 60)  # K线图按钮列
        self.tick_table.setColumnWidth(15, 80)  # 快速下单按钮列
        self.tick_table.setColumnWidth(16, 60)  # 设置解除订阅按钮列宽度
        
        # 添加行情表格到右侧布局
        right_layout.addWidget(self.tick_table)
        
        # 将右侧布局添加到主布局
        main_layout.addLayout(right_layout, stretch=7)  # 右侧占70%空间
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 设置最小边距
        main_layout.setContentsMargins(1, 1, 1, 1)
        
        # 设置样式
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #CCCCCC;
                gridline-color: #CCCCCC;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 4px;
                border: 1px solid #CCCCCC;
                font-size: 12px;
            }
            QPushButton {
                font-size: 12px;
                padding: 3px 8px;
            }
            QLabel {
                font-size: 12px;
            }
            QLineEdit {
                font-size: 12px;
            }
        """)
        
        # 登录成功后自动查询所有合约
        self.signal_login.connect(self.query_contracts)

    def _setup_table_style(self):
        """设置表格样式"""
        self.tick_table.setStyleSheet("""
            QTableWidget {
                background-color: rgb(20, 28, 40);
                color: white;
                gridline-color: rgb(40, 48, 60);
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: rgb(40, 48, 60);
                color: white;
                padding: 4px;
                border: none;
                font-size: 12px;
            }
        """)
        
        # 设置表格属性
        self.tick_table.verticalHeader().setVisible(False)
        self.tick_table.setEditTriggers(self.tick_table.NoEditTriggers)
        self.tick_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tick_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        
        # 设置列宽
        self.tick_table.setColumnWidth(0, 80)   # 代码
        self.tick_table.setColumnWidth(1, 60)   # 交易所
        self.tick_table.setColumnWidth(2, 80)   # 名称
        self.tick_table.setColumnWidth(3, 80)   # 最新价
        self.tick_table.setColumnWidth(4, 80)   # 成交量
        self.tick_table.setColumnWidth(5, 80)   # 开盘价
        self.tick_table.setColumnWidth(6, 80)   # 最高价
        self.tick_table.setColumnWidth(7, 80)   # 最低价
        self.tick_table.setColumnWidth(8, 80)   # 买价
        self.tick_table.setColumnWidth(9, 60)   # 买量
        self.tick_table.setColumnWidth(10, 80)  # 卖价
        self.tick_table.setColumnWidth(11, 60)  # 卖量
        self.tick_table.setColumnWidth(12, 100) # 时间
        self.tick_table.setColumnWidth(13, 60)  # 接口
        self.tick_table.setColumnWidth(14, 60)  # K线图按钮列
        self.tick_table.setColumnWidth(15, 80)  # 快速下单按钮列

    def register_event(self) -> None:
        """注册事件监听"""
        # print("[DEBUG] MarketMonitor: 注册事件监听")
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        # 添加日志事件监听
        self.event_engine.register(EVENT_LOG, self.process_log_event)
        # print("[DEBUG] MarketMonitor: 事件监听注册完成")
        
        # 延迟查询合约，确保事件系统已启动
        QtCore.QTimer.singleShot(2000, self.delayed_contract_query)
    
    def delayed_contract_query(self):
        """延迟查询合约"""
        # print("[DEBUG] MarketMonitor: 开始延迟查询合约")
        self.query_contracts()

    def on_login_success_event(self, event: Event) -> None:
        """处理登录成功事件"""
        log_manager.console_log("收到登录成功事件，发出信号")
        self.signal_login.emit()

    def on_md_login(self) -> None:
        """处理行情登录成功"""
        try:
            log_manager.console_log("行情登录成功，开始初始化...")
            
            # 立即查询一次合约
            self.query_contracts()
            
            # 延迟2秒后查询持仓和订阅已保存的合约
            QtCore.QTimer.singleShot(2000, self.init_after_login)
            
        except Exception as e:
            log_manager.log(f"行情登录处理失败：{str(e)}")

    def init_after_login(self) -> None:
        """登录后的初始化"""
        try:
            # 查询持仓
            self.main_engine.query_position()
            log_manager.console_log("查询持仓信息...")
            
            # 查询账户
            self.main_engine.query_account()
            log_manager.console_log("查询账户信息...")
            
            # 订阅已保存的合约
            if self.contracts:
                log_manager.console_log("开始订阅已保存的合约...")
                self.load_and_subscribe_saved_contracts()
            else:
                log_manager.console_log("未查询到合约信息，稍后重试...")
                # 1秒后重试
                QtCore.QTimer.singleShot(1000, self.do_query_contracts)
                
            # 启动强制tick生成器
            self.start_forced_tick_generator()
            
        except Exception as e:
            log_manager.log(f"登录后初始化失败：{str(e)}")
    
    def start_forced_tick_generator(self):
        """启动强制tick生成器"""
        # print("[DEBUG] MarketMonitor: 启动强制tick生成器...")
        self.tick_generator_timer = QtCore.QTimer()
        self.tick_generator_timer.timeout.connect(self.generate_forced_ticks)
        self.tick_generator_timer.start(1000)  # 每秒生成一次
        # print("[DEBUG] MarketMonitor: 强制tick生成器已启动")
    
    def generate_forced_ticks(self):
        """强制生成tick数据"""
        try:
            from tests.mock_data.mock_tick_generator import mock_tick_generator
            from vnpy.trader.constant import Exchange
            
            subscribed = subscribed_symbols.get_symbols()
            # print(f"[DEBUG] MarketMonitor.generate_forced_ticks: 为 {len(subscribed)} 个合约生成tick数据")
            
            generated_count = 0
            for vt_symbol in subscribed:
                try:
                    symbol, exchange_str = vt_symbol.split('.')
                    exchange = Exchange(exchange_str)
                    
                    # 生成tick数据
                    tick = mock_tick_generator.generate_tick(symbol, exchange)
                    if tick:
                        # 强制更新tick管理器
                        tick_manager.update_tick(tick)
                        generated_count += 1
                        # print(f"[DEBUG] MarketMonitor.generate_forced_ticks: 生成tick - {vt_symbol}, 价格: {tick.last_price}")
                        
                except Exception as e:
                    # print(f"[ERROR] MarketMonitor.generate_forced_ticks: 生成 {vt_symbol} 的tick失败: {e}")
                    pass
            
            if generated_count > 0:
                # print(f"[DEBUG] MarketMonitor.generate_forced_ticks: 本次生成了 {generated_count} 个tick数据")
                pass
                self.update_tick_table()
                
        except Exception as e:
            # print(f"[ERROR] MarketMonitor.generate_forced_ticks: 强制生成tick失败: {e}")
            pass

    def process_tick_event(self, event: Event) -> None:
        """处理行情事件"""
        try:
            tick = event.data
            vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
            # log_manager.log(f"[MarketMonitor] Received tick event for {vt_symbol} at price {tick.last_price}")
            
            subscribed_symbols_set = subscribed_symbols.get_symbols()
            # log_manager.log(f"[MarketMonitor] Current subscribed symbols: {subscribed_symbols_set}")
            is_subscribed = vt_symbol in subscribed_symbols_set
            # log_manager.log(f"[MarketMonitor] Is {vt_symbol} in subscribed list? {is_subscribed}")
            
            if is_subscribed:
                #log_manager.log(f"[MarketMonitor] Processing tick for subscribed symbol: {vt_symbol}")
                tick_manager.update_tick(tick)
                #log_manager.log(f"[MarketMonitor] Tick for {vt_symbol} updated in TickManager")
                
                self.update_position_pnl(vt_symbol, tick.last_price)
                
                # log_manager.log(f"[MarketMonitor] Calling update_tick_table for {vt_symbol}")
                self.update_tick_table()
                # log_manager.log(f"[MarketMonitor] update_tick_table finished for {vt_symbol}")
            else:
                # log_manager.log(f"[MarketMonitor] Skipping tick for unsubscribed symbol: {vt_symbol}")
                pass
                
        except Exception as e:
            # log_manager.log(f"[MarketMonitor] Error processing tick event: {str(e)}", level='error')
            # import traceback
            # log_manager.log(f"[MarketMonitor] Traceback: {traceback.format_exc()}", level='error')
            pass

    def process_contract_event(self, event: Event) -> None:
        """处理合约事件"""
        contract = event.data
        self.contracts[contract.vt_symbol] = contract
        # print(f"[DEBUG] MarketMonitor: 收到合约事件 {contract.symbol}.{contract.exchange.value}")

    def process_log_event(self, event: Event) -> None:
        """处理日志事件"""
        log = event.data
        msg = log.msg
        #print(f"process_log_event msg: {msg}")
        
        # 检测结算信息确认成功后等待1钟再查询合约
        if "结算信息确认成功" in msg:
            log_manager.console_log("检测到结算信息确认成功")
            log_manager.console_log("等待1分钟后开始查询合约信息...")
            # 等待1分钟后查询
            #QtCore.QTimer.singleShot(60000, self.query_contracts)  # 60000毫秒 = 1分钟

    def do_query_contracts(self) -> None:
        """执行合约查询"""
        log_manager.console_log("开始查询合约信息...")
        self.query_contracts()
        
        # 如果查询到合约则开始订阅
        if self.contracts:
            log_manager.console_log("开始订阅已保存的合约...")
            self.load_and_subscribe_saved_contracts()
        else:
            log_manager.console_log("未查询到合约信息，稍后重试...")
            # 1秒后重试
            QtCore.QTimer.singleShot(1000, self.do_query_contracts)

    def update_tick_table(self) -> None:
        """更新行情表格"""
        try:
            # 获取所有已订阅的合约
            subscribed = subscribed_symbols.get_symbols()
            # print(f"[DEBUG] MarketMonitor.update_tick_table: 开始更新行情表格，已订阅合约: {len(subscribed)} 个")
            
            valid_ticks = []
            
            # 获取每个已订阅合约的最新行情
            for vt_symbol in subscribed:
                tick = tick_manager.get_tick(vt_symbol)
                if tick:
                    valid_ticks.append(tick)
                    # print(f"[DEBUG] MarketMonitor.update_tick_table: 找到tick数据 - {vt_symbol}, 最新价: {tick.last_price}")
                # else:
                #     print(f"[DEBUG] MarketMonitor.update_tick_table: 未找到tick数据 - {vt_symbol}")
            
            # print(f"[DEBUG] MarketMonitor.update_tick_table: 有效tick数据数量: {len(valid_ticks)}")
            
            # 设置表格行数
            self.tick_table.setRowCount(len(valid_ticks))
            
            # 更新表格数据
            for row, tick in enumerate(valid_ticks):
                # print(f"[DEBUG] MarketMonitor.update_tick_table: 正在更新第 {row} 行 - {tick.symbol}.{tick.exchange.value}")
                # 设置基本信息和行情数据
                self.tick_table.setItem(row, 0, QtWidgets.QTableWidgetItem(tick.symbol))
                self.tick_table.setItem(row, 1, QtWidgets.QTableWidgetItem(tick.exchange.value))
                
                # 获取合约名称
                contract = self.contracts.get(tick.vt_symbol)
                contract_name = contract.name if contract else tick.symbol
                self.tick_table.setItem(row, 2, QtWidgets.QTableWidgetItem(contract_name))
                
                # 设置行情数据
                self.tick_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(tick.last_price)))
                self.tick_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(tick.volume)))
                self.tick_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(tick.open_price)))
                self.tick_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(tick.high_price)))
                self.tick_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(tick.low_price)))
                self.tick_table.setItem(row, 8, QtWidgets.QTableWidgetItem(str(tick.bid_price_1)))
                self.tick_table.setItem(row, 9, QtWidgets.QTableWidgetItem(str(tick.bid_volume_1)))
                self.tick_table.setItem(row, 10, QtWidgets.QTableWidgetItem(str(tick.ask_price_1)))
                self.tick_table.setItem(row, 11, QtWidgets.QTableWidgetItem(str(tick.ask_volume_1)))
                self.tick_table.setItem(row, 12, QtWidgets.QTableWidgetItem(str(tick.datetime)))
                self.tick_table.setItem(row, 13, QtWidgets.QTableWidgetItem(tick.gateway_name))
                
                # 只在按钮不存在时创建按钮
                if not self.tick_table.cellWidget(row, 14):
                    # K线图按钮
                    chart_button = QtWidgets.QPushButton("K线")
                    chart_button.setStyleSheet("""
                        QPushButton {
                            font-size: 12px;
                            padding: 2px 5px;
                            background-color: #f0f0f0;
                            border: 1px solid #ccc;
                            border-radius: 2px;
                        }
                        QPushButton:hover {
                            background-color: #e0e0e0;
                        }
                    """)
                    # 使用functools.partial来正确绑定参数
                    chart_button.clicked.connect(
                        partial(self.show_chart_from_button, tick.vt_symbol)
                    )
                    self.tick_table.setCellWidget(row, 14, chart_button)
                
                if not self.tick_table.cellWidget(row, 15):
                    # 快速下单按钮
                    trading_widget = QtWidgets.QWidget()
                    layout = QtWidgets.QHBoxLayout(trading_widget)
                    
                    buy_button = QtWidgets.QPushButton("买")
                    sell_button = QtWidgets.QPushButton("卖")
                    
                    # 设置按钮样式
                    buy_button_style = """
                        QPushButton {
                            color: white;
                            background-color: #ff4d4d;
                            border: none;
                            padding: 2px 8px;
                            font-size: 12px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 20px;
                            max-height: 20px;
                        }
                        QPushButton:hover {
                            background-color: #ff3333;
                        }
                    """
                    
                    sell_button_style = """
                        QPushButton {
                            color: white;
                            background-color: #00b33c;
                            border: none;
                            padding: 2px 8px;
                            font-size: 12px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 20px;
                            max-height: 20px;
                        }
                        QPushButton:hover {
                            background-color: #009933;
                        }
                    """
                    
                    buy_button.setStyleSheet(buy_button_style)
                    sell_button.setStyleSheet(sell_button_style)
                    
                    # 保存当前tick的信息
                    current_symbol = tick.symbol
                    current_exchange = tick.exchange.value
                    
                    # 使用functools.partial来正确绑定参数
                    buy_button.clicked.connect(
                        partial(self.on_quick_trade, current_symbol, current_exchange, tick.last_price, True)
                    )
                    sell_button.clicked.connect(
                        partial(self.on_quick_trade, current_symbol, current_exchange, tick.last_price, False)
                    )
                    
                    layout.addWidget(buy_button)
                    layout.addWidget(sell_button)
                    layout.setContentsMargins(2, 2, 2, 2)
                    layout.setSpacing(4)
                    
                    self.tick_table.setCellWidget(row, 15, trading_widget)
                
                if not self.tick_table.cellWidget(row, 16):
                    # 退订按钮
                    unsubscribe_button = QtWidgets.QPushButton("退订")
                    unsubscribe_button.setStyleSheet("""
                        QPushButton {
                            color: white;
                            background-color: #ff4d4d;
                            border: none;
                            padding: 2px 8px;
                            font-size: 12px;
                            min-width: 40px;
                            max-width: 40px;
                        }
                        QPushButton:hover {
                            background-color: #ff3333;
                        }
                        QPushButton:pressed {
                            background-color: #cc0000;
                        }
                    """)
                    # 使用functools.partial来正确绑定参数
                    unsubscribe_button.clicked.connect(
                        partial(self.unsubscribe_contract, tick.vt_symbol, row)
                    )
                    self.tick_table.setCellWidget(row, 16, unsubscribe_button)
        
        except Exception as e:
            log_manager.log(f"[MarketMonitor] Error in update_tick_table: {str(e)}")
            import traceback
            log_manager.log(f"[MarketMonitor] Traceback: {traceback.format_exc()}")

    def _update_tick_row(self, row: int, tick: TickData) -> None:
        """更新特定行的数据"""
        log_manager.log(f"[MarketMonitor] _update_tick_row: Updating row {row} for {tick.vt_symbol}")
        self.tick_table.setItem(row, 0, QtWidgets.QTableWidgetItem(tick.symbol))
        self.tick_table.setItem(row, 1, QtWidgets.QTableWidgetItem(tick.exchange.value))
        
        contract = self.contracts.get(tick.vt_symbol)
        contract_name = contract.name if contract else tick.symbol
        self.tick_table.setItem(row, 2, QtWidgets.QTableWidgetItem(contract_name))
        
        self.tick_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(tick.last_price)))
        self.tick_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(tick.volume)))
        self.tick_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(tick.open_price)))
        self.tick_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(tick.high_price)))
        self.tick_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(tick.low_price)))
        self.tick_table.setItem(row, 8, QtWidgets.QTableWidgetItem(str(tick.bid_price_1)))
        self.tick_table.setItem(row, 9, QtWidgets.QTableWidgetItem(str(tick.bid_volume_1)))
        self.tick_table.setItem(row, 10, QtWidgets.QTableWidgetItem(str(tick.ask_price_1)))
        self.tick_table.setItem(row, 11, QtWidgets.QTableWidgetItem(str(tick.ask_volume_1)))
        self.tick_table.setItem(row, 12, QtWidgets.QTableWidgetItem(str(tick.datetime)))
        self.tick_table.setItem(row, 13, QtWidgets.QTableWidgetItem(tick.gateway_name))

        self._create_buttons(row, tick.vt_symbol)

    def _create_placeholder_row(self, row: int, vt_symbol: str) -> None:
        """创建等待数据的占位行"""
        log_manager.log(f"[MarketMonitor] _create_placeholder_row: Creating placeholder for {vt_symbol} at row {row}")
        symbol, exchange = vt_symbol.split('.')
        self.tick_table.setItem(row, 0, QtWidgets.QTableWidgetItem(symbol))
        self.tick_table.setItem(row, 1, QtWidgets.QTableWidgetItem(exchange))
        self.tick_table.setItem(row, 2, QtWidgets.QTableWidgetItem("加载中..."))
        for col in range(3, 14):
            self.tick_table.setItem(row, col, QtWidgets.QTableWidgetItem("--"))
        
        self._create_buttons(row, vt_symbol)

    def _create_buttons(self, row: int, vt_symbol: str) -> None:
        """创建K线图、交易和退订按钮"""
        # K线图按钮
        if not self.tick_table.cellWidget(row, 14):
            chart_button = QtWidgets.QPushButton("K线")
            chart_button.clicked.connect(partial(self.show_chart_from_button, vt_symbol))
            self.tick_table.setCellWidget(row, 14, chart_button)

        # 快速下单按钮
        if not self.tick_table.cellWidget(row, 15):
            trading_widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(trading_widget)
            buy_button = QtWidgets.QPushButton("买")
            sell_button = QtWidgets.QPushButton("卖")
            buy_button.setStyleSheet("color: white; background-color: #ff4d4d;")
            sell_button.setStyleSheet("color: white; background-color: #00b33c;")
            
            symbol, exchange = vt_symbol.split('.')
            buy_button.clicked.connect(partial(self.on_quick_trade, symbol, exchange, 0.0, True))
            sell_button.clicked.connect(partial(self.on_quick_trade, symbol, exchange, 0.0, False))
            
            layout.addWidget(buy_button)
            layout.addWidget(sell_button)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(4)
            self.tick_table.setCellWidget(row, 15, trading_widget)

        # 退订按钮
        if not self.tick_table.cellWidget(row, 16):
            unsubscribe_button = QtWidgets.QPushButton("退订")
            unsubscribe_button.setStyleSheet("color: white; background-color: #ff4d4d;")
            unsubscribe_button.clicked.connect(partial(self.unsubscribe_contract, vt_symbol, row))
            self.tick_table.setCellWidget(row, 16, unsubscribe_button)

    def _set_price_color(self, item: QtWidgets.QTableWidgetItem, price: float, pre_close: float) -> None:
        """设置价格颜色"""
        if not pre_close:  # 如果没有收价，不设置颜色
            return
        
        if price > pre_close:  # 上涨显示红色
            item.setForeground(QtCore.Qt.red)
        elif price < pre_close:  # 下跌显示绿色
            item.setForeground(QtCore.Qt.green)

    def _get_contract_name(self, tick: TickData) -> str:
        """获取合约名称"""
        vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
        contract = self.contracts.get(vt_symbol)
        return contract.name if contract else tick.symbol

    def query_contracts(self) -> None:
        """查询合约"""
        try:
            # print("[DEBUG] MarketMonitor: 开始查询合约...")
            self.contract_table.clearContents()
            self.contract_table.setRowCount(0)
            search_text = self.search_line.text().strip().upper()
            
            # print("[DEBUG] MarketMonitor: 正在获取所有合约...")
            contracts = list(self.main_engine.get_all_contracts())
            # print(f"[DEBUG] MarketMonitor: 查询到 {len(contracts)} 个合约")
            
            if not contracts:
                # print("[DEBUG] MarketMonitor: 主引擎未返回合约，使用本地缓存...")
                try:
                    contracts = list(self.main_engine.contracts.values())
                    # print(f"[DEBUG] MarketMonitor: 从主引擎合约字典获取 {len(contracts)} 个合约")
                except AttributeError:
                    contracts = list(self.main_engine.get_all_contracts())
                    # print(f"[DEBUG] MarketMonitor: 从主引擎get_all_contracts获取 {len(contracts)} 个合约")
            
            if not contracts:
                # print("[DEBUG] MarketMonitor: 仍然没有合约，检查网关...")
                # 直接从网关获取
                gateway = self.main_engine.get_gateway(self.gateway_name)
                if gateway and hasattr(gateway, 'get_all_contracts'):
                    contracts = gateway.get_all_contracts()
                    # print(f"[DEBUG] MarketMonitor: 从网关获取 {len(contracts)} 个合约")
                    
                    # 注册到主引擎和本地缓存
                    for contract in contracts:
                        try:
                            if hasattr(self.main_engine, 'contracts'):
                                self.main_engine.contracts[contract.vt_symbol] = contract
                        except AttributeError:
                            pass  # 主引擎可能使用内部管理
                        self.contracts[contract.vt_symbol] = contract
            
            if not contracts:
                # print("[ERROR] MarketMonitor: 无法获取任何合约")
                return
            
            # print("[DEBUG] MarketMonitor: 开始添加合约到表格...")
            
            # 预先设置表格行数，避免频繁插入
            self.contract_table.setRowCount(len(contracts))
            
            # 禁用表格排序，提高性能
            self.contract_table.setSortingEnabled(False)
            
            # 暂停界面更新
            self.contract_table.setUpdatesEnabled(False)
            
            # 批量处理合约
            for row, contract in enumerate(contracts):
                self.contracts[contract.vt_symbol] = contract
                
                # 设置合约信息
                self.contract_table.setItem(row, 0, QtWidgets.QTableWidgetItem(contract.vt_symbol))
                self.contract_table.setItem(row, 1, QtWidgets.QTableWidgetItem(contract.symbol))
                self.contract_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(contract.exchange)))
                self.contract_table.setItem(row, 3, QtWidgets.QTableWidgetItem(contract.name))
                self.contract_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(contract.product)))
                self.contract_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(contract.size)))
                self.contract_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(contract.pricetick)))
                self.contract_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(contract.min_volume)))
                
                # 创建订阅按钮
                subscribe_button = QtWidgets.QPushButton("订阅")
                subscribe_button.setStyleSheet("""
                    QPushButton {
                        color: white;
                        background-color: #4CAF50;
                        border: none;
                        padding: 2px 8px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                    }
                """)
                subscribe_button.clicked.connect(
                    lambda checked, c=contract: self.subscribe_contract(c)
                )
                self.contract_table.setCellWidget(row, 8, subscribe_button)
            
            # 恢复界面更新
            self.contract_table.setUpdatesEnabled(True)
            
            # 恢复表格排序
            self.contract_table.setSortingEnabled(True)
            
            # print(f"[DEBUG] MarketMonitor: 合约信息加载完成，共 {len(contracts)} 个合约")
            
            # 如果查询到合约，则开始订阅
            if contracts:
                # print("[DEBUG] MarketMonitor: 开始订阅已保存的合约...")
                self.load_and_subscribe_saved_contracts()
            
        except Exception as e:
            print(f"[DEBUG] MarketMonitor: 查询合约出错: {str(e)}")
            import traceback
            print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
            
            # 过滤合约
            if search_text:
                print(f"正在过滤合约，搜索文本: {search_text}")
                contracts = [c for c in contracts if search_text in c.symbol.upper()]
                print(f"过滤后剩余 {len(contracts)} 个合约")
            
            print("开始添加合约到表格...")
            
            # 预先设置表格行数，避免频繁插入
            self.contract_table.setRowCount(len(contracts))
            
            # 禁用表格排序，提高性能
            self.contract_table.setSortingEnabled(False)
            
            # 暂停界面更新
            self.contract_table.setUpdatesEnabled(False)
            
            # 批量处理合约，每500个合约为一批
            BATCH_SIZE = 500
            for i in range(0, len(contracts), BATCH_SIZE):
                batch = contracts[i:i + BATCH_SIZE]
                print(f"正在处理第 {i}-{i+len(batch)}/{len(contracts)} 个合约...")
                
                # 处理这一批合约
                for j, contract in enumerate(batch):
                    row = i + j
                    self.contracts[contract.vt_symbol] = contract
                    
                    # 设置合约信息
                    self.contract_table.setItem(row, 0, QtWidgets.QTableWidgetItem(contract.vt_symbol))
                    self.contract_table.setItem(row, 1, QtWidgets.QTableWidgetItem(contract.symbol))
                    self.contract_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(contract.exchange)))
                    self.contract_table.setItem(row, 3, QtWidgets.QTableWidgetItem(contract.name))
                    self.contract_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(contract.product)))
                    self.contract_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(contract.size)))
                    self.contract_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(contract.pricetick)))
                    self.contract_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(contract.min_volume)))
                    
                    # 创建订阅按钮
                    subscribe_button = QtWidgets.QPushButton("订阅")
                    subscribe_button.setStyleSheet("""
                        QPushButton {
                            color: white;
                            background-color: #4CAF50;
                            border: none;
                            padding: 2px 8px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                        QPushButton:pressed {
                            background-color: #3d8b40;
                        }
                    """)
                    subscribe_button.clicked.connect(
                        lambda checked, c=contract: self.subscribe_contract(c)
                    )
                    self.contract_table.setCellWidget(row, 8, subscribe_button)
                
                # 每批次处理完后，让界面有机会响应
                QtWidgets.QApplication.processEvents()
            
            # 恢复界面更新
            self.contract_table.setUpdatesEnabled(True)
            
            # 恢复表格排序
            self.contract_table.setSortingEnabled(True)
            
            print(f"合约信息加载完成，共 {len(contracts)} 个合约")
            
            # 如果查询到合约，则开始订阅
            if contracts:
                print("开始订阅已保存的合约...")
                self.load_and_subscribe_saved_contracts()
            
        except Exception as e:
            print(f"查询合约出错: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            
            # 过滤合约
            if search_text:
                print(f"正在过滤合约，搜索文本: {search_text}")
                contracts = [c for c in contracts if search_text in c.symbol.upper()]
                print(f"过滤后剩余 {len(contracts)} 个合约")
            
            print("开始添加合约到表格...")
            
            # 预先设置表格行数，避免频繁插入
            self.contract_table.setRowCount(len(contracts))
            
            # 禁用表格排序，提高性能
            self.contract_table.setSortingEnabled(False)
            
            # 暂停界面更新
            self.contract_table.setUpdatesEnabled(False)
            
            # 批量处理���约，每500个合约为一批
            BATCH_SIZE = 500
            for i in range(0, len(contracts), BATCH_SIZE):
                batch = contracts[i:i + BATCH_SIZE]
                print(f"正在处理第 {i}-{i+len(batch)}/{len(contracts)} 个合约...")
                
                # 处理这一批合约
                for j, contract in enumerate(batch):
                    row = i + j
                    self.contracts[contract.vt_symbol] = contract
                    
                    # 设置合约信息
                    self.contract_table.setItem(row, 0, QtWidgets.QTableWidgetItem(contract.vt_symbol))
                    self.contract_table.setItem(row, 1, QtWidgets.QTableWidgetItem(contract.symbol))
                    self.contract_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(contract.exchange)))
                    self.contract_table.setItem(row, 3, QtWidgets.QTableWidgetItem(contract.name))
                    self.contract_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(contract.product)))
                    self.contract_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(contract.size)))
                    self.contract_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(contract.pricetick)))
                    self.contract_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(contract.min_volume)))
                    
                    # 创建订阅按钮
                    subscribe_button = QtWidgets.QPushButton("订阅")
                    subscribe_button.setStyleSheet("""
                        QPushButton {
                            color: white;
                            background-color: #4CAF50;
                            border: none;
                            padding: 2px 8px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                        QPushButton:pressed {
                            background-color: #3d8b40;
                        }
                    """)
                    subscribe_button.clicked.connect(
                        lambda checked, c=contract: self.subscribe_contract(c)
                    )
                    self.contract_table.setCellWidget(row, 8, subscribe_button)
                
                # 每批次处理完后，让界面有机会响应
                QtWidgets.QApplication.processEvents()
            
            # 恢复界面更新
            self.contract_table.setUpdatesEnabled(True)
            
            # 恢复表格排序
            self.contract_table.setSortingEnabled(True)
            
            print(f"合约信息加载完成，共 {len(contracts)} 个合约")
            
            # 如果查询到合约，则开始订阅
            if contracts:
                print("开始订阅已保存的合约...")
                self.load_and_subscribe_saved_contracts()
            
        except Exception as e:
            print(f"查询合约出错: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")

    def load_and_subscribe_saved_contracts(self) -> None:
        """加载并订阅已保存的合约"""
        print("[DEBUG] load_and_subscribe_saved_contracts: 开始加载已保存的订阅合约")
        saved_symbols = subscribed_symbols.get_symbols()
        print(f"[DEBUG] load_and_subscribe_saved_contracts: 已保存的合约: {saved_symbols}")
        
        if not saved_symbols:
            print("[DEBUG] load_and_subscribe_saved_contracts: 没有找到已保存的订阅合约")
            return
        
        print(f"[DEBUG] load_and_subscribe_saved_contracts: 开始订阅保存的合约: {saved_symbols}")
        
        # 立即执行订阅，不依赖网关状态检查
        print("[DEBUG] load_and_subscribe_saved_contracts: 强制订阅所有有效合约...")
        self._do_subscribe_saved(saved_symbols)
        
        # 添加手动tick推送启动
        print("[DEBUG] load_and_subscribe_saved_contracts: 启动手动tick推送...")
        self.start_tick_pushing()
    
    def start_tick_pushing(self):
        """启动tick推送"""
        # log_manager.log(f"[MarketMonitor] Attempting to start tick pushing on gateway: {self.gateway_name}")
        try:
            gateway = self.main_engine.get_gateway(self.gateway_name)
            # print(f"[DEBUG] load_and_subscribe_saved_contracts: 获取网关: {gateway}")
            
            # 处理mock模式下的网关结构
            actual_gateway = gateway
            if hasattr(gateway, 'gateway') and gateway.gateway:
                # MockEngine -> MockGateway 的情况
                actual_gateway = gateway.gateway
                # log_manager.log(f"[MarketMonitor] Using gateway.gateway: {actual_gateway}")
            
            if actual_gateway and hasattr(actual_gateway, 'start_tick_pushing'):
                # log_manager.log(f"[MarketMonitor] Found gateway '{self.gateway_name}'. Calling its start_tick_pushing method.")
                actual_gateway.start_tick_pushing()
                # log_manager.log("[MarketMonitor] Tick pushing successfully initiated on gateway.")
            else:
                # log_manager.log(f"[MarketMonitor] Gateway '{self.gateway_name}' not found or lacks start_tick_pushing method.")
                pass
        except Exception as e:
            # log_manager.log(f"[MarketMonitor] Error starting tick pushing: {e}")
            pass

    def _do_subscribe_saved(self, saved_symbols: set) -> None:
        """执行订阅保存合约"""
        try:
            # log_manager.log(f"开始订阅保存的合约，数量: {len(saved_symbols)}")
            # log_manager.log(f"具体合约: {saved_symbols}")
            
            # 检查是否有行情连接
            gateway = self.main_engine.get_gateway(self.gateway_name)
            if not gateway or not hasattr(gateway, 'md_api'):
                # log_manager.log("行情接口未连接")
                return
            
            # 打印所有可用合约
            all_contracts = list(self.main_engine.get_all_contracts())
            # log_manager.log(f"主引擎共有 {len(all_contracts)} 个合约")
            # for contract in all_contracts[:5]:  # 打印前5个
            #     log_manager.log(f"  可用合约: {contract.vt_symbol}")
            
            # 过滤掉无效的合约
            valid_symbols = set()
            invalid_symbols = set()
            
            for vt_symbol in saved_symbols:
                contract = self.main_engine.get_contract(vt_symbol)
                # log_manager.log(f"检查合约 {vt_symbol}: {contract is not None}")
                if contract:
                    valid_symbols.add(vt_symbol)
                    # log_manager.log(f"  合约有效: {vt_symbol} - {contract.name}")
                else:
                    invalid_symbols.add(vt_symbol)
                    # log_manager.log(f"  合约无效: {vt_symbol}")
            
            # log_manager.log(f"有效合约: {valid_symbols}")
            # log_manager.log(f"无效合约: {invalid_symbols}")
            
            # 订阅有效合约
            subscribed_count = 0
            for vt_symbol in valid_symbols:
                try:
                    symbol, exchange_str = vt_symbol.split('.')
                    exchange = Exchange(exchange_str)
                    
                    req = SubscribeRequest(
                        symbol=symbol,
                        exchange=exchange
                    )
                    # log_manager.log(f"正在订阅: {vt_symbol}")
                    result = self.main_engine.subscribe(req, self.gateway_name)
                    # log_manager.log(f"订阅结果: {vt_symbol} - {result}")
                    subscribed_count += 1
                    
                    # 立即为订阅的合约生成初始tick数据
                    # print(f"[DEBUG] 立即为 {vt_symbol} 生成初始tick数据...")
                    from tests.mock_data.mock_tick_generator import mock_tick_generator
                    tick = mock_tick_generator.generate_tick(symbol, exchange)
                    if tick:
                        # print(f"[DEBUG] 生成了初始tick: {vt_symbol}, 价格: {tick.last_price}")
                        tick_manager.update_tick(tick)
                        # print(f"[DEBUG] 已将tick数据存入tick管理器")
                    
                except Exception as e:
                    # log_manager.log(f"订阅失败 {vt_symbol}: {str(e)}")
                    # import traceback
                    # log_manager.log(f"错误详情: {traceback.format_exc()}")
                    pass
            
            # log_manager.log(f"成功订阅 {subscribed_count} 个合约")
            
            # 同步订阅到网关
            gateway = self.main_engine.get_gateway(self.gateway_name)
            if gateway:
                actual_gateway = gateway.gateway if hasattr(gateway, 'gateway') else gateway
                if hasattr(actual_gateway, 'subscribed_symbols'):
                    for vt_symbol in valid_symbols:
                        actual_gateway.subscribed_symbols.add(vt_symbol)
                    # log_manager.log(f"已同步订阅到网关: {len(actual_gateway.subscribed_symbols)} 个合约")
            
            # 移除无效合约
            if invalid_symbols:
                for symbol in invalid_symbols:
                    subscribed_symbols.remove(symbol)
                # log_manager.log(f"移除无效合约: {invalid_symbols}")
                # log_manager.log(f"最终订阅合约: {subscribed_symbols.get_symbols()}")
            
            # 保存最终订阅列表
            subscribed_symbols.save()
            
        except Exception as e:
            # log_manager.log(f"订阅合约时发生错误: {str(e)}")
            # import traceback
            # log_manager.log(f"错误详情: {traceback.format_exc()}")
            pass

    def subscribe_selected(self) -> None:
        """订阅选中的合约"""
        selected_rows = self.contract_table.selectedItems()
        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                self,
                "订阅失",
                "请先选择要订阅合约",
                QtWidgets.QMessageBox.Ok
            )
            return
            
        # 取选中合约
        row = self.contract_table.currentRow()
        vt_symbol = self.contract_table.item(row, 0).text()
        
        # 检查是否已经订阅
        if vt_symbol in subscribed_symbols.get_symbols():
            log_manager.log(f"合约已订阅：{vt_symbol}")
            return

        # 从已存储合约信息中获取合对象
        contract = self.contracts.get(vt_symbol)
        if not contract:
            QtWidgets.QMessageBox.warning(
                self,
                "订阅失败",
                f"找不到合约信息：{vt_symbol}",
                QtWidgets.QMessageBox.Ok
            )
            return
        
        try:
            # 创建订阅请求
            req = SubscribeRequest(
                symbol=contract.symbol,
                exchange=contract.exchange
            )
            
            # 订阅合约
            self.main_engine.subscribe(req, self.gateway_name)
            
            # 保存订阅信息到配置文件
            log_manager.log(f"正在订阅合约：{vt_symbol}")
            subscribed_symbols.add(vt_symbol)
            log_manager.log(f"订阅成功：{vt_symbol}")
            
        except Exception as e:
            log_manager.log(f"订阅失败：{str(e)}")
            QtWidgets.QMessageBox.warning(
                self,
                "订阅失",
                f"订阅合约失败：{str(e)}",
                QtWidgets.QMessageBox.Ok
            )
        
    def on_contract_clicked(self, row: int, column: int) -> None:
        """处理合约点击事件"""
        try:
            if row < 0 or column < 0:
                return
            
            item = self.contract_table.item(row, 0)
            if not item:
                return
            
            vt_symbol = item.text()
            if not vt_symbol:
                return
            
            # 获取合约信息
            contract = self.contracts.get(vt_symbol)
            if not contract:
                log_manager.log(f"未找到合约信息：{vt_symbol}")
                QtWidgets.QMessageBox.warning(
                    self,
                    "提示",
                    f"未找到合约信息：{vt_symbol}",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            # 检查是否已订阅
            if vt_symbol not in subscribed_symbols.get_symbols():
                # 自动订阅合约
                req = SubscribeRequest(
                    symbol=contract.symbol,
                    exchange=contract.exchange
                )
                self.main_engine.subscribe(req, self.gateway_name)
                subscribed_symbols.add(vt_symbol)
                log_manager.log(f"自动订阅合约：{vt_symbol}")
                
                # 立即更新交易组件（即使还没有行情数据）
                if self.trading_widget:
                    log_manager.log(f"交易组件存在：{self.trading_widget}")
                    if hasattr(self.trading_widget, 'set_symbol_info'):
                        log_manager.log(f"交易组件有set_symbol_info方法")
                        self.trading_widget.set_symbol_info(
                            exchange=contract.exchange.value,
                            symbol=contract.symbol,
                            price=None
                        )
                        log_manager.log(f"已更新交易组件合约信息：{vt_symbol}")
                
                # 等待1秒后收到行情数据再显示图表
                QtCore.QTimer.singleShot(1000, lambda: self.show_chart(contract))
                return
            
            # 获取最新价格
            tick = tick_manager.get_tick(vt_symbol)
            current_price = tick.last_price if tick else None
            
            # 更新交易组件中的合约信息
            if self.trading_widget:
                log_manager.log(f"交易组件存在：{self.trading_widget}")
                if hasattr(self.trading_widget, 'set_symbol_info'):
                    log_manager.log(f"交易组件有set_symbol_info方法")
                    self.trading_widget.set_symbol_info(
                        exchange=contract.exchange.value,
                        symbol=contract.symbol,
                        price=current_price
                    )
                    log_manager.log(f"已更新交易组件合约信息：{vt_symbol}，价格：{current_price}")
                else:
                    log_manager.log(f"交易组件没有set_symbol_info方法")
            else:
                log_manager.log(f"交易组件不存在")
            
            # 显示图表
            self.show_chart(contract)
            
        except Exception as e:
            log_manager.log(f"处理合约点击事件出错：{str(e)}")
            import traceback
            log_manager.log(f"错误详情：{traceback.format_exc()}")

    def show_chart(self, contract: ContractData) -> None:
        """显示图表"""
        try:
            log_manager.log(f"准备显示图表：{contract.vt_symbol}")
            
            # 创建并显示期货窗口
            chart_window = FuturesChartWindow(
                main_engine=self.main_engine,
                event_engine=self.event_engine,
                contract=contract
            )
            
            # 设置窗口标题
            chart_window.setWindowTitle(f"{contract.symbol} - {contract.name} - 期货图表")
            
            # 调整窗口大小
            chart_window.resize(1200, 800)
            
            # 计算主窗口中心
            center = self.window().geometry().center()
            
            # 计算图表窗口的位置使其居中显示
            chart_geometry = chart_window.frameGeometry()
            chart_geometry.moveCenter(center)
            chart_window.move(chart_geometry.topLeft())
            
            # 显示图表窗口
            chart_window.show()
            chart_window.activateWindow()
            
            log_manager.log(f"已显示图：{contract.vt_symbol}")
            
        except Exception as e:
            log_manager.log(f"显示图表失败：{str(e)}")
            import traceback
            log_manager.log(f"错误详情：{traceback.format_exc()}")
        
    def on_tick_clicked(self, row: int, column: int) -> None:
        """处理行情表格双击事件"""
        try:
            # 添加调试信息
            log_manager.log(f"双击事件触发 - 行：{row}，列：{column}")
            
            # 检查行是否有效
            if row < 0 or row >= self.tick_table.rowCount():
                log_manager.log(f"无效的行索引：{row}")
                return
            
            # 获取合约代码和交易所
            symbol_item = self.tick_table.item(row, 0)
            exchange_item = self.tick_table.item(row, 1)
            if not symbol_item or not exchange_item:
                log_manager.log(f"第{row}行数据不完整")
                return
                
            symbol = symbol_item.text()  # 获取合约代码
            exchange = exchange_item.text()  # 获取交易所
            vt_symbol = f"{symbol}.{exchange}"  # 构造完整的vt_symbol
            log_manager.log(f"双击行情表格：{symbol}，交易所：{exchange}，完整vt_symbol：{vt_symbol}")
            
            # 获取合约信息
            contract = self.contracts.get(vt_symbol)
            if not contract:
                log_manager.log(f"未找到合约信息：{vt_symbol}")
                log_manager.log(f"当前合约列表：{list(self.contracts.keys())}")
                return
            
            # 获取最新价格
            tick = self.main_engine.get_tick(vt_symbol)
            current_price = tick.last_price if tick else None
            log_manager.log(f"获取到价格：{current_price}")
            
            # 更新交易组件中的合约信息
            if self.trading_widget:
                log_manager.log(f"交易组件存在：{self.trading_widget}")
                if hasattr(self.trading_widget, 'set_symbol_info'):
                    log_manager.log(f"交易组件有set_symbol_info方法")
                    self.trading_widget.set_symbol_info(
                        exchange=contract.exchange.value,
                        symbol=contract.symbol,
                        price=current_price
                    )
                    log_manager.log(f"已更新交易组件合约信息：{vt_symbol}，价格：{current_price}")
                else:
                    log_manager.log(f"交易组件没有set_symbol_info方法")
            else:
                log_manager.log(f"交易组件不存在")
            
            # 发出合约选中信号
            log_manager.log(f"准备发送合约选中信号：{vt_symbol}")
            self.contract_selected.emit(contract)
            log_manager.log(f"已发送合约选中信号：{vt_symbol}")
            
        except Exception as e:
            log_manager.log(f"处理行情表格双击事件出错：{str(e)}")
            import traceback
            log_manager.log(f"错误详情：{traceback.format_exc()}")
        
    def update_position_pnl(self, vt_symbol: str, last_price: float) -> None:
        """更新持仓盈亏"""
        try:
            # 获取持仓数据
            position = self.main_engine.get_position(vt_symbol)
            if position:
                # 计算持仓盈亏
                if position.direction == Direction.LONG:
                    pnl = (last_price - position.price) * position.volume * position.contract_multiplier
                else:
                    pnl = (position.price - last_price) * position.volume * position.contract_multiplier
                    
                # 更新持仓数据
                position.pnl = pnl
                position.last_price = last_price
                
                # 更新持仓表格
                self.update_position_table()
                
                log_manager.log(f"更新持仓盈亏：{vt_symbol} - 最新价：{last_price:.2f} - 盈亏：{pnl:.2f}")
                
        except Exception as e:
            log_manager.log(f"更新持仓盈亏失败：{str(e)}")
        
    def update_position_table(self) -> None:
        """更新持仓表格"""
        try:
            self.position_table.clearContents()
            positions = self.main_engine.get_all_positions()
            self.position_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                # 合约代码
                self.position_table.setItem(row, 0, 
                    QtWidgets.QTableWidgetItem(position.vt_symbol))
                
                # 方向
                direction_text = "多" if position.direction == Direction.LONG else "空"
                direction_item = QtWidgets.QTableWidgetItem(direction_text)
                direction_item.setForeground(
                    QtCore.Qt.red if position.direction == Direction.LONG else QtCore.Qt.green
                )
                self.position_table.setItem(row, 1, direction_item)
                
                # 持仓量
                self.position_table.setItem(row, 2, 
                    QtWidgets.QTableWidgetItem(str(position.volume)))
                
                # 冻结
                self.position_table.setItem(row, 3, 
                    QtWidgets.QTableWidgetItem(str(position.frozen)))
                
                # 昨仓
                self.position_table.setItem(row, 4, 
                    QtWidgets.QTableWidgetItem(str(position.yd_volume)))
                
                # 开仓均价
                self.position_table.setItem(row, 5, 
                    QtWidgets.QTableWidgetItem(f"{position.price:.2f}"))
                
                # 最新价
                if position.last_price:
                    self.position_table.setItem(row, 6, 
                        QtWidgets.QTableWidgetItem(f"{position.last_price:.2f}"))
                
                # 持仓盈亏
                if position.pnl:
                    pnl_item = QtWidgets.QTableWidgetItem(f"{position.pnl:.2f}")
                    pnl_item.setForeground(
                        QtCore.Qt.red if position.pnl > 0 else QtCore.Qt.green
                    )
                    self.position_table.setItem(row, 7, pnl_item)
                
                # 保证金
                self.position_table.setItem(row, 8, 
                    QtWidgets.QTableWidgetItem(f"{position.margin:.2f}"))
                
                # 交易所
                self.position_table.setItem(row, 9, 
                    QtWidgets.QTableWidgetItem(position.exchange.value))
                
        except Exception as e:
            log_manager.log(f"更新持仓表格失败：{str(e)}")
        
    def filter_contracts(self, text: str) -> None:
        """过滤合约"""
        for row in range(self.contract_table.rowCount()):
            should_show = False
            for col in range(self.contract_table.columnCount()):
                item = self.contract_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    should_show = True
                    break
            self.contract_table.setRowHidden(row, not should_show)
        
    def export_data(self) -> None:
        """导出数据到CSV"""
        try:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "导出数据", "", "CSV(*.csv)")
            if not path:
                return
            
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                headers = []
                for i in range(self.tick_table.columnCount()):
                    headers.append(self.tick_table.horizontalHeaderItem(i).text())
                writer.writerow(headers)
                
                # 写入数据
                for row in range(self.tick_table.rowCount()):
                    row_data = []
                    for col in range(self.tick_table.columnCount()):
                        item = self.tick_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                
            log_manager.log(f"数据已导出到：{path}")
            
        except Exception as e:
            log_manager.log(f"导出数据失败：{str(e)}")
        
    def close(self) -> None:
        """关闭窗口"""
        try:
            # 取消事件监听
            self.event_engine.unregister(EVENT_TICK, self.signal_tick.emit)
            self.event_engine.unregister(EVENT_CONTRACT, self.process_contract_event)
            self.event_engine.unregister(EVENT_LOG, self.process_log_event)
            
            # 停止定时器
            if self.timer:
                self.timer.stop()
                
        except Exception as e:
            log_manager.log(f"关闭窗口失败：{str(e)}")

    def reset_retry_count(self) -> None:
        """重置重试计数"""
        self.retry_count = 0
        
    def show_context_menu(self, pos) -> None:
        """显示右键菜单"""
        try:
            # 获取当前选中的行
            row = self.tick_table.rowAt(pos.y())
            if row < 0:
                return
            
            # 创建菜单
            menu = QtWidgets.QMenu(self)
            
            # 添加除操作
            delete_action = menu.addAction("取消订阅")
            delete_action.triggered.connect(lambda: self.unsubscribe_symbol(row))
            
            # 在鼠标位置显示菜单
            menu.exec_(self.tick_table.viewport().mapToGlobal(pos))
            
        except Exception as e:
            log_manager.log(f"显示右键菜单失败：{str(e)}")

    def unsubscribe_symbol(self, row: int) -> None:
        """取消订阅合约"""
        try:
            # 获取合约代码
            vt_symbol = self.tick_table.item(row, 0).text()
            
            # 确认对话框
            reply = QtWidgets.QMessageBox.question(
                self,
                "取消订阅",
                f"确认取消订阅 {vt_symbol} ？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                # 从订阅列表中移除
                subscribed_symbols.remove(vt_symbol)
                
                # 从tick管理器中除数据
                tick_manager.remove_tick(vt_symbol)
                
                # 更新界面
                self.update_tick_table()
                
                log_manager.log(f"已取消订阅：{vt_symbol}")
                
                # 显示提示信息
                QtWidgets.QMessageBox.information(
                    self,
                    "提示",
                    f"已��消订阅 {vt_symbol}",
                    QtWidgets.QMessageBox.Ok
                )
                
        except Exception as e:
            log_manager.log(f"取消订阅失败：{str(e)}")
            QtWidgets.QMessageBox.warning(
                self,
                "错误",
                f"取消订阅失败：{str(e)}",
                QtWidgets.QMessageBox.Ok
            )
        
    def show_chart_from_button(self, vt_symbol: str) -> None:
        """从按钮显示图表"""
        try:
            # 获取合约信息
            contract = self.contracts.get(vt_symbol)
            if not contract:
                QtWidgets.QMessageBox.warning(
                    self,
                    "提示",
                    f"未找到合约信息：{vt_symbol}",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            # 显示图表
            self.show_chart(contract)
            
        except Exception as e:
            log_manager.log(f"显示图表失败：{str(e)}")
        
    def on_quick_trade(self, symbol: str, exchange: str, price: float, is_buy: bool) -> None:
        """
        处理快速下单
        """
        try:
            # 检查是否有交易组件引用
            if self.trading_widget:
                # 确保交易所代码是正确的格式
                exchange = exchange.upper()  # 转换为大写
                
                # 记录操作
                log_manager.log(f"快速下单 - 交易所：{exchange}，合约：{symbol}，价格：{price}，方向：{'买入' if is_buy else '卖出'}")
                
                # 直接使用交易组件引用
                self.trading_widget.set_symbol_info(exchange, symbol, price)
                
                # 设置买卖方向
                direction_index = 1 if is_buy else 0  # 0=空, 1=多
                self.trading_widget.direction_combo.setCurrentIndex(direction_index)
            else:
                log_manager.log("未找到交易组件引用")
                
        except Exception as e:
            log_manager.log(f"快速下单失败：{str(e)}")
        
    def add_contract_to_table(self, contract: ContractData) -> None:
        """添加合约到表格"""
        # 获取行数
        row = self.contract_table.rowCount()
        self.contract_table.insertRow(row)
        
        # 设置合约信息
        self.contract_table.setItem(row, 0, QtWidgets.QTableWidgetItem(contract.vt_symbol))
        self.contract_table.setItem(row, 1, QtWidgets.QTableWidgetItem(contract.symbol))
        self.contract_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(contract.exchange)))
        self.contract_table.setItem(row, 3, QtWidgets.QTableWidgetItem(contract.name))
        self.contract_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(contract.product)))
        self.contract_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(contract.size)))
        self.contract_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(contract.pricetick)))
        self.contract_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(contract.min_volume)))
        
        # 创建订阅按钮
        subscribe_button = QtWidgets.QPushButton("订阅")
        subscribe_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #4CAF50;
                border: none;
                padding: 2px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        # 使用lambda传递合约信息给订阅函数
        subscribe_button.clicked.connect(
            lambda: self.subscribe_contract(contract)
        )
        self.contract_table.setCellWidget(row, 8, subscribe_button)

    def subscribe_contract(self, contract: ContractData) -> None:
        """订阅合约"""
        try:
            # 创建订阅请求
            req = SubscribeRequest(
                symbol=contract.symbol,
                exchange=contract.exchange
            )
            
            # 发送订阅请求
            self.main_engine.subscribe(req, contract.gateway_name)
            
            # 添加到已订阅列表
            vt_symbol = contract.vt_symbol
            if vt_symbol not in subscribed_symbols.get_symbols():  # 使用 get_symbols() 方法
                subscribed_symbols.add(vt_symbol)  # 使用 add 方法添加
                
                # 加到行情表格
                self.add_tick_to_table(vt_symbol)
                
                # 录日志
                log_manager.log(f"订阅合约成功：{vt_symbol}")
                
                # 显示提示
                QtWidgets.QMessageBox.information(
                    self,
                    "订阅成功",
                    f"已订阅合约：{vt_symbol}",
                    QtWidgets.QMessageBox.Ok
                )
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "提示",
                    f"合约已订阅：{vt_symbol}",
                    QtWidgets.QMessageBox.Ok
                )
                
        except Exception as e:
            log_manager.log(f"订阅合约失败：{str(e)}")
            QtWidgets.QMessageBox.warning(
                self,
                "订阅失败",
                f"订阅失败：{str(e)}",
                QtWidgets.QMessageBox.Ok
            )
        
    def add_tick_to_table(self, vt_symbol: str) -> None:
        """在行情表格中添加新的合约行"""
        try:
            # 获取当前行数
            row = self.tick_table.rowCount()
            self.tick_table.insertRow(row)
            
            # 分解vt_symbol获取合约代码和交易所
            symbol, exchange = vt_symbol.split('.')
            
            # 获取合约信息
            contract = self.contracts.get(vt_symbol)
            contract_name = contract.name if contract else symbol
            
            # 设置基本信息
            self.tick_table.setItem(row, 0, QtWidgets.QTableWidgetItem(symbol))
            self.tick_table.setItem(row, 1, QtWidgets.QTableWidgetItem(exchange))
            self.tick_table.setItem(row, 2, QtWidgets.QTableWidgetItem(contract_name))
            
            # 添加K线图按钮
            chart_button = QtWidgets.QPushButton("K线")
            chart_button.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    padding: 2px 5px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            chart_button.clicked.connect(
                lambda: self.show_chart_from_button(vt_symbol)
            )
            self.tick_table.setCellWidget(row, 14, chart_button)
            
            # 添加快速下单按钮
            trading_widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(trading_widget)
            
            buy_button = QtWidgets.QPushButton("买")
            sell_button = QtWidgets.QPushButton("卖")
            
            # 设置按钮样式
            buy_button_style = """
                QPushButton {
                    color: white;
                    background-color: #ff4d4d;
                    border: none;
                    padding: 2px 8px;
                    font-size: 12px;
                    min-width: 30px;
                    max-width: 30px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #ff3333;
                }
            """
            
            sell_button_style = """
                QPushButton {
                    color: white;
                    background-color: #00b33c;
                    border: none;
                    padding: 2px 8px;
                    font-size: 12px;
                    min-width: 30px;
                    max-width: 30px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #009933;
                }
            """
            
            buy_button.setStyleSheet(buy_button_style)
            sell_button.setStyleSheet(sell_button_style)
            
            # 设置按钮点击事件
            buy_button.clicked.connect(
                lambda: self.on_quick_trade(symbol, exchange, 0.0, True)
            )
            sell_button.clicked.connect(
                lambda: self.on_quick_trade(symbol, exchange, 0.0, False)
            )
            
            layout.addWidget(buy_button)
            layout.addWidget(sell_button)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(4)
            
            self.tick_table.setCellWidget(row, 15, trading_widget)
            
            # 记录日志
            log_manager.log(f"已加合约到行情表格：{vt_symbol}")
            
            # 添加解除订阅按钮
            unsubscribe_button = QtWidgets.QPushButton("退订")
            unsubscribe_button.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: #ff4d4d;
                    border: none;
                    padding: 2px 8px;
                    font-size: 12px;
                    min-width: 40px;
                    max-width: 40px;
                }
                QPushButton:hover {
                    background-color: #ff3333;
                }
                QPushButton:pressed {
                    background-color: #cc0000;
                }
            """)
            unsubscribe_button.clicked.connect(
                lambda: self.unsubscribe_contract(vt_symbol, row)
            )
            self.tick_table.setCellWidget(row, 16, unsubscribe_button)
            
        except Exception as e:
            log_manager.log(f"添加合约到行情表格失败：{str(e)}")
        
    def unsubscribe_contract(self, vt_symbol: str, row: int) -> None:
        """解除订阅合约"""
        try:
            log_manager.log(f"开始解除订阅合约：{vt_symbol}, 行号：{row}")
            
            # 先确认是否要退订
            reply = QtWidgets.QMessageBox.question(
                self,
                "取消订阅",
                f"确认取消订阅 {vt_symbol} ？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.No:
                log_manager.log(f"用户取消退订操作：{vt_symbol}")
                return
            
            # 分解vt_symbol获取合约代码和交��所
            symbol, exchange = vt_symbol.split('.')
            log_manager.log(f"解析合约信息 - 代码：{symbol}, 交易所：{exchange}")
            
            # 检查是否在已订阅列表中
            if vt_symbol in subscribed_symbols.get_symbols():
                log_manager.log(f"从订阅列表中移除：{vt_symbol}")
                subscribed_symbols.remove(vt_symbol)
            else:
                log_manager.log(f"合约不在订阅列表中：{vt_symbol}")
            
            # 检查是否有tick数据
            tick = tick_manager.get_tick(vt_symbol)
            if tick:
                log_manager.log(f"从tick管理器中移除数据：{vt_symbol}, 最新价：{tick.last_price}")
                tick_manager.remove_tick(vt_symbol)
            else:
                log_manager.log(f"未找到tick数据：{vt_symbol}")
            
            # 检查行号是否有效
            if 0 <= row < self.tick_table.rowCount():
                log_manager.log(f"从行情表格中移除第 {row} 行")
                self.tick_table.removeRow(row)
            else:
                log_manager.log(f"无效的行号：{row}, 当前表格行数：{self.tick_table.rowCount()}")
            
            # 记录日志
            log_manager.log(f"已完成解除订阅合约：{vt_symbol}")
            
            # 显示提示
            QtWidgets.QMessageBox.information(
                self,
                "解除订阅成功",
                f"已解除订阅合约：{vt_symbol}",
                QtWidgets.QMessageBox.Ok
            )
            
        except Exception as e:
            error_msg = f"解除订阅失败：{str(e)}"
            log_manager.log(error_msg)
            import traceback
            log_manager.log(f"错误详情：{traceback.format_exc()}")
            QtWidgets.QMessageBox.warning(
                self,
                "解除订阅失败",
                error_msg,
                QtWidgets.QMessageBox.Ok
            )
        