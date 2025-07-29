"""
Database models for trading system historical data storage
Phase 1.1.1: SQLite database structure implementation
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    direction: str
    volume: int
    price: float
    trade_time: datetime
    commission: float = 0.0
    strategy_name: str = ""
    order_id: str = ""

@dataclass
class OrderRecord:
    order_id: str
    symbol: str
    direction: str
    volume: int
    price: float
    order_time: datetime
    status: str
    filled_volume: int = 0
    filled_price: float = 0.0
    strategy_name: str = ""

@dataclass
class PositionRecord:
    symbol: str
    direction: str
    volume: int
    price: float
    position_time: datetime
    pnl: float = 0.0
    strategy_name: str = ""

@dataclass
class AccountFlow:
    flow_id: str
    account_id: str
    balance: float
    available: float
    margin: float
    pnl: float
    commission: float
    record_time: datetime

@dataclass
class TickData:
    symbol: str
    datetime: datetime
    last_price: float
    volume: int
    open_interest: int
    bid_price: float
    ask_price: float
    bid_volume: int
    ask_volume: int

class TradingDatabase:
    """SQLite database manager for trading data persistence"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "trading.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('多', '空', 'BUY', 'SELL')),
                volume INTEGER NOT NULL,
                price REAL NOT NULL,
                trade_time DATETIME NOT NULL,
                commission REAL DEFAULT 0.0,
                strategy_name TEXT DEFAULT '',
                order_id TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 订单记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('多', '空', 'BUY', 'SELL')),
                volume INTEGER NOT NULL,
                price REAL NOT NULL,
                order_time DATETIME NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('待成交', '部分成交', '全部成交', '已撤单', '拒单')),
                filled_volume INTEGER DEFAULT 0,
                filled_price REAL DEFAULT 0.0,
                strategy_name TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 持仓历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('多', '空', 'LONG', 'SHORT')),
                volume INTEGER NOT NULL,
                price REAL NOT NULL,
                position_time DATETIME NOT NULL,
                pnl REAL DEFAULT 0.0,
                strategy_name TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 资金流水表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT UNIQUE NOT NULL,
                account_id TEXT NOT NULL,
                balance REAL NOT NULL,
                available REAL NOT NULL,
                margin REAL NOT NULL,
                pnl REAL NOT NULL,
                commission REAL DEFAULT 0.0,
                record_time DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 行情数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                datetime DATETIME NOT NULL,
                last_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                open_interest INTEGER NOT NULL,
                bid_price REAL NOT NULL,
                ask_price REAL NOT NULL,
                bid_volume INTEGER NOT NULL,
                ask_volume INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 分钟K线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                datetime DATETIME NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                open_interest INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引优化查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_time ON trades(trade_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_time ON orders(order_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks(symbol, datetime)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bars_symbol_time ON bars(symbol, datetime)')
        
        conn.commit()
        conn.close()
    
    def save_trade(self, trade: TradeRecord):
        """保存交易记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO trades 
            (trade_id, symbol, direction, volume, price, trade_time, commission, strategy_name, order_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.trade_id, trade.symbol, trade.direction, trade.volume, trade.price,
            trade.trade_time, trade.commission, trade.strategy_name, trade.order_id
        ))
        conn.commit()
        conn.close()
    
    def save_order(self, order: OrderRecord):
        """保存订单记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO orders 
            (order_id, symbol, direction, volume, price, order_time, status, filled_volume, filled_price, strategy_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order.order_id, order.symbol, order.direction, order.volume, order.price,
            order.order_time, order.status, order.filled_volume, order.filled_price, order.strategy_name
        ))
        conn.commit()
        conn.close()
    
    def save_position(self, position: PositionRecord):
        """保存持仓记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO positions 
            (symbol, direction, volume, price, position_time, pnl, strategy_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            position.symbol, position.direction, position.volume, position.price,
            position.position_time, position.pnl, position.strategy_name
        ))
        conn.commit()
        conn.close()
    
    def save_account_flow(self, account_flow: AccountFlow):
        """保存资金流水"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO account_flow 
            (flow_id, account_id, balance, available, margin, pnl, commission, record_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_flow.flow_id, account_flow.account_id, account_flow.balance,
            account_flow.available, account_flow.margin, account_flow.pnl,
            account_flow.commission, account_flow.record_time
        ))
        conn.commit()
        conn.close()
    
    def get_trades(self, symbol: str = None, start_date: datetime = None, end_date: datetime = None, limit: int = None) -> List[TradeRecord]:
        """获取交易记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if start_date:
            query += " AND trade_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_time <= ?"
            params.append(end_date)
        query += " ORDER BY trade_time DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append(TradeRecord(
                trade_id=row[1], symbol=row[2], direction=row[3], volume=row[4],
                price=row[5], trade_time=datetime.fromisoformat(row[6]),
                commission=row[7], strategy_name=row[8], order_id=row[9]
            ))
        return trades
    
    def get_daily_pnl(self, date: datetime) -> float:
        """获取某日盈亏"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(pnl), 0) FROM positions 
            WHERE DATE(position_time) = DATE(?)
        ''', (date,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0
    
    def get_total_trades(self) -> int:
        """获取总交易次数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM trades')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def get_win_rate(self) -> float:
        """计算胜率"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM positions WHERE pnl != 0
        ''')
        result = cursor.fetchone()
        conn.close()
        if result and result[1] > 0:
            return result[0] / result[1]
        return 0.0
    
    def clear_old_data(self, days_to_keep: int = 30):
        """清理过期数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
        
        cursor.execute('DELETE FROM trades WHERE trade_time < ?', (cutoff_date,))
        cursor.execute('DELETE FROM orders WHERE order_time < ?', (cutoff_date,))
        cursor.execute('DELETE FROM positions WHERE position_time < ?', (cutoff_date,))
        cursor.execute('DELETE FROM ticks WHERE datetime < ?', (cutoff_date,))
        cursor.execute('DELETE FROM bars WHERE datetime < ?', (cutoff_date,))
        cursor.execute('DELETE FROM account_flow WHERE record_time < ?', (cutoff_date,))
        
        conn.commit()
        conn.close()

# 创建全局数据库实例
trading_db = TradingDatabase()