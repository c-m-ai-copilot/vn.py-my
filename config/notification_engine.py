
from vnpy.trader.engine import BaseEngine, EventEngine
from vnpy.trader.event import EVENT_TRADE, EVENT_ORDER, EVENT_POSITION, EVENT_LOG
from vnpy.event import Event
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

APP_NAME = "NotificationEngine"

class NotificationEngine(BaseEngine):
    """通知引擎"""

    def __init__(self, main_engine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine, APP_NAME)
        
        self.notifications = []
        self.rules = {}
        self.email_config = {}
        self.webhook_config = {}
        
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(self.data_path, exist_ok=True)
        
        self.register_events()
        self.load_config()

    def init_engine(self):
        """初始化引擎"""
        self.write_log("通知引擎初始化完成")

    def close_engine(self):
        """关闭引擎"""
        self.save_config()
        self.write_log("通知引擎关闭")

    def register_events(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_trade_event(self, event: Event):
        """处理成交事件"""
        trade = event.data
        notification = {
            "type": "trade",
            "title": "成交通知",
            "message": f"{trade.symbol} 成交: {trade.direction} {trade.volume}手 @{trade.price}",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "symbol": trade.symbol,
                "direction": trade.direction,
                "volume": trade.volume,
                "price": trade.price,
                "trade_id": trade.trade_id
            }
        }
        self.add_notification(notification)
        self.send_notification(notification)

    def process_order_event(self, event: Event):
        """处理订单事件"""
        order = event.data
        notification = {
            "type": "order",
            "title": "订单通知",
            "message": f"{order.symbol} 订单: {order.direction} {order.volume}手 @{order.price} ({order.status})",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "symbol": order.symbol,
                "direction": order.direction,
                "volume": order.volume,
                "price": order.price,
                "status": order.status,
                "order_id": order.order_id
            }
        }
        self.add_notification(notification)
        self.send_notification(notification)

    def process_position_event(self, event: Event):
        """处理持仓事件"""
        position = event.data
        if abs(position.volume) > 0:
            notification = {
                "type": "position",
                "title": "持仓变化",
                "message": f"{position.symbol} 持仓: {position.volume}手 @{position.price}",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "price": position.price,
                    "direction": position.direction
                }
            }
            self.add_notification(notification)
            self.send_notification(notification)

    def process_log_event(self, event: Event):
        """处理日志事件"""
        log = event.data
        if "错误" in log.msg or "异常" in log.msg:
            notification = {
                "type": "error",
                "title": "错误通知",
                "message": log.msg,
                "timestamp": datetime.now().isoformat(),
                "level": "error"
            }
            self.add_notification(notification)
            self.send_notification(notification)

    def add_notification(self, notification: Dict[str, Any]):
        """添加通知"""
        self.notifications.append(notification)
        
        # 限制通知数量
        max_notifications = 1000
        if len(self.notifications) > max_notifications:
            self.notifications = self.notifications[-max_notifications:]
        
        self.save_notifications()

    def send_notification(self, notification: Dict[str, Any]):
        """发送通知"""
        # 检查通知规则
        if not self.should_send_notification(notification):
            return

        # 发送邮件通知
        if self.email_config.get("enabled"):
            self.send_email_notification(notification)

        # 发送Webhook通知
        if self.webhook_config.get("enabled"):
            self.send_webhook_notification(notification)

    def should_send_notification(self, notification: Dict[str, Any]) -> bool:
        """检查是否应该发送通知"""
        notification_type = notification["type"]
        
        # 检查类型规则
        if notification_type in self.rules:
            rule = self.rules[notification_type]
            if not rule.get("enabled", True):
                return False
                
            # 检查关键词过滤
            keywords = rule.get("keywords", [])
            if keywords:
                message = notification["message"]
                return any(keyword in message for keyword in keywords)
        
        return True

    def send_email_notification(self, notification: Dict[str, Any]):
        """发送邮件通知"""
        if not self.email_config.get("smtp_server"):
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config["from_email"]
            msg['To'] = self.email_config["to_email"]
            msg['Subject'] = f"[交易系统] {notification['title']}"

            body = f"""
            时间: {notification['timestamp']}
            类型: {notification['type']}
            消息: {notification['message']}
            
            {json.dumps(notification.get('data', {}), indent=2, ensure_ascii=False)}
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP(self.email_config["smtp_server"], 
                                self.email_config.get("smtp_port", 587))
            
            if self.email_config.get("use_tls", True):
                server.starttls()
            
            server.login(self.email_config["username"], 
                        self.email_config["password"])
            
            server.send_message(msg)
            server.quit()
            
            self.write_log(f"邮件通知已发送: {notification['title']}")

        except Exception as e:
            self.write_log(f"发送邮件通知失败: {e}")

    def send_webhook_notification(self, notification: Dict[str, Any]):
        """发送Webhook通知"""
        if not self.webhook_config.get("url"):
            return

        try:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"【交易系统通知】\n{notification['title']}\n{notification['message']}"
                }
            }

            headers = {
                'Content-Type': 'application/json'
            }

            if self.webhook_config.get("secret"):
                headers['Authorization'] = f"Bearer {self.webhook_config['secret']}"

            response = requests.post(
                self.webhook_config["url"],
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.write_log(f"Webhook通知已发送: {notification['title']}")
            else:
                self.write_log(f"Webhook通知发送失败: {response.status_code}")

        except Exception as e:
            self.write_log(f"发送Webhook通知失败: {e}")

    def set_email_config(self, config: Dict[str, Any]):
        """设置邮件配置"""
        self.email_config = config
        self.save_config()

    def set_webhook_config(self, config: Dict[str, Any]):
        """设置Webhook配置"""
        self.webhook_config = config
        self.save_config()

    def add_notification_rule(self, rule_type: str, rule: Dict[str, Any]):
        """添加通知规则"""
        self.rules[rule_type] = rule
        self.save_config()

    def get_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取通知列表"""
        return self.notifications[-limit:] if self.notifications else []

    def get_notification_stats(self) -> Dict[str, Any]:
        """获取通知统计"""
        stats = {}
        for notification in self.notifications:
            ntype = notification["type"]
            stats[ntype] = stats.get(ntype, 0) + 1
        return stats

    def clear_notifications(self):
        """清除所有通知"""
        self.notifications = []
        self.save_notifications()

    def load_config(self):
        """加载配置"""
        config_file = os.path.join(self.data_path, "notification_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.email_config = config.get("email", {})
                    self.webhook_config = config.get("webhook", {})
                    self.rules = config.get("rules", {})
            except Exception as e:
                self.write_log(f"加载通知配置失败: {e}")

    def save_config(self):
        """保存配置"""
        config_file = os.path.join(self.data_path, "notification_config.json")
        config = {
            "email": self.email_config,
            "webhook": self.webhook_config,
            "rules": self.rules
        }
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.write_log(f"保存通知配置失败: {e}")

    def save_notifications(self):
        """保存通知记录"""
        notifications_file = os.path.join(self.data_path, "notifications.json")
        try:
            with open(notifications_file, 'w', encoding='utf-8') as f:
                json.dump(self.notifications, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.write_log(f"保存通知记录失败: {e}")

    def write_log(self, message: str):
        """写入日志"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
