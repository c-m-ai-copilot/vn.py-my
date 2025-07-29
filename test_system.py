#!/usr/bin/env python3
"""
CTA交易系统测试脚本
"""
import sys
import os
import json
import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_strategy_engine():
    """测试策略引擎"""
    print("=== 测试策略引擎 ===")
    
    try:
        from config.strategy_engine import StrategyEngine
        from vnpy.trader.engine import MainEngine, EventEngine
        
        # 创建测试环境
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        strategy_engine = StrategyEngine(main_engine, event_engine)
        
        # 初始化引擎
        strategy_engine.init_engine()
        
        # 添加测试策略
        strategy_id = strategy_engine.add_strategy(
            name="测试策略",
            strategy_type="moving_average",
            parameters={
                "short_window": 5,
                "long_window": 20,
                "trade_volume": 1
            },
            symbols=["rb2405", "cu2405"]
        )
        print(f"✅ 成功添加策略: {strategy_id}")
        
        # 获取策略列表
        strategies = strategy_engine.get_strategies()
        print(f"✅ 策略列表: {len(strategies)} 个策略")
        
        # 启动策略
        strategy_engine.start_strategy(strategy_id)
        print("✅ 策略启动成功")
        
        # 获取活跃策略
        active_strategies = strategy_engine.get_active_strategies()
        print(f"✅ 活跃策略: {len(active_strategies)} 个")
        
        # 停止策略
        strategy_engine.stop_strategy(strategy_id)
        print("✅ 策略停止成功")
        
        # 关闭引擎
        strategy_engine.close_engine()
        print("✅ 策略引擎测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略引擎测试失败: {e}")
        return False

def test_risk_engine():
    """测试风险引擎"""
    print("\n=== 测试风险引擎 ===")
    
    try:
        from config.risk_engine import RiskEngine
        from vnpy.trader.engine import MainEngine, EventEngine
        
        # 创建测试环境
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        risk_engine = RiskEngine(main_engine, event_engine)
        
        # 初始化引擎
        risk_engine.init_engine()
        
        # 测试风险规则
        risk_engine.add_risk_rule("test_rule", {
            "max_position_ratio": 0.8,
            "max_loss_per_day": 10000,
            "enabled": True
        })
        print("✅ 添加风险规则成功")
        
        # 获取风险状态
        risk_status = risk_engine.get_risk_status()
        print(f"✅ 风险状态: {risk_status}")
        
        # 获取风险规则
        rules = risk_engine.get_risk_rules()
        print(f"✅ 风险规则: {len(rules)} 个")
        
        # 关闭引擎
        risk_engine.close_engine()
        print("✅ 风险引擎测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 风险引擎测试失败: {e}")
        return False

def test_notification_engine():
    """测试通知引擎"""
    print("\n=== 测试通知引擎 ===")
    
    try:
        from config.notification_engine import NotificationEngine
        from vnpy.trader.engine import MainEngine, EventEngine
        
        # 创建测试环境
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        notification_engine = NotificationEngine(main_engine, event_engine)
        
        # 初始化引擎
        notification_engine.init_engine()
        
        # 设置邮件配置（测试用）
        notification_engine.set_email_config({
            "enabled": False,  # 实际测试中不发送邮件
            "smtp_server": "smtp.test.com",
            "from_email": "test@example.com",
            "to_email": "receiver@example.com",
            "username": "test",
            "password": "test"
        })
        
        # 设置Webhook配置（测试用）
        notification_engine.set_webhook_config({
            "enabled": False,  # 实际测试中不发送Webhook
            "url": "https://webhook.test.com/notify",
            "secret": "test_secret"
        })
        
        # 添加通知规则
        notification_engine.add_notification_rule("trade", {
            "enabled": True,
            "keywords": ["测试"]
        })
        
        # 获取通知统计
        stats = notification_engine.get_notification_stats()
        print(f"✅ 通知统计: {stats}")
        
        # 获取通知列表
        notifications = notification_engine.get_notifications(10)
        print(f"✅ 通知列表: {len(notifications)} 条")
        
        # 关闭引擎
        notification_engine.close_engine()
        print("✅ 通知引擎测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知引擎测试失败: {e}")
        return False

def test_backtest_function():
    """测试回测功能"""
    print("\n=== 测试回测功能 ===")
    
    try:
        from config.strategy_engine import StrategyEngine
        from vnpy.trader.engine import MainEngine, EventEngine
        
        # 创建测试环境
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        strategy_engine = StrategyEngine(main_engine, event_engine)
        
        # 初始化引擎
        strategy_engine.init_engine()
        
        # 添加测试策略
        strategy_id = strategy_engine.add_strategy(
            name="回测策略",
            strategy_type="backtest",
            parameters={
                "short_window": 5,
                "long_window": 20,
                "trade_volume": 1
            },
            symbols=["test_symbol"]
        )
        
        # 创建测试数据
        create_test_data(strategy_engine)
        
        # 运行回测
        start_date = "2024-01-01"
        end_date = "2024-12-31"
        result = strategy_engine.backtest_strategy(strategy_id, start_date, end_date)
        
        if "error" not in result:
            print(f"✅ 回测成功: {result['total_trades']} 笔交易")
            print(f"✅ 总收益: {result['total_profit']}")
            print(f"✅ 胜率: {result['win_rate']:.2%}")
        else:
            print(f"❌ 回测失败: {result['error']}")
        
        # 关闭引擎
        strategy_engine.close_engine()
        
        return "error" not in result
        
    except Exception as e:
        print(f"❌ 回测功能测试失败: {e}")
        return False

def create_test_data(strategy_engine):
    """创建测试数据"""
    import pandas as pd
    import numpy as np
    
    # 创建测试历史数据
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # 生成模拟价格数据
    np.random.seed(42)
    price_changes = np.random.normal(0, 0.02, len(dates))
    prices = 100 * np.exp(np.cumsum(price_changes))
    
    # 创建数据框
    df = pd.DataFrame({
        'datetime': dates,
        'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
        'close': prices,
        'volume': np.random.randint(1000, 10000, len(dates))
    })
    
    # 保存测试数据
    csv_file = os.path.join(strategy_engine.data_path, "test_symbol_historical.csv")
    df.to_csv(csv_file, index=False)
    print(f"✅ 创建测试数据: {csv_file}")

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始CTA交易系统测试...")
    
    results = [
        test_strategy_engine(),
        test_risk_engine(),
        test_notification_engine(),
        test_backtest_function()
    ]
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 测试结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统功能正常")
    else:
        print("⚠️  部分测试失败，请检查相关功能")

if __name__ == "__main__":
    run_all_tests()