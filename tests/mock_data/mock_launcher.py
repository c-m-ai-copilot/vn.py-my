"""
Mock模式启动器
通过环境变量启用mock模式
"""

import os
import sys
from pathlib import Path

# 添加mock数据路径
sys.path.insert(0, str(Path(__file__).parent))

def enable_mock_mode():
    """启用mock模式"""
    os.environ['USE_MOCK_DATA'] = 'true'
    print("🚀 Mock模式已启用")

def disable_mock_mode():
    """禁用mock模式"""
    os.environ['USE_MOCK_DATA'] = 'false'
    print("🔌 Mock模式已禁用")

def is_mock_enabled() -> bool:
    """检查是否启用mock模式"""
    return os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'

if __name__ == "__main__":
    enable_mock_mode()
    print("Mock模式测试启动...")
    
    # 这里可以添加简单的测试代码
    from tests.mock_data.mock_engine import get_mock_engine
    from vnpy.event import EventEngine
    
    event_engine = EventEngine()
    mock_engine = get_mock_engine(None, event_engine)
    
    print("✅ Mock数据系统加载成功")
    print("支持的合约数量:", len(mock_engine.get_all_contracts()))
    print("账户余额:", mock_engine.get_account().balance if mock_engine.get_account() else "N/A")