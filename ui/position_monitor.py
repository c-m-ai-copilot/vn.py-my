from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_POSITION
from vnpy.event import Event
from vnpy.trader.object import PositionData

class PositionMonitor(QtWidgets.QTableWidget):
    """持仓监控组件"""
    
    signal_position = QtCore.pyqtSignal(Event)  # 添加信号
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # 初始化界面
        self.init_ui()
        
        # 连接信号到处理函数
        self.signal_position.connect(self.process_position_event)
        
        # 注册事件监听
        self.event_engine.register(EVENT_POSITION, self.signal_position.emit)
        
        # 初始查询一次持仓数据
        self.init_position_data()
        
    def init_ui(self):
        """初始化界面"""
        labels = [
            "代码", "方向", "数量", "昨仓", "今仓", 
            "持仓均价", "持仓盈亏"
        ]
        
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        
        # 设置表格属性
        self.verticalHeader().setVisible(False)  # 隐藏行号
        self.setEditTriggers(self.NoEditTriggers)  # 不可编辑
        self.setSelectionBehavior(self.SelectRows)  # 整行选择
        self.setSelectionMode(self.SingleSelection)  # 单选模式
        
        # 设置列宽
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        # 设置样式
        self.setStyleSheet("""
            QTableWidget {
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 4px;
                border: 1px solid #CCCCCC;
                font-size: 12px;
            }
        """)
    
    def init_position_data(self):
        """初始化持仓数据"""
        positions = self.main_engine.get_all_positions()
        self.setRowCount(len(positions))
        for row, position in enumerate(positions):
            self.process_position_data(position, row)
    
    def process_position_data(self, position: PositionData, row: int):
        """处理持仓数据"""
        try:
            # 基本信息
            self.setItem(row, 0, self._create_item(position.symbol))
            
            # 方向
            direction_item = self._create_item(position.direction.value)
            if position.direction.value == "多":
                direction_item.setForeground(QtCore.Qt.red)
            else:
                direction_item.setForeground(QtCore.Qt.green)
            self.setItem(row, 1, direction_item)
            
            # 数量
            volume_item = self._create_item(str(position.volume))
            volume_item.setForeground(QtCore.Qt.red if position.direction.value == "多" else QtCore.Qt.green)
            self.setItem(row, 2, volume_item)
            
            # 昨仓和今仓
            self.setItem(row, 3, self._create_item(str(position.yd_volume)))
            self.setItem(row, 4, self._create_item(str(position.volume - position.yd_volume)))
            
            # 持仓均价
            self.setItem(row, 5, self._create_item(f"{position.price:.2f}"))
            
            # 持仓盈亏
            profit = getattr(position, "pnl", 0.0)
            if profit == 0.0:
                profit = getattr(position, "positionProfit", 0.0)
            profit_item = self._create_item(f"{profit:.2f}")
            self._set_profit_color(profit_item, profit)
            self.setItem(row, 6, profit_item)
            
        except Exception as e:
            print(f"处理持仓数据出错：{str(e)}")
    
    def process_position_event(self, event: Event):
        """处理持仓事件"""
        position = event.data
        
        # 查找是否已存在该合约的持仓
        for row in range(self.rowCount()):
            symbol = self.item(row, 0).text()
            direction = self.item(row, 1).text()
            if symbol == position.symbol and direction == position.direction.value:
                self.process_position_data(position, row)
                break
        else:
            # 不存在则添加新行
            self.insertRow(self.rowCount())
            self.process_position_data(position, self.rowCount() - 1)
    
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