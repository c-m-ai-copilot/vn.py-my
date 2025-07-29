from typing import Dict
from vnpy.trader.object import TickData

class TickManager:
    """行情数据管理器"""
    
    def __init__(self):
        self.ticks: Dict[str, TickData] = {}  # vt_symbol: TickData
    
    def update_tick(self, tick: TickData) -> None:
        """更新行情数据"""
        vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
        self.ticks[vt_symbol] = tick
    
    def get_tick(self, vt_symbol: str) -> TickData:
        """获取行情数据"""
        return self.ticks.get(vt_symbol)

# 创建全局实例
tick_manager = TickManager() 