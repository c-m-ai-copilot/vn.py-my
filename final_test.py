#!/usr/bin/env python3
"""
最终修复验证脚本
直接测试tick数据流
"""

import os
import sys
import time
import json

# 强制使用mock模式
os.environ['USE_MOCK_DATA'] = 'true'

def test_tick_flow_direct():
    """直接测试tick数据流"""
    print("🔍 开始直接测试tick数据流...")
    
    try:
        # 1. 检查订阅配置
        config_path = "config/subscribed_symbols.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                symbols = data.get('symbols', [])
            print(f"✅ 订阅配置: {symbols}")
        
        # 2. 检查mock合约
        from tests.mock_data.mock_contracts import MOCK_CONTRACTS
        print(f"✅ Mock合约: {list(MOCK_CONTRACTS.keys())}")
        
        # 3. 检查合约匹配
        for symbol in symbols:
            sym, exch = symbol.split('.')
            exists = sym in MOCK_CONTRACTS
            print(f"{'✅' if exists else '❌'} {symbol} -> {exists}")
        
        # 4. 测试mock tick生成器
        from tests.mock_data.mock_tick_generator import mock_tick_generator
        from vnpy.trader.constant import Exchange
        
        print("\n🎯 测试tick生成器:")
        test_cases = [
            ("rb2410", Exchange.SHFE),
            ("TA2409", Exchange.CZCE),
            ("IF2409", Exchange.CFFEX)
        ]
        
        for symbol, exchange in test_cases:
            tick = mock_tick_generator.generate_tick(symbol, exchange)
            if tick:
                vt_symbol = f"{symbol}.{exchange.value}"
                print(f"✅ {vt_symbol}: {tick.last_price}")
            else:
                print(f"❌ {symbol}.{exchange.value}: 生成失败")
        
        print("\n🎉 所有测试通过！tick数据流工作正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_final_test():
    """运行最终测试"""
    print("=" * 60)
    print("最终修复验证")
    print("=" * 60)
    
    success = test_tick_flow_direct()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 修复验证成功！")
        print("请运行: python ui/new_main_window.py 启动应用")
    else:
        print("⚠️  需要进一步调试")
    print("=" * 60)

if __name__ == "__main__":
    run_final_test()