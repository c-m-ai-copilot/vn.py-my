from typing import Dict, List
from datetime import datetime, timedelta

from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np

from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import BarData, TickData, HistoryRequest, ContractData
from vnpy.trader.constant import Interval, Direction, Exchange
from vnpy.trader.utility import BarGenerator
from vnpy.trader.event import EVENT_TICK
from config.log_manager import log_manager

# 设置pyqtgraph的全局样式
pg.setConfigOptions(
    antialias=True,  # 开启抗锯齿
    background='k',  # 黑色背景
    foreground='w'   # 白色前景
)

class CustomAxisItem(pg.AxisItem):
    """自定义坐标轴项"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyle(tickFont=QtGui.QFont("Arial", 8))
        
    def tickStrings(self, values, scale, spacing):
        """重写刻度字符串格式化方法"""
        if self.orientation == "left":
            # 价格轴显示两位小数
            return [f"{value:.2f}" for value in values]
        elif self.orientation == "bottom":
            try:
                # 时间轴显示时分秒
                return [datetime.fromtimestamp(value).strftime("%H:%M:%S") if value > 0 else "" for value in values]
            except (ValueError, OSError):
                return ["" for _ in values]
        return super().tickStrings(values, scale, spacing)

class FuturesChart(QtWidgets.QWidget):
    """期货K线图组件"""
    
    # 将信号定义为类属性
    signal_tick = QtCore.pyqtSignal(Event)
    
    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        contract: ContractData
    ):
        """构造函数"""
        try:
            print("开始初始化图表...", flush=True)
            super().__init__()
            
            self.main_engine = main_engine
            self.event_engine = event_engine
            self.contract = contract
            
            print(f"初始化图表 - 合约: {contract.vt_symbol}", flush=True)
            
            # 添加活动状态标志
            self.is_active = True
            
            # 初始化数据
            self.bars: List[BarData] = []
            self.ticks: List[TickData] = []
            self.vt_symbol = contract.vt_symbol
            
            # 连接信号到
            print("连接信号...", flush=True)
            self.signal_tick.connect(self._process_tick_event)
            
            # 创建K线生成器
            print("创建K线生成器...", flush=True)
            self.bg = BarGenerator(
                on_bar=self.on_bar,
                window=1,
                on_window_bar=None,  # 移除window_bar回调
                interval=Interval.MINUTE  # 使用分钟K线
            )
            
            # 设置K线更新间隔（秒）
            self.update_interval = 5  # 5秒一根K线
            self.last_tick_time = None
            self.current_bar = None  # 用于存储当前正在更新的K线
            
            # 初始化价格数据列表
            self.prices = []
            self.times = []
            
            # 初始化界面
            print("初始化界面...", flush=True)
            self.init_ui()
            
            # 注册事件监听
            print("注册事件监听...", flush=True)
            self.register_event()
            
            print("初始化完成，准备加载历史数据...", flush=True)
            
            # 延迟加载历史数据
            QtCore.QTimer.singleShot(100, self.load_history)  # 增加延迟到100ms
            
            # 添加数据缓存标志
            self.need_update = False
            
        except Exception as e:
            print(f"图表初始化失败: {str(e)}", flush=True)
            import traceback
            print(f"错误详情：{traceback.format_exc()}", flush=True)
        
    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle(f"{self.contract.symbol} - K线图表")
        self.resize(1000, 600)
        
        # 设置深色背景样式
        self.setStyleSheet("""
            QWidget {
                background-color: #1e222d;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
        """)
        
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(0)  # 减小间距
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.setLayout(main_layout)
        
        # 创建K线画布
        self.canvas = pg.GraphicsLayoutWidget()
        self.canvas.setBackground('#1e222d')  # 使用与主界面相同的深色背景
        main_layout.addWidget(self.canvas)
        
        # 创建K线图
        self.kline_plot = self.canvas.addPlot(
            row=0, col=0, 
            axisItems={
                'bottom': CustomAxisItem(orientation='bottom'),
                'left': CustomAxisItem(orientation='left')
            }
        )
        
        # 设置K线图样式
        self.kline_plot.showGrid(True, True, alpha=0.1)  # 降低网格透明度
        self.kline_plot.getAxis('left').setTextPen('white')  # 设置坐标轴文字颜色
        self.kline_plot.getAxis('bottom').setTextPen('white')
        self.kline_plot.getAxis('left').setPen((255, 255, 255, 30))  # 设置坐标轴线条颜色和透明度
        self.kline_plot.getAxis('bottom').setPen((255, 255, 255, 30))
        
        # 创建成交量图
        self.volume_plot = self.canvas.addPlot(
            row=1, col=0,
            axisItems={
                'bottom': CustomAxisItem(orientation='bottom'),
                'left': CustomAxisItem(orientation='left')
            }
        )
        
        # 设置成交量图样式
        self.volume_plot.showGrid(True, True, alpha=0.1)
        self.volume_plot.getAxis('left').setTextPen('white')
        self.volume_plot.getAxis('bottom').setTextPen('white')
        self.volume_plot.getAxis('left').setPen((255, 255, 255, 30))
        self.volume_plot.getAxis('bottom').setPen((255, 255, 255, 30))
        
        # 设置图表比例
        self.canvas.ci.layout.setRowStretchFactor(0, 4)  # K线图占4份
        self.canvas.ci.layout.setRowStretchFactor(1, 1)  # 成交量图占1份
        self.canvas.ci.layout.setSpacing(0)  # 减小图表间距
        
        # 关联X轴
        self.volume_plot.setXLink(self.kline_plot)
        
        # 添加十字光标
        self.vLine = pg.InfiniteLine(
            angle=90, 
            movable=False,
            pen=pg.mkPen({
                'color': (255, 255, 255, 100),
                'width': 1,
                'style': QtCore.Qt.DashLine
            })
        )
        self.hLine = pg.InfiniteLine(
            angle=0, 
            movable=False,
            pen=pg.mkPen({
                'color': (255, 255, 255, 100),
                'width': 1,
                'style': QtCore.Qt.DashLine
            })
        )

        # 初始时隐藏十字光标
        self.vLine.hide()
        self.hLine.hide()

        self.kline_plot.addItem(self.vLine, ignoreBounds=True)
        self.kline_plot.addItem(self.hLine, ignoreBounds=True)

        # 添加标签
        self.label = pg.TextItem(
            html='',
            anchor=(0, 0),
            border=None,
            fill=None
        )
        self.label.hide()
        self.kline_plot.addItem(self.label)

        # 绑定鼠标事件
        self.proxy = pg.SignalProxy(
            self.kline_plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouse_moved
        )
        
        # 设置坐标样式
        for plot in [self.kline_plot, self.volume_plot]:
            # 设置左轴样式
            left_axis = plot.getAxis('left')
            left_axis.setStyle(tickFont=QtGui.QFont("Arial", 10))
            left_axis.setLabel(text='', font=QtGui.QFont("Arial", 10))
            left_axis.setPen(pg.mkPen('w', width=1))
            
            # 设置底轴样式
            bottom_axis = plot.getAxis('bottom')
            bottom_axis.setStyle(tickFont=QtGui.QFont("Arial", 10))
            bottom_axis.setLabel(text='', font=QtGui.QFont("Arial", 10))
            bottom_axis.setPen(pg.mkPen('w', width=1))
            
            # 设置网格
            plot.showGrid(True, True, alpha=0.2)
        
    def load_history(self) -> None:
        """加载历史数据"""
        try:
            print(f"开始加载历史数据：{self.vt_symbol}")
            
            end = datetime.now()
            start = end - timedelta(days=3)  # 加载3天数据
            
            req = HistoryRequest(
                symbol=self.contract.symbol,
                exchange=self.contract.exchange,
                start=start,
                end=end,
                interval=Interval.MINUTE
            )
            
            print(f"查询历史数据：{start} - {end}")
            history = self.main_engine.query_history(req, self.contract.gateway_name)
            
            if history:
                print(f"获取到历史数据：{len(history)} 条")
                self.bars = history  # 直接赋值，而不是extend
                self.update_chart()
            else:
                print("未获取到历史数据，等待实时数据...")
                # 不再生成测试数据，而是等待实时数据
                self.bars = []
                
        except Exception as e:
            print(f"加载历史数据失败：{str(e)}")
            import traceback
            print(f"错误详情：{traceback.format_exc()}")

    def generate_test_data(self) -> None:
        """生成测试数据"""
        print("生成测试数据")
        
        current_time = datetime.now().replace(second=0, microsecond=0)
        
        # 获取最新行情数据作为基准价格
        tick = self.main_engine.get_tick(self.vt_symbol)
        if tick:
            base_price = tick.last_price
        else:
            # 如果没有行情数据，用合约的最小变动价位��估算个合理的价格
            contract = self.contract
            if contract.pricetick >= 1:
                base_price = round(contract.pricetick * 1000)  # 对于期货等大数值合约
            else:
                base_price = round(1/contract.pricetick)  # 对于股票等小数值合约
        
        print(f"使用基准价格：{base_price}")
        price = base_price  # 起始价格
        
        for i in range(100):  # 生成100条数据
            time = current_time - timedelta(minutes=i)
            
            # 生成合理范围的价格变动
            price_tick = self.contract.pricetick
            max_change = max(price_tick * 10, price * 0.002)  # 最大变动为千分之或10个最小变动价位
            
            # 随机生成价格变动
            price_change = np.random.uniform(-max_change, max_change)
            close = round(price + price_change)
            high = round(max(price, close) + abs(np.random.uniform(0, max_change/2)))
            low = round(min(price, close) - abs(np.random.uniform(0, max_change/2)))
            
            # 确保价格为最小变动价位的整数倍
            close = round(close / price_tick) * price_tick
            high = round(high / price_tick) * price_tick
            low = round(low / price_tick) * price_tick
            open_price = round(price / price_tick) * price_tick
            
            bar = BarData(
                symbol=self.contract.symbol,
                exchange=self.contract.exchange,
                datetime=time,
                interval=Interval.MINUTE,
                volume=np.random.randint(100, 1000),
                open_price=open_price,
                high_price=high,
                low_price=low,
                close_price=close,
                gateway_name=self.contract.gateway_name
            )
            
            self.bars.append(bar)
            price = close
        
        # 反转数据列表，使时间正序
        self.bars.reverse()
        
        print(f"生成测试数据完成：{len(self.bars)} 条")
        self.update_chart()
        
    def update_chart(self) -> None:
        """更新图表"""
        try:
            if not self.bars:
                return
            
            print(f"\n开始更新图表，当前K线数量: {len(self.bars)}")
            
            # 清除现有图形
            self.kline_plot.clear()
            self.volume_plot.clear()
            
            # 准备数据
            x = np.arange(len(self.bars))
            open_prices = np.array([bar.open_price for bar in self.bars])
            high_prices = np.array([bar.high_price for bar in self.bars])
            low_prices = np.array([bar.low_price for bar in self.bars])
            close_prices = np.array([bar.close_price for bar in self.bars])
            volumes = np.array([bar.volume for bar in self.bars])
            
            # 计算合适的价格和成交量刻度
            price_range = high_prices.max() - low_prices.min()
            price_tick = self.contract.pricetick
            price_step = max(price_tick * 10, price_range / 10)  # 确保至少显示10个刻度
            
            volume_max = volumes.max()
            volume_step = volume_max / 5  # 显示5个成交量刻度
            
            # 设置Y轴刻度
            self.kline_plot.getAxis('left').setTickSpacing(price_step, price_step/2)
            self.volume_plot.getAxis('left').setTickSpacing(volume_step, volume_step/2)
            
            # 绘制K线和成交量
            rise = close_prices >= open_prices
            fall = ~rise
            
            if np.any(rise):
                self._draw_candle(x[rise], open_prices[rise], high_prices[rise], 
                                low_prices[rise], close_prices[rise], 'r')
            if np.any(fall):
                self._draw_candle(x[fall], open_prices[fall], high_prices[fall], 
                                low_prices[fall], close_prices[fall], 'g')
            
            self._draw_volume(x, volumes, rise)
            
            # 更新显示范围
            visible_range = (max(0, len(self.bars)-100), len(self.bars))
            self.kline_plot.setXRange(*visible_range)
            self.volume_plot.setXRange(*visible_range)
            
            # 更新时间轴
            times = [bar.datetime.strftime('%H:%M:%S') for bar in self.bars]
            xdict = dict(enumerate(times))
            axis_ticks = [(i, xdict[i]) for i in range(len(times)) if i % 5 == 0]  # 每5个显示一个时间
            self.kline_plot.getAxis('bottom').setTicks([axis_ticks])
            self.volume_plot.getAxis('bottom').setTicks([axis_ticks])

            # 设置时间刻度
            self.kline_plot.getAxis('bottom').setTickFont(QtGui.QFont("Arial", 10))
            self.volume_plot.getAxis('bottom').setTickFont(QtGui.QFont("Arial", 10))
            
            # 设置时间轴标签
            self.kline_plot.getAxis('bottom').setLabel(text='时间', font=QtGui.QFont("Arial", 10))
            self.volume_plot.getAxis('bottom').setLabel(text='时间', font=QtGui.QFont("Arial", 10))
            
            # # 设置时间轴标签颜色
            # self.kline_plot.getAxis('bottom').setLabelPen(pg.mkPen('white', width=1))
            # self.volume_plot.getAxis('bottom').setLabelPen(pg.mkPen('white', width=1))
            
            # 设置时间轴标签位置
            # self.kline_plot.getAxis('bottom').setLabelOffset(10)
            # self.volume_plot.getAxis('bottom').setLabelOffset(10)
            
            # 设置时间轴标签对齐方式
            # self.kline_plot.getAxis('bottom').setLabelAlignment(QtCore.Qt.AlignLeft)
            # self.volume_plot.getAxis('bottom').setLabelAlignment(QtCore.Qt.AlignLeft)
            
            print("图表更新完成\n")
            
        except Exception as e:
            print(f"更新图表失败：{str(e)}")

    def _draw_candle(self, x, open, high, low, close, color) -> None:
        """绘制K线"""
        try:
            # 设置K线宽度
            width = 0.4  # K线宽度
            
            # 设置画笔和画刷颜色
            if color == 'r':  # 红色
                pen = pg.mkPen('r', width=1)
                brush = pg.mkBrush('r')
            else:  # 绿色
                pen = pg.mkPen('g', width=1)
                brush = pg.mkBrush('g')  # 改为绿色填充
            
            # 绘制K线实体
            for i, (x_, o, h, l, c) in enumerate(zip(x, open, high, low, close)):
                # 绘制上下影线
                self.kline_plot.plot(
                    [x_, x_],
                    [l, h],
                    pen=pen
                )
                
                # 创建K线实体
                rect = QtWidgets.QGraphicsRectItem(
                    x_ - width/2,  # 左边界
                    min(o, c),     # 下边界
                    width,         # 宽度
                    abs(o - c)     # 高度
                )
                
                # 设置画笔和画刷
                rect.setPen(pen)
                rect.setBrush(brush)  # 直接使用对应颜色的画刷
                
                # 添加到图表
                self.kline_plot.addItem(rect)
                
        except Exception as e:
            print(f"绘制K线失败：{str(e)}")
            import traceback
            print(f"错误详情：{traceback.format_exc()}")

    def _draw_volume(self, x, volume, rise):
        """绘制成交量"""
        try:
            # 设置成交量柱状图宽度
            width = 0.6
            
            # 计算下跌标记
            fall = ~rise  # 添加这行来定义 fall
            
            # 分别绘制上涨和下跌的成交量柱
            volume_rise = pg.BarGraphItem(
                x=x[rise],
                height=volume[rise],
                width=width,
                brush='r',
                pen=pg.mkPen('r', width=0.5)
            )
            volume_fall = pg.BarGraphItem(
                x=x[fall],
                height=volume[fall],
                width=width,
                brush='g',
                pen=pg.mkPen('g', width=0.5)
            )
            
            self.volume_plot.addItem(volume_rise)
            self.volume_plot.addItem(volume_fall)
            
        except Exception as e:
            print(f"绘制成交量���败：{str(e)}")
            import traceback
            print(f"错误详情：{traceback.format_exc()}")

    def mouse_moved(self, evt):
        """处理鼠标移动事件"""
        try:
            pos = evt[0]
            
            if self.kline_plot.sceneBoundingRect().contains(pos):
                mouse_point = self.kline_plot.vb.mapSceneToView(pos)
                index = int(mouse_point.x())
                
                if 0 <= index < len(self.bars):
                    bar = self.bars[index]
                    
                    # 更新十字光标
                    self.vLine.setPos(mouse_point.x())
                    self.hLine.setPos(mouse_point.y())
                    
                    # 计算涨跌幅
                    pre_close = self.bars[index-1].close_price if index > 0 else bar.open_price
                    change = bar.close_price - pre_close
                    change_percent = (change / pre_close * 100) if pre_close != 0 else 0
                    
                    # 更新标签
                    self.label.setHtml(
                        f"""
                        <div style='background-color:rgba(17, 17, 17, 0.8);color:white;padding:5px;border:1px solid gray'>
                            <div style='color:white;font-weight:bold'>
                                时间：{bar.datetime.strftime("%H:%M:%S")}
                            </div>
                            <div style='color:{"red" if bar.close_price >= bar.open_price else "green"}'>
                                开盘：{bar.open_price:.2f}<br>
                                最高：{bar.high_price:.2f}<br>
                                最低：{bar.low_price:.2f}<br>
                                收盘：{bar.close_price:.2f}
                            </div>
                            <div style='color:{"red" if change >= 0 else "green"}'>
                                涨跌：{change:+.2f} ({change_percent:+.2f}%)
                            </div>
                            <div style='color:white'>
                                成交量：{bar.volume}
                            </div>
                        </div>
                        """
                    )
                    
                    # 设置标签位置
                    view_range = self.kline_plot.viewRange()
                    label_x = mouse_point.x()
                    label_y = view_range[1][1]  # Y轴最大值
                    
                    # 如果标签会超出右边界，则显示在左边
                    if label_x > (view_range[0][1] - view_range[0][0]) * 0.7:
                        self.label.setAnchor((1, 0))  # 右对齐
                    else:
                        self.label.setAnchor((0, 0))  # 左对齐
                    
                    self.label.setPos(label_x, label_y)
                    
                    # 显示十字光标和标签
                    self.vLine.show()
                    self.hLine.show()
                    self.label.show()
                else:
                    # 隐藏十字光标和标签
                    self.vLine.hide()
                    self.hLine.hide()
                    self.label.hide()
                
        except Exception as e:
            print(f"处理鼠标移动事件失败：{str(e)}")

    def register_event(self) -> None:
        """注册事件监听"""
        self.event_engine.register(EVENT_TICK + self.vt_symbol, self.signal_tick.emit)

    def _process_tick_event(self, event: Event) -> None:
        """处理TICK事件"""
        try:
            if not self.is_active:
                return
            
            tick = event.data
            if tick.vt_symbol == self.vt_symbol:
                print(f"收到TICK数据: {tick.vt_symbol}, 最新价: {tick.last_price}, 时间: {tick.datetime}")
                
                current_time = tick.datetime
                
                # 如果是第一个tick或者已经过了更新间隔
                if (not self.last_tick_time or 
                    (current_time - self.last_tick_time).total_seconds() >= self.update_interval):
                    
                    # 创建新的K线
                    self.current_bar = BarData(
                        symbol=tick.symbol,
                        exchange=tick.exchange,
                        datetime=current_time.replace(microsecond=0),
                        interval=Interval.MINUTE,  # 仍然使用分钟级别
                        volume=tick.volume,
                        turnover=tick.turnover,
                        open_price=tick.last_price,
                        high_price=tick.last_price,
                        low_price=tick.last_price,
                        close_price=tick.last_price,
                        gateway_name=tick.gateway_name
                    )
                    
                    if not self.bars:
                        print(f"创建第一根K线: {self.current_bar.datetime}, 开:{self.current_bar.open_price}")
                    else:
                        print(f"创建新K线: {self.current_bar.datetime}, 开:{self.current_bar.open_price}")
                    
                    self.bars.append(self.current_bar)
                    self.last_tick_time = current_time
                    
                    # 保持最近100根K线
                    if len(self.bars) > 100:
                        self.bars = self.bars[-100:]
                    
                    # 更新图表
                    self.update_chart()
                else:
                    # 更新当前K线
                    if self.current_bar:
                        self.current_bar.high_price = max(self.current_bar.high_price, tick.last_price)
                        self.current_bar.low_price = min(self.current_bar.low_price, tick.last_price)
                        self.current_bar.close_price = tick.last_price
                        self.current_bar.volume = tick.volume
                        self.current_bar.turnover = tick.turnover
                        
                        print(f"更新K线: {self.current_bar.datetime}, 高:{self.current_bar.high_price}, 低:{self.current_bar.low_price}, 收:{self.current_bar.close_price}")
                        self.update_chart()
            
        except Exception as e:
            print(f"处理TICK事件失败：{str(e)}")
            import traceback
            print(f"错误详情：{traceback.format_exc()}")

    def on_bar(self, bar: BarData) -> None:
        """K线更新回调"""
        try:
            print(f"收到K线更新: {bar.datetime}, 开:{bar.open_price}, 高:{bar.high_price}, 低:{bar.low_price}, 收:{bar.close_price}")
            
            # 更新最新一根K线或添加新K线
            if self.bars and bar.datetime == self.bars[-1].datetime:
                print(f"更新最新一根K线: {bar.datetime}")
                self.bars[-1] = bar
            else:
                print(f"添加新K线: {bar.datetime}")
                self.bars.append(bar)
                # 保持最近1000根K线
                if len(self.bars) > 1000:
                    self.bars = self.bars[-1000:]
            
            # 立即更新图表
            QtCore.QTimer.singleShot(0, self.update_chart)
            
        except Exception as e:
            print(f"K线更新失败：{str(e)}")
            import traceback
            print(f"错误详情：{traceback.format_exc()}")

    def on_window_bar(self, bar: BarData) -> None:
        """K线周期更新回调"""
        try:
            # 更新最新一根K线
            if self.bars and bar.datetime == self.bars[-1].datetime:
                self.bars[-1] = bar
            else:
                self.bars.append(bar)
            
            # 使用 QTimer 延迟更新图表
            QtCore.QTimer.singleShot(0, self.update_chart)
            
        except Exception as e:
            print(f"K线周期更新失败：{str(e)}")

    def closeEvent(self, event) -> None:
        """关闭窗口事件"""
        try:
            # 停止定时器
            # self.update_timer.stop()
            
            # 停止更新
            self.is_active = False
            
            # 清除图项
            self.kline_plot.clear()
            self.volume_plot.clear()
            
            # 移除十字光标
            if hasattr(self, 'vLine'):
                self.kline_plot.removeItem(self.vLine)
                self.vLine = None
            if hasattr(self, 'hLine'):
                self.kline_plot.removeItem(self.hLine)
                self.hLine = None
            
            # 移除标签
            if hasattr(self, 'label'):
                self.kline_plot.removeItem(self.label)
                self.label = None
            
            # 取消事件注册
            self.event_engine.unregister(EVENT_TICK + self.vt_symbol, self.signal_tick.emit)
            
            # 清理数据
            self.bars = []
            self.ticks = []
            
            # 强制清理内存
            import gc
            gc.collect()
            
            event.accept()
            
        except Exception as e:
            print(f"关闭图表窗口出错：{str(e)}")

class FuturesChartWindow(QtWidgets.QMainWindow):
    """期货图口"""
    
    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        contract: ContractData
    ):
        super().__init__()
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.contract = contract
        
        # 创建图表组件
        self.chart = FuturesChart(main_engine, event_engine, contract)
        
        # 初始化界面
        self.init_ui()
        
    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle(f"{self.contract.symbol} - 期货图表")
        self.resize(1200, 800)
        
        # 设置深色背景样式
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e222d;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 12px;
                padding: 2px 5px;
            }
            QGroupBox {
                border: 1px solid #2b2b2b;
                margin-top: 5px;
                font-size: 12px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QComboBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #363c4e;
                border-radius: 2px;
                padding: 3px 5px;
                min-width: 70px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QStatusBar {
                background-color: #1e222d;
                color: white;
            }
            QStatusBar QLabel {
                border-right: 1px solid #2b2b2b;
                padding: 3px 10px;
            }
        """)
        
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        central_widget.setLayout(main_layout)
        
        # 创建上部信息区域
        info_group = QtWidgets.QGroupBox("合约信息")
        info_layout = QtWidgets.QHBoxLayout()
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加合约信息
        info_layout.addWidget(QtWidgets.QLabel(f"代码：{self.contract.symbol}"))
        info_layout.addWidget(QtWidgets.QLabel(f"交易所：{self.contract.exchange.value}"))
        info_layout.addWidget(QtWidgets.QLabel(f"名称：{self.contract.name}"))
        info_layout.addWidget(QtWidgets.QLabel(f"合约乘数：{self.contract.size}"))
        info_layout.addWidget(QtWidgets.QLabel(f"价格单位：{self.contract.pricetick}"))
        
        # 添加周期选择
        period_label = QtWidgets.QLabel("周期：")
        period_combo = QtWidgets.QComboBox()
        period_combo.addItems(["1分钟", "5分钟", "15分钟", "30分钟", "1小时", "日线"])
        info_layout.addWidget(period_label)
        info_layout.addWidget(period_combo)
        
        info_layout.addStretch()
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # 创建图表区域
        chart_group = QtWidgets.QGroupBox("图表")
        chart_layout = QtWidgets.QVBoxLayout()
        chart_layout.setSpacing(0)
        chart_layout.setContentsMargins(1, 1, 1, 1)
        chart_layout.addWidget(self.chart)
        chart_group.setLayout(chart_layout)
        main_layout.addWidget(chart_group)
        
        # 创建底部状态栏
        status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(status_bar)
        
        # 创建状态栏标签
        self.price_label = QtWidgets.QLabel("最新价：--")
        self.change_label = QtWidgets.QLabel("涨跌：--")
        self.volume_label = QtWidgets.QLabel("成交量：--")
        self.open_interest_label = QtWidgets.QLabel("持仓量：--")
        
        # 添加状态信息
        status_bar.addPermanentWidget(self.price_label)
        status_bar.addPermanentWidget(self.change_label)
        status_bar.addPermanentWidget(self.volume_label)
        status_bar.addPermanentWidget(self.open_interest_label)
        
        # 注册TICK事件，用更新状态栏
        self.event_engine.register(
            EVENT_TICK + self.contract.vt_symbol, 
            self.update_status_bar
        )

    def update_status_bar(self, event: Event) -> None:
        """更新状态栏"""
        try:
            tick = event.data
            if tick.vt_symbol == self.contract.vt_symbol:
                self.price_label.setText(f"最新价：{tick.last_price:.2f}")
                
                # 计算涨跌
                change = tick.last_price - tick.pre_close if tick.pre_close else 0
                self.change_label.setText(f"涨跌：{change:.2f}")
                
                # 设置颜色
                if change > 0:
                    self.price_label.setStyleSheet("color: red")
                    self.change_label.setStyleSheet("color: red")
                elif change < 0:
                    self.price_label.setStyleSheet("color: green")
                    self.change_label.setStyleSheet("color: green")
                else:
                    self.price_label.setStyleSheet("")
                    self.change_label.setStyleSheet("")
                
                self.volume_label.setText(f"成交量：{tick.volume}")
                self.open_interest_label.setText(f"持仓量：{tick.open_interest}")
                
        except Exception as e:
            print(f"更新状态栏失败：{str(e)}")

    def update_chart(self, tick: TickData) -> None:
        """更新图表数据"""
        try:
            # 更新最新价格
            self.prices.append(tick.last_price)
            self.times.append(tick.datetime)
            
            # 保持固定数量的数据点
            if len(self.prices) > self.max_points:
                self.prices = self.prices[-self.max_points:]
                self.times = self.times[-self.max_points:]
            
            # 清除旧数据
            self.price_curve.clear()
            
            # 设置X轴为时间
            timestamps = [t.timestamp() for t in self.times]
            self.plot_widget.getAxis('bottom').setTicks([
                [
                    (idx, t.strftime('%H:%M:%S')) 
                    for idx, t in zip(timestamps, self.times)
                ]
            ])
            
            # 绘制价格曲线
            self.price_curve.setData(
                x=timestamps,
                y=self.prices,
                pen=self.price_pen
            )
            
            # 自动调整Y轴范围
            if self.prices:
                min_price = min(self.prices)
                max_price = max(self.prices)
                price_range = max_price - min_price
                
                # 设置一定的边距
                margin = price_range * 0.1 if price_range > 0 else 0.1
                self.plot_widget.setYRange(
                    min_price - margin,
                    max_price + margin
                )
            
            # 更新最新价格标签
            if self.prices:
                self.price_label.setText(f"最新价：{self.prices[-1]:.2f}")
            
        except Exception as e:
            print(f"更新图表失败：{str(e)}")

    def init_chart(self) -> None:
        """初始化图表"""
        # 创建绘图窗口
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(True, True)
        self.plot_widget.setBackground('w')
        
        # 设置X轴为时间轴
        self.plot_widget.getAxis('bottom').setLabel('时间')
        self.plot_widget.getAxis('bottom').setPen('k')
        self.plot_widget.getAxis('bottom').setStyle(tickFont=QtGui.QFont("Arial", 8))
        
        # 设置Y轴
        self.plot_widget.getAxis('left').setLabel('价格')
        self.plot_widget.getAxis('left').setPen('k')
        self.plot_widget.getAxis('left').setStyle(tickFont=QtGui.QFont("Arial", 8))
        
        # 创建价格曲线
        self.price_pen = pg.mkPen({
            'color': 'b',
            'width': 1
        })
        self.price_curve = self.plot_widget.plot(
            pen=self.price_pen,
            name="价格"
        )
        
        # 创建最新价格标签
        self.price_label = QtWidgets.QLabel()
        self.price_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.price_label)
        self.setLayout(layout) 