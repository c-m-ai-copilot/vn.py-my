from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QComboBox,
    QDialog,
    QLineEdit,
    QGridLayout,
    QMessageBox,
    QDoubleValidator,
    QSpinBox
)
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta
from typing import Dict, List
from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.event import (
    EVENT_CTA_LOG,
    EVENT_CTA_STRATEGY,
    EVENT_CTA_STOPORDER
)
from vnpy_ctastrategy import (
    CtaEngine,
    StrategyTemplate,
    StopOrder
)
from vnpy.trader.database import get_database
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import BarData, TickData
from vnpy.trader.utility import load_json, save_json

class CtaManager(QWidget):
    """CTA策略管理组件"""
    signal_log = Qt.pyqtSignal(Event)
    signal_strategy = Qt.pyqtSignal(Event)
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """构造函数"""
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.cta_engine = main_engine.get_engine("CtaStrategy")
        
        # 添加数据库连接
        self.database = get_database()
        
        # 添加配置文件路径
        self.setting_filename = "cta_strategy_setting.json"
        self.data_filename = "cta_strategy_data.json"
        
        self.strategy_loaded = False
        self.strategy_instances: Dict[str, StrategyTemplate] = {}
        
        self.init_ui()
        self.register_event()
        self.load_strategy_settings()
        
    def register_event(self):
        """注册事件监听"""
        self.signal_log.connect(self.process_log_event)
        self.signal_strategy.connect(self.process_strategy_event)
        
        self.event_engine.register(EVENT_CTA_LOG, self.signal_log.emit)
        self.event_engine.register(EVENT_CTA_STRATEGY, self.signal_strategy.emit)
        
        # 添加停止单事件监听
        self.event_engine.register(EVENT_CTA_STOPORDER, self.process_stop_order_event)
        
    def process_log_event(self, event: Event):
        """处理日志事件"""
        msg = event.data
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        row = self.log_widget.rowCount()
        self.log_widget.insertRow(row)
        self.log_widget.setItem(row, 0, QTableWidgetItem(timestamp))
        self.log_widget.setItem(row, 1, QTableWidgetItem(msg))
        self.log_widget.scrollToBottom()
        
    def process_strategy_event(self, event: Event):
        """处理策略事件"""
        data = event.data
        strategy_name = data["strategy_name"]
        
        # 更新策略状态表格
        for row in range(self.strategy_table.rowCount()):
            if self.strategy_table.item(row, 0).text() == strategy_name:
                inited = data["inited"]
                trading = data["trading"]
                
                status = "已初始化" if inited else "未初始化"
                status += " | " + ("交易中" if trading else "停止")
                
                self.strategy_table.setItem(row, 2, QTableWidgetItem(status))
                break
                
    def process_stop_order_event(self, event: Event):
        """处理停止单事件"""
        stop_order: StopOrder = event.data
        
        # 更新停止单表格
        for row in range(self.stop_order_table.rowCount()):
            if self.stop_order_table.item(row, 0).text() == stop_order.stop_orderid:
                if stop_order.status.value == "已撤销" or stop_order.status.value == "已触发":
                    self.stop_order_table.removeRow(row)
                else:
                    self.update_stop_order_row(row, stop_order)
                break
        else:
            if stop_order.status.value not in ["已撤销", "已触发"]:
                self.insert_stop_order_row(stop_order)

    def insert_stop_order_row(self, stop_order: StopOrder):
        """插入停止单数据"""
        row = self.stop_order_table.rowCount()
        self.stop_order_table.insertRow(row)
        self.update_stop_order_row(row, stop_order)

    def update_stop_order_row(self, row: int, stop_order: StopOrder):
        """更新停止单数据"""
        self.stop_order_table.setItem(row, 0, QTableWidgetItem(stop_order.stop_orderid))
        self.stop_order_table.setItem(row, 1, QTableWidgetItem(stop_order.strategy_name))
        self.stop_order_table.setItem(row, 2, QTableWidgetItem(stop_order.vt_symbol))
        self.stop_order_table.setItem(row, 3, QTableWidgetItem(stop_order.direction.value))
        self.stop_order_table.setItem(row, 4, QTableWidgetItem(str(stop_order.price)))
        self.stop_order_table.setItem(row, 5, QTableWidgetItem(str(stop_order.volume)))
        self.stop_order_table.setItem(row, 6, QTableWidgetItem(stop_order.status.value))
        self.stop_order_table.setItem(row, 7, QTableWidgetItem(str(stop_order.stop_price)))

    def load_strategy_settings(self):
        """加载策略配置"""
        self.strategy_loaded = True
        
        # 获取策略类列表
        strategies = self.cta_engine.get_all_strategy_class_names()
        self.strategy_combo.clear()
        self.strategy_combo.addItems(strategies)
        
        # 加载已有策略实例
        for strategy_name in self.cta_engine.strategies:
            self.add_strategy_display(strategy_name)
            
    def add_strategy_display(self, strategy_name: str):
        """添加策略显示"""
        # 获取策略实例
        strategy = self.cta_engine.strategies[strategy_name]
        self.strategy_instances[strategy_name] = strategy
        
        # 创建操作按钮
        init_button = QPushButton("初始化")
        start_button = QPushButton("启动")
        stop_button = QPushButton("停止")
        edit_button = QPushButton("编辑")
        remove_button = QPushButton("移除")
        
        init_button.clicked.connect(lambda: self.init_strategy(strategy_name))
        start_button.clicked.connect(lambda: self.start_strategy(strategy_name))
        stop_button.clicked.connect(lambda: self.stop_strategy(strategy_name))
        edit_button.clicked.connect(lambda: self.edit_strategy(strategy_name))
        remove_button.clicked.connect(lambda: self.remove_strategy(strategy_name))
        
        # 创建按钮布局
        button_widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout.addWidget(init_button)
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(remove_button)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_widget.setLayout(button_layout)
        
        # 添加策略信息到表格
        row = self.strategy_table.rowCount()
        self.strategy_table.insertRow(row)
        self.strategy_table.setItem(row, 0, QTableWidgetItem(strategy_name))
        self.strategy_table.setItem(row, 1, QTableWidgetItem(strategy.vt_symbol))
        self.strategy_table.setItem(row, 2, QTableWidgetItem("未初始化"))
        self.strategy_table.setCellWidget(row, 3, button_widget)

    def add_strategy(self):
        """添加策略"""
        dialog = AddStrategyDialog(self.strategy_combo.currentText(), self)
        if dialog.exec_():
            strategy_name = dialog.name_line.text()
            vt_symbol = dialog.symbol_line.text()
            
            if strategy_name in self.strategy_instances:
                QMessageBox.warning(self, "添加失败", "已存在同名的策略实例")
                return
                
            # 创建策略实例
            strategy_class = self.cta_engine.get_strategy_class_by_name(
                self.strategy_combo.currentText()
            )
            self.cta_engine.add_strategy(
                strategy_class,
                strategy_name,
                vt_symbol,
                {}
            )
            self.add_strategy_display(strategy_name)

    def init_strategy(self, strategy_name: str):
        """初始化策略"""
        strategy = self.strategy_instances[strategy_name]
        
        if strategy.inited:
            self.write_log(f"{strategy_name}已经完成初始化，无需重复操作")
            return
            
        # 加载历史数据
        days = 10   # 加载10天数据用于初始化
        if strategy.on_tick:
            data = self.load_tick(strategy.vt_symbol, days)
        else:
            data = self.load_bar(strategy.vt_symbol, days, strategy.interval)
            
        # 初始化策略
        self.cta_engine.init_strategy(strategy_name, data)
        
    def start_strategy(self, strategy_name: str):
        """启动策略"""
        strategy = self.strategy_instances[strategy_name]
        
        if not strategy.inited:
            self.write_log(f"策略{strategy_name}尚未初始化")
            return
            
        if strategy.trading:
            self.write_log(f"{strategy_name}已经启动，无需重复操作")
            return
            
        # 加载上次运行的数据
        self.load_strategy_data()
        
        # 启动策略
        self.cta_engine.start_strategy(strategy_name)
        
    def stop_strategy(self, strategy_name: str):
        """停止策略"""
        strategy = self.strategy_instances[strategy_name]
        
        if not strategy.trading:
            self.write_log(f"{strategy_name}已经停止，无需重复操作")
            return
            
        # 停止策略
        self.cta_engine.stop_strategy(strategy_name)
        
        # 保存策略数据
        self.save_strategy_data()

    def edit_strategy(self, strategy_name: str):
        """编辑策略"""
        strategy = self.strategy_instances[strategy_name]
        dialog = EditStrategyDialog(strategy, self)
        dialog.exec_()
        
    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if not self.strategy_instances[strategy_name].trading:
            self.cta_engine.remove_strategy(strategy_name)
            
            # 移除表格显示
            for row in range(self.strategy_table.rowCount()):
                if self.strategy_table.item(row, 0).text() == strategy_name:
                    self.strategy_table.removeRow(row)
                    break
            
            # 移除实例缓存
            self.strategy_instances.pop(strategy_name)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("CTA策略")
        
        # 创建顶部按钮区域
        top_layout = QHBoxLayout()
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["BollChannelStrategy", "其他策略"]) # 这里需要动态获取策略列表
        
        add_button = QPushButton("添加策略")
        init_all_button = QPushButton("全部初始化")
        start_all_button = QPushButton("全部启动")
        stop_all_button = QPushButton("全部停止")
        clear_log_button = QPushButton("清空日志")
        
        migrate_button = QPushButton("移仓助手")
        top_layout.addWidget(self.strategy_combo)
        top_layout.addWidget(add_button)
        top_layout.addWidget(init_all_button)
        top_layout.addWidget(start_all_button) 
        top_layout.addWidget(stop_all_button)
        top_layout.addWidget(clear_log_button)
        top_layout.addWidget(migrate_button)
        top_layout.addStretch()
        
        # 创建策略监控表格
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(4)
        self.strategy_table.setHorizontalHeaderLabels([
            "策略名称",
            "合约",
            "策略状态",
            "操作" 
        ])
        self.strategy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 创建停止单监控表格
        self.stop_order_table = QTableWidget()
        self.stop_order_table.setColumnCount(8)
        self.stop_order_table.setHorizontalHeaderLabels([
            "委托号",
            "策略名",
            "合约代码",
            "方向",
            "价格",
            "数量",
            "状态",
            "触发价"
        ])
        self.stop_order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 创建策略绩效表格
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(7)
        self.performance_table.setHorizontalHeaderLabels([
            "策略名",
            "盈亏",
            "成交笔数",
            "胜率",
            "盈亏比",
            "最大回撤",
            "夏普比率"
        ])
        self.performance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 创建日志区域
        self.log_widget = QTableWidget()
        self.log_widget.setColumnCount(2)
        self.log_widget.setHorizontalHeaderLabels([
            "时间",
            "信息"
        ])
        self.log_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.strategy_table)
        layout.addWidget(self.stop_order_table)
        layout.addWidget(self.performance_table)
        layout.addWidget(self.log_widget)
        self.setLayout(layout)
        
        # 绑定按钮事件
        add_button.clicked.connect(self.add_strategy)
        init_all_button.clicked.connect(self.init_all_strategy)
        start_all_button.clicked.connect(self.start_all_strategy)
        stop_all_button.clicked.connect(self.stop_all_strategy)
        clear_log_button.clicked.connect(self.clear_log)
        migrate_button.clicked.connect(self.show_migrate_dialog)
        
    def init_all_strategy(self):
        """初始化所有策略"""
        reply = QMessageBox.question(
            self,
            "初始化确认",
            "确认要初始化所有策略吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for strategy_name in self.strategy_instances.keys():
                self.cta_engine.init_strategy(strategy_name)

    def start_all_strategy(self):
        """启动所有策略"""
        reply = QMessageBox.question(
            self,
            "启动确认",
            "确认要启动所有策略吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for strategy_name in self.strategy_instances.keys():
                self.cta_engine.start_strategy(strategy_name)

    def stop_all_strategy(self):
        """停止所有策略"""
        reply = QMessageBox.question(
            self,
            "停止确认",
            "确认要停止所有策略吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for strategy_name in self.strategy_instances.keys():
                self.cta_engine.stop_strategy(strategy_name)

    def clear_log(self):
        """清空日志"""
        self.log_widget.setRowCount(0)
        
    def show_migrate_dialog(self):
        """显示移仓助手对话框"""
        dialog = MigrateDialog(self)
        dialog.exec_()

    def update_performance(self):
        """更新策略绩效"""
        self.performance_table.clearContents()
        self.performance_table.setRowCount(0)
        
        for strategy_name, strategy in self.strategy_instances.items():
            stats = strategy.get_statistics()  # 获取策略统计数据
            if not stats:
                continue
            
            row = self.performance_table.rowCount()
            self.performance_table.insertRow(row)
            self.performance_table.setItem(row, 0, QTableWidgetItem(strategy_name))
            self.performance_table.setItem(row, 1, QTableWidgetItem(f"{stats['total_pnl']:.2f}"))
            self.performance_table.setItem(row, 2, QTableWidgetItem(str(stats['total_trade'])))
            self.performance_table.setItem(row, 3, QTableWidgetItem(f"{stats['win_rate']:.1%}"))
            self.performance_table.setItem(row, 4, QTableWidgetItem(f"{stats['profit_loss_ratio']:.2f}"))
            self.performance_table.setItem(row, 5, QTableWidgetItem(f"{stats['max_drawdown']:.2f}"))
            self.performance_table.setItem(row, 6, QTableWidgetItem(f"{stats['sharpe_ratio']:.2f}"))

    def load_bar(self, vt_symbol: str, days: int, interval: Interval = Interval.MINUTE):
        """加载历史K线数据"""
        symbol, exchange = vt_symbol.split(".")
        
        # 计算开始日期
        end = datetime.now()
        start = end - timedelta(days)
        
        # 从数据库加载数据
        bars = self.database.load_bar_data(
            symbol=symbol,
            exchange=Exchange(exchange),
            interval=interval,
            start=start,
            end=end
        )
        return bars
        
    def load_tick(self, vt_symbol: str, days: int):
        """加载历史Tick数据"""
        symbol, exchange = vt_symbol.split(".")
        
        # 计算开始日期  
        end = datetime.now()
        start = end - timedelta(days)
        
        # 从数据库加载数据
        ticks = self.database.load_tick_data(
            symbol=symbol,
            exchange=Exchange(exchange),
            start=start,
            end=end
        )
        return ticks
        
    def save_strategy_data(self):
        """保存策略数据"""
        data = {}
        for strategy_name, strategy in self.strategy_instances.items():
            data[strategy_name] = {
                "pos": strategy.pos,
                "variables": strategy.get_variables(),
            }
            
        save_json(self.data_filename, data)
        
    def load_strategy_data(self):
        """加载策略数据"""
        data = load_json(self.data_filename)
        
        for strategy_name, strategy_data in data.items():
            if strategy_name not in self.strategy_instances:
                continue
                
            strategy = self.strategy_instances[strategy_name]
            
            # 恢复策略持仓
            strategy.pos = strategy_data.get("pos", 0)
            
            # 恢复策略变量
            variables = strategy_data.get("variables", {})
            for name, value in variables.items():
                setattr(strategy, name, value)

class AddStrategyDialog(QDialog):
    """添加策略对话框"""
    
    def __init__(self, strategy_class_name: str, parent=None):
        super().__init__(parent)
        
        self.strategy_class_name = strategy_class_name
        self.parameters = {}
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("添加策略")
        
        # 创建表单
        form = QGridLayout()
        
        name_label = QLabel("实例名称:")
        self.name_line = QLineEdit()
        
        symbol_label = QLabel("合约代码:")
        self.symbol_line = QLineEdit()
        
        form.addWidget(name_label, 0, 0)
        form.addWidget(self.name_line, 0, 1)
        form.addWidget(symbol_label, 1, 0)
        form.addWidget(self.symbol_line, 1, 1)
        
        # 获取策略类的默认参数
        strategy_class = self.parent().cta_engine.get_strategy_class_by_name(
            self.strategy_class_name
        )
        parameters = strategy_class.parameters
        
        validator_float = QDoubleValidator()
        validator_float.setBottom(0)
        
        for index, name in enumerate(parameters):
            current_value = getattr(strategy_class, name)
            
            label = QLabel(f"{name}:")
            line = QLineEdit(str(current_value))
            
            # 设置浮点数校验
            if isinstance(current_value, float):
                line.setValidator(validator_float)
                
            form.addWidget(label, index + 2, 0)
            form.addWidget(line, index + 2, 1)
            
            self.parameters[name] = line
            
        # 创建按钮
        button_box = QHBoxLayout()
        cancel_button = QPushButton("取消")
        add_button = QPushButton("添加")
        button_box.addWidget(cancel_button)
        button_box.addWidget(add_button)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_box)
        self.setLayout(layout)
        
        # 绑定按钮事件
        cancel_button.clicked.connect(self.reject)
        add_button.clicked.connect(self.accept)
        
    def accept(self):
        """确认添加"""
        # 获取策略参数
        params = {}
        for name, line in self.parameters.items():
            value = line.text()
            
            # 获取参数默认值以判断类型
            strategy_class = self.parent().cta_engine.get_strategy_class_by_name(
                self.strategy_class_name
            )
            param_value = getattr(strategy_class, name)
            
            # 类型转换
            if isinstance(param_value, bool):
                value = bool(value)
            elif isinstance(param_value, int):
                value = int(value)
            elif isinstance(param_value, float):
                value = float(value)
                
            params[name] = value
            
        self.params = params
        super().accept()

class EditStrategyDialog(QDialog):
    """策略编辑对话框"""

    def __init__(self, strategy: StrategyTemplate, parent=None):
        super().__init__(parent)
        
        self.strategy = strategy
        self.parameters = {}
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"策略参数编辑 - {self.strategy.strategy_name}")
        
        form = QGridLayout()
        
        # 获取策略参数字典
        parameters = self.strategy.get_parameters()
        validator_float = QDoubleValidator()
        validator_float.setBottom(0)
        
        for index, (name, value) in enumerate(parameters.items()):
            label = QLabel(f"{name}:")
            line = QLineEdit(str(value))
            
            # 设置浮点数校验
            if isinstance(value, float):
                line.setValidator(validator_float)
                
            form.addWidget(label, index, 0)
            form.addWidget(line, index, 1)
            
            self.parameters[name] = line
            
        button_box = QHBoxLayout()
        cancel_button = QPushButton("取消")
        save_button = QPushButton("确定")
        button_box.addWidget(cancel_button)
        button_box.addWidget(save_button)
        
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_box)
        self.setLayout(layout)
        
        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self.save_parameters)
        
    def save_parameters(self):
        """保存策略参数"""
        # 获取所有参数值
        params = {}
        for name, line in self.parameters.items():
            value = line.text()
            
            # 类型转换
            param_value = getattr(self.strategy, name)
            if isinstance(param_value, bool):
                value = bool(value)
            elif isinstance(param_value, int):
                value = int(value)
            elif isinstance(param_value, float):
                value = float(value)
                
            params[name] = value
            
        # 调用引擎更新策略参数
        self.parent().cta_engine.edit_strategy(self.strategy.strategy_name, params)
        self.accept()

# 添加移仓助手对话框
class MigrateDialog(QDialog):
    """移仓助手对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("移仓助手")
        self.setMinimumWidth(400)
        
        # 创建表单
        form = QGridLayout()
        
        old_symbol_label = QLabel("移仓合约:")
        self.old_symbol_combo = QComboBox()
        self.old_symbol_combo.addItems(self.get_strategy_symbols())
        
        new_symbol_label = QLabel("目标合约:")
        self.new_symbol_line = QLineEdit()
        
        slippage_label = QLabel("委托超价:")
        self.slippage_spin = QSpinBox()
        self.slippage_spin.setRange(1, 100)
        self.slippage_spin.setValue(5)
        
        form.addWidget(old_symbol_label, 0, 0)
        form.addWidget(self.old_symbol_combo, 0, 1)
        form.addWidget(new_symbol_label, 1, 0)
        form.addWidget(self.new_symbol_line, 1, 1)
        form.addWidget(slippage_label, 2, 0)
        form.addWidget(self.slippage_spin, 2, 1)
        
        # 创建按钮
        button_box = QHBoxLayout()
        cancel_button = QPushButton("取消")
        migrate_button = QPushButton("移仓")
        button_box.addWidget(cancel_button)
        button_box.addWidget(migrate_button)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_box)
        self.setLayout(layout)
        
        # 绑定按钮事件
        cancel_button.clicked.connect(self.reject)
        migrate_button.clicked.connect(self.migrate_position)
        
    def get_strategy_symbols(self) -> List[str]:
        """获取策略合约列表"""
        symbols = set()
        for strategy in self.parent.strategy_instances.values():
            symbols.add(strategy.vt_symbol)
        return list(symbols)
        
    def migrate_position(self):
        """执行移仓操作"""
        old_symbol = self.old_symbol_combo.currentText()
        new_symbol = self.new_symbol_line.text()
        slippage = self.slippage_spin.value()
        
        reply = QMessageBox.question(
            self,
            "移仓确认",
            f"确认要将{old_symbol}移仓到{new_symbol}吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.parent.cta_engine.migrate_strategy(
                old_symbol,
                new_symbol,
                slippage
            )
            self.accept() 