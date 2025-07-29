#!/usr/bin/env python3
"""
Debug script to test mock engine contract loading
"""

import os
import sys
from PyQt5 import QtWidgets
from vnpy.trader.engine import MainEngine, EventEngine
from tests.mock_data.mock_engine import MockEngine

def test_mock_contracts():
    """测试mock引擎合约加载"""
    print("=== 测试Mock引擎合约加载 ===")
    
    # 设置环境变量使用mock数据
    os.environ['USE_MOCK_DATA'] = 'true'
    
    # 创建事件引擎和主引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    print("[DEBUG] 创建主引擎和事件引擎")
    
    # 添加mock网关
    try:
        from tests.mock_data.mock_engine import MockEngine as CtpGateway
        print("[DEBUG] 使用MockEngine")
    except ImportError:
        print("[ERROR] MockEngine导入失败")
        return
    
    # 创建mock引擎实例
    mock_engine = CtpGateway(main_engine, event_engine)
    main_engine.gateways["CTP"] = mock_engine
    
    print(f"[DEBUG] 已添加网关: {list(main_engine.gateways.keys())}")
    
    # 测试获取合约
    print("[DEBUG] 开始获取合约...")
    contracts = list(main_engine.get_all_contracts())
    print(f"[DEBUG] 获取到合约数量: {len(contracts)}")
    
    if contracts:
        print("[DEBUG] 合约列表:")
        for contract in contracts[:5]:  # 只显示前5个
            print(f"  {contract.symbol}.{contract.exchange.value} - {contract.name}")
    else:
        print("[DEBUG] 未获取到任何合约")
        
        # 直接从mock引擎获取
        print("[DEBUG] 尝试从mock引擎直接获取:")
        mock_contracts = mock_engine.get_all_contracts()
        print(f"[DEBUG] 从mock引擎获取合约数量: {len(mock_contracts)}")
        
        if mock_contracts:
            for contract in mock_contracts[:3]:
                print(f"  {contract.symbol}.{contract.exchange.value}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    test_mock_contracts()
    sys.exit(app.exec_())