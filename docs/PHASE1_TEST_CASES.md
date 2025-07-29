# Phase 1 测试用例文档

## Phase 1.1-1.2 测试指南 - 数据管理与分析系统

### 测试目标
验证历史数据存储系统和性能分析仪表板的功能完整性、数据准确性和用户体验

## 📊 Phase 1.1 测试用例清单

### TC-D01: SQLite数据库初始化测试
**测试目的**: 验证数据库结构和表创建是否正常
**测试步骤**:
1. 启动交易系统: `python ui/main.py`
2. 检查数据库文件是否创建: `data/trading.db`
3. 使用SQLite浏览器打开数据库，验证表结构

**预期结果**:
- [ ] 数据库文件自动创建
- [ ] 包含以下表格: trades, orders, positions, account_flow, ticks, bars
- [ ] 每个表都有正确的字段和索引

### TC-D02: 数据自动保存测试
**测试目的**: 验证交易数据是否自动保存到数据库
**前置条件**: 系统已连接CTP服务器
**测试步骤**:
1. 进行一次模拟交易
2. 检查trades表是否有新记录
3. 检查orders表是否同步更新

**预期结果**:
- [ ] 成交后立即在trades表中看到记录
- [ ] 订单状态变化时orders表实时更新
- [ ] 持仓变化时positions表有记录

### TC-D03: 数据查询功能测试
**测试目的**: 验证数据库查询API是否正常
**测试步骤**:
```python
from config.database import trading_db

# 测试获取交易记录
trades = trading_db.get_trades(symbol="rb2410", limit=10)
print(f"螺纹钢最新交易记录: {len(trades)}条")

# 测试统计功能
total_trades = trading_db.get_total_trades()
win_rate = trading_db.get_win_rate()
print(f"总交易次数: {total_trades}")
print(f"胜率: {win_rate:.1%}")
```

**预期结果**:
- [ ] 查询返回正确格式的数据
- [ ] 统计数据准确无误

## 📈 Phase 1.2 测试用例清单

### TC-PA01: 业绩分析窗口打开测试
**测试目的**: 验证业绩分析窗口能正常打开
**测试步骤**:
1. 启动主程序
2. 点击主界面"业绩分析"按钮
3. 观察窗口是否成功打开

**预期结果**:
- [ ] 业绩分析窗口成功打开
- [ ] 窗口标题显示"业绩分析"
- [ ] 窗口包含统计卡片和图表区域

### TC-PA02: 实时图表更新测试
**测试目的**: 验证图表数据实时更新
**前置条件**: 已有交易数据
**测试步骤**:
1. 打开业绩分析窗口
2. 进行一次新的交易
3. 观察图表是否自动更新

**预期结果**:
- [ ] 新交易后图表自动刷新
- [ ] PNL曲线图显示最新数据
- [ ] 胜率饼图比例正确更新

### TC-PA03: 时间范围筛选测试
**测试目的**: 验证不同时间范围的数据筛选
**测试步骤**:
1. 在业绩分析窗口中
2. 选择不同的时间范围: 最近7天/30天/90天/全部
3. 观察图表数据变化

**预期结果**:
- [ ] 选择不同范围后图表数据相应变化
- [ ] 统计数据按所选范围计算

### TC-PA04: 统计数据准确性测试
**测试目的**: 验证统计数据的准确性
**测试步骤**:
1. 手动记录最近的交易数据
2. 对比业绩分析窗口显示的统计数据
3. 验证计算逻辑

**预期数据验证**:
- [ ] 总交易次数 = 实际交易笔数
- [ ] 胜率 = 盈利交易数 / 总交易数
- [ ] 总盈亏 = 所有交易盈亏总和

### TC-PA05: 报表导出功能测试
**测试目的**: 验证CSV报表导出功能
**测试步骤**:
1. 点击"导出报表"按钮
2. 选择保存位置
3. 打开导出的CSV文件验证内容

**预期结果**:
- [ ] CSV文件成功创建
- [ ] 包含所有交易记录
- [ ] 数据格式正确 (UTF-8编码)
- [ ] 文件命名规范: 业绩报表_YYYYMMDD_HHMMSS.csv

## 🔍 数据完整性测试

### TC-COMPLETE01: 端到端数据流测试
**测试目的**: 验证从交易发生到数据分析的完整流程
**测试场景**:
1. 开仓交易 → 预期: trades表新增记录
2. 平仓交易 → 预期: trades表再次新增记录  
3. 查看业绩分析 → 预期: 图表显示最新盈亏数据
4. 导出报表 → 预期: CSV文件包含所有交易记录

### TC-COMPLETE02: 多品种数据测试
**测试目的**: 验证多品种交易数据管理
**测试步骤**:
1. 交易不同品种 (如螺纹钢、铁矿石、橡胶)
2. 查看各品种独立的交易记录
3. 验证品种筛选功能

## 🗃️ 数据库测试工具

### 手动数据检查工具
```bash
# 安装SQLite浏览器 (可选)
sudo apt-get install sqlitebrowser

# 打开数据库
sqlitebrowser data/trading.db

# 命令行查询示例
sqlite3 data/trading.db "SELECT COUNT(*) FROM trades;"
sqlite3 data/trading.db "SELECT * FROM trades ORDER BY trade_time DESC LIMIT 5;"
```

### Python调试代码
```python
from config.database import trading_db
from datetime import datetime, timedelta

# 检查数据库状态
def check_database():
    print("=== 数据库状态检查 ===")
    print(f"总交易次数: {trading_db.get_total_trades()}")
    print(f"胜率: {trading_db.get_win_rate():.1%}")
    
    # 查看最近的交易
    recent_trades = trading_db.get_trades(limit=5)
    for trade in recent_trades:
        print(f"{trade.trade_time}: {trade.symbol} {trade.direction} {trade.volume}手 @{trade.price}")
    
    # 查看每日盈亏
    print(f"今日盈亏: ¥{trading_db.get_daily_pnl(datetime.now())}")

check_database()
```

## ⚙️ 性能基准测试

### TC-PERF01: 大数据量处理测试
**测试目的**: 验证系统处理大量数据的能力
**测试方法**:
```python
import time
from config.database import TradingDatabase

def performance_test():
    db = TradingDatabase()
    start_time = time.time()
    
    # 模拟1000笔交易数据
    for i in range(1000):
        trade = TradeRecord(
            trade_id=f"TEST_{i}",
            symbol="rb2410",
            direction="多",
            volume=1,
            price=3500 + i,
            trade_time=datetime.now()
        )
        db.save_trade(trade)
    
    end_time = time.time()
    print(f"插入1000条记录耗时: {end_time - start_time:.2f}秒")
    print(f"查询1000条记录耗时: {time.time() - end_time:.2f}秒")

performance_test()
```

**预期性能**:
- 插入1000条记录 < 2秒
- 查询1000条记录 < 1秒

## 🎯 测试完成标准

### Phase 1 完成检查表
- [ ] ✅ 数据库结构正确
- [ ] ✅ 数据自动保存功能正常
- [ ] ✅ 业绩分析窗口正常显示
- [ ] ✅ 图表实时更新无误
- [ ] ✅ 统计数据计算准确
- [ ] ✅ 报表导出功能正常
- [ ] ✅ 系统响应时间符合要求

### 测试数据清理
测试完成后，运行以下代码清理测试数据：
```python
from config.database import trading_db
from datetime import datetime, timedelta

# 清理测试数据 (保留最近7天)
trading_db.clear_old_data(days_to_keep=7)
print("测试数据清理完成")
```

## 📋 测试执行记录表

| 测试用例 | 执行日期 | 执行人 | 结果 | 备注 |
|----------|----------|--------|------|------|
| TC-D01 | | | ☐/☐ | |
| TC-D02 | | | ☐/☐ | |
| TC-D03 | | | ☐/☐ | |
| TC-PA01 | | | ☐/☐ | |
| TC-PA02 | | | ☐/☐ | |
| TC-PA03 | | | ☐/☐ | |
| TC-PA04 | | | ☐/☐ | |
| TC-PA05 | | | ☐/☐ | |
| TC-COMPLETE01 | | | ☐/☐ | |
| TC-COMPLETE02 | | | ☐/☐ | |
| TC-PERF01 | | | ☐/☐ | |

## 🚀 下一步行动
Phase 1测试完成后，建议继续进行Phase 2 (高级风险管理)的开发和测试。