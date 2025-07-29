from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 配置文件目录
CONFIG_DIR = ROOT_DIR / "config"

# 确保配置目录存在
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# 订阅合约的配置文件路径
SUBSCRIBED_SYMBOLS_PATH = CONFIG_DIR / "subscribed_symbols.json" 