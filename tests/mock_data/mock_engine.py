"""
Mock交易引擎
模拟CTP网关的核心功能
"""

import time
import threading
from typing import Dict, List, Optional
from vnpy.trader.engine import BaseEngine
from vnpy.trader.object import ContractData, TickData, OrderData, TradeData, OrderRequest, SubscribeRequest, PositionData, AccountData
from vnpy.trader.event import EVENT_CONTRACT, EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_POSITION
from vnpy.event import Event
from tests.mock_data.mock_contracts import CONTRACT_LIST, MOCK_CONTRACTS
from tests.mock_data.mock_tick_generator import mock_tick_generator
from tests.mock_data.mock_account import mock_account_manager
from tests.mock_data.mock_order_manager import mock_order_manager
from config.log_manager import log_manager
from config.subscribed_symbols import subscribed_symbols

class MockGateway:
    """Mock网关"""
    
    def __init__(self, event_engine):
        self.event_engine = event_engine
        self.gateway_name = "MockCTP"
        self.connected = False
        self.subscribed_symbols = set()
        self.tick_thread = None
        self.running = False
        self._timer = None
        
    def connect(self, setting: dict):
        """连接"""
        # print(f"[DEBUG] MockGateway: 开始连接，设置: {setting}")
        # 模拟连接延迟
        time.sleep(0.1)  # 减少延迟
        self.connected = True
        # print(f"[DEBUG] MockGateway: 连接成功！")
        
        # 发送合约事件
        self._send_contract_events()
        
        # 发送账户和持仓事件
        self._send_account_events()
        self._send_position_events()
        
        # 处理待处理的订阅
        if hasattr(self, 'pending_subscriptions') and self.pending_subscriptions:
            # print(f"[DEBUG] MockGateway: 处理 {len(self.pending_subscriptions)} 个待处理的订阅")
            for vt_symbol in list(self.pending_subscriptions):
                symbol, exchange_str = vt_symbol.split('.')
                from vnpy.trader.constant import Exchange
                req = SubscribeRequest(symbol=symbol, exchange=Exchange(exchange_str))
                self.subscribe(req)
            self.pending_subscriptions.clear()
    
    def _send_contract_events(self):
        """发送合约事件"""
        # print(f"[DEBUG] MockGateway: 开始推送{len(CONTRACT_LIST)}个合约")
        for contract in CONTRACT_LIST:
            # print(f"[DEBUG] MockGateway: 推送合约 {contract.symbol}.{contract.exchange.value}")
            event = Event(EVENT_CONTRACT, contract)
            self.event_engine.put(event)
    
    def _send_account_events(self):
        """发送账户事件"""
        account = mock_account_manager.get_account()
        if account:
            # print(f"[DEBUG] MockGateway: 推送账户信息 - 余额{account.balance}")
            event = Event(EVENT_ACCOUNT, account)
            self.event_engine.put(event)
    
    def _send_position_events(self):
        """发送持仓事件"""
        positions = mock_account_manager.get_all_positions()
        # print(f"[DEBUG] MockGateway: 推送{len(positions)}个持仓")
        for position in positions:
            # print(f"[DEBUG] MockGateway: 推送持仓 {position.symbol} {position.direction.value} {position.volume}手")
            event = Event(EVENT_POSITION, position)
            self.event_engine.put(event)
    
    def start_tick_pushing(self):
        """启动持续的行情推送"""
        if self.running:
            log_manager.log("[MockGateway] Tick pushing is already running.")
            return

        self.running = True
        self.tick_thread = threading.Thread(target=self._tick_pushing_loop)
        self.tick_thread.daemon = True
        self.tick_thread.start()
        log_manager.log("[MockGateway] Tick pushing thread started.")
    
    def get_all_contracts(self) -> List[ContractData]:
        """获取所有合约 - 供主引擎调用"""
        # print(f"[DEBUG] MockGateway: 返回{len(CONTRACT_LIST)}个合约给主引擎")
        return CONTRACT_LIST
    
    def _push_initial_ticks(self):
        """推送初始tick数据"""
        if not self.connected:
            # print("[DEBUG] MockGateway: 未连接，跳过推送初始tick数据")
            return
            
        # 为已订阅的合约生成tick数据
        # print(f"[DEBUG] MockGateway: 推送初始tick数据，已订阅合约: {len(self.subscribed_symbols)}")
        for vt_symbol in self.subscribed_symbols:
            symbol, exchange = vt_symbol.split('.')
            from tests.mock_data.mock_tick_generator import mock_tick_generator
            from vnpy.trader.constant import Exchange
            tick = mock_tick_generator.generate_tick(symbol, Exchange(exchange))
            if tick:
                # print(f"[DEBUG] MockGateway: 推送初始tick - {vt_symbol}, 价格: {tick.last_price}")
                event = Event(EVENT_TICK, tick)
                self.event_engine.put(event)
    
    def _tick_pushing_timer(self):
        """Qt定时器方式的行情推送 - 已废弃"""
        pass
    
    def _tick_pushing_loop(self):
        """行情推送循环 - 保留原始线程版本供测试使用"""
        # print(f"[DEBUG] MockGateway: 启动行情推送循环，订阅合约: {len(self.subscribed_symbols)} - {list(self.subscribed_symbols)}")
        loop_count = 0
        while self.running:
            if self.connected:
                loop_count += 1
                if loop_count % 10 == 1:  # 每10次循环打印一次
                    # print(f"[DEBUG] MockGateway: 行情推送循环 {loop_count} 次，订阅合约: {len(self.subscribed_symbols)}")
                    pass
                
                # 生成并推送已订阅合约的tick数据
                ticks = mock_tick_generator.generate_batch_ticks()
                # print(f"[DEBUG] MockGateway: 生成 {len(ticks)} 个tick数据")
                generated_count = len(ticks)
                pushed_count = 0
                self.subscribed_symbols = subscribed_symbols.get_symbols()
                # print(f"[DEBUG] MockGateway: 已订阅合约: {self.subscribed_symbols}")
                
                for vt_symbol, tick in ticks.items():
                    if vt_symbol in self.subscribed_symbols:
                        # print(f"[DEBUG] MockGateway: 推送tick数据 - {vt_symbol}, 价格: {tick.last_price}, 时间: {tick.datetime}")
                        event = Event(EVENT_TICK, tick)
                        self.event_engine.put(event)
                        pushed_count += 1
                        
                        # 更新持仓盈亏
                        mock_account_manager.update_position_pnl(vt_symbol, tick.last_price)
                        
                        # 发送持仓更新事件
                        positions = mock_account_manager.get_position(vt_symbol)
                        if positions:
                            if isinstance(positions, list):
                                for pos in positions:
                                    event = Event(EVENT_POSITION, pos)
                                    self.event_engine.put(event)
                            else:
                                event = Event(EVENT_POSITION, positions)
                                self.event_engine.put(event)
                else:
                    # print(f"[DEBUG] MockGateway: 未订阅合约 {vt_symbol}")
                    pass
                
                # if pushed_count > 0:
                #     print(f"[DEBUG] MockGateway: 本次循环生成 {generated_count} 个tick，推送 {pushed_count} 个tick")
                # else:
                #     print(f"[DEBUG] MockGateway: 本次循环未生成任何tick")
            else:
                if loop_count % 30 == 1:  # 每30秒打印一次未连接状态
                    print(f"[DEBUG] MockGateway: 未连接，跳过行情推送")
            
            time.sleep(1)  # 每秒更新一次
    
    def stop_tick_pushing(self):
        """停止行情推送"""
        self.running = False
        if hasattr(self, '_timer') and self._timer:
            self._timer.cancel()
        if self.tick_thread:
            self.tick_thread.join(timeout=1)
    
    def subscribe(self, req: SubscribeRequest, gateway_name: str = None) -> bool:
        """订阅行情 - 只推送一次tick数据"""
        vt_symbol = f"{req.symbol}.{req.exchange.value}"
        log_manager.log(f"[MockGateway] Received subscription request for {vt_symbol}")
        self.subscribed_symbols.add(vt_symbol)
        log_manager.log(f"[MockGateway] Total subscribed symbols: {len(self.subscribed_symbols)}")
        
        if self.connected:
            log_manager.log(f"[MockGateway] Gateway is connected. Generating and pushing tick for {vt_symbol}")
            from tests.mock_data.mock_tick_generator import mock_tick_generator
            tick = mock_tick_generator.generate_tick(req.symbol, req.exchange)
            if tick:
                log_manager.log(f"[MockGateway] Generated tick for {vt_symbol}: Price={tick.last_price}, Time={tick.datetime}")
                event = Event(EVENT_TICK, tick)
                self.event_engine.put(event)
                log_manager.log(f"[MockGateway] Pushed tick event for {vt_symbol} to event engine")
            else:
                log_manager.log(f"[MockGateway] Failed to generate tick for {vt_symbol}")
        else:
            log_manager.log(f"[MockGateway] Gateway not connected. Queuing subscription for {vt_symbol}")
            if not hasattr(self, 'pending_subscriptions'):
                self.pending_subscriptions = set()
            self.pending_subscriptions.add(vt_symbol)
        
        return True
    
    def unsubscribe(self, req: SubscribeRequest, gateway_name: str = None) -> bool:
        """取消订阅"""
        vt_symbol = f"{req.symbol}.{req.exchange.value}"
        self.subscribed_symbols.discard(vt_symbol)
        return True
    
    def send_order(self, req: OrderRequest) -> str:
        """发送订单"""
        return mock_order_manager.send_order(req)
    
    def cancel_order(self, req):
        """撤单"""
        return mock_order_manager.cancel_order(req.vt_orderid)
    
    def query_account(self):
        """查询账户"""
        self._send_account_events()
    
    def query_position(self):
        """查询持仓"""
        self._send_position_events()
    
    def query_contract(self):
        """查询合约"""
        self._send_contract_events()
    
    def close(self):
        """关闭连接"""
        self.connected = False
        self.stop_tick_pushing()

class MockEngine:
    """Mock交易引擎"""
    default_name = "MockCTP"
    exchanges = ["SHFE", "DCE", "CZCE", "CFFEX", "INE"]
    
    def __init__(self, main_engine, event_engine):
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.gateway = MockGateway(event_engine)
        self.gateway_name = "MockCTP"
        
    def connect(self, setting: dict):
        """连接"""
        log_manager.log(f"[MockEngine] Delegating connect call to MockGateway with settings: {setting}")
        self.gateway.connect(setting)
    
    def _connect_process(self, setting: dict):
        """连接处理流程 - 完全避免线程问题"""
        # 1. 模拟连接延迟
        time.sleep(0.1)
        
        # 2. 推送所有合约
        self._send_contract_events()
        
        # 3. 推送账户信息
        self._send_account_events()
        
        # 4. 推送持仓信息
        self._send_position_events()
        
        # 5. 不再启动任何推送循环
    
    def _send_contract_events(self):
        """发送所有合约事件"""
        print(f"[DEBUG] MockEngine: 开始发送{len(CONTRACT_LIST)}个合约事件")
        for contract in CONTRACT_LIST:
            print(f"[DEBUG] MockEngine: 发送合约事件 {contract.symbol}.{contract.exchange.value}")
            event = Event(EVENT_CONTRACT, contract)
            self.event_engine.put(event)
        print(f"[DEBUG] MockEngine: 合约事件发送完成")
    
    def _send_account_events(self):
        """发送账户事件"""
        account = mock_account_manager.get_account()
        if account:
            event = Event(EVENT_ACCOUNT, account)
            self.event_engine.put(event)
    
    def _send_position_events(self):
        """发送持仓事件"""
        positions = mock_account_manager.get_all_positions()
        for position in positions:
            event = Event(EVENT_POSITION, position)
            self.event_engine.put(event)
    
    def close(self):
        """关闭"""
        self.gateway.close()
    
    def get_all_contracts(self) -> List[ContractData]:
        """获取所有合约 - 供主引擎调用"""
        print(f"[DEBUG] MockEngine: 返回{len(CONTRACT_LIST)}个合约给主引擎")
        return CONTRACT_LIST
    
    def get_all_active_orders(self) -> List[OrderData]:
        """获取所有活动订单"""
        return mock_order_manager.get_all_orders()
    
    def query_position(self):
        """查询持仓"""
        # Mock模式直接返回持仓，无需实际查询
        positions = mock_account_manager.get_all_positions()
        for position in positions:
            event = Event(EVENT_POSITION, position)
            self.event_engine.put(event)
    
    def query_account(self):
        """查询账户"""
        # Mock模式直接返回账户，无需实际查询
        account = mock_account_manager.get_account()
        if account:
            event = Event(EVENT_ACCOUNT, account)
            self.event_engine.put(event)
    
    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """发送订单"""
        if gateway_name == self.gateway_name:
            return self.gateway.send_order(req)
        return ""
    
    def cancel_order(self, req, gateway_name: str) -> bool:
        """撤单"""
        if gateway_name == self.gateway_name:
            return self.gateway.cancel_order(req)
        return False
    
    def subscribe(self, req: SubscribeRequest, gateway_name: str = None) -> bool:
        """订阅"""
        if gateway_name == self.gateway_name:
            return self.gateway.subscribe(req)
        return False
    
    def get_all_contracts(self) -> List[ContractData]:
        """获取所有合约"""
        return CONTRACT_LIST
    
    def get_contract(self, vt_symbol: str) -> Optional[ContractData]:
        """获取合约"""
        symbol, exchange = vt_symbol.split(".")
        return MOCK_CONTRACTS.get(symbol)
    
    def get_all_active_orders(self) -> List[OrderData]:
        """获取所有活动订单"""
        return mock_order_manager.get_active_orders()
    
    def get_all_orders(self) -> List[OrderData]:
        """获取所有订单"""
        return mock_order_manager.get_all_orders()
    
    def get_all_trades(self) -> List[TradeData]:
        """获取所有成交"""
        return mock_order_manager.get_all_trades()
    
    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        """获取订单"""
        return mock_order_manager.get_order(vt_orderid)
    
    def get_position(self, vt_symbol: str) -> Optional[PositionData]:
        """获取持仓"""
        return mock_account_manager.get_position(vt_symbol)
    
    def get_all_positions(self) -> List[PositionData]:
        """获取所有持仓"""
        return mock_account_manager.get_all_positions()
    
    def get_account(self, accountid: str = None) -> Optional[AccountData]:
        """获取账户"""
        return mock_account_manager.get_account(accountid)
    
    def get_all_accounts(self) -> List[AccountData]:
        """获取所有账户"""
        account = mock_account_manager.get_account()
        return [account] if account else []
    
    def query_account(self):
        """查询账户"""
        self.gateway.query_account()
    
    def query_position(self):
        """查询持仓"""
        self.gateway.query_position()
    
    def query_contract(self):
        """查询合约"""
        self.gateway.query_contract()
    
    def close(self):
        """关闭"""
        self.gateway.close()
    
    def get_all_contracts(self) -> List[ContractData]:
        """获取所有合约 - 供主引擎调用"""
        print(f"[DEBUG] MockEngine: 返回{len(CONTRACT_LIST)}个合约给主引擎")
        return CONTRACT_LIST
    
    def get_all_active_orders(self) -> List[OrderData]:
        """获取所有活动订单"""
        return mock_order_manager.get_all_orders()
    
    def query_position(self):
        """查询持仓"""
        # Mock模式直接返回持仓，无需实际查询
        positions = mock_account_manager.get_all_positions()
        for position in positions:
            event = Event(EVENT_POSITION, position)
            self.event_engine.put(event)
    
    def query_account(self):
        """查询账户"""
        # Mock模式直接返回账户，无需实际查询
        account = mock_account_manager.get_account()
        if account:
            event = Event(EVENT_ACCOUNT, account)
            self.event_engine.put(event)

# 全局实例
mock_engine = None

def get_mock_engine(main_engine, event_engine) -> MockEngine:
    """获取mock引擎"""
    global mock_engine
    if mock_engine is None:
        mock_engine = MockEngine(main_engine, event_engine)
    return mock_engine