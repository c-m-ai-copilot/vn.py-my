
# notification_config.py

import json
import os
from pathlib import Path
from config.paths import CONFIG_DIR

# 通知配置文件路径
NOTIFICATION_CONFIG_PATH = CONFIG_DIR / "notification_config.json"

# 默认通知设置
default_notification_settings = {
    "popup": {
        "enabled": True,
        "duration": 3000  # 显示时长（毫秒）
    },
    "email": {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "from_email": "",
        "to_email": "",
        "use_tls": True
    },
    "webhook": {
        "enabled": False,
        "url": "",
        "secret": ""
    },
    "rules": {
        "trade": {
            "enabled": True,
            "keywords": []
        },
        "order": {
            "enabled": True,
            "keywords": []
        },
        "position": {
            "enabled": False,
            "keywords": []
        },
        "error": {
            "enabled": True,
            "keywords": ["错误", "异常", "失败"]
        },
        "risk": {
            "enabled": True,
            "keywords": ["风险", "警报", "警告"]
        }
    },
    "sound": {
        "enabled": True,
        "volume": 50
    }
}

class NotificationConfig:
    """通知配置管理类"""
    
    def __init__(self):
        self.config_path = NOTIFICATION_CONFIG_PATH
        self.settings = {}
        self.load_config()
    
    def load_config(self):
        """加载通知配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                
                # 合并默认设置
                for key, value in default_notification_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
            else:
                # 使用默认设置
                self.settings = default_notification_settings.copy()
                self.save_config()
        except Exception as e:
            print(f"加载通知配置失败: {e}")
            self.settings = default_notification_settings.copy()
    
    def save_config(self):
        """保存通知配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存通知配置失败: {e}")
    
    def get_setting(self, key, default=None):
        """获取通知设置"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """设置通知设置"""
        self.settings[key] = value
        self.save_config()
    
    def get_all_settings(self):
        """获取所有通知设置"""
        return self.settings.copy()
    
    def reset_to_default(self):
        """重置为默认设置"""
        self.settings = default_notification_settings.copy()
        self.save_config()

# 创建全局实例
notification_config = NotificationConfig()

def get_notification_setting(key, default=None):
    """获取通知设置"""
    return notification_config.get_setting(key, default)

def set_notification_setting(key, value):
    """设置通知设置"""
    notification_config.set_setting(key, value)

def get_all_notification_settings():
    """获取所有通知设置"""
    return notification_config.get_all_settings()

def reset_notification_settings():
    """重置通知设置为默认值"""
    notification_config.reset_to_default()
