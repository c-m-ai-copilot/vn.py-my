# 技术文档

## 系统架构详解

### 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │  Business Logic │    │   Data Layer    │
│                 │    │                 │    │                 │
│ - MainWindow    │◄──►│ - MainEngine    │◄──►│ - CTP Gateway   │
│ - Components    │    │ - EventEngine   │    │ - Market Data   │
│ - Monitors      │    │ - Managers      │    │ - Order Data    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件说明

#### 1. MainEngine (主引擎)
负责整个系统的核心业务逻辑处理：
- 交易接口管理
- 订单管理
- 持仓管理
- 账户管理

#### 2. EventEngine (事件引擎)
基于事件驱动的消息处理机制：
- 实时行情事件
- 交易事件
- 系统事件
- 日志事件

#### 3. Gateway (交易网关)
连接外部交易系统的接口：
- CTP网关：连接期货公司交易系统
- 行情接口：接收实时行情数据
- 交易接口：发送交易指令

## 核心模块详解

### UI模块

#### MainWindow (主窗口)
```python
class MainWindow(QtWidgets.QMainWindow):
    """主窗口类，负责整个界面的布局和事件处理"""
    
    def __init__(self):
        # 初始化事件引擎和主引擎
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        
        # 添加CTP网关
        self.main_engine.add_gateway(CtpGateway)
```

**主要功能：**
- 界面布局管理
- 事件信号处理
- 子组件协调
- 登录对话框管理

#### TradingComponent (交易组件)
```python
class SimpleTradingComponent(QtWidgets.QWidget):
    """交易下单组件"""
    
    def send_order(self):
        """发送委托订单"""
        # 构建订单请求
        req = OrderRequest(
            symbol=symbol,
            exchange=exchange,
            direction=direction,
            type=order_type,
            offset=offset,
            price=price,
            volume=volume
        )
        
        # 发送订单
        vt_orderid = self.main_engine.send_order(req, gateway_name)
```

**主要功能：**
- 订单参数设置
- 风险检查
- 订单发送
- 撤单操作

#### MarketMonitor (行情监控)
```python
class MarketMonitor(QtWidgets.QWidget):
    """行情监控组件"""
    
    def process_tick_event(self, event: Event):
        """处理实时行情事件"""
        tick = event.data
        # 更新行情数据
        tick_manager.update_tick(tick)
        # 更新界面显示
        self.update_tick_table()
```

**主要功能：**
- 合约查询和订阅
- 实时行情显示
- 行情数据管理
- K线图表集成

### 配置模块

#### SubscribedSymbols (订阅管理)
```python
class SubscribedSymbols:
    """管理订阅的合约符号"""
    
    def add(self, vt_symbol: str):
        """添加订阅合约"""
        self.symbols.add(vt_symbol)
        self.save()
    
    def remove(self, vt_symbol: str):
        """移除订阅合约"""
        self.symbols.discard(vt_symbol)
        self.save()
```

#### LogManager (日志管理)
```python
class LogManager:
    """日志管理器"""
    
    def log(self, message: str):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 发送到所有注册的处理器
        for handler in self.handlers:
            handler(log_message)
```

## 数据流处理

### 行情数据流
```
CTP服务器 → CTP Gateway → EventEngine → MarketMonitor → UI更新
```

1. **数据接收**：CTP Gateway接收服务器推送的行情数据
2. **事件发布**：将行情数据封装为EVENT_TICK事件
3. **事件处理**：MarketMonitor接收并处理行情事件
4. **界面更新**：更新行情表格显示

### 交易数据流
```
UI操作 → TradingComponent → MainEngine → CTP Gateway → CTP服务器
```

1. **用户操作**：用户在交易面板输入订单信息
2. **订单构建**：TradingComponent构建OrderRequest对象
3. **订单发送**：MainEngine通过Gateway发送到服务器
4. **状态反馈**：服务器返回订单状态更新

## 事件系统

### 事件类型
```python
# 行情事件
EVENT_TICK = "eTick"

# 交易事件  
EVENT_ORDER = "eOrder"
EVENT_TRADE = "eTrade"

# 账户事件
EVENT_ACCOUNT = "eAccount"
EVENT_POSITION = "ePosition"

# 合约事件
EVENT_CONTRACT = "eContract"

# 日志事件
EVENT_LOG = "eLog"
```

### 事件处理机制
```python
# 注册事件处理器
self.event_engine.register(EVENT_TICK, self.process_tick_event)

# 发布事件
event = Event(EVENT_TICK, tick_data)
self.event_engine.put(event)

# 处理事件
def process_tick_event(self, event: Event):
    tick = event.data
    # 处理行情数据
```

## 风险控制机制

### 1. 持仓检查
```python
def check_position_before_close(self, symbol, direction, volume):
    """平仓前检查持仓"""
    positions = self.main_engine.get_all_positions()
    # 检查持仓是否足够
    if available_volume < volume:
        raise InsufficientPositionError()
```

### 2. 价格偏离检查
```python
def check_price_deviation(self, order_price, market_price):
    """检查委托价格偏离"""
    deviation = abs(order_price - market_price) / market_price
    if deviation > 0.1:  # 偏离超过10%
        return self.show_confirmation_dialog()
```

### 3. 资金检查
```python
def check_margin_before_open(self, symbol, volume, price):
    """开仓前检查保证金"""
    required_margin = self.calculate_margin(symbol, volume, price)
    available_balance = self.get_available_balance()
    
    if required_margin > available_balance:
        raise InsufficientMarginError()
```

## 性能优化

### 1. 界面更新优化
```python
# 使用定时器批量更新，避免频繁刷新
self.timer = QtCore.QTimer(self)
self.timer.timeout.connect(self.update_tick_table)
self.timer.start(2000)  # 2秒更新一次
```

### 2. 数据缓存
```python
class TickManager:
    """行情数据缓存管理"""
    
    def __init__(self):
        self.tick_cache = {}  # 缓存最新行情
        
    def update_tick(self, tick):
        """更新行情缓存"""
        self.tick_cache[tick.vt_symbol] = tick
```

### 3. 批量处理
```python
# 合约查询时批量处理，提高性能
BATCH_SIZE = 500
for i in range(0, len(contracts), BATCH_SIZE):
    batch = contracts[i:i + BATCH_SIZE]
    self.process_contract_batch(batch)
    QtWidgets.QApplication.processEvents()  # 保持界面响应
```

## 错误处理

### 1. 网络异常处理
```python
try:
    self.main_engine.connect(settings, gateway_name)
except ConnectionError as e:
    self.show_error_message(f"连接失败: {str(e)}")
    self.retry_connection()
```

### 2. 交易异常处理
```python
def send_order_with_retry(self, req, gateway_name, max_retries=3):
    """带重试的订单发送"""
    for attempt in range(max_retries):
        try:
            return self.main_engine.send_order(req, gateway_name)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)  # 等待1秒后重试
```

### 3. 数据异常处理
```python
def safe_float_convert(self, value, default=0.0):
    """安全的浮点数转换"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default
```

## 扩展开发指南

### 1. 添加新的监控组件
```python
class CustomMonitor(QtWidgets.QWidget):
    """自定义监控组件"""
    
    def __init__(self, main_engine, event_engine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # 注册事件监听
        self.event_engine.register(EVENT_CUSTOM, self.process_event)
    
    def process_event(self, event):
        """处理自定义事件"""
        pass
```

### 2. 添加新的交易策略
```python
class TradingStrategy:
    """交易策略基类"""
    
    def __init__(self, main_engine):
        self.main_engine = main_engine
    
    def on_tick(self, tick):
        """行情回调"""
        # 实现策略逻辑
        pass
    
    def send_order(self, req):
        """发送订单"""
        return self.main_engine.send_order(req, "CTP")
```

### 3. 添加技术指标
```python
class TechnicalIndicator:
    """技术指标基类"""
    
    def __init__(self, period=20):
        self.period = period
        self.data = []
    
    def update(self, value):
        """更新数据"""
        self.data.append(value)
        if len(self.data) > self.period:
            self.data.pop(0)
    
    def calculate(self):
        """计算指标值"""
        raise NotImplementedError
```

## 测试指南

### 1. 单元测试
```python
import unittest
from ui.trading_component import SimpleTradingComponent

class TestTradingComponent(unittest.TestCase):
    
    def setUp(self):
        self.component = SimpleTradingComponent(mock_engine, mock_event_engine)
    
    def test_order_validation(self):
        """测试订单验证"""
        # 测试代码
        pass
```

### 2. 集成测试
```python
def test_market_data_flow():
    """测试行情数据流"""
    # 模拟行情数据
    mock_tick = create_mock_tick()
    
    # 发送事件
    event = Event(EVENT_TICK, mock_tick)
    event_engine.put(event)
    
    # 验证处理结果
    assert market_monitor.tick_count > 0
```

### 3. 性能测试
```python
def test_performance():
    """性能测试"""
    import time
    
    start_time = time.time()
    
    # 执行大量操作
    for i in range(10000):
        process_tick_data(mock_tick)
    
    end_time = time.time()
    
    # 验证性能指标
    assert (end_time - start_time) < 1.0  # 1秒内完成
```

## 部署说明

### 1. 环境配置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件
```python
# config/config.py
TRADING_CONFIG = {
    "gateway": "CTP",
    "timeout": 30,
    "retry_count": 3,
    "log_level": "INFO"
}
```

### 3. 启动脚本
```batch
@echo off
cd /d %~dp0
call venv\Scripts\activate
python ui\main.py
pause
```

## 维护指南

### 1. 日志监控
- 定期检查系统日志
- 监控交易异常
- 分析性能指标

### 2. 数据备份
- 定期备份配置文件
- 保存交易记录
- 备份订阅设置

### 3. 版本更新
- 测试新版本兼容性
- 备份现有配置
- 逐步升级依赖库

---

本技术文档提供了系统的详细技术实现说明，便于开发人员理解和扩展系统功能。