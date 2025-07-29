
from PyQt5 import QtWidgets, QtCore, QtGui
from vnpy.trader.engine import MainEngine, EventEngine
from config.notification_engine import NotificationEngine
from config.notification_config import get_all_notification_settings, set_notification_setting, get_notification_setting, reset_notification_settings
import json

class EmailConfigDialog(QtWidgets.QDialog):
    """邮件配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("邮件配置")
        self.setFixedSize(400, 350)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        form_layout = QtWidgets.QFormLayout()
        
        self.enabled_checkbox = QtWidgets.QCheckBox("启用邮件通知")
        form_layout.addRow(self.enabled_checkbox)
        
        self.smtp_server = QtWidgets.QLineEdit()
        self.smtp_server.setPlaceholderText("如: smtp.gmail.com")
        form_layout.addRow("SMTP服务器:", self.smtp_server)
        
        self.smtp_port = QtWidgets.QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        form_layout.addRow("SMTP端口:", self.smtp_port)
        
        self.username = QtWidgets.QLineEdit()
        form_layout.addRow("用户名:", self.username)
        
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow("密码:", self.password)
        
        self.from_email = QtWidgets.QLineEdit()
        form_layout.addRow("发件人邮箱:", self.from_email)
        
        self.to_email = QtWidgets.QLineEdit()
        form_layout.addRow("收件人邮箱:", self.to_email)
        
        self.use_tls = QtWidgets.QCheckBox("使用TLS加密")
        self.use_tls.setChecked(True)
        form_layout.addRow(self.use_tls)
        
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """加载邮件设置"""
        email_config = get_notification_setting("email", {})
        self.enabled_checkbox.setChecked(email_config.get("enabled", False))
        self.smtp_server.setText(email_config.get("smtp_server", ""))
        self.smtp_port.setValue(email_config.get("smtp_port", 587))
        self.username.setText(email_config.get("username", ""))
        self.password.setText(email_config.get("password", ""))
        self.from_email.setText(email_config.get("from_email", ""))
        self.to_email.setText(email_config.get("to_email", ""))
        self.use_tls.setChecked(email_config.get("use_tls", True))
    
    def get_email_config(self):
        """获取邮件配置"""
        return {
            "enabled": self.enabled_checkbox.isChecked(),
            "smtp_server": self.smtp_server.text(),
            "smtp_port": self.smtp_port.value(),
            "username": self.username.text(),
            "password": self.password.text(),
            "from_email": self.from_email.text(),
            "to_email": self.to_email.text(),
            "use_tls": self.use_tls.isChecked()
        }

class WebhookConfigDialog(QtWidgets.QDialog):
    """Webhook配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Webhook配置")
        self.setFixedSize(400, 200)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        form_layout = QtWidgets.QFormLayout()
        
        self.enabled_checkbox = QtWidgets.QCheckBox("启用Webhook通知")
        form_layout.addRow(self.enabled_checkbox)
        
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("如: https://oapi.dingtalk.com/robot/send?access_token=xxx")
        form_layout.addRow("Webhook URL:", self.url_input)
        
        self.secret_input = QtWidgets.QLineEdit()
        self.secret_input.setPlaceholderText("可选: 密钥或token")
        form_layout.addRow("密钥:", self.secret_input)
        
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """加载Webhook设置"""
        webhook_config = get_notification_setting("webhook", {})
        self.enabled_checkbox.setChecked(webhook_config.get("enabled", False))
        self.url_input.setText(webhook_config.get("url", ""))
        self.secret_input.setText(webhook_config.get("secret", ""))
    
    def get_webhook_config(self):
        """获取Webhook配置"""
        return {
            "enabled": self.enabled_checkbox.isChecked(),
            "url": self.url_input.text(),
            "secret": self.secret_input.text()
        }

class NotificationManager(QtWidgets.QWidget):
    """通知管理组件"""
    
    def __init__(self, main_engine, event_engine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # 创建通知引擎
        self.notification_engine = NotificationEngine(main_engine, event_engine)
        self.notification_engine.init_engine()
        
        self.init_ui()
        self.load_settings()
        self.update_notifications()
        
        # 定时更新通知列表
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_notifications)
        self.timer.start(5000)  # 每5秒更新一次
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("通知管理")
        self.resize(1000, 700)
        
        main_layout = QtWidgets.QVBoxLayout()
        
        # 顶部配置区域
        config_group = QtWidgets.QGroupBox("通知配置")
        config_layout = QtWidgets.QHBoxLayout()
        
        # 通知方式
        methods_group = QtWidgets.QGroupBox("通知方式")
        methods_layout = QtWidgets.QVBoxLayout()
        
        popup_config = get_notification_setting("popup", {})
        email_config = get_notification_setting("email", {})
        webhook_config = get_notification_setting("webhook", {})
        
        self.popup_checkbox = QtWidgets.QCheckBox("弹窗通知")
        self.popup_checkbox.setChecked(popup_config.get("enabled", True))
        self.popup_checkbox.stateChanged.connect(self.save_popup_settings)
        
        self.email_checkbox = QtWidgets.QCheckBox("邮件通知")
        self.email_checkbox.setChecked(email_config.get("enabled", False))
        self.email_checkbox.stateChanged.connect(self.save_email_settings)
        
        self.webhook_checkbox = QtWidgets.QCheckBox("Webhook通知")
        self.webhook_checkbox.setChecked(webhook_config.get("enabled", False))
        self.webhook_checkbox.stateChanged.connect(self.save_webhook_settings)
        
        methods_layout.addWidget(self.popup_checkbox)
        methods_layout.addWidget(self.email_checkbox)
        methods_layout.addWidget(self.webhook_checkbox)
        methods_group.setLayout(methods_layout)
        
        # 通知规则
        rules_group = QtWidgets.QGroupBox("通知规则")
        rules_layout = QtWidgets.QVBoxLayout()
        
        rules = get_notification_setting("rules", {})
        
        self.trade_rule = QtWidgets.QCheckBox("成交通知")
        self.trade_rule.setChecked(rules.get("trade", {}).get("enabled", True))
        
        self.order_rule = QtWidgets.QCheckBox("订单通知")
        self.order_rule.setChecked(rules.get("order", {}).get("enabled", True))
        
        self.position_rule = QtWidgets.QCheckBox("持仓通知")
        self.position_rule.setChecked(rules.get("position", {}).get("enabled", False))
        
        self.error_rule = QtWidgets.QCheckBox("错误通知")
        self.error_rule.setChecked(rules.get("error", {}).get("enabled", True))
        
        self.risk_rule = QtWidgets.QCheckBox("风险通知")
        self.risk_rule.setChecked(rules.get("risk", {}).get("enabled", True))
        
        rules_layout.addWidget(self.trade_rule)
        rules_layout.addWidget(self.order_rule)
        rules_layout.addWidget(self.position_rule)
        rules_layout.addWidget(self.error_rule)
        rules_layout.addWidget(self.risk_rule)
        rules_group.setLayout(rules_layout)
        
        # 配置按钮
        config_buttons_group = QtWidgets.QGroupBox("配置管理")
        config_buttons_layout = QtWidgets.QVBoxLayout()
        
        self.email_config_btn = QtWidgets.QPushButton("邮件配置")
        self.email_config_btn.clicked.connect(self.show_email_config)
        
        self.webhook_config_btn = QtWidgets.QPushButton("Webhook配置")
        self.webhook_config_btn.clicked.connect(self.show_webhook_config)
        
        self.sound_checkbox = QtWidgets.QCheckBox("声音提醒")
        sound_config = get_notification_setting("sound", {})
        self.sound_checkbox.setChecked(sound_config.get("enabled", True))
        self.sound_checkbox.stateChanged.connect(self.save_sound_settings)
        
        config_buttons_layout.addWidget(self.email_config_btn)
        config_buttons_layout.addWidget(self.webhook_config_btn)
        config_buttons_layout.addWidget(self.sound_checkbox)
        config_buttons_group.setLayout(config_buttons_layout)
        
        config_layout.addWidget(methods_group)
        config_layout.addWidget(rules_group)
        config_layout.addWidget(config_buttons_group)
        config_group.setLayout(config_layout)
        
        # 保存按钮
        save_btn = QtWidgets.QPushButton("保存所有设置")
        save_btn.clicked.connect(self.save_all_settings)
        config_layout.addWidget(save_btn)
        
        # 通知列表区域
        notifications_group = QtWidgets.QGroupBox("通知记录")
        notifications_layout = QtWidgets.QVBoxLayout()
        
        # 通知统计
        stats_layout = QtWidgets.QHBoxLayout()
        self.total_label = QtWidgets.QLabel("总通知: 0")
        self.trade_label = QtWidgets.QLabel("成交: 0")
        self.order_label = QtWidgets.QLabel("订单: 0")
        self.error_label = QtWidgets.QLabel("错误: 0")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.trade_label)
        stats_layout.addWidget(self.order_label)
        stats_layout.addWidget(self.error_label)
        stats_layout.addStretch()
        
        # 通知表格
        self.notifications_table = QtWidgets.QTableWidget()
        self.notifications_table.setColumnCount(4)
        self.notifications_table.setHorizontalHeaderLabels(["时间", "类型", "标题", "消息"])
        self.notifications_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.notifications_table.setMaximumHeight(400)
        
        # 操作按钮
        buttons_layout = QtWidgets.QHBoxLayout()
        self.clear_btn = QtWidgets.QPushButton("清空记录")
        self.clear_btn.clicked.connect(self.clear_notifications)
        
        self.refresh_btn = QtWidgets.QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.update_notifications)
        
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addStretch()
        
        notifications_layout.addLayout(stats_layout)
        notifications_layout.addWidget(self.notifications_table)
        notifications_layout.addLayout(buttons_layout)
        notifications_group.setLayout(notifications_layout)
        
        # 添加到主布局
        main_layout.addWidget(config_group)
        main_layout.addWidget(notifications_group)
        
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
    
    def load_settings(self):
        """加载所有设置"""
        # 方法设置已在init_ui中加载
        # 规则设置已在init_ui中加载
        pass
    
    def save_popup_settings(self):
        """保存弹窗设置"""
        popup_config = get_notification_setting("popup", {})
        popup_config["enabled"] = self.popup_checkbox.isChecked()
        set_notification_setting("popup", popup_config)
    
    def save_email_settings(self):
        """保存邮件设置"""
        email_config = get_notification_setting("email", {})
        email_config["enabled"] = self.email_checkbox.isChecked()
        set_notification_setting("email", email_config)
    
    def save_webhook_settings(self):
        """保存Webhook设置"""
        webhook_config = get_notification_setting("webhook", {})
        webhook_config["enabled"] = self.webhook_checkbox.isChecked()
        set_notification_setting("webhook", webhook_config)
    
    def save_sound_settings(self):
        """保存声音设置"""
        sound_config = get_notification_setting("sound", {})
        sound_config["enabled"] = self.sound_checkbox.isChecked()
        set_notification_setting("sound", sound_config)
    
    def save_all_settings(self):
        """保存所有设置"""
        try:
            # 保存规则设置
            rules = {
                "trade": {"enabled": self.trade_rule.isChecked(), "keywords": []},
                "order": {"enabled": self.order_rule.isChecked(), "keywords": []},
                "position": {"enabled": self.position_rule.isChecked(), "keywords": []},
                "error": {"enabled": self.error_rule.isChecked(), "keywords": ["错误", "异常", "失败"]},
                "risk": {"enabled": self.risk_rule.isChecked(), "keywords": ["风险", "警报", "警告"]}
            }
            set_notification_setting("rules", rules)
            
            QtWidgets.QMessageBox.information(self, "成功", "所有通知设置已保存")
            
            # 更新引擎配置
            settings = get_all_notification_settings()
            self.notification_engine.set_email_config(settings.get("email", {}))
            self.notification_engine.set_webhook_config(settings.get("webhook", {}))
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")
    
    def show_email_config(self):
        """显示邮件配置对话框"""
        dialog = EmailConfigDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            email_config = dialog.get_email_config()
            set_notification_setting("email", email_config)
            self.email_checkbox.setChecked(email_config["enabled"])
    
    def show_webhook_config(self):
        """显示Webhook配置对话框"""
        dialog = WebhookConfigDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            webhook_config = dialog.get_webhook_config()
            set_notification_setting("webhook", webhook_config)
            self.webhook_checkbox.setChecked(webhook_config["enabled"])
    
    def update_notifications(self):
        """更新通知列表"""
        notifications = self.notification_engine.get_notifications(limit=100)
        
        self.notifications_table.setRowCount(len(notifications))
        
        # 更新统计
        stats = self.notification_engine.get_notification_stats()
        self.total_label.setText(f"总通知: {len(notifications)}")
        self.trade_label.setText(f"成交: {stats.get('trade', 0)}")
        self.order_label.setText(f"订单: {stats.get('order', 0)}")
        self.error_label.setText(f"错误: {stats.get('error', 0)}")
        
        # 填充表格
        for i, notification in enumerate(notifications):
            # 时间
            time_item = QtWidgets.QTableWidgetItem(notification['timestamp'][:19])
            self.notifications_table.setItem(i, 0, time_item)
            
            # 类型
            type_item = QtWidgets.QTableWidgetItem(notification['type'])
            type_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.notifications_table.setItem(i, 1, type_item)
            
            # 标题
            title_item = QtWidgets.QTableWidgetItem(notification['title'])
            self.notifications_table.setItem(i, 2, title_item)
            
            # 消息
            message_item = QtWidgets.QTableWidgetItem(notification['message'])
            self.notifications_table.setItem(i, 3, message_item)
    
    def clear_notifications(self):
        """清空通知记录"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认", "确定要清空所有通知记录吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.notification_engine.clear_notifications()
            self.update_notifications()
    
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        self.notification_engine.close_engine()
        super().closeEvent(event)
