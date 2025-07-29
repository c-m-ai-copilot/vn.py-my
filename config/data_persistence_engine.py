"""
Data Persistence Engine for trading system
Phase 1.1.2: Auto-save trading data and manage historical data
"""

from vnpy.trader.engine import BaseEngine, EventEngine
from vnpy.trader.event import EVENT_TRADE, EVENT_ORDER, EVENT_POSITION, EVENT_ACCOUNT
from vnpy.event import Event
from config.database import TradingDatabase, TradeRecord, OrderRecord, PositionRecord, AccountFlow
from datetime import datetime
import uuid

APP_NAME = "DataPersistenceEngine"

class DataPersistenceEngine(BaseEngine):
    """自动数据持久化引擎"""
    
    def __init__(self, main_engine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine, APP_NAME)
        self.database = TradingDatabase()
        self.register_events()
        self.main_engine.write_log("数据持久化引擎初始化完成")
    
    def register_events(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
    
    def process_trade_event(self, event: Event):
        """处理成交事件并保存到数据库"""
        trade = event.data
        trade_record = TradeRecord(
            trade_id=trade.tradeid,
            symbol=trade.symbol,
            direction=trade.direction.value,
            volume=trade.volume,
            price=trade.price,
            trade_time=trade.datetime,
            commission=trade.commission,
            strategy_name=getattr(trade, 'strategy_name', ''),
            order_id=trade.orderid
        )
        self.database.save_trade(trade_record)
        self.main_engine.write_log(f"成交数据已保存: {trade.symbol} {trade.direction.value} {trade.volume}手 @{trade.price}")
    
    def process_order_event(self, event: Event):
        """处理订单事件并保存到数据库"""
        order = event.data
        order_record = OrderRecord(
            order_id=order.orderid,
            symbol=order.symbol,
            direction=order.direction.value,
            volume=order.volume,
            price=order.price,
            order_time=order.datetime,
            status=order.status.value,
            filled_volume=order.traded,
            filled_price=order.price,
            strategy_name=getattr(order, 'strategy_name', '')
        )
        self.database.save_order(order_record)
        self.main_engine.write_log(f"订单数据已保存: {order.symbol} {order.direction.value} {order.volume}手 @{order.price}")
    
    def process_position_event(self, event: Event):
        """处理持仓事件并保存到数据库"""
        position = event.data
        position_record = PositionRecord(
            symbol=position.symbol,
            direction='多' if position.volume > 0 else '空',
            volume=abs(position.volume),
            price=position.price,
            position_time=datetime.now(),
            pnl=position.pnl,
            strategy_name=getattr(position, 'strategy_name', '')
        )
        self.database.save_position(position_record)
        self.main_engine.write_log(f"持仓数据已保存: {position.symbol} {position.volume}手")
    
    def process_account_event(self, event: Event):
        """处理账户事件并保存到数据库"""
        account = event.data
        account_flow = AccountFlow(
            flow_id=str(uuid.uuid4()),
            account_id=account.accountid,
            balance=account.balance,
            available=account.available,
            margin=account.margin,
            pnl=getattr(account, 'pnl', 0.0),
            commission=account.commission,
            record_time=datetime.now()
        )
        self.database.save_account_flow(account_flow)
        self.main_engine.write_log(f"账户数据已保存: 余额{account.balance}, 可用{account.available}, 盈亏{getattr(account, 'pnl', 0.0)}")
    
    def get_trading_summary(self, days: int = 30) -> dict:
        """获取交易汇总统计"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        trades = self.database.get_trades(start_date=start_date)
        total_trades = len(trades)
        win_rate = self.database.get_win_rate()
        total_pnl = sum(trade.commission for trade in trades)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'start_date': start_date,
            'end_date': datetime.now()
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """清理过期数据"""
        self.database.clear_old_data(days_to_keep)
        self.main_engine.write_log(f"已清理{days_to_keep}天前的历史数据")

# 数据库初始化检查
try:
    # 测试数据库连接
    db = TradingDatabase()
    print("数据库初始化成功")
except Exception as e:
    print(f"数据库初始化失败: {e}")