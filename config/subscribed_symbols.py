import json
from typing import List, Set
from config.paths import SUBSCRIBED_SYMBOLS_PATH

class SubscribedSymbols:
    """订阅合约管理类"""
    
    def __init__(self) -> None:
        self.symbols: Set[str] = set()
        self.config_path = SUBSCRIBED_SYMBOLS_PATH
        # print(f"订阅配置文件路径: {self.config_path}")
        self.load()
    
    def load(self) -> None:
        """从文件加载订阅列表"""
        try:
            if SUBSCRIBED_SYMBOLS_PATH.exists():
                with open(SUBSCRIBED_SYMBOLS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.symbols = set(data.get("symbols", []))
                # print(f"已加载订阅合约: {self.symbols}")
            else:
                # print(f"订阅配置文件不存在: {SUBSCRIBED_SYMBOLS_PATH}")
                pass
        except Exception as e:
            # print(f"加载订阅配置失败: {e}")
            self.symbols = set()
    
    def save(self) -> None:
        """保存订阅列表到文件"""
        try:
            data = {"symbols": list(self.symbols)}
            with open(SUBSCRIBED_SYMBOLS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            # print(f"已保存订阅合约: {self.symbols}")
        except Exception as e:
            # print(f"保存订阅配置失败: {e}")
            pass
    
    def add(self, symbol: str) -> None:
        """添加订阅合约"""
        # print(f"[DEBUG] SubscribedSymbols: 添加订阅合约 - {symbol}")
        # print(f"[DEBUG] SubscribedSymbols: 添加前订阅列表: {self.symbols}")
        self.symbols.add(symbol)
        # print(f"[DEBUG] SubscribedSymbols: 添加后订阅列表: {self.symbols}")
        self.save()
    
    def remove(self, symbol: str) -> None:
        """移除订阅合约"""
        # print(f"[DEBUG] SubscribedSymbols: 移除订阅合约 - {symbol}")
        # print(f"[DEBUG] SubscribedSymbols: 移除前订阅列表: {self.symbols}")
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            # print(f"[DEBUG] SubscribedSymbols: 移除后订阅列表: {self.symbols}")
            self.save()
    
    def clear(self) -> None:
        """清空订阅列表"""
        # print(f"[DEBUG] SubscribedSymbols: 清空订阅列表")
        # print(f"[DEBUG] SubscribedSymbols: 清空前订阅列表: {self.symbols}")
        self.symbols.clear()
        # print(f"[DEBUG] SubscribedSymbols: 清空后订阅列表: {self.symbols}")
        self.save()
    
    def get_symbols(self) -> List[str]:
        """获取所有订阅的合约列表"""
        symbols = list(self.symbols)
        # print(f"[DEBUG] SubscribedSymbols: 获取订阅列表: {symbols}")
        return symbols

# 这里添加您想要订阅的期货合约代码
SUBSCRIBED_SYMBOLS = [
    "rb2410",    # 螺纹钢2410合约
    "IF2406",    # 沪深300期货2406合约
    "au2406",    # 黄金2406合约
    # 添加更多您需要的合约...
]

# 创建全局实例
subscribed_symbols = SubscribedSymbols() 