# Mock数据规范文档

## 概述

本文档定义了期货交易系统的Mock数据规范，用于在不连接真实交易所的情况下测试系统交互逻辑。Mock数据模拟真实交易所的行为，包括行情、合约、订单、成交等核心功能。

## 数据类型

### 1. 合约数据 (Contract)

#### 数据结构
```json
{
  "symbol": "rb2410",
  "exchange": "SHFE",
  "name": "螺纹钢2410",
  "product": "FUTURES",
  "size": 10,
  "pricetick": 1.0,
  "min_volume": 1,
  "gateway_name": "CTP",
  "vt_symbol": "rb2410.SHFE"
}
```

#### 预定义合约列表
| 合约代码 | 名称 | 交易所 | 合约乘数 | 最小变动价位 | 最小下单量 |
|---------|------|--------|----------|--------------|------------|
| rb2410 | 螺纹钢2410 | SHFE | 10 | 1.0 | 1 |
| cu2409 | 沪铜2409 | SHFE | 5 | 10.0 | 1 |
| au2412 | 沪金2412 | SHFE | 1000 | 0.05 | 1 |
| i2409 | 铁矿石2409 | DCE | 100 | 0.5 | 1 |
| m2409 | 豆粕2409 | DCE | 10 | 1.0 | 1 |
| SR2409 | 白糖2409 | CZCE | 10 | 1.0 | 1 |
| TA2409 | PTA2409 | ZCE | 5 | 2.0 | 1 |
| IF2409 | 沪深2409 | CFFEX | 300 | 0.2 | 1 |

### 2. 行情数据 (Tick)

#### 数据结构
```json
{
  "symbol": "rb2410",
  "exchange": "SHFE",
  "datetime": "2024-07-22 09:30:00",
  "last_price": 3500.0,
  "volume": 1250,
  "open_interest": 150000,
  "open_price": 3485.0,
  "high_price": 3515.0,
  "low_price": 3480.0,
  "pre_close": 3490.0,
  "bid_price_1": 3499.0,
  "bid_volume_1": 120,
  "ask_price_1": 3501.0,
  "ask_volume_1": 85,
  "gateway_name": "CTP"
}
```

#### 行情生成规则
- **价格范围**: 根据基准价上下浮动 ±2%
- **成交量**: 随机生成 100-5000 手
- **持仓量**: 随机生成 10000-200000 手
- **更新频率**: 每1-3秒更新一次
- **波动模式**: 
  - 趋势行情：连续同方向小幅波动
  - 震荡行情：价格在区间内来回波动
  - 跳跃行情：偶尔出现较大价格跳跃

### 3. 账户数据 (Account)

#### 数据结构
```json
{
  "accountid": "123456",
  "balance": 1000000.0,
  "available": 800000.0,
  "frozen": 200000.0,
  "commission": 0.0,
  "margin": 180000.0,
  "close_profit": 0.0,
  "position_profit": 20000.0,
  "gateway_name": "CTP"
}
```

### 4. 持仓数据 (Position)

#### 数据结构
```json
{
  "symbol": "rb2410",
  "exchange": "SHFE",
  "direction": "LONG",
  "volume": 10,
  "frozen": 0,
  "yd_volume": 10,
  "price": 3490.0,
  "pnl": 1000.0,
  "margin": 35000.0,
  "gateway_name": "CTP"
}
```

### 5. 订单数据 (Order)

#### 数据结构
```json
{
  "orderid": "12345",
  "symbol": "rb2410",
  "exchange": "SHFE",
  "direction": "LONG",
  "offset": "OPEN",
  "type": "LIMIT",
  "price": 3500.0,
  "volume": 5,
  "traded": 0,
  "status": "NOT_TRADED",
  "datetime": "2024-07-22 09:31:00",
  "gateway_name": "CTP"
}
```

#### 订单状态流转
1. **NOT_TRADED** → **PART_TRADED** → **ALL_TRADED** (成交)
2. **NOT_TRADED** → **CANCELLED** (撤单)
3. **PART_TRADED** → **CANCELLED** (部分成交后撤单)

### 6. 成交数据 (Trade)

#### 数据结构
```json
{
  "tradeid": "T12345",
  "orderid": "12345",
  "symbol": "rb2410",
  "exchange": "SHFE",
  "direction": "LONG",
  "offset": "OPEN",
  "price": 3500.0,
  "volume": 5,
  "datetime": "2024-07-22 09:32:00",
  "gateway_name": "CTP"
}
```

## Mock数据配置

### 配置文件
`config/mock_config.json`

#### 配置示例
```json
{
  "enabled": true,
  "data_source": "mock",
  "update_interval": 1.5,
  "price_volatility": 0.02,
  "volume_range": [100, 5000],
  "mock_accounts": [
    {
      "accountid": "123456",
      "balance": 1000000,
      "available": 800000
    }
  ],
  "mock_positions": [
    {
      "symbol": "rb2410",
      "direction": "LONG",
      "volume": 10,
      "price": 3490
    }
  ]
}
```

### 环境变量
- `USE_MOCK_DATA=true` 启用mock数据
- `MOCK_DATA_DELAY=1000` 模拟网络延迟(毫秒)
- `MOCK_ERROR_RATE=0.01` 模拟错误率(1%)

## Mock数据生成规则

### 1. 价格生成
```python
def generate_price(base_price, volatility=0.02):
    change = random.uniform(-volatility, volatility)
    return base_price * (1 + change)
```

### 2. 成交量生成
```python
def generate_volume():
    return random.randint(100, 5000)
```

### 3. 订单撮合规则
- **限价单**: 当市场价达到或优于限价时成交
- **市价单**: 立即以当前市场价成交
- **成交比例**: 每次撮合30-100%的挂单量
- **撮合延迟**: 100-500毫秒模拟真实撮合

### 4. 持仓盈亏计算
```python
def calculate_pnl(position_price, current_price, volume, direction):
    if direction == "LONG":
        return (current_price - position_price) * volume * contract_size
    else:
        return (position_price - current_price) * volume * contract_size
```

## 使用指南

### 1. 启用Mock模式
```bash
# Linux/Mac
export USE_MOCK_DATA=true
python ui/main.py

# Windows
set USE_MOCK_DATA=true
python ui/main.py
```

### 2. 配置文件启用
```json
// config/settings.json
{
  "mock": {
    "enabled": true,
    "data_source": "mock"
  }
}
```

### 3. 代码中使用
```python
from tests.mock_data import MockEngine

# 创建mock引擎
mock_engine = MockEngine()

# 获取mock合约
contracts = mock_engine.get_contracts()

# 获取mock行情
tick = mock_engine.get_tick("rb2410.SHFE")

# 模拟下单
order = mock_engine.send_order(order_request)
```

## 测试场景

### 1. 基础功能测试
- [ ] 合约查询
- [ ] 行情订阅
- [ ] 下单/撤单
- [ ] 持仓查询
- [ ] 资金查询

### 2. 边界情况测试
- [ ] 涨停/跌停价格测试
- [ ] 最大持仓限制
- [ ] 资金不足情况
- [ ] 合约到期处理

### 3. 异常处理测试
- [ ] 网络中断模拟
- [ ] 交易所错误码
- [ ] 重复撤单处理
- [ ] 无效合约处理

## 数据验证

### 1. 数据一致性检查
- 持仓量 × 合约乘数 × 价格 = 持仓市值
- 可用资金 + 冻结资金 + 保证金 = 总资金
- 成交总量 = 买入成交 + 卖出成交

### 2. 业务规则验证
- 价格不能为负数
- 成交量必须为正整数
- 持仓方向只能是LONG或SHORT
- 订单状态流转符合业务规则

## 扩展开发

### 添加新的Mock合约
1. 在`tests/mock_data/contracts.py`中添加合约定义
2. 更新预定义合约列表
3. 设置行情生成参数

### 自定义行情模式
1. 继承`BasePriceGenerator`类
2. 实现`generate_next_price`方法
3. 在配置中指定使用的生成器

### 添加交易规则
1. 在`tests/mock_data/exchange_rules.py`中定义规则
2. 实现相应的验证逻辑
3. 在Mock引擎中应用规则