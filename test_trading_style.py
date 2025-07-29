#!/usr/bin/env python3
"""
测试交易组件样式修复
"""

import sys
import os
from PyQt5 import QtWidgets
from vnpy.trader.engine import MainEngine, EventEngine
from ui.trading_component import SimpleTradingComponent

def test_trading_style():
    """测试交易组件样式"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 创建引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 创建交易组件
    trading_component = SimpleTradingComponent(main_engine, event_engine)
    
    # 设置窗口标题和大小
    trading_component.setWindowTitle("交易组件样式测试")
    trading_component.resize(350, 400)
    
    # 显示窗口
    trading_component.show()
    
    print("交易组件样式测试窗口已显示")
    print("检查是否还有竖线分隔符")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(test_trading_style()) 