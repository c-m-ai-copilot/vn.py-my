#!/usr/bin/env python3
"""
Direct test of mock engine contract loading
"""

import os
import sys
sys.path.insert(0, '/mnt/d/home/vnpy-test-v2')

# 设置mock模式
os.environ['USE_MOCK_DATA'] = 'true'

from vnpy.trader.engine import MainEngine, EventEngine
from tests.mock_data.mock_engine import MockEngine

def test_direct():
    """直接测试mock引擎"""
    print("=== 直接测试Mock引擎合约加载 ===")
    
    # 创建主引擎和事件引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 创建mock引擎
    mock_engine = MockEngine(main_engine, event_engine)
    
    # 获取合约
    contracts = mock_engine.get_all_contracts()
    print(f"[DEBUG] MockEngine返回合约数量: {len(contracts)}")
    
    if contracts:
        print("[DEBUG] 合约详情:")
        for i, contract in enumerate(contracts[:3]):
            print(f"  {i+1}. {contract.symbol}.{contract.exchange.value} - {contract.name}")
    
    # 检查主引擎的合约管理
    print(f"[DEBUG] 主引擎get_all_contracts(): {len(main_engine.get_all_contracts())}")
    
    # 测试合约注册
    all_contracts = main_engine.get_all_contracts()
    print(f"[DEBUG] 主引擎返回合约数量: {len(all_contracts)}")
    
    return len(contracts) > 0

if __name__ == "__main__":
    success = test_direct()
    print(f"\n[DEBUG] 测试是否成功: {success}")