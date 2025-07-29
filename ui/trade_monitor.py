from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_TRADE
from vnpy.trader.object import TradeData
from vnpy.trader.constant import Direction
from vnpy.event import Event

class TradeMonitor(QtWidgets.QTableWidget):
    """
    成交监控组件
    """
    signal_trade = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.cells = {}
        
        # 设置表头
        self.headers = [
            "成交号", "委托号", "代码", "交易所", 
            "方向", "开平", "价格", "数量", 
            "时间", "接口"
        ]
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        
        # 设置表格样式
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        
        # 设置水平表头自动调整模式
        header = self.horizontalHeader()
        header.setStretchLastSection(True)  # 最后一列自动填充
        
        # 设置各列的宽度比例
        column_widths = {
            0: 100,  # 成交号
            1: 100,  # 委托号
            2: 100,  # 代码
            3: 80,   # 交易所
            4: 60,   # 方向
            5: 60,   # 开平
            6: 80,   # 价格
            7: 60,   # 数量
            8: 140,  # 时间
            9: 80    # 接口
        }
        
        # 设置列宽
        for col, width in column_widths.items():
            self.setColumnWidth(col, width)
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Interactive)  # 允许用户调整列宽
        
        # 设置表格样式
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
        
        # 注册事件监听
        self.signal_trade.connect(self.process_trade_event)
        self.event_engine.register(EVENT_TRADE, self.signal_trade.emit)

    def process_trade_event(self, event: Event) -> None:
        """处理成交事件"""
        trade: TradeData = event.data
        
        # 获取行数
        row = self.rowCount()
        self.insertRow(row)
        
        # 设置成交信息
        cells = {}
        cells["tradeid"] = QtWidgets.QTableWidgetItem(str(trade.tradeid))
        cells["orderid"] = QtWidgets.QTableWidgetItem(str(trade.orderid))
        cells["symbol"] = QtWidgets.QTableWidgetItem(trade.symbol)
        cells["exchange"] = QtWidgets.QTableWidgetItem(str(trade.exchange))
        cells["direction"] = QtWidgets.QTableWidgetItem(str(trade.direction))
        cells["offset"] = QtWidgets.QTableWidgetItem(str(trade.offset))
        cells["price"] = QtWidgets.QTableWidgetItem(str(trade.price))
        cells["volume"] = QtWidgets.QTableWidgetItem(str(trade.volume))
        cells["datetime"] = QtWidgets.QTableWidgetItem(str(trade.datetime))
        cells["gateway"] = QtWidgets.QTableWidgetItem(trade.gateway_name)
        
        # 设置单元格颜色
        if trade.direction == Direction.LONG:
            color = QtCore.Qt.red
        else:
            color = QtCore.Qt.green
            
        for cell in cells.values():
            cell.setForeground(color)
        
        # 添加到表格
        for column, cell in enumerate(cells.values()):
            self.setItem(row, column, cell)
            
        # 保存单元格引用
        self.cells[trade.vt_tradeid] = cells 