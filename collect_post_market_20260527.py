#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年5月27日收盘后数据收集脚本 - 获取今日完整行情数据
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_core import (
    get_market_index,
    industry_comparison,
    get_northbound_flow,
    get_dragon_tiger_board,
    get_stock_quote,
    get_stock_news,
    ths_hot_reason
)
import json
from datetime import datetime

def collect_market_data():
    """收集今日市场数据"""
    print("="*70)
    print("📊 2026年5月27日收盘后数据收集")
    print("="*70)
    print(f"收集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    data = {
        'collect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'report_date': '2026-05-27',
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
        data['market_index'] = result
        print("   ✅ 大盘指数获取成功")
        if result:
            for code, info in result.items():
                print(f"      {info.get('name', '')} ({code}): {info.get('price', 0)}元, 涨跌幅: {info.get('change_pct', 0):.2f}%")
    except Exception as e:
        print(f"   ❌ 大盘指数获取失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")

    # 2. 获取行业涨跌幅排名
    print("\n2️⃣ 获取行业涨跌幅排名...")
    try:
        result = industry_comparison()
        data['industry_rankings'] = result
        print("   ✅ 行业排名获取成功")
        if result:
            top = result.get('top', [])[:5]
            bottom = result.get('bottom', [])[-5:]
            if top:
                print("   涨幅前5:")
                for i, ind in enumerate(top):
                    print(f"      {i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%")
            if bottom:
                print("   跌幅前5:")
                for i, ind in enumerate(bottom):
                    print(f"      {i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%")
    except Exception as e:
        print(f"   ❌ 行业排名获取失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")

    # 3. 获取热点股票
    print("\n3️⃣ 获取热点股票...")
    try:
        result = ths_hot_reason('2026-05-27')
        if hasattr(result, 'to_dict'):
            data['hot_stocks'] = result.to_dict('records')
        else:
            data['hot_stocks'] = result
        print("   ✅ 热点股票获取成功")
        if result is not None and len(result) > 0:
            print(f"      获取到热点股票数据")
    except Exception as e:
        print(f"   ❌ 热点股票获取失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")

    # 4. 获取北向资金
    print("\n4️⃣ 获取北向资金数据...")
    try:
        result = get_northbound_flow()
        data['northbound_flow'] = result
        print("   ✅ 北向资金获取成功")
        if result:
            print(f"      沪股通: {result.get('hgt', 0):.2f}亿元")
            print(f"      深股通: {result.get('sgt', 0):.2f}亿元")
            print(f"      合计: {result.get('total', 0):.2f}亿元")
    except Exception as e:
        print(f"   ❌ 北向资金获取失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")

    # 5. 获取龙虎榜
    print("\n5️⃣ 获取龙虎榜数据...")
    try:
        result = get_dragon_tiger_board('2026-05-27')
        data['dragon_tiger_board'] = result
        print("   ✅ 龙虎榜获取成功")
        if result:
            print(f"      龙虎榜已获取")
        else:
            print(f"      今日暂无龙虎榜数据")
    except Exception as e:
        print(f"   ❌ 龙虎榜获取失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")

    # 6. 获取重点个股行情
    print("\n6️⃣ 获取重点个股行情...")
    key_stocks = ['600519', '000858', '300750', '600036', '600584', '601318', '000333']
    for code in key_stocks:
        try:
            result = get_stock_quote(code)
            data['key_stocks'][code] = result
            if result:
                name = result.get(code, {}).get('name', code)
                change = result.get(code, {}).get('change_pct', 0)
                price = result.get(code, {}).get('price', 0)
                print(f"   ✅ {name} ({code}): {price:.2f}元, {change:+.2f}%")
            else:
                print(f"   ❌ {code}: 获取失败")
        except Exception as e:
            print(f"   ❌ {code} 获取失败: {e}")

    return data

if __name__ == '__main__':
    data = collect_market_data()

    # 保存数据
    output_file = '/Users/houpengyuan/Documents/trae_projects/a-stock-data/reports/收盘后数据收集_2026-05-27.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存到: {output_file}")
