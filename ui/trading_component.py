# trading_component.py
# A simple trading component using vn.py with event handling

from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.object import OrderRequest, SubscribeRequest, TickData, OrderData
from vnpy.trader.constant import Direction, Offset, OrderType, Exchange, Status
from vnpy.event import Event
from pathlib import Path
import json
from config.subscribed_symbols import subscribed_symbols
from config.log_manager import log_manager

# 在文件开头添加方向映射字典
DIRECTION_VT2TXT = {
    Direction.LONG: "多",
    Direction.SHORT: "空"
}

DIRECTION_TXT2VT = {
    "多": Direction.LONG,
    "空": Direction.SHORT
}

# 在文件开头的导入部分下方添加
SUBSCRIPTION_FILE = Path("config/subscriptions.json")

# 确保配置目录存在
SUBSCRIPTION_FILE.parent.mkdir(parents=True, exist_ok=True)

# 在文件开头添加交易所映射字典
EXCHANGE_MAP = {
    "SHFE": "SHFE",  # 上期所
    "DCE": "DCE",    # 大商所
    "CZCE": "CZCE",  # 郑商所
    "CFFEX": "CFFEX",# 中金所
    "INE": "INE",    # ���中心
}

class SimpleTradingComponent(QtWidgets.QWidget):
    """简单交易组件"""
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setFixedWidth(300)  # 设置固定宽度
        
        # 创建主布局
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 创建表单布局
        form_layout = QtWidgets.QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)
        
        # 设置统一的输入框宽度
        input_width = 240
        
        # 交易所选择
        self.exchange_combo = QtWidgets.QComboBox()
        self.exchange_combo.setMinimumWidth(input_width)
        self.exchange_combo.setMaximumWidth(input_width)
        for exchange in EXCHANGE_MAP.values():
            self.exchange_combo.addItem(exchange)
        form_layout.addRow("交易所", self.exchange_combo)
        
        # 代码输入
        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.setMinimumWidth(input_width)
        self.symbol_line.setMaximumWidth(input_width)
        self.symbol_line.setText("bu2412")
        form_layout.addRow("代码", self.symbol_line)
        
        # 名称显示
        self.name_line = QtWidgets.QLineEdit()
        self.name_line.setMinimumWidth(input_width)
        self.name_line.setMaximumWidth(input_width)
        self.name_line.setText("bu2412")
        self.name_line.setReadOnly(True)
        form_layout.addRow("名称", self.name_line)
        
        # 方向选择
        self.direction_combo = QtWidgets.QComboBox()
        self.direction_combo.setMinimumWidth(input_width)
        self.direction_combo.setMaximumWidth(input_width)
        self.direction_combo.addItems(["空", "多"])
        form_layout.addRow("方向", self.direction_combo)
        
        # 开平选择
        self.offset_combo = QtWidgets.QComboBox()
        self.offset_combo.setMinimumWidth(input_width)
        self.offset_combo.setMaximumWidth(input_width)
        self.offset_combo.addItems(["平", "开"])
        form_layout.addRow("开平", self.offset_combo)
        
        # 类型选择
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.setMinimumWidth(input_width)
        self.type_combo.setMaximumWidth(input_width)
        self.type_combo.addItems(["限价"])
        form_layout.addRow("类型", self.type_combo)
        
        # 价格输入
        self.price_line = QtWidgets.QLineEdit()
        self.price_line.setMinimumWidth(input_width)
        self.price_line.setMaximumWidth(input_width)
        form_layout.addRow("价格", self.price_line)
        
        # 数量输入
        self.volume_line = QtWidgets.QLineEdit()
        self.volume_line.setMinimumWidth(input_width)
        self.volume_line.setMaximumWidth(input_width)
        form_layout.addRow("数量", self.volume_line)
        
        # 接口选择
        self.gateway_combo = QtWidgets.QComboBox()
        self.gateway_combo.setMinimumWidth(input_width)
        self.gateway_combo.setMaximumWidth(input_width)
        self.gateway_combo.addItem("CTP")
        form_layout.addRow("接口", self.gateway_combo)
        
        # 添加表单到主布局
        layout.addLayout(form_layout)
        
        # 添加委托和全撤按钮
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(10)
        
        send_button = QtWidgets.QPushButton("委托")
        send_button.setFixedHeight(24)
        send_button.clicked.connect(self.send_order)
        button_layout.addWidget(send_button)
        
        cancel_button = QtWidgets.QPushButton("全撤")
        cancel_button.setFixedHeight(24)
        cancel_button.clicked.connect(self.cancel_all)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 在底部显示价格和涨幅
        price_layout = QtWidgets.QHBoxLayout()
        
        self.price_label = QtWidgets.QLabel("3520.0")
        self.price_label.setStyleSheet("font-size: 16px;")
        price_layout.addWidget(self.price_label)
        
        self.change_label = QtWidgets.QLabel("1.21%")
        self.change_label.setStyleSheet("color: #00AA00; font-size: 16px;")
        price_layout.addWidget(self.change_label)
        
        layout.addStretch()
        layout.addLayout(price_layout)
        
        self.setLayout(layout)
        
        # 设置基本样式
        self.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #CCCCCC;
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #CCCCCC;
            }
            QPushButton {
                padding: 4px 15px;
                border: 1px solid #CCCCCC;
                background-color: #F8F9FA;
            }
            QPushButton:hover {
                background-color: #E9ECEF;
            }
            QPushButton:pressed {
                background-color: #DEE2E6;
            }
            QFormLayout {
                /* 去掉表单布局的分隔符 */
            }
            QLabel {
                /* 确保标签没有边框 */
                border: none;
            }
        """)
        
        # 去掉QFormLayout的分隔符
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        form_layout.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    
    def send_order(self):
        """发送委托"""
        try:
            symbol = self.symbol_line.text()
            exchange_text = self.exchange_combo.currentText()
            
            # 创建Exchange对象
            try:
                exchange = Exchange(exchange_text)
            except ValueError as e:
                log_manager.log(f"交易所代码无效：{exchange_text}")
                QtWidgets.QMessageBox.warning(
                    self,
                    "委托失败",
                    f"交易所代码无效：{exchange_text}",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            direction = Direction.SHORT if self.direction_combo.currentText() == "空" else Direction.LONG
            
            # 检查数量输入
            volume_text = self.volume_line.text()
            if not volume_text:
                QtWidgets.QMessageBox.warning(
                    self,
                    "委托失败",
                    "请输入数量",
                    QtWidgets.QMessageBox.Ok
                )
                return
            volume = float(volume_text)
            
            # 如果是平仓，检查持仓量
            if self.offset_combo.currentText() == "平":
                vt_symbol = f"{symbol}.{exchange.value}"
                # 获取所有持仓
                all_positions = self.main_engine.get_all_positions()
                # 过滤出当前合约的持仓
                positions = [pos for pos in all_positions if pos.vt_symbol == vt_symbol]
                
                if not positions:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "委托失败",
                        f"没有持仓：{vt_symbol}",
                        QtWidgets.QMessageBox.Ok
                    )
                    return
                
                # 分别获取多空持仓
                long_pos = 0
                short_pos = 0
                for pos in positions:
                    if pos.direction == Direction.LONG:
                        long_pos = pos.volume
                    else:
                        short_pos = pos.volume
                
                # 买(多)是平空仓，卖出(空)是平多仓
                if direction == Direction.LONG:  # 买入平空
                    if short_pos < volume:  # 检查空头持仓是否足够
                        QtWidgets.QMessageBox.warning(
                            self,
                            "委托失败",
                            f"空头持仓不足，当前持仓：{short_pos}，平仓量：{volume}",
                            QtWidgets.QMessageBox.Ok
                        )
                        return
                else:  # direction == Direction.SHORT，卖出平多
                    if long_pos < volume:  # 检查多头持仓是否足够
                        QtWidgets.QMessageBox.warning(
                            self,
                            "委托失败",
                            f"多头持仓不足，当前持仓：{long_pos}，平仓量：{volume}",
                            QtWidgets.QMessageBox.Ok
                        )
                        return
            
            # 设置开平方向
            if self.offset_combo.currentText() == "平":
                # 对于上期所和能源中心，需要区分平今平昨
                if exchange in [Exchange.SHFE, Exchange.INE]:
                    # 获取持仓
                    vt_symbol = f"{symbol}.{exchange.value}"
                    position = self.main_engine.get_position(vt_symbol)
                    
                    if position:
                        # 如果有今仓，优先平今
                        if position.yd_volume:
                            offset = Offset.CLOSETODAY
                        else:
                            offset = Offset.CLOSEYESTERDAY
                    else:
                        offset = Offset.CLOSETODAY
                else:
                    # 其他交易所不区分平今平昨
                    offset = Offset.CLOSE
            else:
                offset = Offset.OPEN
            
            # 检查价格输入
            price_text = self.price_line.text()
            if not price_text:
                QtWidgets.QMessageBox.warning(
                    self,
                    "委托失败",
                    "请输入价格",
                    QtWidgets.QMessageBox.Ok
                )
                return
            price = float(price_text)
            
            # 获取合约信息
            vt_symbol = f"{symbol}.{exchange.value}"
            contract = self.main_engine.get_contract(vt_symbol)
            
            if not contract:
                QtWidgets.QMessageBox.warning(
                    self,
                    "委托失败",
                    f"未找到合约信息：{vt_symbol}",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            # 检查价格是否合理
            last_tick = self.main_engine.get_tick(vt_symbol)
            if last_tick:
                last_price = last_tick.last_price
                if abs(price - last_price) / last_price > 0.1:  # 价格偏离超过10%
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "价格确认",
                        f"委托价格 {price} 与最新价 {last_price} 偏差较大，是否确认下单？",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.No
                    )
                    if reply == QtWidgets.QMessageBox.No:
                        return
            
            order_type = OrderType.LIMIT
            
            # 构建委托请求
            req = OrderRequest(
                symbol=symbol,
                exchange=exchange,
                direction=direction,
                type=order_type,
                offset=offset,
                price=price,
                volume=volume
            )
            
            # 获取网关名称
            gateway_name = self.gateway_combo.currentText()
            
            # 发送委托
            vt_orderid = self.main_engine.send_order(req, gateway_name)
            
            if vt_orderid:
                # 委托成功提示
                direction_text = "买入" if direction == Direction.LONG else "卖出"
                offset_text = "平仓" if offset in [Offset.CLOSE, Offset.CLOSETODAY, Offset.CLOSEYESTERDAY] else "开仓"
                
                QtWidgets.QMessageBox.information(
                    self,
                    "委托成功",
                    f"委托已发送\n"
                    f"合约：{symbol}\n"
                    f"方向：{direction_text}\n"
                    f"开平：{offset_text}\n"
                    f"价格：{price}\n"
                    f"数量：{volume}\n"
                    f"委托号：{vt_orderid}",
                    QtWidgets.QMessageBox.Ok
                )
                
                # 清空数量输入框，方便下次输入
                self.volume_line.clear()
                
                # 记录日志
                log_manager.log(f"发送委托成功 - 合约：{symbol}，方向：{direction_text}，"
                              f"开平：{offset_text}，价格：{price}，数量：{volume}，"
                              f"委托号：{vt_orderid}")
            else:
                # 委托失败提示
                QtWidgets.QMessageBox.warning(
                    self,
                    "委托失败",
                    "发送委托失败，请检查网络连接和交易接口状态",
                    QtWidgets.QMessageBox.Ok
                )
                
                # 记录日志
                log_manager.log("发送委托失败")
            
        except Exception as e:
            # 异常提示
            error_msg = str(e)
            QtWidgets.QMessageBox.warning(
                self,
                "委托失败",
                f"委托失败：{error_msg}",
                QtWidgets.QMessageBox.Ok
            )
            
            # 记录日志
            log_manager.log(f"委托失败：{error_msg}")
    
    def cancel_all(self):
        """全部撤单"""
        try:
            # 获取当前接口称
            gateway_name = self.gateway_combo.currentText()
            
            # 获取所有未完成委托
            active_orders = []
            for order in self.main_engine.get_all_active_orders():
                # 只撤销当前接口的委托
                if order.gateway_name == gateway_name:
                    active_orders.append(order)
            
            # 如果没有活动委托，显示提示
            if not active_orders:
                QtWidgets.QMessageBox.information(
                    self,
                    "提示",
                    "没有活动委托",
                    QtWidgets.QMessageBox.Ok
                )
                return
            
            # 显示确认对话框
            reply = QtWidgets.QMessageBox.question(
                self,
                "全部撤单",
                f"确认要撤销所有{len(active_orders)}个委托吗？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                # 逐个撤销委托
                for order in active_orders:
                    req = order.create_cancel_request()
                    self.main_engine.cancel_order(req, gateway_name)
                
                # 显示撤单成功提示
                QtWidgets.QMessageBox.information(
                    self,
                    "撤单成功",
                    f"已发送{len(active_orders)}个撤单请求",
                    QtWidgets.QMessageBox.Ok
                )
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "撤单失败",
                f"撤单失败：{str(e)}",
                QtWidgets.QMessageBox.Ok
            )

    def set_symbol_info(self, exchange: str, symbol: str, price: float = None):
        """
        设置合约信息
        """
        try:
            log_manager.log(f"开始设置合约信息 - 交易所：{exchange}，代码：{symbol}，价格：{price}")
            
            # 将交易所代码转换为标准格式
            exchange = exchange.upper()
            log_manager.log(f"标准化后的交易所：{exchange}")
            
            # 设置交易所
            index = self.exchange_combo.findText(exchange)
            log_manager.log(f"查找交易所'{exchange}'的索引：{index}")
            
            if index >= 0:
                self.exchange_combo.setCurrentIndex(index)
                log_manager.log(f"设置交易所成功：{exchange}")
            else:
                # 尝试使用映射
                mapped_exchange = EXCHANGE_MAP.get(exchange)
                log_manager.log(f"尝试映射交易所'{exchange}'到：{mapped_exchange}")
                
                if mapped_exchange:
                    index = self.exchange_combo.findText(mapped_exchange)
                    log_manager.log(f"查找映射交易所'{mapped_exchange}'的索引：{index}")
                    
                    if index >= 0:
                        self.exchange_combo.setCurrentIndex(index)
                        log_manager.log(f"使用映射设置交易所成功：{mapped_exchange}")
                    else:
                        log_manager.log(f"未找到交易所：{mapped_exchange}")
                else:
                    log_manager.log(f"未找到交易所映射：{exchange}")
            
            # 设置合约代码
            self.symbol_line.setText(symbol)
            self.name_line.setText(symbol)
            log_manager.log(f"已设置合约代码：{symbol}")
            
            # 如果提供了价格，设置价格
            if price is not None:
                self.price_line.setText(str(price))
                log_manager.log(f"已设置价格：{price}")
            
            # 将焦点设置到数量输入框
            self.volume_line.setFocus()
            
            log_manager.log(f"合约信息设置完成 - 交易所：{exchange}，代码：{symbol}，价格：{price}")
            
        except Exception as e:
            log_manager.log(f"设置合约信息失败：{str(e)}")
            import traceback
            log_manager.log(f"错误详情：{traceback.format_exc()}")
