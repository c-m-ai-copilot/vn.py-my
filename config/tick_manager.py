from typing import Optional
from vnpy.trader.object import TickData
from config.log_manager import log_manager

class TickManager:
    """行情数据管理器"""
    
    def __init__(self):
        """初始化"""
        self.ticks = {}  # 存储最新的tick数据
        # log_manager.log("[TickManager] Initialized")
        
    def update_tick(self, tick: TickData) -> None:
        """更新行情数据"""
        vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
        # log_manager.log(f"[TickManager] Updating tick for {vt_symbol} at price {tick.last_price}")
        
        old_tick = self.ticks.get(vt_symbol)
        if old_tick:
            # log_manager.log(f"[TickManager] Replacing old tick for {vt_symbol}. Old price: {old_tick.last_price}, New price: {tick.last_price}")
            pass
        else:
            # log_manager.log(f"[TickManager] Storing new tick for {vt_symbol}")
            pass
            
        self.ticks[vt_symbol] = tick
        # log_manager.log(f"[TickManager] Total ticks stored: {len(self.ticks)}")
        
    def get_tick(self, vt_symbol: str) -> Optional[TickData]:
        """获取行情数据"""
        # log_manager.log(f"[TickManager] Attempting to get tick for {vt_symbol}")
        tick = self.ticks.get(vt_symbol, None)
        exists = tick is not None
        
        if exists:
            # log_manager.log(f"[TickManager] Found tick for {vt_symbol}: Price={tick.last_price}, Time={tick.datetime}")
            pass
        else:
            # log_manager.log(f"[TickManager] Tick for {vt_symbol} not found in manager")
            pass
            
        return tick
        
    def remove_tick(self, vt_symbol: str) -> None:
        """移除行情数据"""
        # log_manager.log(f"[TickManager] Attempting to remove tick for {vt_symbol}")
        if vt_symbol in self.ticks:
            removed_tick = self.ticks.pop(vt_symbol)
            # log_manager.log(f"[TickManager] Removed tick for {vt_symbol}. Last price: {removed_tick.last_price}")
            # log_manager.log(f"[TickManager] Total ticks remaining: {len(self.ticks)}")
            pass
        else:
            # log_manager.log(f"[TickManager] Attempted to remove non-existent tick: {vt_symbol}")
            pass

# 创建全局实例
tick_manager = TickManager()