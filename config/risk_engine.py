
from vnpy.trader.engine import BaseEngine, EventEngine
from vnpy.trader.event import EVENT_TRADE, EVENT_POSITION, EVENT_ORDER, EVENT_ACCOUNT
from vnpy.event import Event
from .risk_config import get_risk_setting, set_risk_setting
from PyQt5 import QtWidgets
import json
import os
from datetime import datetime
from typing import Dict, List, Any

APP_NAME = "RiskEngine"

class RiskEngine(BaseEngine):
    """风险引擎"""

    def __init__(self, main_engine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine, APP_NAME)

        self.daily_pnl = 0
        self.positions = {}
        self.orders = {}
        self.trades = []
        self.risk_rules = {}
        self.alerts = []
        
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(self.data_path, exist_ok=True)
        
        self.register_events()
        self.load_risk_rules()

    def init_engine(self):
        """初始化引擎"""
        self.write_log("风险引擎初始化完成")

    def close_engine(self):
        """关闭引擎"""
        self.save_risk_rules()
        self.write_log("风险引擎关闭")

    def register_events(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)

    def process_trade_event(self, event: Event):
        """处理成交事件"""
        trade = event.data
        self.trades.append(trade)
        
        position = self.positions.get(trade.vt_symbol)
        if position:
            # 计算平仓盈亏
            if trade.direction == "SHORT":  # 平多
                pnl = (trade.price - position.price) * trade.volume * position.contract_multiplier
            else:  # 平空
                pnl = (position.price - trade.price) * trade.volume * position.contract_multiplier
            self.daily_pnl += pnl
            
            self.check_daily_loss()
            self.check_trade_risk(trade)
            self.check_total_loss()

    def process_position_event(self, event: Event):
        """处理持仓事件"""
        position = event.data
        self.positions[position.vt_symbol] = position
        self.check_position_risk()
        self.check_concentration_risk()

    def process_order_event(self, event: Event):
        """处理订单事件"""
        order = event.data
        self.orders[order.order_id] = order
        self.check_order_risk(order)

    def process_account_event(self, event: Event):
        """处理账户事件"""
        account = event.data
        self.check_account_risk(account)

    def check_position_risk(self):
        """检查持仓风险"""
        total_position_value = 0
        for position in self.positions.values():
            total_position_value += position.volume * position.price * position.contract_multiplier
        
        account = self.main_engine.get_account()
        if account and account.balance > 0:
            position_ratio = total_position_value / account.balance
            max_position_ratio = get_risk_setting("max_position_ratio")
            if position_ratio > max_position_ratio:
                self.trigger_alert(f"最大持仓比例已超过阈值: {position_ratio:.2%}")
                return False
        return True

    def check_daily_loss(self):
        """检查每日亏损"""
        max_loss_per_day = get_risk_setting("max_loss_per_day")
        if self.daily_pnl < -max_loss_per_day:
            self.trigger_alert(f"每日亏损已超过阈值: {self.daily_pnl:.2f}")
            return False
        return True

    def check_total_loss(self):
        """检查总亏损"""
        max_total_loss = get_risk_setting("max_total_loss", 100000)
        if self.daily_pnl < -max_total_loss:
            self.trigger_alert(f"总亏损已超过阈值: {self.daily_pnl:.2f}")
            return False
        return True

    def check_concentration_risk(self):
        """检查集中度风险"""
        if not self.positions:
            return True
            
        total_value = sum(pos.volume * pos.price * pos.contract_multiplier 
                         for pos in self.positions.values())
        
        for symbol, position in self.positions.items():
            position_value = position.volume * position.price * position.contract_multiplier
            concentration_ratio = position_value / total_value if total_value > 0 else 0
            max_concentration = get_risk_setting("max_concentration_ratio", 0.3)
            
            if concentration_ratio > max_concentration:
                self.trigger_alert(f"{symbol} 持仓过于集中: {concentration_ratio:.2%}")
                return False
        return True

    def check_trade_risk(self, trade):
        """检查单笔交易风险"""
        max_trade_volume = get_risk_setting("max_trade_volume", 100)
        if trade.volume > max_trade_volume:
            self.trigger_alert(f"单笔交易量过大: {trade.volume}")
            return False
        return True

    def check_order_risk(self, order):
        """检查订单风险"""
        if order.direction == "BUY":
            max_buy_price = get_risk_setting("max_buy_price", 100000)
            if order.price > max_buy_price:
                self.trigger_alert(f"买单价格过高: {order.price}")
                return False
        return True

    def check_account_risk(self, account):
        """检查账户风险"""
        min_balance = get_risk_setting("min_balance", 10000)
        if account.balance < min_balance:
            self.trigger_alert(f"账户余额过低: {account.balance}")
            return False
        return True

    def add_risk_rule(self, rule_name: str, rule_config: Dict[str, Any]):
        """添加风险规则"""
        self.risk_rules[rule_name] = rule_config
        self.save_risk_rules()

    def remove_risk_rule(self, rule_name: str):
        """移除风险规则"""
        if rule_name in self.risk_rules:
            del self.risk_rules[rule_name]
            self.save_risk_rules()

    def get_risk_rules(self) -> Dict[str, Any]:
        """获取所有风险规则"""
        return self.risk_rules

    def get_risk_status(self) -> Dict[str, Any]:
        """获取风险状态"""
        return {
            "daily_pnl": self.daily_pnl,
            "positions": len(self.positions),
            "orders": len(self.orders),
            "trades": len(self.trades),
            "alerts": len(self.alerts),
            "risk_score": self.calculate_risk_score()
        }

    def calculate_risk_score(self) -> float:
        """计算风险评分"""
        score = 100.0
        
        # 根据各种风险因素调整评分
        if not self.check_position_risk():
            score -= 20
        if not self.check_daily_loss():
            score -= 30
        if not self.check_concentration_risk():
            score -= 15
            
        return max(0, score)

    def trigger_alert(self, message: str):
        """触发警报"""
        alert = {
            "time": datetime.now().isoformat(),
            "message": message,
            "level": "WARNING"
        }
        self.alerts.append(alert)
        
        # 保存警报记录
        alerts_file = os.path.join(self.data_path, "alerts.json")
        try:
            with open(alerts_file, 'a', encoding='utf-8') as f:
                json.dump(alert, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            self.write_log(f"保存警报失败: {e}")

        QtWidgets.QMessageBox.warning(None, "风险警报", message)

    def load_risk_rules(self):
        """加载风险规则"""
        rules_file = os.path.join(self.data_path, "risk_rules.json")
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    self.risk_rules = json.load(f)
            except Exception as e:
                self.write_log(f"加载风险规则失败: {e}")

    def save_risk_rules(self):
        """保存风险规则"""
        rules_file = os.path.join(self.data_path, "risk_rules.json")
        try:
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.risk_rules, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.write_log(f"保存风险规则失败: {e}")

    def reset_daily_pnl(self):
        """重置每日盈亏"""
        self.daily_pnl = 0
        self.trades = []
        self.write_log("每日盈亏已重置")

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取警报记录"""
        return self.alerts[-limit:] if self.alerts else []

    def write_log(self, message: str):
        """写入日志"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
