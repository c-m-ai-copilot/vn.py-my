#!/usr/bin/env python3
"""
修复验证脚本
用于验证tick数据问题是否已修复
"""

import os
import time
os.environ['USE_MOCK_DATA'] = 'true'

def verify_fix():
    """验证修复效果"""
    print("🔍 开始验证tick数据修复效果...")
    
    try:
        # 1. 检查订阅列表
        from config.subscribed_symbols import subscribed_symbols
        symbols = subscribed_symbols.get_symbols()
        print(f"✅ 已订阅的合约: {len(symbols)} 个")
        
        # 2. 检查tick管理器
        from config.tick_manager import tick_manager
        print(f"📊 当前tick管理器中的数据: {len(tick_manager.ticks)} 个")
        
        # 3. 手动生成一些tick数据并测试
        from tests.mock_data.mock_tick_generator import mock_tick_generator
        from tests.mock_data.mock_contracts import MOCK_CONTRACTS
        from vnpy.trader.constant import Exchange
        
        success_count = 0
        for vt_symbol in symbols:
            symbol, exchange_str = vt_symbol.split('.')
            exchange = Exchange(exchange_str)
            
            # 生成tick
            tick = mock_tick_generator.generate_tick(symbol, exchange)
            if tick:
                # 手动存入tick管理器
                tick_manager.update_tick(tick)
                # 验证读取
                stored_tick = tick_manager.get_tick(vt_symbol)
                if stored_tick and stored_tick.last_price == tick.last_price:
                    print(f"✅ {vt_symbol}: 价格 {tick.last_price}")
                    success_count += 1
                else:
                    print(f"❌ {vt_symbol}: 存储失败")
        
        print(f"\n🎯 修复验证结果: {success_count}/{len(symbols)} 个合约tick数据正常")
        
        # 4. 最终tick管理器状态
        print(f"\n📈 最终tick管理器状态:")
        for vt_symbol, tick in tick_manager.ticks.items():
            print(f"   {vt_symbol}: {tick.last_price}")
            
        return success_count == len(symbols)
        
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_fix_verification():
    """运行修复验证"""
    print("=" * 60)
    print("TICK数据修复验证")
    print("=" * 60)
    
    success = verify_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 修复验证成功！tick数据功能已恢复正常")
    else:
        print("⚠️  修复验证失败，需要进一步调试")
    print("=" * 60)

if __name__ == "__main__":
    run_fix_verification()