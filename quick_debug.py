#!/usr/bin/env python3
"""
快速调试脚本
用于测试tick数据流
"""

import os
import sys
import time
from PyQt5 import QtWidgets

# 设置mock模式
os.environ['USE_MOCK_DATA'] = 'true'

def test_tick_flow():
    """测试tick数据流"""
    print("🔍 开始测试tick数据流...")
    
    try:
        # 检查订阅列表
        from config.subscribed_symbols import subscribed_symbols
        symbols = subscribed_symbols.get_symbols()
        print(f"📋 已订阅的合约: {symbols}")
        
        # 检查mock合约
        from tests.mock_data.mock_contracts import MOCK_CONTRACTS
        print(f"📊 Mock系统中定义的合约: {list(MOCK_CONTRACTS.keys())}")
        
        # 检查合约匹配
        for vt_symbol in symbols:
            symbol, exchange = vt_symbol.split('.')
            exists = symbol in MOCK_CONTRACTS
            print(f"🔄 合约 {vt_symbol} 在mock系统中: {'✅' if exists else '❌'}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def run_debug_script():
    """运行调试脚本"""
    print("=" * 60)
    print("TICK数据调试工具")
    print("=" * 60)
    
    # 运行快速测试
    test_tick_flow()
    
    print("\n" + "=" * 60)
    print("建议运行完整调试: python debug_tick_flow.py")
    print("=" * 60)

if __name__ == "__main__":
    run_debug_script()