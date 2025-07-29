#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy_ctp import CtpGateway

def main():
    print("开始测试...")
    
    # 创建事件引擎
    event_engine = EventEngine()
    print("事件引擎创建成功")
    
    # 创建主引擎
    main_engine = MainEngine(event_engine)
    print("主引擎创建成功")
    
    # 添加CTP网关
    main_engine.add_gateway(CtpGateway)
    print("CTP网关添加成功")
    
    print("测试完成，系统可以正常启动")

if __name__ == "__main__":
    main() 