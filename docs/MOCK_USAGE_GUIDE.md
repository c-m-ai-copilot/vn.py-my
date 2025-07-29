# Mock数据系统使用指南

## 快速开始

### 1. Windows系统直接启动
```batch
start_mock.bat
```

### 2. 手动启动Mock模式
```bash
# Linux/Mac
export USE_MOCK_DATA=true
python ui/main.py

# Windows
set USE_MOCK_DATA=true
python ui/main.py
```

### 3. 使用新界面启动
```bash
# Linux/Mac
export USE_MOCK_DATA=true
python ui/new_main_window.py

# Windows
set USE_MOCK_DATA=true
python ui/new_main_window.py
```

## Mock系统特性

### 1. 预定义数据
- **合约**: 10个常用期货合约（螺纹钢、沪铜、沪金等）
- **账户**: 初始资金100万元
- **持仓**: 预设3个持仓（螺纹钢多头、沪铜空头、豆粕多头）

### 2. 实时行情
- 价格波动 ±2%随机波动
- 每秒更新一次行情
- 支持买卖盘挂单模拟

### 3. 订单系统
- 订单成交率80%
- 支持部分成交和全部成交
- 模拟100-500毫秒成交延迟

### 4. 账户管理
- 实时更新持仓盈亏
- 保证金计算（10%保证金率）
- 手续费计算（万分之一）

## 测试场景

### 基础测试
1. 合约查询和订阅
2. 行情订阅和显示
3. 下单和撤单操作
4. 持仓和资金查询

### 边界测试
- 涨停跌停价格测试
- 资金不足情况
- 重复撤单处理

### 性能测试
- 同时订阅多个合约
- 高频下单撤单
- 大数据量行情推送

## 文件结构

```
tests/mock_data/
├── __init__.py           # 模块初始化
├── mock_engine.py        # Mock交易引擎
├── mock_contracts.py     # Mock合约数据
├── mock_tick_generator.py # Mock行情生成器
├── mock_account.py       # Mock账户管理
├── mock_order_manager.py # Mock订单管理
├── mock_launcher.py      # Mock模式启动器
└── test_mock.py          # 测试脚本
```

## 自定义扩展

### 添加新合约
编辑 `mock_contracts.py`，在 `MOCK_CONTRACTS` 字典中添加新合约信息。

### 调整行情参数
编辑 `mock_tick_generator.py`，修改以下参数：
- `volatility`: 行情波动率 (0.001-0.01)
- `trend_factor`: 趋势因子 (-0.001, 0.001)

### 修改账户初始资金
编辑 `mock_account.py` 中的 `MockAccountManager._init_accounts()` 方法。

## 故障排除

### Q: 行情不更新？
A: 检查是否已订阅合约，确保在合约列表中点击"订阅"按钮。

### Q: 订单无法成交？
A: Mock系统成交率为80%，可调整 `mock_order_manager.py` 中的 `match_probability` 参数。

### Q: 资金显示异常？
A: 检查持仓盈亏计算是否正确，确保合约乘数设置准确。

## 开发调试

### 调试模式
```python
# 在代码中添加调试输出
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 数据验证
运行测试脚本验证数据完整性：
```bash
python tests/mock_data/test_mock.py
```

### 日志查看
Mock系统会输出调试信息到控制台，关注以下关键字：
- `MockCTP`: Mock引擎相关日志
- `MOCK_ORDER`: 订单相关日志
- `MOCK_TICK`: 行情相关日志

## 真实环境切换

### 切换到真实环境
```bash
# Linux/Mac
unset USE_MOCK_DATA
python ui/main.py

# Windows
set USE_MOCK_DATA=false
python ui/main.py
```

### 环境变量说明
- `USE_MOCK_DATA=true`: 启用mock模式
- `MOCK_DELAY=500`: 设置网络延迟（毫秒）
- `MOCK_ERROR_RATE=0.01`: 设置错误率（1%）