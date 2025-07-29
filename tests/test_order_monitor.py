from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import pytest
from unittest.mock import MagicMock
from vnpy.trader.object import OrderData
from vnpy.trader.constant import Direction, Offset, Status, OrderType, Exchange
from vnpy.trader.event import Event, EVENT_ORDER
from ui.order_monitor import OrderMonitor
import datetime

@pytest.fixture
def app():
    return QApplication([])

@pytest.fixture
def order_monitor(app):
    main_engine = MagicMock()
    event_engine = MagicMock()
    monitor = OrderMonitor(main_engine, event_engine)
    return monitor

def create_test_order(
    orderid: str = "123",
    direction: Direction = Direction.LONG,
    offset: Offset = Offset.OPEN,
    price: float = 3500.0,
    volume: float = 1.0,
    traded: float = 0.0,
    status: Status = Status.SUBMITTING
) -> OrderData:
    """创建测试用的委托数据"""
    order = OrderData(
        symbol="rb2410",
        exchange=Exchange.SHFE,
        orderid=orderid,
        type=OrderType.LIMIT,
        direction=direction,
        offset=offset,
        price=price,
        volume=volume,
        traded=traded,
        status=status,
        gateway_name="CTP",
        datetime=datetime.datetime.now()
    )
    return order

def test_order_display(order_monitor):
    """测试委托显示"""
    # 创建测试委托
    order = create_test_order()
    
    # 模拟委托事件
    event = Event(EVENT_ORDER, order)
    order_monitor.update_order(event)
    
    # 验证表格行数
    assert order_monitor.rowCount() == 1
    
    # 验证各列数据
    assert order_monitor.item(0, 0).text() == "123"  # 委托号
    assert order_monitor.item(0, 2).text() == "rb2410"  # 代码
    assert order_monitor.item(0, 5).text() == Direction.LONG.value  # 方向
    assert order_monitor.item(0, 7).text() == "3500.0"  # 价格
    
    # 验证买入方向显示为红色
    assert order_monitor.item(0, 5).foreground().color().name() == "#ff0000"

def test_order_update(order_monitor):
    """测试委托更新"""
    # 创建初始委托
    order = create_test_order(traded=0.0, status=Status.SUBMITTING)
    event = Event(EVENT_ORDER, order)
    order_monitor.update_order(event)
    
    # 更新委托状态
    updated_order = create_test_order(traded=1.0, status=Status.ALLTRADED)
    event = Event(EVENT_ORDER, updated_order)
    order_monitor.update_order(event)
    
    # 验证更新后的数据
    assert order_monitor.item(0, 9).text() == "1.0"  # 已成交
    assert order_monitor.item(0, 10).text() == Status.ALLTRADED.value  # 状态

def test_multiple_orders(order_monitor):
    """测试多个委托"""
    # 创建多个测试委托
    orders = [
        create_test_order(orderid="1", direction=Direction.LONG),
        create_test_order(orderid="2", direction=Direction.SHORT),
        create_test_order(orderid="3", direction=Direction.LONG)
    ]
    
    # 发送委托事件
    for order in orders:
        event = Event(EVENT_ORDER, order)
        order_monitor.update_order(event)
    
    # 验证表格行数
    assert order_monitor.rowCount() == 3
    
    # 验证方向颜色
    assert order_monitor.item(0, 5).foreground().color().name() == "#ff0000"  # 买入红色
    assert order_monitor.item(1, 5).foreground().color().name() == "#008000"  # 卖出绿色
    assert order_monitor.item(2, 5).foreground().color().name() == "#ff0000"  # 买入红色

def test_column_resize(order_monitor):
    """测试列宽调整"""
    # 验证列可以调整
    assert order_monitor.horizontalHeader().sectionsMovable() == False
    assert order_monitor.horizontalHeader().sectionResizeMode(0) == order_monitor.horizontalHeader().Interactive

if __name__ == "__main__":
    pytest.main([__file__]) 