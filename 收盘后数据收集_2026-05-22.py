#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收盘后数据收集脚本 - 获取今日完整行情数据
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_mcp import (
    get_market_index,
    get_industry_rankings,
    get_ths_hot_stocks,
    get_northbound_flow,
    get_dragon_tiger_board,
    get_stock_quote
)
import json
from datetime import datetime

def collect_market_data():
    """收集今日市场数据"""
    print("="*70)
    print("📊 收盘后数据收集")
    print("="*70)
    print(f"收集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    data = {
        'collect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_index': None,
        'industry_rankings': None,
        'hot_stocks': None,
        'northbound_flow': None,
        'dragon_tiger_board': None,
        'key_stocks': {}
    }

    # 1. 获取大盘指数
    print("1️⃣ 获取大盘指数...")
    try:
        result = get_market_index()
        data['market_index'] = json.loads(result)
        print("   ✅ 大盘指数获取成功")
        print(json.dumps(data['market_index'], ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"   ❌ 大盘指数获取失败: {e}")

    # 2. 获取行业涨跌幅排名
    print("\n2️⃣ 获取行业涨跌幅排名...")
    try:
        result = get_industry_rankings()
        data['industry_rankings'] = json.loads(result)
        print("   ✅ 行业排名获取成功")
    except Exception as e:
        print(f"   ❌ 行业排名获取失败: {e}")

    # 3. 获取热点股票
    print("\n3️⃣ 获取热点股票...")
    try:
        result = get_ths_hot_stocks()
        data['hot_stocks'] = json.loads(result)
        print("   ✅ 热点股票获取成功")
    except Exception as e:
        print(f"   ❌ 热点股票获取失败: {e}")

    # 4. 获取北向资金
    print("\n4️⃣ 获取北向资金数据...")
    try:
        result = get_northbound_flow()
        data['northbound_flow'] = json.loads(result)
        print("   ✅ 北向资金获取成功")
        print(json.dumps(data['northbound_flow'], ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"   ❌ 北向资金获取失败: {e}")

    # 5. 获取龙虎榜
    print("\n5️⃣ 获取龙虎榜数据...")
    try:
        result = get_dragon_tiger_board()
        data['dragon_tiger_board'] = json.loads(result)
        print("   ✅ 龙虎榜获取成功")
    except Exception as e:
        print(f"   ❌ 龙虎榜获取失败: {e}")

    # 6. 获取重点个股行情
    print("\n6️⃣ 获取重点个股行情...")
    key_stocks = ['600519', '000858', '300750', '600036', '600584', '601318']
    for code in key_stocks:
        try:
            result = get_stock_quote(code)
            data['key_stocks'][code] = json.loads(result)
            print(f"   ✅ {code} 获取成功")
        except Exception as e:
            print(f"   ❌ {code} 获取失败: {e}")

    return data

if __name__ == '__main__':
    data = collect_market_data()

    # 保存数据
    output_file = '/Users/houpengyuan/Documents/trae_projects/a-stock-data/reports/收盘后数据收集_2026-05-22.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存到: {output_file}")
