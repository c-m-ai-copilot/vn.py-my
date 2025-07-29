# API 参考文档

## 核心API接口

### MainEngine API

#### 连接管理
```python
def connect(self, setting: dict, gateway_name: str) -> None:
    """
    连接交易网关
    
    Args:
        setting: 连接配置字典
        gateway_name: 网关名称
    """

def disconnect(self, gateway_name: str) -> None:
    """
    断开网关连接
    
    Args:
        gateway_name: 网关名称
    """

def get_gateway(self, gateway_name: str) -> BaseGateway:
    """
    获取网关对象
    
    Args:
        gateway_name: 网关名称
        
    Returns:
        网关对象实例
    """
```

#### 交易操作
```python
def send_order(self, req: OrderRequest, gateway_name: str) -> str:
    """
    发送委托订单
    
    Args:
        req: 订单请求对象
        gateway_name: 网关名称
        
    Returns:
        委托编号(vt_orderid)
    """

def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
    """
    撤销委托订单
    
    Args:
        req: 撤单请求对象
        gateway_name: 网关名称
    """

def get_all_active_orders(self) -> List[OrderData]:
    """
    获取所有活动委托
    
    Returns:
        活动委托列表
    """
```

#### 数据查询
```python
def get_contract(self, vt_symbol: str) -> ContractData:
    """
    获取合约信息
    
    Args:
        vt_symbol: 合约代码
        
    Returns:
        合约数据对象
    """

def get_all_contracts(self) -> List[ContractData]:
    """
    获取所有合约信息
    
    Returns:
        合约列表
    """

def get_tick(self, vt_symbol: str) -> TickData:
    """
    获取最新行情
    
    Args:
        vt_symbol: 合约代码
        
    Returns:
        行情数据对象
    """

def get_position(self, vt_symbol: str) -> PositionData:
    """
    获取持仓信息
    
    Args:
        vt_symbol: 合约代码
        
    Returns:
        持仓数据对象
    """

def get_all_positions(self) -> List[PositionData]:
    """
    获取所有持仓
    
    Returns:
        持仓列表
    """

def get_account(self) -> AccountData:
    """
    获取账户信息
    
    Returns:
        账户数据对象
    """
```

#### 行情订阅
```python
def subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
    """
    订阅行情
    
    Args:
        req: 订阅请求对象
        gateway_name: 网关名称
    """

def unsubscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
    """
    取消订阅
    
    Args:
        req: 订阅请求对象
        gateway_name: 网关名称
    """
```

### EventEngine API

#### 事件注册
```python
def register(self, type_: str, handler: Callable) -> None:
    """
    注册事件处理器
    
    Args:
        type_: 事件类型
        handler: 处理函数
    """

def unregister(self, type_: str, handler: Callable) -> None:
    """
    注销事件处理器
    
    Args:
        type_: 事件类型
        handler: 处理函数
    """
```

#### 事件发布
```python
def put(self, event: Event) -> None:
    """
    发布事件
    
    Args:
        event: 事件对象
    """

def start(self) -> None:
    """启动事件引擎"""

def stop(self) -> None:
    """停止事件引擎"""
```

## 数据对象定义

### OrderRequest (委托请求)
```python
@dataclass
class OrderRequest:
    symbol: str         # 合约代码
    exchange: Exchange  # 交易所
    direction: Direction # 方向
    type: OrderType     # 委托类型
    volume: float       # 数量
    price: float        # 价格
    offset: Offset      # 开平
    reference: str = "" # 备注
```

### OrderData (委托数据)
```python
@dataclass
class OrderData:
    orderid: str        # 委托编号
    symbol: str         # 合约代码
    exchange: Exchange  # 交易所
    direction: Direction # 方向
    offset: Offset      # 开平
    type: OrderType     # 委托类型
    volume: float       # 委托数量
    traded: float       # 成交数量
    status: Status      # 委托状态
    datetime: datetime  # 委托时间
    price: float        # 委托价格
    gateway_name: str   # 网关名称
```

### TickData (行情数据)
```python
@dataclass
class TickData:
    symbol: str         # 合约代码
    exchange: Exchange  # 交易所
    datetime: datetime  # 时间
    name: str          # 合约名称
    volume: float      # 成交量
    turnover: float    # 成交额
    open_interest: float # 持仓量
    last_price: float  # 最新价
    last_volume: float # 最新成交量
    limit_up: float    # 涨停价
    limit_down: float  # 跌停价
    open_price: float  # 开盘价
    high_price: float  # 最高价
    low_price: float   # 最低价
    pre_close: float   # 昨收价
    
    # 买卖盘
    bid_price_1: float
    bid_volume_1: float
    ask_price_1: float
    ask_volume_1: float
    
    gateway_name: str  # 网关名称
```

### PositionData (持仓数据)
```python
@dataclass
class PositionData:
    symbol: str         # 合约代码
    exchange: Exchange  # 交易所
    direction: Direction # 持仓方向
    volume: float       # 持仓数量
    frozen: float       # 冻结数量
    price: float        # 持仓均价
    pnl: float         # 持仓盈亏
    yd_volume: float   # 昨仓数量
    gateway_name: str  # 网关名称
```

### AccountData (账户数据)
```python
@dataclass
class AccountData:
    accountid: str      # 账户编号
    balance: float      # 账户余额
    frozen: float       # 冻结资金
    available: float    # 可用资金
    gateway_name: str   # 网关名称
```

### ContractData (合约数据)
```python
@dataclass
class ContractData:
    symbol: str         # 合约代码
    exchange: Exchange  # 交易所
    name: str          # 合约名称
    product: Product   # 产品类型
    size: float        # 合约乘数
    pricetick: float   # 最小价格变动
    min_volume: float  # 最小交易量
    stop_supported: bool # 是否支持止损
    net_position: bool  # 是否净持仓
    history_data: bool  # 是否支持历史数据
    gateway_name: str   # 网关名称
```

## 枚举类型定义

### Direction (方向)
```python
class Direction(Enum):
    LONG = "多"    # 多头
    SHORT = "空"   # 空头
```

### Offset (开平)
```python
class Offset(Enum):
    NONE = ""           # 无
    OPEN = "开"         # 开仓
    CLOSE = "平"        # 平仓
    CLOSETODAY = "平今"  # 平今
    CLOSEYESTERDAY = "平昨" # 平昨
```

### OrderType (委托类型)
```python
class OrderType(Enum):
    LIMIT = "限价"      # 限价单
    MARKET = "市价"     # 市价单
    STOP = "停损"       # 停损单
    FAK = "FAK"        # 即时成交剩余撤销
    FOK = "FOK"        # 全部成交或撤销
```

### Status (状态)
```python
class Status(Enum):
    SUBMITTING = "提交中"   # 提交中
    NOTTRADED = "未成交"    # 未成交
    PARTTRADED = "部分成交"  # 部分成交
    ALLTRADED = "全部成交"   # 全部成交
    CANCELLED = "已撤销"    # 已撤销
    REJECTED = "拒单"       # 拒单
```

### Exchange (交易所)
```python
class Exchange(Enum):
    SHFE = "SHFE"      # 上海期货交易所
    DCE = "DCE"        # 大连商品交易所
    CZCE = "CZCE"      # 郑州商品交易所
    CFFEX = "CFFEX"    # 中国金融期货交易所
    INE = "INE"        # 上海国际能源交易中心
```

## 事件类型常量

```python
# 行情事件
EVENT_TICK = "eTick"

# 交易事件
EVENT_ORDER = "eOrder"
EVENT_TRADE = "eTrade"

# 持仓事件
EVENT_POSITION = "ePosition"

# 账户事件
EVENT_ACCOUNT = "eAccount"

# 合约事件
EVENT_CONTRACT = "eContract"

# 日志事件
EVENT_LOG = "eLog"

# 定时器事件
EVENT_TIMER = "eTimer"
```

## UI组件API

### TradingComponent API

```python
class SimpleTradingComponent(QtWidgets.QWidget):
    
    def set_symbol_info(self, exchange: str, symbol: str, price: float = None):
        """
        设置合约信息
        
        Args:
            exchange: 交易所代码
            symbol: 合约代码
            price: 价格（可选）
        """
    
    def send_order(self):
        """发送委托订单"""
    
    def cancel_all(self):
        """撤销所有订单"""
```

### MarketMonitor API

```python
class MarketMonitor(QtWidgets.QWidget):
    
    # 信号定义
    signal_tick = QtCore.pyqtSignal(Event)
    contract_selected = QtCore.pyqtSignal(object)
    
    def query_contracts(self):
        """查询合约信息"""
    
    def subscribe_contract(self, contract: ContractData):
        """
        订阅合约行情
        
        Args:
            contract: 合约对象
        """
    
    def unsubscribe_contract(self, vt_symbol: str, row: int):
        """
        取消订阅合约
        
        Args:
            vt_symbol: 合约代码
            row: 表格行号
        """
    
    def filter_contracts(self, text: str):
        """
        过滤合约
        
        Args:
            text: 过滤文本
        """
```

## 配置管理API

### SubscribedSymbols API

```python
class SubscribedSymbols:
    
    def add(self, vt_symbol: str):
        """
        添加订阅合约
        
        Args:
            vt_symbol: 合约代码
        """
    
    def remove(self, vt_symbol: str):
        """
        移除订阅合约
        
        Args:
            vt_symbol: 合约代码
        """
    
    def get_symbols(self) -> set:
        """
        获取所有订阅合约
        
        Returns:
            合约代码集合
        """
    
    def save(self):
        """保存到文件"""
    
    def load(self):
        """从文件加载"""
```

### LogManager API

```python
class LogManager:
    
    def log(self, message: str):
        """
        记录日志
        
        Args:
            message: 日志消息
        """
    
    def console_log(self, message: str):
        """
        控制台日志
        
        Args:
            message: 日志消息
        """
    
    def register_handler(self, handler: Callable):
        """
        注册日志处理器
        
        Args:
            handler: 处理函数
        """
```

## 使用示例

### 基本交易流程
```python
# 1. 创建引擎
event_engine = EventEngine()
main_engine = MainEngine(event_engine)

# 2. 添加网关
main_engine.add_gateway(CtpGateway)

# 3. 连接
settings = {
    "用户名": "your_username",
    "密码": "your_password",
    "经纪商代码": "broker_id",
    "交易服务器": "trading_server",
    "行情服务器": "market_server"
}
main_engine.connect(settings, "CTP")

# 4. 订阅行情
req = SubscribeRequest(
    symbol="cu2506",
    exchange=Exchange.SHFE
)
main_engine.subscribe(req, "CTP")

# 5. 发送订单
order_req = OrderRequest(
    symbol="cu2506",
    exchange=Exchange.SHFE,
    direction=Direction.LONG,
    type=OrderType.LIMIT,
    volume=1,
    price=75000,
    offset=Offset.OPEN
)
vt_orderid = main_engine.send_order(order_req, "CTP")

# 6. 查询持仓
positions = main_engine.get_all_positions()
for pos in positions:
    print(f"合约: {pos.symbol}, 方向: {pos.direction}, 数量: {pos.volume}")
```

### 事件处理示例
```python
def on_tick(event: Event):
    """处理行情事件"""
    tick = event.data
    print(f"收到行情: {tick.symbol} 最新价: {tick.last_price}")

def on_order(event: Event):
    """处理委托事件"""
    order = event.data
    print(f"委托更新: {order.symbol} 状态: {order.status}")

# 注册事件处理器
event_engine.register(EVENT_TICK, on_tick)
event_engine.register(EVENT_ORDER, on_order)

# 启动事件引擎
event_engine.start()
```

---

本API文档提供了系统所有核心接口的详细说明，便于开发人员集成和扩展功能。