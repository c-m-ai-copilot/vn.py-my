
from vnpy.trader.engine import BaseEngine, EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_POSITION
from vnpy.event import Event
from typing import Dict, List, Any
import json
import os
from datetime import datetime

APP_NAME = "StrategyEngine"

class StrategyEngine(BaseEngine):
    """策略引擎"""

    def __init__(self, main_engine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine, APP_NAME)
        
        self.strategies: Dict[str, Dict[str, Any]] = {}
        self.active_strategies: Dict[str, Dict[str, Any]] = {}
        self.strategy_data: Dict[str, Dict[str, Any]] = {}
        self.strategy_results: Dict[str, List[Dict[str, Any]]] = {}
        
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(self.data_path, exist_ok=True)

    def init_engine(self):
        """初始化引擎"""
        self.load_strategies()
        self.register_events()
        self.write_log("策略引擎初始化完成")

    def close_engine(self):
        """关闭引擎"""
        self.save_strategies()
        self.write_log("策略引擎关闭")

    def register_events(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)

    def process_tick_event(self, event: Event):
        """处理行情事件"""
        tick = event.data
        for strategy in self.active_strategies.values():
            if strategy.get("symbols") and tick.symbol in strategy["symbols"]:
                self.on_strategy_tick(strategy, tick)

    def process_order_event(self, event: Event):
        """处理订单事件"""
        order = event.data
        for strategy in self.active_strategies.values():
            if strategy.get("orders") and order.order_id in strategy["orders"]:
                self.on_strategy_order(strategy, order)

    def process_trade_event(self, event: Event):
        """处理成交事件"""
        trade = event.data
        for strategy in self.active_strategies.values():
            if strategy.get("trades") and trade.order_id in strategy.get("orders", []):
                self.on_strategy_trade(strategy, trade)

    def process_position_event(self, event: Event):
        """处理持仓事件"""
        position = event.data
        for strategy in self.active_strategies.values():
            if strategy.get("positions") and position.symbol in strategy["positions"]:
                self.on_strategy_position(strategy, position)

    def add_strategy(self, name: str, strategy_type: str, parameters: Dict[str, Any], symbols: List[str]):
        """添加策略"""
        strategy_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        strategy = {
            "id": strategy_id,
            "name": name,
            "type": strategy_type,
            "parameters": parameters,
            "symbols": symbols,
            "status": "stopped",
            "created_at": datetime.now().isoformat(),
            "orders": [],
            "trades": [],
            "positions": {},
            "performance": {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit": 0.0,
                "max_drawdown": 0.0
            }
        }
        self.strategies[strategy_id] = strategy
        self.save_strategies()
        return strategy_id

    def start_strategy(self, strategy_id: str):
        """启动策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id]["status"] = "running"
            self.active_strategies[strategy_id] = self.strategies[strategy_id]
            self.write_log(f"策略 {strategy_id} 已启动")

    def stop_strategy(self, strategy_id: str):
        """停止策略"""
        if strategy_id in self.active_strategies:
            self.strategies[strategy_id]["status"] = "stopped"
            del self.active_strategies[strategy_id]
            self.write_log(f"策略 {strategy_id} 已停止")

    def remove_strategy(self, strategy_id: str):
        """移除策略"""
        self.stop_strategy(strategy_id)
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            self.save_strategies()
            self.write_log(f"策略 {strategy_id} 已移除")

    def get_strategies(self) -> List[Dict[str, Any]]:
        """获取所有策略"""
        return list(self.strategies.values())

    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """获取活跃策略"""
        return list(self.active_strategies.values())

    def load_strategies(self):
        """加载策略配置"""
        strategies_file = os.path.join(self.data_path, "strategies.json")
        if os.path.exists(strategies_file):
            try:
                with open(strategies_file, 'r', encoding='utf-8') as f:
                    self.strategies = json.load(f)
            except Exception as e:
                self.write_log(f"加载策略配置失败: {e}")

    def save_strategies(self):
        """保存策略配置"""
        strategies_file = os.path.join(self.data_path, "strategies.json")
        try:
            with open(strategies_file, 'w', encoding='utf-8') as f:
                json.dump(self.strategies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.write_log(f"保存策略配置失败: {e}")

    def on_strategy_tick(self, strategy: Dict[str, Any], tick):
        """处理策略行情"""
        pass

    def on_strategy_order(self, strategy: Dict[str, Any], order):
        """处理策略订单"""
        pass

    def on_strategy_trade(self, strategy: Dict[str, Any], trade):
        """处理策略成交"""
        strategy["trades"].append({
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "direction": trade.direction,
            "volume": trade.volume,
            "price": trade.price,
            "time": datetime.now().isoformat()
        })
        strategy["performance"]["total_trades"] += 1
        self.calculate_performance(strategy)

    def on_strategy_position(self, strategy: Dict[str, Any], position):
        """处理策略持仓"""
        strategy["positions"][position.symbol] = {
            "volume": position.volume,
            "price": position.price,
            "direction": position.direction
        }

    def calculate_performance(self, strategy: Dict[str, Any]):
        """计算策略绩效"""
        trades = strategy["trades"]
        if len(trades) > 0:
            profitable_trades = [t for t in trades if t.get("profit", 0) > 0]
            strategy["performance"]["win_rate"] = len(profitable_trades) / len(trades)

    def backtest_strategy(self, strategy_id: str, start_date: str, end_date: str, data_source: str = "csv") -> Dict[str, Any]:
        """回测策略"""
        if strategy_id not in self.strategies:
            return {"error": "策略不存在"}
        
        strategy = self.strategies[strategy_id]
        symbols = strategy["symbols"]
        parameters = strategy["parameters"]
        
        # 加载历史数据
        historical_data = self.load_historical_data(symbols, start_date, end_date, data_source)
        if not historical_data:
            return {"error": "无法加载历史数据"}
        
        # 执行回测
        backtest_result = self.run_backtest(strategy, historical_data, parameters)
        
        # 保存回测结果
        self.save_backtest_result(strategy_id, backtest_result)
        
        return backtest_result

    def load_historical_data(self, symbols: List[str], start_date: str, end_date: str, data_source: str) -> Dict[str, List[Dict[str, Any]]]:
        """加载历史数据"""
        historical_data = {}
        
        for symbol in symbols:
            if data_source == "csv":
                data = self.load_csv_data(symbol, start_date, end_date)
            elif data_source == "database":
                data = self.load_database_data(symbol, start_date, end_date)
            else:
                data = []
            
            historical_data[symbol] = data
        
        return historical_data

    def load_csv_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """从CSV加载历史数据"""
        import pandas as pd
        
        csv_file = os.path.join(self.data_path, f"{symbol}_historical.csv")
        if not os.path.exists(csv_file):
            return []
        
        try:
            df = pd.read_csv(csv_file)
            df['datetime'] = pd.to_datetime(df['datetime'])
            mask = (df['datetime'] >= start_date) & (df['datetime'] <= end_date)
            filtered_df = df.loc[mask]
            
            return filtered_df.to_dict('records')
        except Exception as e:
            self.write_log(f"加载CSV数据失败: {e}")
            return []

    def load_database_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """从数据库加载历史数据"""
        # 这里可以添加数据库查询逻辑
        return []

    def run_backtest(self, strategy: Dict[str, Any], historical_data: Dict[str, List[Dict[str, Any]]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行回测"""
        trades = []
        positions = {}
        total_profit = 0
        max_drawdown = 0
        
        # 模拟回测逻辑
        for symbol, data in historical_data.items():
            if not data:
                continue
            
            # 这里可以添加具体的策略逻辑
            for tick in data:
                # 模拟交易信号
                if self.should_buy(tick, parameters):
                    trade = {
                        "symbol": symbol,
                        "direction": "BUY",
                        "volume": parameters.get("trade_volume", 1),
                        "price": tick["close"],
                        "time": tick["datetime"]
                    }
                    trades.append(trade)
                elif self.should_sell(tick, parameters):
                    trade = {
                        "symbol": symbol,
                        "direction": "SELL",
                        "volume": parameters.get("trade_volume", 1),
                        "price": tick["close"],
                        "time": tick["datetime"]
                    }
                    trades.append(trade)
        
        # 计算回测结果
        if trades:
            total_profit = sum(t.get("profit", 0) for t in trades)
            win_trades = [t for t in trades if t.get("profit", 0) > 0]
            win_rate = len(win_trades) / len(trades)
        else:
            win_rate = 0
        
        return {
            "strategy_id": strategy["id"],
            "start_date": min(d["datetime"] for data in historical_data.values() for d in data),
            "end_date": max(d["datetime"] for data in historical_data.values() for d in data),
            "total_trades": len(trades),
            "total_profit": total_profit,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "trades": trades,
            "positions": positions,
            "parameters": parameters
        }

    def should_buy(self, tick: Dict[str, Any], parameters: Dict[str, Any]) -> bool:
        """判断是否应该买入"""
        # 这里可以添加具体的买入逻辑
        return False

    def should_sell(self, tick: Dict[str, Any], parameters: Dict[str, Any]) -> bool:
        """判断是否应该卖出"""
        # 这里可以添加具体的卖出逻辑
        return False

    def save_backtest_result(self, strategy_id: str, result: Dict[str, Any]):
        """保存回测结果"""
        backtest_file = os.path.join(self.data_path, f"backtest_{strategy_id}.json")
        try:
            with open(backtest_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.write_log(f"保存回测结果失败: {e}")

    def get_backtest_results(self, strategy_id: str) -> List[Dict[str, Any]]:
        """获取策略的回测结果"""
        backtest_file = os.path.join(self.data_path, f"backtest_{strategy_id}.json")
        if os.path.exists(backtest_file):
            try:
                with open(backtest_file, 'r', encoding='utf-8') as f:
                    return [json.load(f)]
            except Exception as e:
                self.write_log(f"加载回测结果失败: {e}")
        return []

    def get_all_backtest_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有策略的回测结果"""
        results = {}
        for strategy_id in self.strategies.keys():
            results[strategy_id] = self.get_backtest_results(strategy_id)
        return results

    def write_log(self, message: str):
        """写入日志"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
