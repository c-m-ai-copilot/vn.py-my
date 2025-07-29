from typing import Dict, List
from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT, EVENT_LOG
from vnpy.trader.object import TickData, ContractData, SubscribeRequest
from vnpy.trader.constant import Exchange
from vnpy.event import Event
from config.subscribed_symbols import subscribed_symbols
from config.tick_data import tick_manager
from config.log_manager import log_manager

class MarketMonitor(QtWidgets.QWidget):
    """行情监控组件"""
    
    signal_tick = QtCore.pyqtSignal(Event)
    signal_login = QtCore.pyqtSignal()  # 添加登录信号
    signal_md_login = QtCore.pyqtSignal()  # 添加行情登录信号
    signal_query = QtCore.pyqtSignal()  # 添加查询信号
    
    def __init__(
        self, 
        main_engine: MainEngine, 
        event_engine: EventEngine, 
        gateway_name: str = "CTP"
    ) -> None:
        super().__init__()
        
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.gateway_name = gateway_name
        self.contracts: Dict[str, ContractData] = {}
        self.retry_count = 0
        
        # 初始化UI
        self.init_ui()
        self.register_event()
        
        # 连接信号
        self.signal_query.connect(self.do_query_contracts)
        
        # 添加定时器定期更新行情
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_tick_table)
        self.timer.start(1000)  # 每秒更新一次

    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle("行情监控")
        
        # 创建主布局
        vbox = QtWidgets.QVBoxLayout()
        
        # 创建合约查询部分
        contract_group = QtWidgets.QGroupBox("合约查询")
        contract_layout = QtWidgets.QVBoxLayout()
        
        # 搜索栏
        search_layout = QtWidgets.QHBoxLayout()
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("输入合约代码查询")
        self.search_button = QtWidgets.QPushButton("查询")
        self.search_button.clicked.connect(self.query_contracts)
        
        search_layout.addWidget(self.search_line)
        search_layout.addWidget(self.search_button)
        
        # 合约列表
        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(8)
        self.contract_table.setHorizontalHeaderLabels([
            "本地代码", "代码", "交易所", "名称",
            "合约类型", "合约数", "价跳动", "最小数量"
        ])
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        
        # 设置列宽
        self.contract_table.setColumnWidth(0, 120)  # 本地代码
        self.contract_table.setColumnWidth(1, 80)   # 代码
        self.contract_table.setColumnWidth(2, 80)   # 交易所
        self.contract_table.setColumnWidth(3, 120)  # 名称
        self.contract_table.setColumnWidth(4, 80)   # 合约类型
        self.contract_table.setColumnWidth(5, 80)   # 合约乘数
        self.contract_table.setColumnWidth(6, 80)   # 价格跳动
        self.contract_table.setColumnWidth(7, 80)   # 最小数量
        
        # 订阅按钮
        button_layout = QtWidgets.QHBoxLayout()
        subscribe_button = QtWidgets.QPushButton("订阅行情")
        subscribe_button.clicked.connect(self.subscribe_selected)
        button_layout.addStretch()
        button_layout.addWidget(subscribe_button)
        
        # 添加到合约查询布局
        contract_layout.addLayout(search_layout)
        contract_layout.addWidget(self.contract_table)
        contract_layout.addLayout(button_layout)
        contract_group.setLayout(contract_layout)
        
        # 行情表
        market_group = QtWidgets.QGroupBox("行情信息")
        market_layout = QtWidgets.QVBoxLayout()
        
        self.tick_table = QtWidgets.QTableWidget()
        self.tick_table.setColumnCount(8)
        self.tick_table.setHorizontalHeaderLabels([
            "合约代码", "最新价", "涨跌幅", "成交量",
            "买价", "买量", "卖价", "卖量"
        ])
        self.tick_table.verticalHeader().setVisible(False)
        self.tick_table.setEditTriggers(self.tick_table.NoEditTriggers)
        
        # 连接双击事件
        self.tick_table.itemDoubleClicked.connect(self.on_tick_table_double_clicked)
        
        market_layout.addWidget(self.tick_table)
        market_group.setLayout(market_layout)
        
        # 添加到主布局
        vbox.addWidget(contract_group)
        vbox.addWidget(market_group)
        self.setLayout(vbox)

    def register_event(self) -> None:
        """注册事件监听"""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        # 添加日志事件监听
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def on_login_success_event(self, event: Event) -> None:
        """处理登录成功事件"""
        log_manager.console_log("收到登录成功事件，发出信号")
        self.signal_login.emit()

    def on_md_login(self) -> None:
        """处理行情登录成功"""
        log_manager.console_log("3秒后开始查询合约信息...")
        # 延迟3秒后执行查询
        QtCore.QTimer.singleShot(3000, self.query_contracts)
        
        log_manager.console_log("5秒后开始订阅已保存的合约...")
        # 等待5秒后开始订阅（确保合约信息已加载）
        QtCore.QTimer.singleShot(5000, self.load_and_subscribe_saved_contracts)

    def process_tick_event(self, event: Event) -> None:
        """处理行情事件"""
        tick = event.data
        vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
        
        # 只处理已订阅的合约
        if vt_symbol in subscribed_symbols.get_symbols():
            # 只在价格变化时输出日志
            tick_manager.update_tick(tick)
            self.update_tick_table()
            
            # 强制更新界面
            QtWidgets.QApplication.processEvents()

    def process_contract_event(self, event: Event) -> None:
        """处理合约事件"""
        contract = event.data
        self.contracts[contract.vt_symbol] = contract

    def process_log_event(self, event: Event) -> None:
        """处理日志事件"""
        log = event.data
        msg = log.msg
        #print(f"process_log_event msg: {msg}")
        
        # 检测结算信息确认成功后等待1分钟再查询合约
        if "结算信息确认成功" in msg:
            log_manager.console_log("检测到结算信息确认成功")
            log_manager.console_log("等待1分钟后开始查询合约信息...")

    def do_query_contracts(self) -> None:
        """执行合约查询"""
        log_manager.console_log("开始查询合约信息...")
        self.query_contracts()
        
        # 如果查询到合约，则开始订阅
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
            self.tick_table.clearContents()
            
            # 获取已订阅的合约列表
            subscribed = subscribed_symbols.get_symbols()
            
            # 从tick管理器获取行情数据
            valid_ticks = []
            need_resubscribe = False  # 添加标志
            
            for vt_symbol in subscribed:
                tick = tick_manager.get_tick(vt_symbol)
                if tick:
                    valid_ticks.append(tick)
                else:
                    # 如果没有行情数据，标记需要重新订阅
                    need_resubscribe = True
            
            # 只在需要时重新订阅，并且只打印一次日志
            if need_resubscribe and self.retry_count < 5:
                self.retry_count += 1
                for vt_symbol in subscribed:
                    if not tick_manager.get_tick(vt_symbol):
                        symbol, exchange_str = vt_symbol.split('.')
                        exchange = Exchange(exchange_str)
                        req = SubscribeRequest(
                            symbol=symbol,
                            exchange=exchange
                        )
                        self.main_engine.subscribe(req, self.gateway_name)
                log_manager.log(f"重新订阅未收到行情的合约，重试次数: {self.retry_count}")
            
            self.tick_table.setRowCount(len(valid_ticks))
            
            for row, tick in enumerate(valid_ticks):
                vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
                
                # 显示合约代码
                self.tick_table.setItem(row, 0, QtWidgets.QTableWidgetItem(vt_symbol))
                
                # 显示最新价（添加颜色）
                if tick.last_price:
                    price_item = QtWidgets.QTableWidgetItem(f"{tick.last_price:.2f}")
                    if tick.last_price > tick.pre_close:
                        price_item.setForeground(QtCore.Qt.red)
                    elif tick.last_price < tick.pre_close:
                        price_item.setForeground(QtCore.Qt.green)
                    self.tick_table.setItem(row, 1, price_item)
                
                # 显示涨跌幅（添加颜色）
                if tick.pre_close and tick.pre_close != 0:
                    change = (tick.last_price - tick.pre_close) / tick.pre_close * 100
                    change_item = QtWidgets.QTableWidgetItem(f"{change:.2f}%")
                    if change > 0:
                        change_item.setForeground(QtCore.Qt.red)
                    elif change < 0:
                        change_item.setForeground(QtCore.Qt.green)
                    self.tick_table.setItem(row, 2, change_item)
                
                # 显示成交量
                self.tick_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(tick.volume)))
                
                # 显示买卖价格和数量
                if tick.bid_price_1:
                    self.tick_table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{tick.bid_price_1:.2f}"))
                if tick.bid_volume_1:
                    self.tick_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(tick.bid_volume_1)))
                if tick.ask_price_1:
                    self.tick_table.setItem(row, 6, QtWidgets.QTableWidgetItem(f"{tick.ask_price_1:.2f}"))
                if tick.ask_volume_1:
                    self.tick_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(tick.ask_volume_1)))
            
            # 强制更新界面
            self.tick_table.update()
            QtWidgets.QApplication.processEvents()
            
        except Exception as e:
            log_manager.log(f"更新行情表格出错: {str(e)}")

    def query_contracts(self) -> None:
        """查询合约"""
        try:
            self.contract_table.clearContents()
            search_text = self.search_line.text().strip().upper()
            
            # 获取��有合约
            contracts = list(self.main_engine.get_all_contracts())
            log_manager.console_log(f"查询到 {len(contracts)} 个合约")
            
            # 如果没有查询到合约，等待1秒后重试
            if not contracts:
                log_manager.console_log("未查询到合约，1秒后重试...")
                QtCore.QTimer.singleShot(1000, self.query_contracts)
                return
            
            if search_text:
                contracts = [c for c in contracts if search_text in c.symbol.upper()]
            
            # 设置表格行数
            self.contract_table.setRowCount(len(contracts))
            
            # 填充合约信息
            for row, contract in enumerate(contracts):
                self.contracts[contract.vt_symbol] = contract
                self.contract_table.setItem(row, 0, QtWidgets.QTableWidgetItem(contract.vt_symbol))
                self.contract_table.setItem(row, 1, QtWidgets.QTableWidgetItem(contract.symbol))
                self.contract_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(contract.exchange)))
                self.contract_table.setItem(row, 3, QtWidgets.QTableWidgetItem(contract.name))
                self.contract_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(contract.product)))
                self.contract_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(contract.size)))
                self.contract_table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(contract.pricetick)))
                self.contract_table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(contract.min_volume)))
            
            log_manager.console_log(f"合约信息加载完成，共 {len(contracts)} 个合约")
            
            # 如果查询到合约，则开始订阅
            if contracts:
                log_manager.console_log("开始订阅已保存的合约...")
                self.load_and_subscribe_saved_contracts()
            
        except Exception as e:
            log_manager.log(f"查询合约出错: {str(e)}")
            import traceback
            log_manager.log(f"错误详情: {traceback.format_exc()}")

    def load_and_subscribe_saved_contracts(self) -> None:
        """加载并订阅已保存的合约"""
        saved_symbols = subscribed_symbols.get_symbols()
        if not saved_symbols:
            log_manager.log("没有找到已保存的订阅合约")
            return
        
        log_manager.log(f"开始订阅保存的合约: {saved_symbols}")
        # 直接调用订阅方法
        self._do_subscribe_saved(saved_symbols)

    def _do_subscribe_saved(self, saved_symbols: set) -> None:
        """执行订阅保存合约"""
        log_manager.log(f"开始订阅保存的合约，数量: {len(saved_symbols)}")
        
        # 检查是否有行情连接
        gateway = self.main_engine.get_gateway(self.gateway_name)
        if not gateway or not gateway.md_api:
            log_manager.log("行情接口未连接")
            return
        
        for vt_symbol in saved_symbols:
            try:
                symbol, exchange_str = vt_symbol.split('.')
                exchange = Exchange(exchange_str)
                
                # 检查合约信息
                contract = self.main_engine.get_contract(vt_symbol)
                if not contract:
                    log_manager.log(f"未找到合约信息: {vt_symbol}")
                    continue
                
                req = SubscribeRequest(
                    symbol=symbol,
                    exchange=exchange
                )
                self.main_engine.subscribe(req, self.gateway_name)
                log_manager.log(f"已订阅合约: {vt_symbol}")
                
            except Exception as e:
                log_manager.log(f"订阅失败 {vt_symbol}: {str(e)}")
        
        # 如果有未成功订阅的合约稍后重试
        if self.retry_count < 5:  # 最多试5次
            self.retry_count += 1
            QtCore.QTimer.singleShot(5000, lambda: self._do_subscribe_saved(saved_symbols))

    def subscribe_selected(self) -> None:
        """订阅选中的合约"""
        selected_rows = self.contract_table.selectedItems()
        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                self,
                "订阅失败",
                "请先选择要订阅合约",
                QtWidgets.QMessageBox.Ok
            )
            return
            
        # 获取选中合约
        row = self.contract_table.currentRow()
        vt_symbol = self.contract_table.item(row, 0).text()
        
        # 检查是否已经订阅
        if vt_symbol in subscribed_symbols.get_symbols():
            log_manager.log(f"合约已订阅：{vt_symbol}")
            return

        # 从已存储的合约信息中获取合约对象
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
                "订阅失败",
                f"订阅合约失败：{str(e)}",
                QtWidgets.QMessageBox.Ok
            )

    def on_tick_table_double_clicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        """处理行情表格双击事件"""
        try:
            row = item.row()
            vt_symbol = self.tick_table.item(row, 0).text()
            
            # 创建K线图窗口
            from ui.widgets.futures_chart import FuturesChart
            chart_window = QtWidgets.QMainWindow()
            chart_widget = FuturesChart(self.main_engine, self.event_engine)
            chart_window.setCentralWidget(chart_widget)
            chart_window.setWindowTitle(f"K线图 - {vt_symbol}")
            chart_window.resize(1000, 600)
            
            # 设置合约并加载数据
            chart_widget.set_vt_symbol(vt_symbol)
            chart_widget.load_data()
            
            # 显示窗口
            chart_window.show()
            
        except Exception as e:
            log_manager.log(f"打开K线图失败：{str(e)}") 