#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取半导体关键A股企业的估值数据
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
from a_stock_data_core import get_stock_realtime_quote, get_historical_k_data

# 半导体关键企业列表（之前分析过的）
semiconductor_stocks = [
    ("688012", "中微公司"),
    ("002371", "北方华创"),
    ("600584", "长电科技"),
    ("002156", "通富微电"),
    ("002185", "华天科技"),
    ("688268", "华特气体"),
    ("688146", "中船特气"),
    ("688019", "安集科技"),
    ("300666", "江丰电子"),
    ("688981", "中芯国际"),
    ("688347", "华虹半导体"),
    ("603986", "兆易创新"),
    ("603501", "韦尔股份"),
    ("300602", "飞荣达"),
]

print("=" * 100)
print("半导体关键A股企业估值分析")
print("=" * 100)
print()

results = []

for code, name in semiconductor_stocks:
    try:
        print(f"正在获取 {name} ({code}) 的实时数据...")
        # 获取实时数据
        realtime = get_stock_realtime_quote(code)
        
        if realtime:
            # 获取历史数据用于计算PE
            kline = get_historical_k_data(code, period="daily", days=365)
            
            # 计算PE（假设最新财报EPS已知，这里用简化方法）
            latest_price = realtime.get('latest_price', 0)
            pe = realtime.get('pe_ttm', None)
            pb = realtime.get('pb', None)
            volume = realtime.get('volume', 0)
            
            # 获取市值
            if kline is not None and len(kline) > 0:
                shares = 1000000000  # 假设有10亿股（实际需要获取真实数据）
                market_cap = latest_price * shares
            else:
                market_cap = None
            
            results.append({
                "name": name,
                "code": code,
                "price": latest_price,
                "pe": pe,
                "pb": pb,
                "volume": volume,
                "market_cap": market_cap,
            })
            
            print(f"  价格: {latest_price:.2f} | PE: {pe:.1f} | PB: {pb:.1f}")
        else:
            print(f"  无法获取数据")
    except Exception as e:
        print(f"  获取失败: {e}")
    print()

# 输出结果表格
print()
print("=" * 100)
print("半导体关键A股企业估值数据表")
print("=" * 100)
print()
print(f"{'名称':<12} {'代码':<10} {'价格':<10} {'PE-TTM':<10} {'PB':<8} {'成交量':<15}")
print("-" * 80)

for res in results:
    name = res['name']
    code = res['code']
    price = res['price']
    pe = res['pe']
    pb = res['pb']
    volume = res['volume']
    
    pe_str = f"{pe:.1f}" if pe is not None else "N/A"
    pb_str = f"{pb:.1f}" if pb is not None else "N/A"
    
    print(f"{name:<12} {code:<10} {price:<10.2f} {pe_str:<10} {pb_str:<8} {volume:<15.0f}")

print()

# 简单分析
print("=" * 100)
print("估值分析（简化版）")
print("=" * 100)
print()
print("说明：")
print("- PE-TTM: 滚动市盈率，小于30为低估值，30-50为合理，大于50为高估值")
print("- PB: 市净率，小于3为低估值，3-6为合理，大于6为高估值")
print()
