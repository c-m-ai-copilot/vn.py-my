
from PyQt5 import QtWidgets, QtCore, QtGui
from vnpy.trader.engine import MainEngine, EventEngine
from config.strategy_engine import StrategyEngine
from config.strategy_config import get_strategy_templates, add_strategy_template, remove_strategy_template
import json
import os

class AddStrategyDialog(QtWidgets.QDialog):
    """添加策略对话框"""

    def __init__(self, parent=None, strategy_engine=None):
        super().__init__(parent)
        self.strategy_engine = strategy_engine
        
        self.setWindowTitle("添加策略")
        self.setFixedSize(400, 500)
        
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        form_layout = QtWidgets.QFormLayout()
        
        # 策略基本信息
        self.name_input = QtWidgets.QLineEdit()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["CTA策略", "套利策略", "高频策略", "自定义策略"])
        
        # 交易品种
        self.symbols_input = QtWidgets.QLineEdit()
        self.symbols_input.setPlaceholderText("例如: rb2410,IF2406,au2406")
        
        # 策略参数
        self.parameters_edit = QtWidgets.QTextEdit()
        self.parameters_edit.setPlainText(json.dumps({
            "trade_volume": 1,
            "stop_loss": 10,
            "take_profit": 20,
            "ma_period": 20,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30
        }, indent=2, ensure_ascii=False))
        
        form_layout.addRow("策略名称:", self.name_input)
        form_layout.addRow("策略类型:", self.type_combo)
        form_layout.addRow("交易品种:", self.symbols_input)
        form_layout.addRow("策略参数:", self.parameters_edit)
        
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)

    def get_strategy_details(self):
        """获取策略详情"""
        try:
            parameters = json.loads(self.parameters_edit.toPlainText())
        except json.JSONDecodeError:
            parameters = {}
            
        symbols = [s.strip() for s in self.symbols_input.text().split(",") if s.strip()]
        
        return {
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "symbols": symbols,
            "parameters": parameters
        }

class StrategyManager(QtWidgets.QWidget):
    """策略管理组件"""
    
    def __init__(self, main_engine, event_engine, strategy_engine=None):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # 使用传入的策略引擎或创建新的
        if strategy_engine:
            self.strategy_engine = strategy_engine
        else:
            from config.strategy_engine import StrategyEngine
            self.strategy_engine = StrategyEngine(main_engine, event_engine)
            self.strategy_engine.init_engine()
        
        self.init_ui()
        self.load_strategies()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("策略管理")
        self.resize(1000, 600)
        
        # 主布局
        main_layout = QtWidgets.QHBoxLayout()
        
        # 左侧策略列表
        left_layout = QtWidgets.QVBoxLayout()
        
        # 策略列表标题
        left_layout.addWidget(QtWidgets.QLabel("策略列表"))
        
        # 策略表格
        self.strategy_table = QtWidgets.QTableWidget()
        self.strategy_table.setColumnCount(6)
        self.strategy_table.setHorizontalHeaderLabels([
            "策略ID", "策略名称", "策略类型", "状态", "交易品种", "总盈利"
        ])
        self.strategy_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.strategy_table.itemSelectionChanged.connect(self.on_strategy_selected)
        
        left_layout.addWidget(self.strategy_table)
        
        # 按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        
        add_button = QtWidgets.QPushButton("添加策略")
        add_button.clicked.connect(self.add_strategy)
        
        start_button = QtWidgets.QPushButton("启动策略")
        start_button.clicked.connect(self.start_strategy)
        
        stop_button = QtWidgets.QPushButton("停止策略")
        stop_button.clicked.connect(self.stop_strategy)
        
        remove_button = QtWidgets.QPushButton("移除策略")
        remove_button.clicked.connect(self.remove_strategy)
        
        backtest_button = QtWidgets.QPushButton("回测策略")
        backtest_button.clicked.connect(self.backtest_strategy)
        
        refresh_button = QtWidgets.QPushButton("刷新")
        refresh_button.clicked.connect(self.load_strategies)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(backtest_button)
        button_layout.addWidget(refresh_button)
        
        left_layout.addLayout(button_layout)
        
        # 右侧策略详情
        right_layout = QtWidgets.QVBoxLayout()
        
        # 策略详情标题
        right_layout.addWidget(QtWidgets.QLabel("策略详情"))
        
        # 策略详情文本框
        self.strategy_details = QtWidgets.QTextEdit()
        self.strategy_details.setReadOnly(True)
        self.strategy_details.setMaximumWidth(400)
        
        right_layout.addWidget(self.strategy_details)
        
        # 策略参数
        right_layout.addWidget(QtWidgets.QLabel("策略参数"))
        self.strategy_parameters = QtWidgets.QTextEdit()
        self.strategy_parameters.setReadOnly(True)
        self.strategy_parameters.setMaximumWidth(400)
        
        right_layout.addWidget(self.strategy_parameters)
        
        # 策略绩效
        right_layout.addWidget(QtWidgets.QLabel("策略绩效"))
        self.strategy_performance = QtWidgets.QTextEdit()
        self.strategy_performance.setReadOnly(True)
        self.strategy_performance.setMaximumWidth(400)
        
        right_layout.addWidget(self.strategy_performance)
        
        # 添加到主布局
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        self.setLayout(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                margin: 2px;
            }
            QTableWidget {
                font-size: 12px;
            }
            QTextEdit {
                font-size: 12px;
                font-family: Consolas, Monaco, monospace;
            }
        """)

    def load_strategies(self):
        """加载策略列表"""
        strategies = self.strategy_engine.get_strategies()
        
        self.strategy_table.setRowCount(len(strategies))
        for i, strategy in enumerate(strategies):
            # 策略ID
            self.strategy_table.setItem(i, 0, QtWidgets.QTableWidgetItem(strategy["id"]))
            
            # 策略名称
            self.strategy_table.setItem(i, 1, QtWidgets.QTableWidgetItem(strategy["name"]))
            
            # 策略类型
            self.strategy_table.setItem(i, 2, QtWidgets.QTableWidgetItem(strategy["type"]))
            
            # 状态
            status_item = QtWidgets.QTableWidgetItem(strategy["status"])
            if strategy["status"] == "running":
                status_item.setBackground(QtGui.QColor(144, 238, 144))  # 绿色
            elif strategy["status"] == "stopped":
                status_item.setBackground(QtGui.QColor(255, 182, 193))  # 红色
            self.strategy_table.setItem(i, 3, status_item)
            
            # 交易品种
            symbols = ",".join(strategy["symbols"])
            self.strategy_table.setItem(i, 4, QtWidgets.QTableWidgetItem(symbols))
            
            # 总盈利
            profit = strategy["performance"]["profit"]
            profit_item = QtWidgets.QTableWidgetItem(f"{profit:.2f}")
            if profit > 0:
                profit_item.setForeground(QtGui.QColor(0, 128, 0))  # 绿色
            elif profit < 0:
                profit_item.setForeground(QtGui.QColor(255, 0, 0))  # 红色
            self.strategy_table.setItem(i, 5, profit_item)

    def on_strategy_selected(self):
        """策略选中事件"""
        selected_row = self.strategy_table.currentRow()
        if selected_row >= 0:
            strategies = self.strategy_engine.get_strategies()
            if selected_row < len(strategies):
                strategy = strategies[selected_row]
                
                # 显示策略详情
                details = f"""
策略ID: {strategy['id']}
策略名称: {strategy['name']}
策略类型: {strategy['type']}
状态: {strategy['status']}
创建时间: {strategy['created_at']}
交易品种: {', '.join(strategy['symbols'])}
                """
                self.strategy_details.setPlainText(details.strip())
                
                # 显示策略参数
                parameters = json.dumps(strategy['parameters'], indent=2, ensure_ascii=False)
                self.strategy_parameters.setPlainText(parameters)
                
                # 显示策略绩效
                performance = strategy['performance']
                perf_text = f"""
总交易次数: {performance['total_trades']}
胜率: {performance['win_rate']:.2%}
总盈利: {performance['profit']:.2f}
最大回撤: {performance['max_drawdown']:.2f}
                """
                self.strategy_performance.setPlainText(perf_text.strip())

    def add_strategy(self):
        """添加策略"""
        dialog = AddStrategyDialog(self, self.strategy_engine)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            details = dialog.get_strategy_details()
            strategy_id = self.strategy_engine.add_strategy(
                details["name"],
                details["type"],
                details["parameters"],
                details["symbols"]
            )
            self.load_strategies()
            QtWidgets.QMessageBox.information(self, "成功", f"策略已添加: {strategy_id}")

    def start_strategy(self):
        """启动策略"""
        selected_row = self.strategy_table.currentRow()
        if selected_row >= 0:
            strategies = self.strategy_engine.get_strategies()
            if selected_row < len(strategies):
                strategy = strategies[selected_row]
                strategy_id = strategy["id"]
                self.strategy_engine.start_strategy(strategy_id)
                self.load_strategies()
                QtWidgets.QMessageBox.information(self, "成功", f"策略已启动: {strategy_id}")

    def stop_strategy(self):
        """停止策略"""
        selected_row = self.strategy_table.currentRow()
        if selected_row >= 0:
            strategies = self.strategy_engine.get_strategies()
            if selected_row < len(strategies):
                strategy = strategies[selected_row]
                strategy_id = strategy["id"]
                self.strategy_engine.stop_strategy(strategy_id)
                self.load_strategies()
                QtWidgets.QMessageBox.information(self, "成功", f"策略已停止: {strategy_id}")

    def remove_strategy(self):
        """移除策略"""
        selected_row = self.strategy_table.currentRow()
        if selected_row >= 0:
            strategies = self.strategy_engine.get_strategies()
            if selected_row < len(strategies):
                strategy = strategies[selected_row]
                strategy_id = strategy["id"]
                
                reply = QtWidgets.QMessageBox.question(
                    self, "确认", f"确定要移除策略 {strategy_id} 吗？",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    self.strategy_engine.remove_strategy(strategy_id)
                    self.load_strategies()
                    QtWidgets.QMessageBox.information(self, "成功", f"策略已移除: {strategy_id}")

    def backtest_strategy(self):
        """回测策略"""
        selected_row = self.strategy_table.currentRow()
        if selected_row >= 0:
            strategies = self.strategy_engine.get_strategies()
            if selected_row < len(strategies):
                strategy = strategies[selected_row]
                strategy_id = strategy["id"]
                
                # 简单的回测对话框
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle("回测策略")
                dialog.setFixedSize(300, 200)
                
                layout = QtWidgets.QFormLayout()
                
                start_date = QtWidgets.QDateEdit()
                start_date.setDate(QtCore.QDate.currentDate().addDays(-30))
                start_date.setCalendarPopup(True)
                
                end_date = QtWidgets.QDateEdit()
                end_date.setDate(QtCore.QDate.currentDate())
                end_date.setCalendarPopup(True)
                
                layout.addRow("开始日期:", start_date)
                layout.addRow("结束日期:", end_date)
                
                button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
                button_box.accepted.connect(dialog.accept)
                button_box.rejected.connect(dialog.reject)
                
                layout.addWidget(button_box)
                dialog.setLayout(layout)
                
                if dialog.exec_() == QtWidgets.QDialog.Accepted:
                    start_str = start_date.date().toString("yyyy-MM-dd")
                    end_str = end_date.date().toString("yyyy-MM-dd")
                    
                    try:
                        result = self.strategy_engine.backtest_strategy(strategy_id, start_str, end_str)
                        if "error" in result:
                            QtWidgets.QMessageBox.warning(self, "回测失败", result["error"])
                        else:
                            QtWidgets.QMessageBox.information(
                                self, 
                                "回测完成", 
                                f"回测完成！\n总交易次数: {result['total_trades']}\n总盈利: {result['total_profit']:.2f}\n胜率: {result['win_rate']:.2%}"
                            )
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(self, "回测失败", str(e))
