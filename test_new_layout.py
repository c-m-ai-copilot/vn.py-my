#!/usr/bin/env python3
"""
测试新的布局设计：左侧交易组件，右侧上方行情组件，右侧下方订阅合约行情
"""

import sys
import os
from PyQt5 import QtWidgets
from vnpy.trader.engine import MainEngine, EventEngine
from ui.market_monitor import MarketMonitor
from ui.trading_component import SimpleTradingComponent
from tests.mock_data.mock_launcher import is_mock_enabled

def test_new_layout():
    """测试新布局"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 创建引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 设置环境变量使用mock数据
    os.environ['USE_MOCK_DATA'] = 'true'
    
    # 创建交易组件
    trading_component = SimpleTradingComponent(main_engine, event_engine)
    
    # 创建行情监控组件
    gateway_name = "MockCTP" if is_mock_enabled() else "CTP"
    market_monitor = MarketMonitor(
        main_engine, 
        event_engine, 
        gateway_name=gateway_name,
        trading_widget=trading_component
    )
    
    # 设置窗口标题和大小
    market_monitor.setWindowTitle("新布局测试 - 左侧交易，右侧行情")
    market_monitor.resize(1600, 900)
    
    # 显示窗口
    market_monitor.show()
    
    print("新布局测试窗口已显示")
    print("布局说明：")
    print("- 左侧：交易组件（固定320px宽度）")
    print("- 右侧上方：合约查询表格")
    print("- 右侧下方：订阅合约行情表格")
    print("- 双击订阅行情表格中的合约可以更新左侧交易组件的合约信息")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(test_new_layout()) 