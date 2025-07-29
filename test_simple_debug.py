#!/usr/bin/env python3
"""
Debug script to test mock engine contract loading
"""

import os
import sys
sys.path.insert(0, '/mnt/d/home/vnpy-test-v2')

from tests.mock_data.mock_contracts import CONTRACT_LIST, MOCK_CONTRACTS
from tests.mock_data.mock_engine import MockEngine

def test_mock_contracts():
    """测试mock引擎合约加载"""
    print("=== 测试Mock合约数据 ===")
    
    print(f"[DEBUG] CONTRACT_LIST长度: {len(CONTRACT_LIST)}")
    print(f"[DEBUG] MOCK_CONTRACTS长度: {len(MOCK_CONTRACTS)}")
    
    if CONTRACT_LIST:
        print("[DEBUG] 合约示例:")
        for i, contract in enumerate(CONTRACT_LIST[:3]):
            print(f"  {i+1}. {contract.symbol}.{contract.exchange.value} - {contract.name}")
    
    print("\n[DEBUG] 测试MockEngine...")
    
    # 创建模拟事件引擎
    class MockEventEngine:
        def put(self, event):
            print(f"[DEBUG] 事件引擎收到事件: {event.type}")
    
    mock_engine = MockEngine(None, MockEventEngine())
    contracts = mock_engine.get_all_contracts()
    print(f"[DEBUG] MockEngine.get_all_contracts() 返回: {len(contracts)}")
    
    if contracts:
        print("[DEBUG] 合约详情:")
        for contract in contracts[:2]:
            print(f"  {contract.symbol} @ {contract.exchange.value}")

if __name__ == "__main__":
    test_mock_contracts()