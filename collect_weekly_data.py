#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本周市场数据收集脚本
收集5月19日-23日的数据
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from a_stock_data_core import *

PROJECT_DIR = Path(__file__).parent

def collect_weekly_data():
    """收集本周市场数据"""
    print("="*70)
    print("📊 开始收集本周市场数据（5月19日-23日）")
    print("="*70)
    print()

    # 1. 收集北向资金数据
    print("1️⃣ 收集北向资金数据...")
    northbound = get_northbound_flow()
    print(f"   今日北向资金：沪股通 {northbound.get('hgt', 0):.2f}亿元，")
    print(f"                深股通 {northbound.get('sgt', 0):.2f}亿元")
    print(f"                合计 {northbound.get('total', 0):.2f}亿元")
    print()

    # 2. 收集大盘指数数据
    print("2️⃣ 收集大盘指数数据...")
    try:
        quotes = get_stock_quote("000001,000300,399006,000688")
        index_data = []
        for code, data in quotes.items():
            if '000001' in code:
                name = "上证指数"
            elif '000300' in code:
                name = "沪深300"
            elif '399006' in code:
                name = "创业板指"
            elif '000688' in code:
                name = "科创50"
            else:
                name = code

            index_data.append({
                "name": name,
                "code": code,
                "price": data.get('price', 0),
                "change_pct": data.get('change_pct', 0),
                "change_amt": data.get('change_amt', 0),
                "high": data.get('high', 0),
                "low": data.get('low', 0),
            })
            print(f"   {name}：{data.get('price', 0):.2f} ({data.get('change_pct', 0):+.2f}%)")
    except Exception as e:
        print(f"   ⚠️ 获取指数数据失败：{e}")
        index_data = []
    print()

    # 3. 收集重点个股数据
    print("3️⃣ 收集重点个股数据...")
    key_stocks = ["600519", "000858", "300750", "600036", "601318", "600584"]
    try:
        quotes = get_stock_quote(",".join(key_stocks))
        stock_data = []
        for code in key_stocks:
            if code in quotes:
                data = quotes[code]
                stock_data.append({
                    "name": data.get('name', code),
                    "code": code,
                    "price": data.get('price', 0),
                    "change_pct": data.get('change_pct', 0),
                    "turnover_pct": data.get('turnover_pct', 0),
                    "mcap_yi": data.get('mcap_yi', 0),
                    "pe_ttm": data.get('pe_ttm', 0),
                })
                print(f"   {data.get('name', code)}：{data.get('price', 0):.2f}元 ({data.get('change_pct', 0):+.2f}%)")
    except Exception as e:
        print(f"   ⚠️ 获取个股数据失败：{e}")
        stock_data = []
    print()

    # 4. 收集行业涨跌数据
    print("4️⃣ 收集行业涨跌数据...")
    try:
        industry_data = industry_comparison(top_n=20)
        print(f"   共获取 {industry_data.get('total', 0)} 个行业数据")
        print("   涨幅前5行业：")
        for i, ind in enumerate(industry_data.get('top', [])[:5], 1):
            print(f"     {i}. {ind['name']}：{ind['change_pct']:+.2f}%")
        print("   跌幅前5行业：")
        bottom = industry_data.get('bottom', [])
        if bottom:
            for i, ind in enumerate(reversed(bottom[-5:]), 1):
                print(f"     {i}. {ind['name']}：{ind['change_pct']:+.2f}%")
    except Exception as e:
        print(f"   ⚠️ 获取行业数据失败：{e}")
        industry_data = {"top": [], "bottom": [], "total": 0}
    print()

    # 5. 收集热点题材数据
    print("5️⃣ 收集热点题材数据...")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        hot_stocks = ths_hot_reason(date=today)
        if not hot_stocks.empty:
            print(f"   今日热点题材共 {len(hot_stocks)} 只")
            hot_list = []
            for idx, row in hot_stocks.head(10).iterrows():
                hot_list.append({
                    "name": row.get('名称', ''),
                    "code": row.get('代码', ''),
                    "涨跌幅": row.get('涨幅%', 0),
                    "题材": row.get('题材归因', ''),
                })
                print(f"   - {row.get('名称', '')}：{row.get('涨幅%', 0):+.2f}% ({row.get('题材归因', '')})")
        else:
            hot_list = []
            print("   ⚠️ 今日热点数据为空")
    except Exception as e:
        print(f"   ⚠️ 获取热点题材失败：{e}")
        hot_list = []
    print()

    # 6. 保存数据
    print("6️⃣ 保存数据...")
    data = {
        "collect_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "week_range": "2026-05-19 to 2026-05-23",
        "northbound": northbound,
        "index": index_data,
        "key_stocks": stock_data,
        "industry": {
            "top": industry_data.get('top', [])[:10],
            "bottom": industry_data.get('bottom', [])[-10:],
        },
        "hot_stocks": hot_list,
    }

    output_file = PROJECT_DIR / "reports" / f"本周市场数据收集_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 数据已保存到：{output_file}")
    print()

    return data

if __name__ == '__main__':
    print("开始收集本周市场数据...")
    print()
    data = collect_weekly_data()
    print()
    print("="*70)
    print("✅ 数据收集完成！")
    print("="*70)
