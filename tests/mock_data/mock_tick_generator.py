"""
Mock Tick行情生成器
模拟真实行情数据生成
"""

import time
import random
import datetime
from typing import Dict, Optional
from vnpy.trader.object import TickData
from vnpy.trader.constant import Exchange
from tests.mock_data.mock_contracts import MOCK_CONTRACTS

class MockTickGenerator:
    """Mock行情生成器"""
    
    def __init__(self):
        self.base_prices: Dict[str, float] = {
            "rb2410": 3500.0,
            "cu2409": 70000.0,
            "au2412": 480.0,
            "i2409": 800.0,
            "m2409": 3000.0,
            "SR2409": 6000.0,
            "TA2409": 5800.0,
            "IF2409": 3500.0,
            "sc2409": 600.0,
            "ag2409": 7500.0
        }
        self.last_ticks: Dict[str, TickData] = {}
        self.volatility = 0.002  # 0.2%波动率
        self.trend_factor = 0.0  # 趋势因子
        self.update_interval = 1.0  # 更新间隔(秒)
        self.last_update_time = time.time()
    
    def get_base_price(self, symbol: str) -> float:
        """获取基准价格"""
        return self.base_prices.get(symbol, 5000.0)
    
    def generate_tick(self, symbol: str, exchange: Exchange) -> TickData:
        """生成单个合约的mock tick数据"""
        vt_symbol = f"{symbol}.{exchange.value}"
        base_price = self.get_base_price(symbol)
        contract = MOCK_CONTRACTS.get(symbol)
        
        now = datetime.datetime.now()
        current_time = time.time()
        
        # 计算价格变化
        if vt_symbol in self.last_ticks:
            last_price = self.last_ticks[vt_symbol].last_price
        else:
            last_price = base_price
        
        # 添加随机波动和趋势
        price_change = random.uniform(-self.volatility, self.volatility) + self.trend_factor * 0.0001
        new_price = max(0.01, last_price * (1 + price_change))
        new_price = round(new_price, 2)
        
        # 生成买卖价差 (0.1%-0.5%)
        spread = max(0.01, new_price * random.uniform(0.001, 0.005))
        bid_price = round(new_price - spread/2, 2)
        ask_price = round(new_price + spread/2, 2)
        
        # 生成买卖量
        bid_volume = random.randint(50, 500)
        ask_volume = random.randint(50, 500)
        volume = random.randint(100, 2000)
        open_interest = random.randint(50000, 200000)
        
        # 生成日内价格范围
        daily_range = new_price * 0.02  # 2%日波动范围
        open_price = base_price
        high_price = max(new_price, open_price + random.uniform(0, daily_range))
        low_price = min(new_price, open_price - random.uniform(0, daily_range))
        pre_close = base_price
        
        tick = TickData(
            symbol=symbol,
            exchange=exchange,
            datetime=now,
            name=contract.name if contract else symbol,
            last_price=new_price,
            volume=volume,
            open_interest=open_interest,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            pre_close=pre_close,
            bid_price_1=bid_price,
            bid_volume_1=bid_volume,
            ask_price_1=ask_price,
            ask_volume_1=ask_volume,
            gateway_name="MockCTP"
        )
        
        self.last_ticks[vt_symbol] = tick
        return tick
    
    def generate_batch_ticks(self) -> Dict[str, TickData]:
        """批量生成所有合约的tick数据"""
        ticks = {}
        # print(f"[DEBUG] MockTickGenerator: 开始生成tick数据，合约总数: {len(MOCK_CONTRACTS)}")
        
        for symbol, contract in MOCK_CONTRACTS.items():
            tick = self.generate_tick(symbol, contract.exchange)
            ticks[tick.vt_symbol] = tick
            # print(f"[DEBUG] MockTickGenerator: 生成tick数据 - {tick.vt_symbol}, 价格: {tick.last_price}")
        
        # print(f"[DEBUG] MockTickGenerator: 完成生成tick数据，总数: {len(ticks)}")
        return ticks
    
    def update_trend(self, new_trend: float):
        """更新趋势因子 (-0.001, 0.001)"""
        self.trend_factor = max(-0.001, min(0.001, new_trend))
    
    def set_volatility(self, volatility: float):
        """设置波动率 (0.001 - 0.01)"""
        self.volatility = max(0.001, min(0.01, volatility))
    
    def reset_prices(self):
        """重置价格到基准价"""
        self.last_ticks.clear()
        self.trend_factor = 0.0
    
    def simulate_market_scenario(self, scenario: str):
        """模拟特定市场场景"""
        scenarios = {
            "bull_market": 0.0005,      # 牛市
            "bear_market": -0.0005,     # 熊市
            "high_volatility": 0.005,   # 高波动
            "low_volatility": 0.001,    # 低波动
            "sideways": 0.0             # 横盘
        }
        
        if scenario in scenarios:
            if scenario.endswith("volatility"):
                self.set_volatility(scenarios[scenario])
            else:
                self.update_trend(scenarios[scenario])

# 全局生成器实例
mock_tick_generator = MockTickGenerator()