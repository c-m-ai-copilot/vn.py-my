from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_ORDER
from vnpy.trader.object import OrderData
from vnpy.trader.constant import Direction, Offset, Status
from vnpy.event import Event
from config.log_manager import log_manager

class OrderMonitor(QtWidgets.QTableWidget):
    """
    委托监控组件
    """
    signal_order = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.cells = {}  # 用于存储单元格的字典
        self.order_cells = {}  # 用于存储每个委托号对应的行号
        
        # 设置表头
        self.headers = [
            "委托号", "来源", "代码", "交易所", 
            "类型", "方向", "开平", "价格", 
            "总数量", "已成交", "状态", "时间", 
            "接口", "撤单"
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
        header.setStretchLastSection(True)
        
        # 设置各列的宽度
        column_widths = {
            0: 120,  # 委托号
            1: 100,  # 来源
            2: 120,  # 代码
            3: 100,  # 交易所
            4: 80,   # 类型
            5: 80,   # 方向
            6: 80,   # 开平
            7: 100,  # 价格
            8: 80,   # 总数量
            9: 80,   # 已成交
            10: 100, # 状态
            11: 160, # 时间
            12: 100, # 接口
            13: 60   # 撤单
        }
        
        # 应用列宽设置
        header = self.horizontalHeader()
        header.setStretchLastSection(False)  # 关闭最后一列自动拉伸
        
        for col, width in column_widths.items():
            self.setColumnWidth(col, width)
            if col == 13:  # 撤单列固定宽度
                header.setSectionResizeMode(col, QtWidgets.QHeaderView.Fixed)
            else:  # 其他列可调整
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
        
        # 注册事件监听
        self.signal_order.connect(self.process_order_event)
        self.event_engine.register(EVENT_ORDER, self.signal_order.emit)
        
        # 设置最后一列的宽度（撤单按钮列）
        self.setColumnWidth(13, 60)

    def process_order_event(self, event: Event) -> None:
        """处理委托事件"""
        order: OrderData = event.data
        
        # 记录委托状态变化日志
        direction_text = "买入" if order.direction == Direction.LONG else "卖出"
        offset_text = "开仓"
        if order.offset == Offset.CLOSE:
            offset_text = "平仓"
        elif order.offset == Offset.CLOSETODAY:
            offset_text = "平今"
        elif order.offset == Offset.CLOSEYESTERDAY:
            offset_text = "平昨"
        
        # 如果是新委托或状态发生变化，记录日志
        if order.orderid not in self.order_cells or \
            self.cells[order.vt_orderid]["status"].text() != str(order.status):
            log_manager.log(
                f"委托状态更新 - 委托号：{order.orderid}，"
                f"合约：{order.symbol}，"
                f"方向：{direction_text}，"
                f"开平：{offset_text}，"
                f"价格：{order.price}，"
                f"数量：{order.volume}，"
                f"状态：{order.status}，"
                f"已成交：{order.traded}"
            )
        
        # 创建单元格
        cells = {}
        cells["orderid"] = QtWidgets.QTableWidgetItem(str(order.orderid))
        cells["source"] = QtWidgets.QTableWidgetItem(order.gateway_name)
        cells["symbol"] = QtWidgets.QTableWidgetItem(order.symbol)
        cells["exchange"] = QtWidgets.QTableWidgetItem(str(order.exchange))
        cells["type"] = QtWidgets.QTableWidgetItem(str(order.type))
        cells["direction"] = QtWidgets.QTableWidgetItem(str(order.direction))
        cells["offset"] = QtWidgets.QTableWidgetItem(str(order.offset))
        cells["price"] = QtWidgets.QTableWidgetItem(str(order.price))
        cells["volume"] = QtWidgets.QTableWidgetItem(str(order.volume))
        cells["traded"] = QtWidgets.QTableWidgetItem(str(order.traded))
        cells["status"] = QtWidgets.QTableWidgetItem(str(order.status))
        cells["datetime"] = QtWidgets.QTableWidgetItem(str(order.datetime))
        cells["gateway"] = QtWidgets.QTableWidgetItem(order.gateway_name)
        
        # 设置单元格颜色
        if order.direction == Direction.LONG:
            color = QtCore.Qt.red
        else:
            color = QtCore.Qt.green
            
        for cell in cells.values():
            cell.setForeground(color)
        
        # 添加撤单按钮
        if order.status not in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
            cancel_button = QtWidgets.QPushButton("撤单")
            cancel_button.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: #d9534f;
                    border: none;
                    padding: 2px 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c9302c;
                }
            """)
            cancel_button.clicked.connect(lambda: self.cancel_order(order))
        else:
            cancel_button = None
        
        # 检查是否已存在该委托号的行
        if order.orderid in self.order_cells:
            # 更新现有行
            row = self.order_cells[order.orderid]
            for column, cell in enumerate(cells.values()):
                self.setItem(row, column, cell)
            # 更新撤单按钮
            if cancel_button:
                self.setCellWidget(row, 13, cancel_button)
            else:
                self.removeCellWidget(row, 13)
                self.setItem(row, 13, QtWidgets.QTableWidgetItem(""))
        else:
            # 创建新行
            row = self.rowCount()
            self.insertRow(row)
            for column, cell in enumerate(cells.values()):
                self.setItem(row, column, cell)
            if cancel_button:
                self.setCellWidget(row, 13, cancel_button)
            self.order_cells[order.orderid] = row
        
        # 保存单元格引用
        self.cells[order.vt_orderid] = cells
        
        # 如果委托已完成，考虑移除该行
        if order.status in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
            # 可选：延迟一段时间后移除该行
            QtCore.QTimer.singleShot(30000, lambda: self.remove_order_row(order.orderid))

    def remove_order_row(self, orderid: str) -> None:
        """移除指定委托号的行"""
        if orderid in self.order_cells:
            row = self.order_cells[orderid]
            self.removeRow(row)
            del self.order_cells[orderid]
            # 更新其他行的索引
            for oid, r in self.order_cells.items():
                if r > row:
                    self.order_cells[oid] = r - 1

    def cancel_order(self, order: OrderData) -> None:
        """撤销委托"""
        try:
            # 获取最新的委托状态
            active_orders = self.main_engine.get_all_active_orders()
            current_order = None
            for active_order in active_orders:
                if active_order.orderid == order.orderid:
                    current_order = active_order
                    break
            
            # 检查委托是否仍然活跃
            if not current_order:
                QtWidgets.QMessageBox.warning(
                    self,
                    "撤单失败",
                    f"委托已完成或已撤销\n委托号：{order.orderid}",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            # 检查委托状态
            if current_order.status in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
                QtWidgets.QMessageBox.warning(
                    self,
                    "撤单失败",
                    f"委托状态已变更为：{current_order.status}\n委托号：{order.orderid}",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            # 创建撤单请求
            req = current_order.create_cancel_request()
            
            # 发送撤单请求
            self.main_engine.cancel_order(req, current_order.gateway_name)
            
            # 记录日志
            log_manager.log(f"发送撤单请求 - 委托号：{order.orderid}")
            
            # 显示提示
            QtWidgets.QMessageBox.information(
                self,
                "撤单请求已发送",
                f"已发送撤单请求\n委托号：{order.orderid}",
                QtWidgets.QMessageBox.Ok
            )
            
        except Exception as e:
            # 记录错误日志
            log_manager.log(f"撤单失败：{str(e)}")
            
            # 显示错误提示
            QtWidgets.QMessageBox.warning(
                self,
                "撤单失败",
                f"撤单失败：{str(e)}",
                QtWidgets.QMessageBox.Ok
            )