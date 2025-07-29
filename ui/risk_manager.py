
from PyQt5 import QtWidgets, QtCore, QtGui
from vnpy.trader.engine import MainEngine, EventEngine
from config.risk_engine import RiskEngine
from config.risk_config import get_all_risk_settings, set_risk_setting, reset_risk_settings, RiskConfig
import json
import os

class RiskSettingsDialog(QtWidgets.QDialog):
    """风险设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("风险设置")
        self.setFixedSize(500, 700)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QtWidgets.QVBoxLayout()
        
        # 创建滚动区域
        scroll_area = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QFormLayout()
        
        # 风险控制设置
        self.max_loss_per_trade = QtWidgets.QDoubleSpinBox()
        self.max_loss_per_trade.setRange(0, 1000000)
        self.max_loss_per_trade.setDecimals(2)
        scroll_layout.addRow("单笔最大亏损:", self.max_loss_per_trade)
        
        self.max_loss_per_day = QtWidgets.QDoubleSpinBox()
        self.max_loss_per_day.setRange(0, 10000000)
        self.max_loss_per_day.setDecimals(2)
        scroll_layout.addRow("每日最大亏损:", self.max_loss_per_day)
        
        self.max_total_loss = QtWidgets.QDoubleSpinBox()
        self.max_total_loss.setRange(0, 100000000)
        self.max_total_loss.setDecimals(2)
        scroll_layout.addRow("总最大亏损:", self.max_total_loss)
        
        self.max_position_ratio = QtWidgets.QDoubleSpinBox()
        self.max_position_ratio.setRange(0, 1)
        self.max_position_ratio.setDecimals(2)
        self.max_position_ratio.setSingleStep(0.1)
        scroll_layout.addRow("最大仓位比例:", self.max_position_ratio)
        
        self.max_concentration_ratio = QtWidgets.QDoubleSpinBox()
        self.max_concentration_ratio.setRange(0, 1)
        self.max_concentration_ratio.setDecimals(2)
        self.max_concentration_ratio.setSingleStep(0.1)
        scroll_layout.addRow("最大集中持仓比例:", self.max_concentration_ratio)
        
        self.max_trade_volume = QtWidgets.QSpinBox()
        self.max_trade_volume.setRange(1, 10000)
        scroll_layout.addRow("单笔最大交易量:", self.max_trade_volume)
        
        self.min_balance = QtWidgets.QDoubleSpinBox()
        self.min_balance.setRange(0, 100000000)
        self.min_balance.setDecimals(2)
        scroll_layout.addRow("最小账户余额:", self.min_balance)
        
        self.max_buy_price = QtWidgets.QDoubleSpinBox()
        self.max_buy_price.setRange(0, 1000000)
        self.max_buy_price.setDecimals(2)
        scroll_layout.addRow("最大买入价格:", self.max_buy_price)
        
        self.max_leverage = QtWidgets.QDoubleSpinBox()
        self.max_leverage.setRange(1, 100)
        self.max_leverage.setDecimals(1)
        scroll_layout.addRow("最大杠杆倍数:", self.max_leverage)
        
        self.max_open_orders = QtWidgets.QSpinBox()
        self.max_open_orders.setRange(1, 100)
        scroll_layout.addRow("最大挂单数量:", self.max_open_orders)
        
        self.max_positions = QtWidgets.QSpinBox()
        self.max_positions.setRange(1, 100)
        scroll_layout.addRow("最大持仓品种数:", self.max_positions)
        
        self.max_daily_trades = QtWidgets.QSpinBox()
        self.max_daily_trades.setRange(1, 1000)
        scroll_layout.addRow("每日最大交易次数:", self.max_daily_trades)
        
        self.risk_score_threshold = QtWidgets.QSpinBox()
        self.risk_score_threshold.setRange(0, 100)
        scroll_layout.addRow("风险评分阈值:", self.risk_score_threshold)
        
        self.alert_enabled = QtWidgets.QCheckBox()
        scroll_layout.addRow("启用警报:", self.alert_enabled)
        
        self.auto_stop_loss = QtWidgets.QCheckBox()
        scroll_layout.addRow("自动止损:", self.auto_stop_loss)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        reset_button = QtWidgets.QPushButton("重置为默认")
        reset_button.clicked.connect(self.reset_to_default)
        
        save_button = QtWidgets.QPushButton("保存")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QtWidgets.QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(reset_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """加载设置"""
        settings = get_all_risk_settings()
        
        self.max_loss_per_trade.setValue(settings.get("max_loss_per_trade", 1000))
        self.max_loss_per_day.setValue(settings.get("max_loss_per_day", 5000))
        self.max_total_loss.setValue(settings.get("max_total_loss", 10000))
        self.max_position_ratio.setValue(settings.get("max_position_ratio", 0.5))
        self.max_concentration_ratio.setValue(settings.get("max_concentration_ratio", 0.3))
        self.max_trade_volume.setValue(settings.get("max_trade_volume", 100))
        self.min_balance.setValue(settings.get("min_balance", 10000))
        self.max_buy_price.setValue(settings.get("max_buy_price", 100000))
        self.max_leverage.setValue(settings.get("max_leverage", 10))
        self.max_open_orders.setValue(settings.get("max_open_orders", 5))
        self.max_positions.setValue(settings.get("max_positions", 10))
        self.max_daily_trades.setValue(settings.get("max_daily_trades", 50))
        self.risk_score_threshold.setValue(settings.get("risk_score_threshold", 70))
        self.alert_enabled.setChecked(settings.get("alert_enabled", True))
        self.auto_stop_loss.setChecked(settings.get("auto_stop_loss", True))
    
    def save_settings(self):
        """保存设置"""
        settings = {
            "max_loss_per_trade": self.max_loss_per_trade.value(),
            "max_loss_per_day": self.max_loss_per_day.value(),
            "max_total_loss": self.max_total_loss.value(),
            "max_position_ratio": self.max_position_ratio.value(),
            "max_concentration_ratio": self.max_concentration_ratio.value(),
            "max_trade_volume": self.max_trade_volume.value(),
            "min_balance": self.min_balance.value(),
            "max_buy_price": self.max_buy_price.value(),
            "max_leverage": self.max_leverage.value(),
            "max_open_orders": self.max_open_orders.value(),
            "max_positions": self.max_positions.value(),
            "max_daily_trades": self.max_daily_trades.value(),
            "risk_score_threshold": self.risk_score_threshold.value(),
            "alert_enabled": self.alert_enabled.isChecked(),
            "auto_stop_loss": self.auto_stop_loss.isChecked()
        }
        
        for key, value in settings.items():
            set_risk_setting(key, value)
    
    def reset_to_default(self):
        """重置为默认值"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认", "确定要重置所有风险设置为默认值吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            reset_risk_settings()
            self.load_settings()

class RiskManager(QtWidgets.QWidget):
    """风险管理组件"""
    
    def __init__(self, main_engine, event_engine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # 创建风险引擎
        self.risk_engine = RiskEngine(main_engine, event_engine)
        self.risk_engine.init_engine()
        
        self.init_ui()
        self.update_risk_status()
        
        # 定时更新风险状态
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_risk_status)
        self.timer.start(5000)  # 每5秒更新一次
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("风险管理")
        self.resize(1000, 700)
        
        main_layout = QtWidgets.QHBoxLayout()
        
        # 左侧布局 - 风险概览
        left_layout = QtWidgets.QVBoxLayout()
        
        # 风险概览
        overview_group = QtWidgets.QGroupBox("风险概览")
        overview_layout = QtWidgets.QFormLayout()
        
        self.daily_pnl_label = QtWidgets.QLabel("0.00")
        self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        
        self.risk_score_label = QtWidgets.QLabel("100")
        self.risk_score_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.total_positions_label = QtWidgets.QLabel("0")
        self.total_orders_label = QtWidgets.QLabel("0")
        self.total_trades_label = QtWidgets.QLabel("0")
        self.total_alerts_label = QtWidgets.QLabel("0")
        
        overview_layout.addRow("今日盈亏:", self.daily_pnl_label)
        overview_layout.addRow("风险评分:", self.risk_score_label)
        overview_layout.addRow("当前持仓:", self.total_positions_label)
        overview_layout.addRow("当前挂单:", self.total_orders_label)
        overview_layout.addRow("今日成交:", self.total_trades_label)
        overview_layout.addRow("风险警报:", self.total_alerts_label)
        
        overview_group.setLayout(overview_layout)
        left_layout.addWidget(overview_group)
        
        # 风险警报
        alerts_group = QtWidgets.QGroupBox("风险警报")
        alerts_layout = QtWidgets.QVBoxLayout()
        
        self.alerts_table = QtWidgets.QTableWidget()
        self.alerts_table.setColumnCount(3)
        self.alerts_table.setHorizontalHeaderLabels(["时间", "级别", "消息"])
        self.alerts_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.alerts_table.setMaximumHeight(200)
        
        alerts_layout.addWidget(self.alerts_table)
        alerts_group.setLayout(alerts_layout)
        left_layout.addWidget(alerts_group)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        settings_button = QtWidgets.QPushButton("风险设置")
        settings_button.clicked.connect(self.show_risk_settings)
        
        reset_button = QtWidgets.QPushButton("重置盈亏")
        reset_button.clicked.connect(self.reset_daily_pnl)
        
        refresh_button = QtWidgets.QPushButton("刷新")
        refresh_button.clicked.connect(self.update_risk_status)
        
        button_layout.addWidget(settings_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(refresh_button)
        left_layout.addLayout(button_layout)
        
        # 右侧布局 - 详细风险信息
        right_layout = QtWidgets.QVBoxLayout()
        
        # 持仓风险
        positions_group = QtWidgets.QGroupBox("持仓风险")
        positions_layout = QtWidgets.QVBoxLayout()
        
        self.positions_table = QtWidgets.QTableWidget()
        self.positions_table.setColumnCount(5)
        self.positions_table.setHorizontalHeaderLabels(["品种", "数量", "价格", "市值", "占比"])
        positions_layout.addWidget(self.positions_table)
        positions_group.setLayout(positions_layout)
        right_layout.addWidget(positions_group)
        
        # 风险规则
        rules_group = QtWidgets.QGroupBox("风险规则")
        rules_layout = QtWidgets.QVBoxLayout()
        
        self.rules_table = QtWidgets.QTableWidget()
        self.rules_table.setColumnCount(3)
        self.rules_table.setHorizontalHeaderLabels(["规则", "当前值", "阈值"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        
        rules_layout.addWidget(self.rules_table)
        rules_group.setLayout(rules_layout)
        right_layout.addWidget(rules_group)
        
        # 设置主布局
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        
        self.setLayout(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 8px 15px;
                margin: 5px;
                font-weight: bold;
            }
            QTableWidget {
                font-size: 12px;
            }
            QLabel {
                font-size: 12px;
            }
        """)
    
    def update_risk_status(self):
        """更新风险状态"""
        try:
            status = self.risk_engine.get_risk_status()
            
            # 更新概览信息
            self.daily_pnl_label.setText(f"{status['daily_pnl']:.2f}")
            if status['daily_pnl'] >= 0:
                self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
            else:
                self.daily_pnl_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
            
            # 风险评分颜色
            risk_score = status['risk_score']
            self.risk_score_label.setText(str(risk_score))
            if risk_score >= 80:
                color = "green"
            elif risk_score >= 60:
                color = "orange"
            else:
                color = "red"
            self.risk_score_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
            
            self.total_positions_label.setText(str(status['positions']))
            self.total_orders_label.setText(str(status['orders']))
            self.total_trades_label.setText(str(status['trades']))
            self.total_alerts_label.setText(str(status['alerts']))
            
            # 更新警报列表
            self.update_alerts_table()
            
            # 更新风险规则表
            self.update_rules_table()
            
        except Exception as e:
            print(f"更新风险状态失败: {e}")
    
    def update_alerts_table(self):
        """更新警报表格"""
        alerts = self.risk_engine.get_alerts(limit=10)
        
        self.alerts_table.setRowCount(len(alerts))
        for i, alert in enumerate(alerts):
            # 时间
            time_item = QtWidgets.QTableWidgetItem(alert['time'][:19])
            self.alerts_table.setItem(i, 0, time_item)
            
            # 级别
            level_item = QtWidgets.QTableWidgetItem(alert['level'])
            if alert['level'] == 'WARNING':
                level_item.setBackground(QtGui.QColor(255, 255, 0))
            elif alert['level'] == 'ERROR':
                level_item.setBackground(QtGui.QColor(255, 0, 0))
            self.alerts_table.setItem(i, 1, level_item)
            
            # 消息
            message_item = QtWidgets.QTableWidgetItem(alert['message'])
            self.alerts_table.setItem(i, 2, message_item)
    
    def update_rules_table(self):
        """更新风险规则表格"""
        settings = get_all_risk_settings()
        
        rules = [
            ("单笔最大亏损", f"{settings.get('max_loss_per_trade', 1000):.2f}", "≤ 设置值"),
            ("每日最大亏损", f"{settings.get('max_loss_per_day', 5000):.2f}", "≤ 设置值"),
            ("最大仓位比例", f"{settings.get('max_position_ratio', 0.5):.2%}", "≤ 设置值"),
            ("最大集中持仓比例", f"{settings.get('max_concentration_ratio', 0.3):.2%}", "≤ 设置值"),
            ("单笔最大交易量", str(settings.get('max_trade_volume', 100)), "≤ 设置值"),
            ("最小账户余额", f"{settings.get('min_balance', 10000):.2f}", "≥ 设置值"),
            ("最大买入价格", f"{settings.get('max_buy_price', 100000):.2f}", "≤ 设置值"),
            ("最大杠杆倍数", str(settings.get('max_leverage', 10)), "≤ 设置值"),
            ("最大挂单数量", str(settings.get('max_open_orders', 5)), "≤ 设置值"),
            ("最大持仓品种数", str(settings.get('max_positions', 10)), "≤ 设置值"),
            ("每日最大交易次数", str(settings.get('max_daily_trades', 50)), "≤ 设置值"),
        ]
        
        self.rules_table.setRowCount(len(rules))
        for i, (rule, current, threshold) in enumerate(rules):
            rule_item = QtWidgets.QTableWidgetItem(rule)
            current_item = QtWidgets.QTableWidgetItem(current)
            threshold_item = QtWidgets.QTableWidgetItem(threshold)
            
            self.rules_table.setItem(i, 0, rule_item)
            self.rules_table.setItem(i, 1, current_item)
            self.rules_table.setItem(i, 2, threshold_item)
    
    def show_risk_settings(self):
        """显示风险设置对话框"""
        dialog = RiskSettingsDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            dialog.save_settings()
            QtWidgets.QMessageBox.information(self, "成功", "风险设置已保存")
            self.update_risk_status()
    
    def reset_daily_pnl(self):
        """重置每日盈亏"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认", "确定要重置每日盈亏记录吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.risk_engine.reset_daily_pnl()
            self.update_risk_status()
            QtWidgets.QMessageBox.information(self, "成功", "每日盈亏已重置")
    
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        self.risk_engine.close_engine()
        super().closeEvent(event)

