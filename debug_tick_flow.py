#!/usr/bin/env python3
"""
Tick数据流程调试工具
用于全面追踪tick数据的生成、传输和接收过程
"""

import time
import sys
import traceback
from typing import Dict, List, Optional
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT, EVENT_LOG
from vnpy.trader.object import TickData, ContractData, SubscribeRequest
from vnpy.event import Event
from config.tick_manager import tick_manager
from config.subscribed_symbols import subscribed_symbols
from config.log_manager import log_manager

class TickFlowDebugger:
    """Tick数据流程调试器"""
    
    def __init__(self):
        self.main_engine = None
        self.event_engine = None
        self.debug_logs = []
        
    def log(self, message: str, level: str = "INFO"):
        """记录调试日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.debug_logs.append(log_entry)
        print(log_entry)
        
    def analyze_tick_flow(self):
        """分析tick数据流程"""
        print("=" * 80)
        print("TICK数据流程调试分析")
        print("=" * 80)
        
        # 1. 检查订阅列表
        self.check_subscription_list()
        
        # 2. 检查合约是否存在
        self.check_contracts()
        
        # 3. 检查tick管理器状态
        self.check_tick_manager()
        
        # 4. 检查事件系统
        self.check_event_system()
        
        # 5. 模拟订阅流程
        self.simulate_subscription_flow()
        
    def check_subscription_list(self):
        """检查订阅列表"""
        self.log("=== 1. 检查订阅列表 ===")
        
        try:
            symbols = subscribed_symbols.get_symbols()
            self.log(f"已订阅的合约数量: {len(symbols)}")
            
            for symbol in symbols:
                self.log(f"  订阅合约: {symbol}")
                
            # 检查json文件内容
            import json
            import os
            config_path = os.path.join(os.path.dirname(__file__), "config", "subscribed_symbols.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.log(f"配置文件中的symbols: {data.get('symbols', [])}")
            else:
                self.log("配置文件不存在", "WARNING")
                
        except Exception as e:
            self.log(f"检查订阅列表时出错: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
    def check_contracts(self):
        """检查合约信息"""
        self.log("=== 2. 检查合约信息 ===")
        
        try:
            # 尝试从mock系统获取合约
            from tests.mock_data.mock_contracts import MOCK_CONTRACTS, CONTRACT_LIST
            
            self.log(f"Mock系统中定义的总合约数: {len(MOCK_CONTRACTS)}")
            self.log(f"Mock系统中定义的合约列表数: {len(CONTRACT_LIST)}")
            
            for symbol, contract in MOCK_CONTRACTS.items():
                self.log(f"  合约: {symbol} -> {contract.exchange.value}.{contract.name}")
                
            # 检查当前订阅的合约是否在mock系统中存在
            symbols = subscribed_symbols.get_symbols()
            for vt_symbol in symbols:
                symbol, exchange = vt_symbol.split('.')
                exists = symbol in MOCK_CONTRACTS
                self.log(f"  合约 {vt_symbol} 在mock系统中: {'✓' if exists else '✗'}")
                
        except Exception as e:
            self.log(f"检查合约时出错: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
    def check_tick_manager(self):
        """检查tick管理器状态"""
        self.log("=== 3. 检查tick管理器状态 ===")
        
        try:
            # 检查tick管理器中的缓存
            tick_count = len(tick_manager.ticks)
            self.log(f"Tick管理器中缓存的tick数量: {tick_count}")
            
            for vt_symbol, tick in tick_manager.ticks.items():
                self.log(f"  合约 {vt_symbol} 的tick数据:")
                self.log(f"    最新价: {tick.last_price}")
                self.log(f"    时间: {tick.datetime}")
                self.log(f"    成交量: {tick.volume}")
                
            # 检查订阅的合约是否有tick数据
            symbols = subscribed_symbols.get_symbols()
            for vt_symbol in symbols:
                has_tick = tick_manager.get_tick(vt_symbol) is not None
                self.log(f"  合约 {vt_symbol} 是否有tick数据: {'✓' if has_tick else '✗'}")
                
        except Exception as e:
            self.log(f"检查tick管理器时出错: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
    def check_event_system(self):
        """检查事件系统"""
        self.log("=== 4. 检查事件系统 ===")
        
        try:
            # 创建事件引擎
            self.event_engine = EventEngine()
            
            # 注册事件监听器
            def on_tick_event(event: Event):
                tick: TickData = event.data
                vt_symbol = f"{tick.symbol}.{tick.exchange.value}"
                self.log(f"收到TICK事件: {vt_symbol} - 价格: {tick.last_price}")
                
            def on_contract_event(event: Event):
                contract: ContractData = event.data
                self.log(f"收到CONTRACT事件: {contract.vt_symbol}")
                
            def on_log_event(event: Event):
                log = event.data
                self.log(f"收到LOG事件: {log.msg}")
                
            self.event_engine.register(EVENT_TICK, on_tick_event)
            self.event_engine.register(EVENT_CONTRACT, on_contract_event)
            self.event_engine.register(EVENT_LOG, on_log_event)
            
            self.event_engine.start()
            self.log("事件引擎已启动")
            
            # 启动事件引擎
            self.event_engine.start()
            
        except Exception as e:
            self.log(f"检查事件系统时出错: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
    def simulate_subscription_flow(self):
        """模拟订阅流程"""
        self.log("=== 5. 模拟订阅流程 ===")
        
        try:
            # 创建主引擎
            self.main_engine = MainEngine(self.event_engine)
            
            # 添加mock引擎
            from tests.mock_data.mock_engine import MockEngine as CtpGateway
            mock_engine = CtpGateway(self.main_engine, self.event_engine)
            self.main_engine.gateways["CTP"] = mock_engine
            
            self.log("主引擎和mock引擎已创建")
            
            # 获取合约列表
            contracts = mock_engine.get_all_contracts()
            self.log(f"从mock引擎获取合约: {len(contracts)}")
            
            # 模拟订阅流程
            symbols = subscribed_symbols.get_symbols()
            self.log(f"开始模拟订阅 {len(symbols)} 个合约")
            
            for vt_symbol in symbols:
                try:
                    symbol, exchange_str = vt_symbol.split('.')
                    from vnpy.trader.constant import Exchange
                    exchange = Exchange(exchange_str)
                    
                    req = SubscribeRequest(
                        symbol=symbol,
                        exchange=exchange
                    )
                    
                    # 调用订阅方法
                    result = self.main_engine.subscribe(req, "CTP")
                    self.log(f"订阅 {vt_symbol} 结果: {result}")
                    
                    # 检查订阅后的状态
                    time.sleep(0.1)  # 等待事件处理
                    
                    # 检查mock引擎中的订阅状态
                    if hasattr(mock_engine, 'gateway') and hasattr(mock_engine.gateway, 'subscribed_symbols'):
                        subscribed = vt_symbol in mock_engine.gateway.subscribed_symbols
                        self.log(f"  Mock引擎中订阅状态: {'已订阅' if subscribed else '未订阅'}")
                    
                except Exception as e:
                    self.log(f"订阅 {vt_symbol} 时出错: {str(e)}", "ERROR")
                    
        except Exception as e:
            self.log(f"模拟订阅流程时出错: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
    def test_tick_generation(self):
        """测试tick数据生成"""
        self.log("=== 6. 测试tick数据生成 ===")
        
        try:
            from tests.mock_data.mock_tick_generator import mock_tick_generator
            from tests.mock_data.mock_contracts import MOCK_CONTRACTS
            
            # 生成单个tick
            for symbol, contract in MOCK_CONTRACTS.items():
                vt_symbol = f"{symbol}.{contract.exchange.value}"
                
                # 检查是否在订阅列表中
                if vt_symbol in subscribed_symbols.get_symbols():
                    tick = mock_tick_generator.generate_tick(symbol, contract.exchange)
                    if tick:
                        self.log(f"为 {vt_symbol} 生成tick数据: {tick.last_price}")
                        
                        # 手动触发事件
                        event = Event(EVENT_TICK, tick)
                        self.event_engine.put(event)
                        
                        # 检查tick管理器
                        time.sleep(0.1)
                        stored_tick = tick_manager.get_tick(vt_symbol)
                        self.log(f"  Tick管理器中的数据: {'✓' if stored_tick else '✗'}")
                    else:
                        self.log(f"  无法为 {vt_symbol} 生成tick数据", "WARNING")
                        
        except Exception as e:
            self.log(f"测试tick生成时出错: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
    def save_debug_report(self):
        """保存调试报告"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"debug_tick_flow_{timestamp}.log"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("TICK数据流程调试报告\n")
                f.write("=" * 80 + "\n")
                f.write("\n".join(self.debug_logs))
                
            self.log(f"调试报告已保存到: {filename}")
            
        except Exception as e:
            self.log(f"保存调试报告时出错: {str(e)}", "ERROR")
            
    def run_full_debug(self):
        """运行完整调试"""
        print("开始运行tick数据流程完整调试...")
        
        try:
            self.analyze_tick_flow()
            self.test_tick_generation()
            self.save_debug_report()
            
            print("\n调试完成！")
            print("请检查生成的调试报告文件")
            
        except Exception as e:
            print(f"调试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debugger = TickFlowDebugger()
    debugger.run_full_debug()