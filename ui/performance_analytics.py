from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta
from config.database import TradingDatabase
from config.data_persistence_engine import DataPersistenceEngine
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_TRADE, EVENT_ACCOUNT
from vnpy.event import Event
import numpy as np

# 配置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class PerformanceChartWidget(QtWidgets.QWidget):
    """性能图表组件"""
    
    def __init__(self, database: TradingDatabase):
        super().__init__()
        self.database = database
        self.init_ui()
        self.setup_chart()
    
    def init_ui(self):
        """初始化界面"""
        layout = QtWidgets.QVBoxLayout()
        
        # 创建图表画布
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
    
    def setup_chart(self):
        """设置图表"""
        self.ax1 = self.figure.add_subplot(2, 2, 1)
        self.ax2 = self.figure.add_subplot(2, 2, 2)
        self.ax3 = self.figure.add_subplot(2, 2, 3)
        self.ax4 = self.figure.add_subplot(2, 2, 4)
        
        self.update_charts()
    
    def update_charts(self):
        """更新所有图表"""
        try:
            trades = self.database.get_trades(limit=1000)
            if not trades:
                self.clear_charts()
                return
            
            # 准备数据
            df = pd.DataFrame([{
                'date': trade.trade_time.date(),
                'pnl': trade.price * trade.volume - trade.commission,
                'volume': trade.volume,
                'direction': trade.direction
            } for trade in trades])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['cumulative_pnl'] = df['pnl'].cumsum()
            
            daily_pnl = df.groupby('date')['pnl'].sum().reset_index()
            daily_volume = df.groupby('date')['volume'].sum().reset_index()
            
            # 1. P&L曲线图
            self.ax1.clear()
            self.ax1.plot(daily_pnl['date'], daily_pnl['pnl'].cumsum(), color='blue', linewidth=2)
            self.ax1.axhline(y=0, color='black', linestyle='--', alpha=0.3)
            self.ax1.set_title('累计盈亏曲线', fontsize=12, fontweight='bold')
            self.ax1.grid(True, alpha=0.3)
            self.ax1.set_ylabel('盈亏 (元)')
            self.ax1.tick_params(axis='x', rotation=45)
            
            # 2. 每日盈亏柱状图
            self.ax2.clear()
            colors = ['red' if x > 0 else 'green' for x in daily_pnl['pnl']]
            self.ax2.bar(daily_pnl['date'], daily_pnl['pnl'], color=colors, alpha=0.7)
            self.ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            self.ax2.set_title('每日盈亏', fontsize=12, fontweight='bold')
            self.ax2.grid(True, alpha=0.3)
            self.ax2.tick_params(axis='x', rotation=45)
            
            # 3. 交易量分析
            self.ax3.clear()
            self.ax3.bar(daily_volume['date'], daily_volume['volume'], alpha=0.7)
            self.ax3.set_title('每日交易量', fontsize=12, fontweight='bold')
            self.ax3.grid(True, alpha=0.3)
            self.ax3.tick_params(axis='x', rotation=45)
            
            # 4. 胜率分析
            self.ax4.clear()
            win_trades = len(df[df['pnl'] > 0])
            loss_trades = len(df[df['pnl'] < 0])
            neutral_trades = len(df[df['pnl'] == 0])
            labels = ['盈利', '亏损', '持平']
            sizes = [win_trades, loss_trades, neutral_trades]
            colors = ['lightgreen', 'lightcoral', 'lightblue']
            self.ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            self.ax4.set_title('交易胜率分析', fontsize=12, fontweight='bold')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"更新图表失败: {e}")
    
    def clear_charts(self):
        """清空图表"""
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=14)
        self.canvas.draw()

class StatisticsWidget(QtWidgets.QWidget):
    """统计信息组件"""
    
    def __init__(self, database: TradingDatabase):
        super().__init__()
        self.database = database
        self.init_ui()
        self.refresh_stats()
    
    def init_ui(self):
        """初始化界面"""
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(10)
        
        # 创建统计卡片
        self.create_stat_card("总交易次数", "0", layout, 0, 0)
        self.create_stat_card("胜率", "0.0%", layout, 0, 1)
        self.create_stat_card("总盈亏", "¥0.00", layout, 0, 2)
        self.create_stat_card("最大回撤", "¥0.00", layout, 0, 3)
        self.create_stat_card("日均收益", "¥0.00", layout, 1, 0)
        self.create_stat_card("夏普比率", "0.00", layout, 1, 1)
        self.create_stat_card("最大连亏", "0", layout, 1, 2)
        self.create_stat_card("盈亏比", "0.00", layout, 1, 3)
        
        self.setLayout(layout)
    
    def create_stat_card(self, title: str, value: str, layout: QtWidgets.QLayout, row: int, col: int):
        """创建统计卡片"""
        card = QtWidgets.QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
                min-height: 60px;
            }
        """)
        card_layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(value)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(label)
        card.setLayout(card_layout)
        layout.addWidget(card, row, col)
    
    def refresh_stats(self):
        """刷新统计数据"""
        try:
            trades = self.database.get_trades(limit=1000)
            if not trades:
                return
            
            # 计算统计数据
            total_trades = len(trades)
            win_trades = [t for t in trades if t.price * t.volume - t.commission > 0]
            loss_trades = [t for t in trades if t.price * t.volume - t.commission < 0]
            win_rate = len(win_trades) / total_trades * 100 if total_trades > 0 else 0
            
            total_pnl = sum(t.price * t.volume - t.commission for t in trades)
            avg_daily_pnl = total_pnl / 30  # 假设30天
            profit_factor = abs(sum(t.price * t.volume - t.commission for t in win_trades) / 
                              sum(t.price * t.volume - t.commission for t in loss_trades)) if loss_trades else 0
            
            # 更新UI
            self.update_stat_value(0, str(total_trades))
            self.update_stat_value(1, f"{win_rate:.1f}%")
            self.update_stat_value(2, f"¥{total_pnl:.2f}")
            self.update_stat_value(3, f"¥{max(0, -total_pnl):.2f}")
            self.update_stat_value(4, f"¥{avg_daily_pnl:.2f}")
            self.update_stat_value(5, f"{profit_factor:.2f}")
            self.update_stat_value(6, str(len(loss_trades)))
            self.update_stat_value(7, f"{profit_factor:.2f}")
            
        except Exception as e:
            print(f"刷新统计数据失败: {e}")
    
    def update_stat_value(self, index: int, value: str):
        """更新统计值"""
        card = self.layout().itemAt(index).widget()
        label = card.layout().itemAt(0).widget()
        label.setText(value)

class PerformanceAnalytics(QtWidgets.QWidget):
    """业绩分析窗口"""
    
    def __init__(self, main_engine, event_engine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.database = TradingDatabase()
        self.init_ui()
        self.register_events()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("业绩分析")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 600)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部控制面板
        control_panel = QtWidgets.QHBoxLayout()
        self.date_range_combo = QtWidgets.QComboBox()
        self.date_range_combo.addItems(['最近7天', '最近30天', '最近90天', '全部数据'])
        self.date_range_combo.currentTextChanged.connect(self.update_analysis)
        control_panel.addWidget(QtWidgets.QLabel("时间范围:"))
        control_panel.addWidget(self.date_range_combo)
        control_panel.addStretch()
        
        refresh_btn = QtWidgets.QPushButton("刷新数据")
        refresh_btn.clicked.connect(self.update_analysis)
        control_panel.addWidget(refresh_btn)
        export_btn = QtWidgets.QPushButton("导出报表")
        export_btn.clicked.connect(self.export_report)
        control_panel.addWidget(export_btn)
        layout.addLayout(control_panel)
        
        # 统计信息区域
        self.stats_widget = StatisticsWidget(self.database)
        layout.addWidget(self.stats_widget)
        
        # 图表区域
        self.chart_widget = PerformanceChartWidget(self.database)
        layout.addWidget(self.chart_widget, stretch=1)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
    
    def register_events(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_TRADE, self.on_trade_event)
        self.event_engine.register(EVENT_ACCOUNT, self.on_account_event)
    
    def on_trade_event(self, event: Event):
        """处理成交事件"""
        QtCore.QTimer.singleShot(100, self.update_analysis)
    
    def on_account_event(self, event: Event):
        """处理账户事件"""
        QtCore.QTimer.singleShot(100, self.update_analysis)
    
    def update_analysis(self):
        """更新分析数据"""
        self.stats_widget.refresh_stats()
        self.chart_widget.update_charts()
    
    def export_report(self):
        """导出业绩报表"""
        try:
            from datetime import datetime
            filename = f"业绩报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "保存业绩报表", filename, "CSV Files (*.csv)"
            )
            if filepath:
                trades = self.database.get_trades(limit=1000)
                if trades:
                    df = pd.DataFrame([{
                        '交易时间': trade.trade_time.strftime('%Y-%m-%d %H:%M:%S'),
                        '合约代码': trade.symbol,
                        '方向': trade.direction,
                        '成交量': trade.volume,
                        '成交价': trade.price,
                        '手续费': trade.commission,
                        '策略': trade.strategy_name
                    } for trade in trades])
                    df.to_csv(filepath, index=False, encoding='utf-8-sig')
                    QtWidgets.QMessageBox.information(self, "成功", f"业绩报表已导出到：{filepath}")
                else:
                    QtWidgets.QMessageBox.information(self, "提示", "暂无交易数据可导出")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")
    
    def closeEvent(self, event):
        """关闭事件"""
        super().closeEvent(event)