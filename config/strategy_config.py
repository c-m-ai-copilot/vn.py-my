
# strategy_config.py

# 策略配置管理
import json
import os
from pathlib import Path
from config.paths import CONFIG_DIR

# 策略模板文件路径
STRATEGY_TEMPLATES_PATH = CONFIG_DIR / "strategy_templates.json"

# 默认策略模板
default_strategy_templates = [
    {
        "name": "双均线策略",
        "type": "CTA策略",
        "description": "基于双均线交叉的趋势跟踪策略",
        "parameters": {
            "fast_ma_period": 5,
            "slow_ma_period": 20,
            "trade_volume": 1,
            "stop_loss": 10,
            "take_profit": 20
        }
    },
    {
        "name": "RSI策略",
        "type": "CTA策略", 
        "description": "基于RSI指标的超买超卖策略",
        "parameters": {
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "trade_volume": 1,
            "stop_loss": 15,
            "take_profit": 25
        }
    },
    {
        "name": "布林带策略",
        "type": "CTA策略",
        "description": "基于布林带突破的均值回归策略",
        "parameters": {
            "bb_period": 20,
            "bb_std": 2,
            "trade_volume": 1,
            "stop_loss": 12,
            "take_profit": 18
        }
    },
    {
        "name": "MACD策略",
        "type": "CTA策略",
        "description": "基于MACD金叉死叉的趋势策略",
        "parameters": {
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "trade_volume": 1,
            "stop_loss": 8,
            "take_profit": 15
        }
    }
]

class StrategyConfig:
    """策略配置管理类"""
    
    def __init__(self):
        self.templates_path = STRATEGY_TEMPLATES_PATH
        self.templates = []
        self.load_templates()
    
    def load_templates(self):
        """加载策略模板"""
        try:
            if self.templates_path.exists():
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                # 使用默认模板
                self.templates = default_strategy_templates
                self.save_templates()
        except Exception as e:
            print(f"加载策略模板失败: {e}")
            self.templates = default_strategy_templates
    
    def save_templates(self):
        """保存策略模板"""
        try:
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存策略模板失败: {e}")
    
    def get_templates(self):
        """获取所有模板"""
        return self.templates
    
    def add_template(self, template):
        """添加模板"""
        self.templates.append(template)
        self.save_templates()
    
    def remove_template(self, index):
        """移除模板"""
        if 0 <= index < len(self.templates):
            self.templates.pop(index)
            self.save_templates()
    
    def get_template_by_name(self, name):
        """根据名称获取模板"""
        for template in self.templates:
            if template["name"] == name:
                return template
        return None

# 创建全局实例
strategy_config = StrategyConfig()

def get_strategy_templates():
    """获取策略模板列表"""
    return strategy_config.get_templates()

def add_strategy_template(template):
    """添加策略模板"""
    strategy_config.add_template(template)

def remove_strategy_template(index):
    """移除策略模板"""
    strategy_config.remove_template(index)

def get_strategy_template_by_name(name):
    """根据名称获取策略模板"""
    return strategy_config.get_template_by_name(name)
