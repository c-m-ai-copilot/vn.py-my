"""
Mock账户管理器
模拟账户资金、持仓等数据
"""

import datetime
from typing import Dict, List, Optional
from vnpy.trader.object import AccountData, PositionData
from vnpy.trader.constant import Direction
from tests.mock_data.mock_contracts import MOCK_CONTRACTS

class MockAccountManager:
    """Mock账户管理器"""
    
    def __init__(self):
        self.accounts: Dict[str, AccountData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.account_id = "123456"
        self.gateway_name = "MockCTP"
        
        # 初始化账户数据
        self._init_accounts()
        self._init_positions()
    
    def _init_accounts(self):
        """初始化账户数据"""
        account = AccountData(
            accountid=self.account_id,
            balance=1000000.0,
            frozen=200000.0,
            gateway_name=self.gateway_name
        )
        # 设置其他属性
        account.available = 800000.0
        account.commission = 0.0
        account.margin = 180000.0
        account.close_profit = 0.0
        account.position_profit = 20000.0
        self.accounts[self.account_id] = account
    
    def _init_positions(self):
        """初始化持仓数据"""
        # 模拟一些持仓
        mock_positions = [
            {
                "symbol": "rb2410",
                "direction": Direction.LONG,
                "volume": 10,
                "price": 3490.0
            },
            {
                "symbol": "cu2409",
                "direction": Direction.SHORT,
                "volume": 2,
                "price": 70200.0
            },
            {
                "symbol": "m2409",
                "direction": Direction.LONG,
                "volume": 5,
                "price": 2980.0
            }
        ]
        
        for pos_data in mock_positions:
            symbol = pos_data["symbol"]
            contract = MOCK_CONTRACTS.get(symbol)
            if not contract:
                continue
                
            vt_symbol = f"{symbol}.{contract.exchange.value}"
            position = PositionData(
                symbol=symbol,
                exchange=contract.exchange,
                direction=pos_data["direction"],
                volume=pos_data["volume"],
                frozen=0,
                yd_volume=pos_data["volume"],
                price=pos_data["price"],
                gateway_name=self.gateway_name
            )
            
            # 计算保证金和盈亏
            position.margin = self._calculate_margin(position)
            position.pnl = 0.0  # 初始盈亏为0
            
            key = f"{vt_symbol}_{pos_data['direction'].value}"
            self.positions[key] = position
    
    def _calculate_margin(self, position: PositionData) -> float:
        """计算保证金"""
        contract = MOCK_CONTRACTS.get(position.symbol)
        if not contract:
            return 0.0
        
        # 简单计算：价格 × 合约乘数 × 手数 × 保证金比例(10%)
        margin_rate = 0.1
        return position.price * contract.size * position.volume * margin_rate
    
    def update_position_pnl(self, vt_symbol: str, current_price: float):
        """更新持仓盈亏"""
        for key, position in self.positions.items():
            if position.vt_symbol == vt_symbol:
                contract = MOCK_CONTRACTS.get(position.symbol)
                if not contract:
                    continue
                
                if position.direction == Direction.LONG:
                    position.pnl = (current_price - position.price) * position.volume * contract.size
                else:
                    position.pnl = (position.price - current_price) * position.volume * contract.size
    
    def get_account(self, accountid: str = None) -> Optional[AccountData]:
        """获取账户信息"""
        return self.accounts.get(accountid or self.account_id)
    
    def get_all_positions(self) -> List[PositionData]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def get_position(self, vt_symbol: str, direction: Direction = None) -> Optional[PositionData]:
        """获取特定持仓"""
        if direction:
            key = f"{vt_symbol}_{direction.value}"
            return self.positions.get(key)
        else:
            # 返回该合约的所有持仓
            positions = []
            for key, pos in self.positions.items():
                if pos.vt_symbol == vt_symbol:
                    positions.append(pos)
            return positions[0] if positions else None
    
    def add_position(self, symbol: str, direction: Direction, volume: int, price: float) -> PositionData:
        """添加新持仓"""
        contract = MOCK_CONTRACTS.get(symbol)
        if not contract:
            return None
            
        vt_symbol = f"{symbol}.{contract.exchange.value}"
        key = f"{vt_symbol}_{direction.value}"
        
        if key in self.positions:
            # 更新现有持仓
            position = self.positions[key]
            old_volume = position.volume
            old_value = position.price * old_volume
            new_value = price * volume
            position.volume += volume
            position.price = (old_value + new_value) / position.volume
            position.yd_volume = position.volume
        else:
            # 创建新持仓
            position = PositionData(
                symbol=symbol,
                exchange=contract.exchange,
                direction=direction,
                volume=volume,
                frozen=0,
                yd_volume=volume,
                price=price,
                gateway_name=self.gateway_name
            )
            self.positions[key] = position
        
        # 更新保证金
        position.margin = self._calculate_margin(position)
        return position
    
    def close_position(self, vt_symbol: str, direction: Direction, volume: int, price: float) -> bool:
        """平仓"""
        key = f"{vt_symbol}_{direction.value}"
        position = self.positions.get(key)
        if not position or position.volume < volume:
            return False
        
        # 计算平仓盈亏
        contract = MOCK_CONTRACTS.get(position.symbol)
        if contract:
            close_pnl = (price - position.price) * volume * contract.size
            if direction == Direction.SHORT:
                close_pnl = -close_pnl
            
            # 更新账户盈亏
            account = self.get_account()
            if account:
                account.close_profit += close_pnl
                account.balance += close_pnl
                account.available += close_pnl
        
        # 更新持仓
        position.volume -= volume
        position.yd_volume = position.volume
        
        if position.volume == 0:
            del self.positions[key]
        else:
            position.margin = self._calculate_margin(position)
        
        return True
    
    def update_account_balance(self, change: float):
        """更新账户余额"""
        account = self.get_account()
        if account:
            account.balance += change
            account.available += change
    
    def freeze_margin(self, amount: float) -> bool:
        """冻结保证金"""
        account = self.get_account()
        if account and account.available >= amount:
            account.available -= amount
            account.frozen += amount
            return True
        return False
    
    def unfreeze_margin(self, amount: float):
        """解冻保证金"""
        account = self.get_account()
        if account:
            account.available += amount
            account.frozen -= amount
    
    def get_account_summary(self) -> dict:
        """获取账户摘要"""
        account = self.get_account()
        positions = self.get_all_positions()
        
        total_margin = sum(pos.margin for pos in positions)
        total_pnl = sum(pos.pnl for pos in positions)
        
        return {
            "balance": account.balance if account else 0,
            "available": account.available if account else 0,
            "total_margin": total_margin,
            "total_pnl": total_pnl,
            "position_count": len(positions)
        }

# 全局实例
mock_account_manager = MockAccountManager()