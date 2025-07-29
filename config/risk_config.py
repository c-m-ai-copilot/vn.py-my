
# risk_config.py

import json
import os
from pathlib import Path
from config.paths import CONFIG_DIR

# 风险配置文件路径
RISK_CONFIG_PATH = CONFIG_DIR / "risk_config.json"

# 默认风险设置（与vn.py风险管理器一致）
default_risk_settings = {
    # 交易风险控制
    "max_loss_per_trade": 1000,  # 单笔最大亏损
    "max_loss_per_day": 5000,    # 每日最大亏损
    "max_total_loss": 10000,     # 总最大亏损
    
    # 仓位风险控制
    "max_position_ratio": 0.5,   # 最大仓位比例
    "max_concentration_ratio": 0.3,  # 最大集中持仓比例
    "max_trade_volume": 100,     # 单笔最大交易量
    
    # 账户风险控制
    "min_balance": 10000,        # 最小账户余额
    "max_buy_price": 100000,     # 最大买入价格
    "max_leverage": 10,          # 最大杠杆倍数
    
    # 策略风险控制
    "max_open_orders": 5,        # 最大挂单数量
    "max_positions": 10,         # 最大持仓品种数
    "max_daily_trades": 50,      # 每日最大交易次数
    
    # 预警设置
    "risk_score_threshold": 70,  # 风险评分阈值
    "alert_enabled": True,       # 是否启用警报
    "auto_stop_loss": True,      # 是否自动止损
    
    # 时间控制
    "trading_hours": {
        "start": "09:00",
        "end": "15:00"
    },
    "max_session_duration": 28800  # 最大交易时长（秒）
}

class RiskConfig:
    """风险配置管理类"""
    
    def __init__(self):
        self.config_path = RISK_CONFIG_PATH
        self.settings = {}
        self.load_config()
    
    def load_config(self):
        """加载风险配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                # 合并默认设置
                for key, value in default_risk_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
            else:
                # 使用默认设置
                self.settings = default_risk_settings.copy()
                self.save_config()
        except Exception as e:
            print(f"加载风险配置失败: {e}")
            self.settings = default_risk_settings.copy()
    
    def save_config(self):
        """保存风险配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存风险配置失败: {e}")
    
    def get_setting(self, key, default=None):
        """获取风险设置"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """设置风险设置"""
        self.settings[key] = value
        self.save_config()
    
    def get_all_settings(self):
        """获取所有风险设置"""
        return self.settings.copy()
    
    def reset_to_default(self):
        """重置为默认设置"""
        self.settings = default_risk_settings.copy()
        self.save_config()
    
    def update_settings(self, new_settings: dict):
        """批量更新设置"""
        self.settings.update(new_settings)
        self.save_config()
    
    def validate_setting(self, key, value):
        """验证设置值的有效性"""
        validators = {
            "max_loss_per_trade": lambda x: isinstance(x, (int, float)) and x > 0,
            "max_loss_per_day": lambda x: isinstance(x, (int, float)) and x > 0,
            "max_position_ratio": lambda x: isinstance(x, (int, float)) and 0 < x <= 1,
            "max_concentration_ratio": lambda x: isinstance(x, (int, float)) and 0 < x <= 1,
            "max_trade_volume": lambda x: isinstance(x, int) and x > 0,
            "min_balance": lambda x: isinstance(x, (int, float)) and x > 0,
            "max_buy_price": lambda x: isinstance(x, (int, float)) and x > 0,
            "max_leverage": lambda x: isinstance(x, (int, float)) and x > 0,
            "max_open_orders": lambda x: isinstance(x, int) and x > 0,
            "max_positions": lambda x: isinstance(x, int) and x > 0,
            "max_daily_trades": lambda x: isinstance(x, int) and x > 0,
            "risk_score_threshold": lambda x: isinstance(x, int) and 0 <= x <= 100,
            "alert_enabled": lambda x: isinstance(x, bool),
            "auto_stop_loss": lambda x: isinstance(x, bool),
        }
        
        if key in validators:
            return validators[key](value)
        return True

# 创建全局实例
risk_config = RiskConfig()

def get_risk_setting(key, default=None):
    """获取风险设置"""
    return risk_config.get_setting(key, default)

def set_risk_setting(key, value):
    """设置风险设置"""
    risk_config.set_setting(key, value)

def get_all_risk_settings():
    """获取所有风险设置"""
    return risk_config.get_all_settings()

def reset_risk_settings():
    """重置风险设置为默认值"""
    risk_config.reset_to_default()
