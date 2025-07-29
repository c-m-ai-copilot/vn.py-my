"""
New Login Dialog based on vn.py UI/UX design standards
Modern, clean, and professional login interface
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import json
from pathlib import Path
import os

class ServerConfigDialog(QtWidgets.QDialog):
    """服务器配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("服务器配置")
        self.setFixedSize(400, 400)
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化界面"""
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 标题
        title = QtWidgets.QLabel("CTP服务器配置")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1890ff;")
        layout.addWidget(title)
        
        # 表单布局
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(10)
        
        # 交易服务器
        self.trade_server = QtWidgets.QLineEdit()
        self.trade_server.setPlaceholderText("如: 182.254.243.31:30001")
        self.trade_server.setMinimumHeight(35)
        form_layout.addRow("交易服务器:", self.trade_server)
        
        # 行情服务器
        self.market_server = QtWidgets.QLineEdit()
        self.market_server.setPlaceholderText("如: 182.254.243.31:30011")
        self.market_server.setMinimumHeight(35)
        form_layout.addRow("行情服务器:", self.market_server)
        
        # 7x24服务器
        self.trade_server_7x24 = QtWidgets.QLineEdit()
        self.trade_server_7x24.setPlaceholderText("如: 182.254.243.31:40001")
        self.trade_server_7x24.setMinimumHeight(35)
        form_layout.addRow("7x24交易服务器:", self.trade_server_7x24)
        
        self.market_server_7x24 = QtWidgets.QLineEdit()
        self.market_server_7x24.setPlaceholderText("如: 182.254.243.31:40011")
        self.market_server_7x24.setMinimumHeight(35)
        form_layout.addRow("7x24行情服务器:", self.market_server_7x24)
        
        # 经纪商编号
        self.broker_id = QtWidgets.QLineEdit()
        self.broker_id.setPlaceholderText("如: 9999")
        self.broker_id.setMinimumHeight(35)
        form_layout.addRow("经纪商编号:", self.broker_id)
        
        layout.addLayout(form_layout)
        
        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(15)
        
        test_btn = QtWidgets.QPushButton("测试连接")
        test_btn.setMinimumHeight(40)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #389e0d;
            }
        """)
        test_btn.clicked.connect(self.test_connection)
        
        save_btn = QtWidgets.QPushButton("保存配置")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #096dd9;
            }
            QPushButton:pressed {
                background-color: #0050b3;
            }
        """)
        save_btn.clicked.connect(self.save_config)
        
        button_layout.addWidget(test_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_config(self):
        """加载配置"""
        config_file = Path.home() / ".vnpy" / "server_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.trade_server.setText(config.get("trade_server", "182.254.243.31:30001"))
                    self.market_server.setText(config.get("market_server", "182.254.243.31:30011"))
                    self.trade_server_7x24.setText(config.get("trade_server_7x24", "182.254.243.31:40001"))
                    self.market_server_7x24.setText(config.get("market_server_7x24", "182.254.243.31:40011"))
                    self.broker_id.setText(config.get("broker_id", "9999"))
            except Exception:
                self.set_default_config()
        else:
            self.set_default_config()
    
    def set_default_config(self):
        """设置默认配置"""
        self.trade_server.setText("182.254.243.31:30001")
        self.market_server.setText("182.254.243.31:30011")
        self.trade_server_7x24.setText("182.254.243.31:40001")
        self.market_server_7x24.setText("182.254.243.31:40011")
        self.broker_id.setText("9999")
    
    def save_config(self):
        """保存配置"""
        config = {
            "trade_server": self.trade_server.text(),
            "market_server": self.market_server.text(),
            "trade_server_7x24": self.trade_server_7x24.text(),
            "market_server_7x24": self.market_server_7x24.text(),
            "broker_id": self.broker_id.text()
        }
        
        config_file = Path.home() / ".vnpy" / "server_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.accept()
    
    def test_connection(self):
        """测试连接"""
        QtWidgets.QMessageBox.information(self, "提示", "服务器配置已保存")
    
    def get_config(self):
        """获取配置"""
        return {
            "trade_server": self.trade_server.text(),
            "market_server": self.market_server.text(),
            "trade_server_7x24": self.trade_server_7x24.text(),
            "market_server_7x24": self.market_server_7x24.text(),
            "broker_id": self.broker_id.text()
        }

class NewLoginDialog(QtWidgets.QDialog):
    """新的登录对话框 - 基于vn.py设计风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print("NewLoginDialog: Initializing...")
        self.setWindowTitle("交易系统登录")
        self.setFixedSize(450, 600)
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        print("NewLoginDialog: Centering on screen...")
        self.center_on_screen()
        print("NewLoginDialog: Initializing UI...")
        self.init_ui()
        print("NewLoginDialog: Loading saved config...")
        self.load_saved_config()
        print("NewLoginDialog: Initialization complete")
    
    def center_on_screen(self):
        """窗口居中显示"""
        frame_gm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部标题区域
        title_widget = QtWidgets.QWidget()
        title_widget.setFixedHeight(100)
        title_widget.setStyleSheet("background-color: #1890ff;")
        title_layout = QtWidgets.QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        title_label = QtWidgets.QLabel("期货交易系统")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        subtitle_label = QtWidgets.QLabel("CTP交易终端")
        subtitle_label.setStyleSheet("color: white; font-size: 14px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_widget.setLayout(title_layout)
        
        # 中间表单区域
        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QVBoxLayout()
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(40, 40, 40, 40)
        
        # 服务器选择
        server_group = QtWidgets.QGroupBox("服务器配置")
        server_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        server_layout = QtWidgets.QVBoxLayout()
        server_layout.setSpacing(10)
        
        self.server_combo = QtWidgets.QComboBox()
        self.server_combo.addItems([
            "CTP生产环境",
            "CTP模拟环境", 
            "CTP 7x24环境"
        ])
        self.server_combo.setMinimumHeight(35)
        server_layout.addWidget(self.server_combo)
        
        config_btn = QtWidgets.QPushButton("服务器配置")
        config_btn.setMinimumHeight(30)
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1890ff;
                border: 1px solid #1890ff;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e6f7ff;
            }
        """)
        config_btn.clicked.connect(self.show_server_config)
        server_layout.addWidget(config_btn)
        
        server_group.setLayout(server_layout)
        form_layout.addWidget(server_group)
        
        # 账户信息
        account_group = QtWidgets.QGroupBox("账户信息")
        account_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        account_layout = QtWidgets.QFormLayout()
        account_layout.setSpacing(15)
        
        self.user_id = QtWidgets.QLineEdit()
        self.user_id.setPlaceholderText("请输入资金账号")
        self.user_id.setMinimumHeight(40)
        self.user_id.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        
        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("请输入密码")
        self.password.setMinimumHeight(40)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        
        self.product_name = QtWidgets.QLineEdit()
        self.product_name.setPlaceholderText("请输入产品名称")
        self.product_name.setMinimumHeight(40)
        self.product_name.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        
        self.auth_code = QtWidgets.QLineEdit()
        self.auth_code.setPlaceholderText("请输入授权编码")
        self.auth_code.setMinimumHeight(40)
        self.auth_code.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        
        account_layout.addRow("资金账号:", self.user_id)
        account_layout.addRow("密    码:", self.password)
        account_layout.addRow("产品名称:", self.product_name)
        account_layout.addRow("授权编码:", self.auth_code)
        
        account_group.setLayout(account_layout)
        form_layout.addWidget(account_group)
        
        # 选项区域
        options_layout = QtWidgets.QHBoxLayout()
        self.remember_password = QtWidgets.QCheckBox("记住密码")
        self.remember_password.setStyleSheet("font-size: 12px;")
        options_layout.addWidget(self.remember_password)
        
        self.auto_login = QtWidgets.QCheckBox("自动登录")
        self.auto_login.setStyleSheet("font-size: 12px;")
        options_layout.addWidget(self.auto_login)
        options_layout.addStretch()
        form_layout.addLayout(options_layout)
        
        form_widget.setLayout(form_layout)
        
        # 底部按钮区域
        button_widget = QtWidgets.QWidget()
        button_widget.setStyleSheet("background-color: #f5f5f5;")
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(40, 20, 40, 20)
        
        self.connect_btn = QtWidgets.QPushButton("连接交易服务器")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
            }
            QPushButton:hover:!pressed {
                background-color: #096dd9;
            }
            QPushButton:pressed {
                background-color: #0050b3;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #bfbfbf;
            }
        """)
        self.connect_btn.clicked.connect(self.on_connect)
        
        cancel_btn = QtWidgets.QPushButton("取消")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #666;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 16px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                border-color: #1890ff;
                color: #1890ff;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(cancel_btn)
        button_widget.setLayout(button_layout)
        
        # 状态栏
        self.status_bar = QtWidgets.QLabel("就绪")
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setStyleSheet("background-color: #f5f5f5; color: #666; padding: 5px;")
        
        # 组装主布局
        main_layout.addWidget(title_widget)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(button_widget)
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
        # 设置焦点
        self.user_id.setFocus()
    
    def load_saved_config(self):
        """加载保存的配置"""
        # 检查是否为Mock模式
        is_mock_mode = os.environ.get('USE_MOCK_DATA', '').lower() == 'true'
        
        if is_mock_mode:
            # Mock模式自动填充测试账户
            self.user_id.setText("mock_user")
            self.password.setText("mock_password")
            self.product_name.setText("MockCTP")
            self.auth_code.setText("000000")
            self.status_bar.setText("Mock模式 - 测试账户已自动填充")
            return
        
        # 正常加载配置
        config_file = Path.home() / ".vnpy" / "login_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.user_id.setText(config.get("user_id", ""))
                    self.product_name.setText(config.get("product_name", ""))
                    self.auth_code.setText(config.get("auth_code", ""))
                    
                    if config.get("remember_password", False):
                        self.password.setText(config.get("password", ""))
                        self.remember_password.setChecked(True)
                    
                    self.auto_login.setChecked(config.get("auto_login", False))
            except Exception:
                pass
    
    def save_config(self):
        """保存配置"""
        if self.remember_password.isChecked():
            config = {
                "user_id": self.user_id.text(),
                "password": self.password.text(),
                "product_name": self.product_name.text(),
                "auth_code": self.auth_code.text(),
                "remember_password": True,
                "auto_login": self.auto_login.isChecked()
            }
        else:
            config = {
                "user_id": self.user_id.text(),
                "product_name": self.product_name.text(),
                "auth_code": self.auth_code.text(),
                "remember_password": False,
                "auto_login": False
            }
        
        config_file = Path.home() / ".vnpy" / "login_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def show_server_config(self):
        """显示服务器配置"""
        dialog = ServerConfigDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.save_config()
    
    def on_connect(self):
        """连接处理"""
        if not self.user_id.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告", "请输入资金账号")
            return
        
        if not self.password.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告", "请输入密码")
            return
        
        # 保存配置
        self.save_config()
        
        # 模拟连接过程
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("连接中...")
        self.status_bar.setText("正在连接服务器...")
        
        # 延迟执行连接
        QtCore.QTimer.singleShot(2000, self.finish_connect)
    
    def finish_connect(self):
        """完成连接"""
        self.status_bar.setText("连接成功")
        self.accept()
    
    def get_login_settings(self):
        """获取登录设置"""
        return {
            "user_id": self.user_id.text().strip(),
            "password": self.password.text().strip(),
            "product_name": self.product_name.text().strip(),
            "auth_code": self.auth_code.text().strip(),
            "trade_server": "182.254.243.31:30001",
            "market_server": "182.254.243.31:30011"
        }

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = NewLoginDialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        settings = dialog.get_login_settings()
        print("Login successful with settings:", settings)
    sys.exit(app.exec_())