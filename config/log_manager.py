import sys
from typing import Callable, List

class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.handlers: List[Callable[[str], None]] = []
    
    def register_handler(self, handler: Callable[[str], None]) -> None:
        """注册日志处理器"""
        self.handlers.append(handler)
    
    def log(self, msg: str) -> None:
        """输出日志到UI和控制台"""
        # 输出到控制台
        self.console_log(msg)
        # 输出到UI
        for handler in self.handlers:
            handler(msg)
    
    def console_log(self, msg: str) -> None:
        """输出日志到控制台"""
        print(msg, flush=True)

# 创建全局实例
log_manager = LogManager() 