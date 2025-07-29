#\!/usr/bin/env python3
"""
调试订阅合约的工具
用于确认mock数据系统正常工作
"""

import os
import time
import sys
from pathlib import Path

# 强制启用mock模式
os.environ['USE_MOCK_DATA'] = 'true'

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from tests.mock_data.mock_engine import MockEngine
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange
from config.subscribed_symbols import subscribed_symbols

def test_subscription():
    """测试订阅功能"""
    print("🚀 启动订阅测试...")
    
    # 创建事件引擎和主引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 创建mock引擎
    mock_engine = MockEngine(main_engine, event_engine)
    main_engine.gateways["CTP"] = mock_engine
    
    # 模拟登录
    print("📊 模拟登录和连接...")
    mock_engine.connect({"user_id": "test", "password": "test"})
    
    # 等待连接完成
    time.sleep(3)
    
    # 获取所有合约
    all_contracts = main_engine.get_all_contracts()
    print(f"📋 可用合约数量: {len(all_contracts)}")
    
    # 订阅保存的合约
    saved_symbols = subscribed_symbols.get_symbols()
    print(f"🔍 需要订阅的合约: {saved_symbols}")
    
    # 逐个订阅
    subscribed_count = 0
    for vt_symbol in saved_symbols:
        try:
            symbol, exchange_str = vt_symbol.split('.')
            exchange = Exchange(exchange_str)
            
            req = SubscribeRequest(
                symbol=symbol,
                exchange=exchange
            )
            
            result = main_engine.subscribe(req, "CTP")
            print(f"✅ 订阅 {vt_symbol}: {'成功' if result else '失败'}")
            
            if result:
                subscribed_count += 1
                
        except Exception as e:
            print(f"❌ 订阅 {vt_symbol} 失败: {e}")
    
    print(f"📊 成功订阅 {subscribed_count}/{len(saved_symbols)} 个合约")
    
    # 等待行情数据
    print("⏳ 等待行情数据...")
    time.sleep(5)
    
    # 检查tick数据
    from config.tick_manager import tick_manager
    
    print("📈 当前tick数据状态:")
    for vt_symbol in saved_symbols:
        tick = tick_manager.get_tick(vt_symbol)
        if tick:
            print(f"   ✅ {vt_symbol}: 最新价 {tick.last_price}")
        else:
            print(f"   ❌ {vt_symbol}: 无数据")
    
    return subscribed_count == len(saved_symbols)

if __name__ == "__main__":
    success = test_subscription()
    if success:
        print("\n🎉 订阅测试成功！tick数据应该可以正常显示")
    else:
        print("\n⚠️  订阅测试发现问题，请检查日志")
    
    input("按Enter键退出...")
EOF < /dev/null
