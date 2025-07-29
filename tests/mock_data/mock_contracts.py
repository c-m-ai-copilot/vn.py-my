"""
Mock合约数据
提供预定义的期货合约信息
"""

from vnpy.trader.object import ContractData
from vnpy.trader.constant import Exchange, Product

MOCK_CONTRACTS = {
    "rb2410": ContractData(
        symbol="rb2410",
        exchange=Exchange.SHFE,
        name="螺纹钢2410",
        product=Product.FUTURES,
        size=10,
        pricetick=1.0,
        min_volume=1,
        gateway_name="CTP"
    ),
    "cu2409": ContractData(
        symbol="cu2409",
        exchange=Exchange.SHFE,
        name="沪铜2409",
        product=Product.FUTURES,
        size=5,
        pricetick=10.0,
        min_volume=1,
        gateway_name="CTP"
    ),
    "au2412": ContractData(
        symbol="au2412",
        exchange=Exchange.SHFE,
        name="沪金2412",
        product=Product.FUTURES,
        size=1000,
        pricetick=0.05,
        min_volume=1,
        gateway_name="CTP"
    ),
    "i2409": ContractData(
        symbol="i2409",
        exchange=Exchange.DCE,
        name="铁矿石2409",
        product=Product.FUTURES,
        size=100,
        pricetick=0.5,
        min_volume=1,
        gateway_name="CTP"
    ),
    "m2409": ContractData(
        symbol="m2409",
        exchange=Exchange.DCE,
        name="豆粕2409",
        product=Product.FUTURES,
        size=10,
        pricetick=1.0,
        min_volume=1,
        gateway_name="CTP"
    ),
    "SR2409": ContractData(
        symbol="SR2409",
        exchange=Exchange.CZCE,
        name="白糖2409",
        product=Product.FUTURES,
        size=10,
        pricetick=1.0,
        min_volume=1,
        gateway_name="CTP"
    ),
    "TA2409": ContractData(
        symbol="TA2409",
        exchange=Exchange.CZCE,
        name="PTA2409",
        product=Product.FUTURES,
        size=5,
        pricetick=2.0,
        min_volume=1,
        gateway_name="CTP"
    ),
    "IF2409": ContractData(
        symbol="IF2409",
        exchange=Exchange.CFFEX,
        name="沪深2409",
        product=Product.FUTURES,
        size=300,
        pricetick=0.2,
        min_volume=1,
        gateway_name="CTP"
    ),
    "sc2409": ContractData(
        symbol="sc2409",
        exchange=Exchange.INE,
        name="原油2409",
        product=Product.FUTURES,
        size=1000,
        pricetick=0.1,
        min_volume=1,
        gateway_name="CTP"
    ),
    "ag2409": ContractData(
        symbol="ag2409",
        exchange=Exchange.SHFE,
        name="沪银2409",
        product=Product.FUTURES,
        size=15,
        pricetick=1.0,
        min_volume=1,
        gateway_name="CTP"
    )
}

# 合约列表
CONTRACT_LIST = list(MOCK_CONTRACTS.values())

# 按交易所分类的合约
CONTRACTS_BY_EXCHANGE = {
    Exchange.SHFE: [c for c in CONTRACT_LIST if c.exchange == Exchange.SHFE],
    Exchange.DCE: [c for c in CONTRACT_LIST if c.exchange == Exchange.DCE],
    Exchange.CZCE: [c for c in CONTRACT_LIST if c.exchange == Exchange.CZCE],
    Exchange.CFFEX: [c for c in CONTRACT_LIST if c.exchange == Exchange.CFFEX],
    Exchange.INE: [c for c in CONTRACT_LIST if c.exchange == Exchange.INE]
}