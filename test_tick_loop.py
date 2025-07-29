#!/usr/bin/env python3
"""
行情推送循环启动测试
专门检查行情推送是否启动
"""

import os
import time
import threading
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange
from config.subscribed_symbols import subscribed_symbols

# 强制mock模式
os.environ['USE_MOCK_DATA'] = 'true'

def test_tick_push_loop():
    """测试行情推送循环"""
    print("=" * 60)
    print("行情推送循环启动测试")
    print("=" * 60)
    
    try:
        # 创建引擎
        print("[TEST] 创建事件引擎...")
        event_engine = EventEngine()
        
        print("[TEST] 创建主引擎...")
        main_engine = MainEngine(event_engine)
        
        # 添加mock引擎
        from tests.mock_data.mock_engine import MockEngine as CtpGateway
        mock_engine = CtpGateway(main_engine, event_engine)
        main_engine.gateways["CTP"] = mock_engine
        
        print("[TEST] 引擎创建完成")
        
        # 注册tick事件监听
        tick_count = 0
        def on_tick(event):
            nonlocal tick_count
            tick_count += 1
            vt_symbol = f"{event.data.symbol}.{event.data.exchange.value}"
            print(f"[TICK] 收到tick #{tick_count}: {vt_symbol} - {event.data.last_price}")
        
        event_engine.register(EVENT_TICK, on_tick)
        
        # 模拟连接
        print("[TEST] 开始连接...")
        main_engine.connect({}, "CTP")
        time.sleep(2)  # 等待连接完成
        
        # 检查网关状态
        gateway = main_engine.get_gateway("CTP")
        if gateway:
            print(f"[TEST] 网关类型: {type(gateway)}")
            if hasattr(gateway, 'gateway'):
                print(f"[TEST] 网关连接状态: {gateway.gateway.connected}")
                print(f"[TEST] 行情推送状态: {gateway.gateway.running}")
                print(f"[TEST] 已订阅合约: {len(gateway.gateway.subscribed_symbols)} - {gateway.gateway.subscribed_symbols}")
        
        # 订阅测试合约
        test_symbols = ["TA2409.CZCE", "cu2409.SHFE"]
        print(f"[TEST] 订阅测试合约: {test_symbols}")
        
        for vt_symbol in test_symbols:
            symbol, exchange_str = vt_symbol.split('.')
            exchange = Exchange(exchange_str)
            req = SubscribeRequest(symbol=symbol, exchange=exchange)
            result = main_engine.subscribe(req, "CTP")
            print(f"[TEST] 订阅 {vt_symbol}: {result}")
        
        print("[TEST] 等待tick数据...")
        time.sleep(5)  # 等待5秒看是否有tick数据
        
        print(f"[TEST] 总共收到 {tick_count} 个tick数据")
        
        if tick_count > 0:
            print("🎉 行情推送循环正常工作！")
        else:
            print("❌ 行情推送循环可能未启动")
            
        # 检查线程状态
        if hasattr(gateway, 'gateway') and gateway.gateway.tick_thread:
            print(f"[TEST] 行情推送线程: {gateway.gateway.tick_thread.is_alive()}")
        
        return tick_count > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tick_push_loop()
    print("\n" + "=" * 60)
    if success:
        print("✅ 行情推送循环测试通过")
    else:
        print("⚠️  需要检查行情推送循环启动逻辑")
    print("=" * 60)