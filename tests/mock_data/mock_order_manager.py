"""
Mock订单管理器
模拟订单生命周期管理
"""

import uuid
import random
import datetime
from typing import Dict, List, Optional
from vnpy.trader.object import OrderData, TradeData, OrderRequest
from vnpy.trader.constant import OrderType, Direction, Offset, Status
from tests.mock_data.mock_contracts import MOCK_CONTRACTS
from tests.mock_data.mock_account import mock_account_manager

class MockOrderManager:
    """Mock订单管理器"""
    
    def __init__(self):
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        self.active_orders: Dict[str, OrderData] = {}
        self.order_counter = 1000
        self.trade_counter = 10000
        self.gateway_name = "MockCTP"
        self.match_probability = 0.8  # 订单成交概率
        self.partial_fill_rate = 0.3  # 部分成交概率
        self.delay_range = (100, 500)  # 成交延迟(毫秒)
    
    def send_order(self, req: OrderRequest) -> str:
        """发送订单"""
        order_id = f"MOCK_{self.order_counter}"
        self.order_counter += 1
        vt_orderid = f"{self.gateway_name}.{order_id}"
        
        now = datetime.datetime.now()
        order = OrderData(
            orderid=order_id,
            symbol=req.symbol,
            exchange=req.exchange,
            direction=req.direction,
            offset=req.offset,
            type=req.type,
            price=req.price,
            volume=req.volume,
            traded=0,
            status=Status.NOT_TRADED,
            datetime=now,
            gateway_name=self.gateway_name
        )
        
        self.orders[vt_orderid] = order
        self.active_orders[vt_orderid] = order
        
        # 模拟订单处理延迟
        self._schedule_order_processing(vt_orderid)
        
        return vt_orderid
    
    def cancel_order(self, vt_orderid: str) -> bool:
        """撤单"""
        order = self.active_orders.get(vt_orderid)
        if not order:
            return False
        
        if order.status in [Status.NOT_TRADED, Status.PART_TRADED]:
            order.status = Status.CANCELLED
            del self.active_orders[vt_orderid]
            return True
        
        return False
    
    def cancel_all_orders(self, symbol: str = None) -> int:
        """全撤单"""
        cancelled_count = 0
        orders_to_cancel = list(self.active_orders.values())
        
        for order in orders_to_cancel:
            if symbol is None or order.symbol == symbol:
                if self.cancel_order(order.vt_orderid):
                    cancelled_count += 1
        
        return cancelled_count
    
    def _schedule_order_processing(self, vt_orderid: str):
        """调度订单处理"""
        import threading
        delay = random.randint(*self.delay_range) / 1000.0
        threading.Timer(delay, self._process_order, args=[vt_orderid]).start()
    
    def _process_order(self, vt_orderid: str):
        """处理订单撮合"""
        order = self.active_orders.get(vt_orderid)
        if not order:
            return
        
        # 模拟成交概率
        if random.random() > self.match_probability:
            order.status = Status.CANCELLED
            del self.active_orders[vt_orderid]
            return
        
        remaining_volume = order.volume - order.traded
        if remaining_volume <= 0:
            return
        
        # 决定成交方式：全部成交、部分成交或逐步成交
        fill_type = random.choice(["full", "partial", "gradual"])
        
        if fill_type == "full":
            self._create_trade(order, remaining_volume)
        elif fill_type == "partial":
            fill_volume = max(1, int(remaining_volume * random.uniform(0.3, 0.7)))
            self._create_trade(order, fill_volume)
            if order.traded < order.volume:
                self._schedule_order_processing(vt_orderid)
        else:  # gradual
            fill_volume = max(1, int(remaining_volume * random.uniform(0.1, 0.3)))
            self._create_trade(order, fill_volume)
            if order.traded < order.volume:
                self._schedule_order_processing(vt_orderid)
    
    def _create_trade(self, order: OrderData, volume: int):
        """创建成交"""
        trade_id = f"MOCK_T{self.trade_counter}"
        self.trade_counter += 1
        vt_tradeid = f"{self.gateway_name}.{trade_id}"
        
        now = datetime.datetime.now()
        contract = MOCK_CONTRACTS.get(order.symbol)
        if not contract:
            return
        
        # 根据订单类型确定成交价
        if order.type == OrderType.LIMIT:
            trade_price = order.price
        elif order.type == OrderType.MARKET:
            # 市价单以当前市场价成交，添加小幅滑点
            base_price = order.price
            slippage = random.uniform(-contract.pricetick, contract.pricetick) * 2
            trade_price = max(0.01, base_price + slippage)
            trade_price = round(trade_price, 2)
        else:
            trade_price = order.price
        
        trade = TradeData(
            tradeid=trade_id,
            orderid=order.orderid,
            symbol=order.symbol,
            exchange=order.exchange,
            direction=order.direction,
            offset=order.offset,
            price=trade_price,
            volume=volume,
            datetime=now,
            gateway_name=self.gateway_name
        )
        
        self.trades[vt_tradeid] = trade
        order.traded += volume
        
        # 更新订单状态
        if order.traded == order.volume:
            order.status = Status.ALL_TRADED
            if order.vt_orderid in self.active_orders:
                del self.active_orders[order.vt_orderid]
        else:
            order.status = Status.PART_TRADED
        
        # 更新账户和持仓
        self._update_account_position(order, trade)
    
    def _update_account_position(self, order: OrderData, trade: TradeData):
        """更新账户和持仓"""
        symbol = order.symbol
        contract = MOCK_CONTRACTS.get(symbol)
        if not contract:
            return
        
        # 计算成交价值
        trade_value = trade.price * trade.volume * contract.size
        commission = trade_value * 0.0001  # 万分之一手续费
        margin_rate = 0.1  # 10%保证金率
        margin_amount = trade_value * margin_rate
        
        # 更新账户
        account = mock_account_manager.get_account()
        account.commission += commission
        account.margin += margin_amount if order.offset == Offset.OPEN else 0
        account.margin = max(0, account.margin - margin_amount if order.offset != Offset.OPEN else account.margin)
        account.available = account.balance - account.margin - account.commission
        
        # 更新持仓
        if order.offset == Offset.OPEN:
            mock_account_manager.add_position(
                symbol, order.direction, trade.volume, trade.price
            )
        else:  # 平仓
            mock_account_manager.close_position(
                order.vt_symbol, order.direction, trade.volume, trade.price
            )
    
    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        """获取订单"""
        return self.orders.get(vt_orderid)
    
    def get_trade(self, vt_tradeid: str) -> Optional[TradeData]:
        """获取成交"""
        return self.trades.get(vt_tradeid)
    
    def get_all_orders(self) -> List[OrderData]:
        """获取所有订单"""
        return list(self.orders.values())
    
    def get_active_orders(self) -> List[OrderData]:
        """获取活动订单"""
        return list(self.active_orders.values())
    
    def get_all_trades(self) -> List[TradeData]:
        """获取所有成交"""
        return list(self.trades.values())
    
    def get_trades_by_order(self, orderid: str) -> List[TradeData]:
        """获取订单相关成交"""
        return [trade for trade in self.trades.values() if trade.orderid == orderid]
    
    def get_trades_by_symbol(self, symbol: str) -> List[TradeData]:
        """获取合约相关成交"""
        return [trade for trade in self.trades.values() if trade.symbol == symbol]
    
    def clear_all_data(self):
        """清空所有数据"""
        self.orders.clear()
        self.trades.clear()
        self.active_orders.clear()
        self.order_counter = 1000
        self.trade_counter = 10000
    
    def get_order_summary(self) -> dict:
        """获取订单统计"""
        total_orders = len(self.orders)
        active_orders = len(self.active_orders)
        total_trades = len(self.trades)
        filled_orders = len([o for o in self.orders.values() if o.status == Status.ALL_TRADED])
        cancelled_orders = len([o for o in self.orders.values() if o.status == Status.CANCELLED])
        
        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "total_trades": total_trades,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders
        }

# 全局实例
mock_order_manager = MockOrderManager()