from PyQt5 import QtWidgets, QtCore
from datetime import datetime, time

class LoginDialog(QtWidgets.QDialog):
    """登录对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.init_ui()
        self.load_settings()
        
        # 设置窗口居中
        self.center()
    
    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle("登录")
        self.setFixedSize(300, 400)
        
        # 设置样式
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
        
        # 创建表单布局
        form = QtWidgets.QFormLayout()
        
        # 创建输入框
        self.userid_line = QtWidgets.QLineEdit()
        self.password_line = QtWidgets.QLineEdit()
        self.password_line.setEchoMode(QtWidgets.QLineEdit.Password)
        self.brokerid_line = QtWidgets.QLineEdit()
        self.td_address_line = QtWidgets.QLineEdit()
        self.md_address_line = QtWidgets.QLineEdit()
        self.appid_line = QtWidgets.QLineEdit()
        self.auth_code_line = QtWidgets.QLineEdit()
        
        # 添加到表单
        form.addRow("用户名", self.userid_line)
        form.addRow("密码", self.password_line)
        form.addRow("经纪商代码", self.brokerid_line)
        form.addRow("交易服务器", self.td_address_line)
        form.addRow("行情服务器", self.md_address_line)
        form.addRow("产品名称", self.appid_line)
        form.addRow("授权编码", self.auth_code_line)
        
        # 创建按钮
        button_box = QtWidgets.QDialogButtonBox()
        login_button = button_box.addButton("登录", QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_button = button_box.addButton("取消", QtWidgets.QDialogButtonBox.RejectRole)
        
        # 设置按钮样式
        login_button.setStyleSheet("""
            QPushButton {
                min-width: 80px;
                min-height: 30px;
                background-color: #1890ff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        
        cancel_button.setStyleSheet("""
            QPushButton {
                min-width: 80px;
                min-height: 30px;
                background-color: #f5f5f5;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 创建主布局
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_settings(self) -> None:
        """加载默认配置"""
        self.userid_line.setText("233998")
        self.password_line.setText("3621191@qazWSX")
        self.brokerid_line.setText("9999")
        
        # 根据当前时间选择合适的服务器地址
        current_time = datetime.now().time()
        is_trading_day = self.is_trading_day()
        
        # 交易日：16:00～次日09:00；非交易日：16:00～次日12:00
        if (time(16, 0) <= current_time or current_time <= time(9, 0)) or \
           (not is_trading_day and time(16, 0) <= current_time <= time(12, 0)):
            # 使用7x24看穿式前置（新地址）
            self.td_address_line.setText("182.254.243.31:40001")
            self.md_address_line.setText("182.254.243.31:40011")

        else:
            # 使用普通地址（新地址）
            self.td_address_line.setText("182.254.243.31:30001")
            self.md_address_line.setText("182.254.243.31:30011")
        
        self.appid_line.setText("simnow_client_test")
        self.auth_code_line.setText("0000000000000000")

    
    def is_trading_day(self) -> bool:
        """判断是否为交易日"""
        current_date = datetime.now()

        weekday = current_date.weekday()
        return weekday < 5
    
    def get_settings(self) -> dict:
        """获取设置"""
        return {
            "用户名": self.userid_line.text(),
            "密码": self.password_line.text(),
            "经纪商代码": self.brokerid_line.text(),
            "交易服务器": self.td_address_line.text(),
            "行情服务器": self.md_address_line.text(),
            "产品名称": self.appid_line.text(),
            "授权编码": self.auth_code_line.text()
            
        }
    
    def center(self) -> None:
        """将窗口移动到屏幕中央"""
        screen = QtWidgets.QApplication.desktop().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    