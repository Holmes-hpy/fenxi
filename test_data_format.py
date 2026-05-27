#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from a_stock_data_core import get_stock_quote, get_historical_k_data

print("=" * 70)
print("测试数据格式")
print("=" * 70)

# 测试 get_stock_quote
print("\n1. 测试 get_stock_quote(\"000001\"):")
try:
    quotes = get_stock_quote("000001")
    print(f"   返回类型: {type(quotes)}")
    print(f"   内容: {quotes}")
    if "000001" in quotes:
        print(f"   000001 的数据: {quotes['000001']}")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

# 测试 get_historical_k_data
print("\n2. 测试 get_historical_k_data(\"000001\", period=\"daily\", days=30):")
try:
    k_data = get_historical_k_data("000001", period="daily", days=30)
    print(f"   返回类型: {type(k_data)}")
    print(f"   形状: {k_data.shape}")
    print(f"   列名: {list(k_data.columns)}")
    print(f"   前5行:")
    print(k_data.head())
    print(f"\n   数据类型:")
    print(k_data.dtypes)
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
