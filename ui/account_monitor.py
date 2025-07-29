from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_ACCOUNT
from vnpy.event import Event
from vnpy.trader.object import AccountData

class AccountMonitor(QtWidgets.QTableWidget):
    """账户监控组件"""
    
    signal_account = QtCore.pyqtSignal(Event)  # 添加信号定义
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.cells = {}
        
        # 设置表头
        self.headers = [
            "账号", "余额", "冻结", "可用", "接口"
        ]
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        self.setRowCount(1)  # 设置为1行，因为只显示一个账户
        
        # 设置表格样式
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        
        # 设置水平表头自动调整模式
        header = self.horizontalHeader()
        header.setStretchLastSection(False)  # 关闭最后一列自动拉伸
        
        # 设置各列的宽度
        column_widths = {
            0: 120,  # 账号
            1: 120,  # 余额
            2: 120,  # 冻结
            3: 120,  # 可用
            4: 100,  # 接口
        }
        
        # 应用列宽设置
        for col, width in column_widths.items():
            self.setColumnWidth(col, width)
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Interactive)
        
        # 设置表格的最小宽度，确保能显示所有列
        min_width = sum(column_widths.values()) + 50  # 加50是为了留一些边距
        self.setMinimumWidth(min_width)
        
        # 设置样式表
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #CCCCCC;
                gridline-color: #CCCCCC;
                font-size: 12px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 4px;
                border: 1px solid #CCCCCC;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QTableWidget::item:selected {
                background-color: #e6f3ff;
            }
        """)
        
        # 连接信号到处理函数
        self.signal_account.connect(self.process_account_event)
        
        # 注册事件监听
        self.event_engine.register(EVENT_ACCOUNT, self.signal_account.emit)
        
        # 初始查询一次账户数据
        self.init_account_data()
        
    def init_account_data(self):
        """初始化账户数据"""
        accounts = self.main_engine.get_all_accounts()
        if accounts:
            self.process_account_data(accounts[0])
    
    def process_account_data(self, account: AccountData):
        """处理账户数据"""
        try:
            # 更新表格数据
            self.setItem(0, 0, self._create_item(account.accountid))  # 账号
            self.setItem(0, 1, self._create_item(f"{account.balance:.2f}"))  # 余额
            self.setItem(0, 2, self._create_item(f"{account.frozen:.2f}"))  # 冻结
            self.setItem(0, 3, self._create_item(f"{account.available:.2f}"))  # 可用
            self.setItem(0, 4, self._create_item(account.gateway_name))  # 接口
            
        except Exception as e:
            print(f"处理账户数据出错：{str(e)}")
    
    def process_account_event(self, event: Event):
        """处理资金事件"""
        account = event.data
        self.process_account_data(account)
    
    def _create_item(self, text: str) -> QtWidgets.QTableWidgetItem:
        """创建表格项"""
        item = QtWidgets.QTableWidgetItem(str(text))
        item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        return item 
    
    def _set_profit_color(self, item: QtWidgets.QTableWidgetItem, value: float) -> None:
        """设置盈亏颜色"""
        if value > 0:
            item.setForeground(QtCore.Qt.red)
        elif value < 0:
            item.setForeground(QtCore.Qt.green)