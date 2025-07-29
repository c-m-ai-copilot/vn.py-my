#!/usr/bin/env python3
"""
Standalone mock contract debug script
"""

import os
import sys
from dataclasses import dataclass
from enum import Enum

# 创建模拟的vnpy类
class Exchange(Enum):
    SHFE = "SHFE"
    DCE = "DCE"
    CZCE = "CZCE"
    CFFEX = "CFFEX"
    INE = "INE"

class Product(Enum):
    FUTURES = "FUTURES"

@dataclass
class ContractData:
    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: int
    pricetick: float
    min_volume: int
    gateway_name: str
    
    @property
    def vt_symbol(self):
        return f"{self.symbol}.{self.exchange.value}"

# 模拟合约数据
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
}

CONTRACT_LIST = list(MOCK_CONTRACTS.values())

def test_standalone():
    """测试独立合约数据"""
    print("=== 独立测试Mock合约数据 ===")
    print(f"[DEBUG] CONTRACT_LIST长度: {len(CONTRACT_LIST)}")
    print(f"[DEBUG] MOCK_CONTRACTS长度: {len(MOCK_CONTRACTS)}")
    
    if CONTRACT_LIST:
        print("[DEBUG] 合约示例:")
        for i, contract in enumerate(CONTRACT_LIST[:3]):
            print(f"  {i+1}. {contract.vt_symbol} - {contract.name}")
    
    return CONTRACT_LIST

if __name__ == "__main__":
    test_standalone()