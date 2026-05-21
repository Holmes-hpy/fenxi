#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取昨日涨停、今日下跌的A股（剔除港股和创业板）
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_core import ths_hot_reason, get_stock_quote
from datetime import datetime, timedelta
import json

def get_yesterday_date():
    """获取昨天的日期字符串"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def is_jiangyouban(change_pct):
    """判断是否涨停（普通股票10%，ST股票5%）"""
    return abs(change_pct - 10) < 0.5 or abs(change_pct - 5) < 0.5

def is_chuangyeban(code):
    """判断是否是创业板（3开头）"""
    return code.startswith('3')

def is_valid_a_share(code):
    """判断是否是有效A股（非创业板，6或0开头）"""
    return code.startswith('6') or code.startswith('0')

def main():
    print('='*60)
    print('📊 昨日涨停、今日下跌的A股筛选')
    print('='*60)
    print()

    # 1. 获取昨日热点股票
    yesterday_date = get_yesterday_date()
    print(f'1. 获取昨日({yesterday_date})热点股票...')
    
    try:
        hot_df = ths_hot_reason(yesterday_date)
        if hot_df.empty:
            print('   ⚠️  没有获取到昨日热点数据，尝试获取今日数据...')
            hot_df = ths_hot_reason()
            if hot_df.empty:
                print('   ❌ 无法获取热点数据')
                return
    except Exception as e:
        print(f'   ❌ 获取热点数据失败: {e}')
        return

    print(f'   ✓ 共获取到 {len(hot_df)} 只热点股票')
    print()

    # 2. 筛选昨日涨停的股票
    print('2. 筛选昨日涨停的股票...')
    yesterday_limit_up = []
    
    for idx, row in hot_df.iterrows():
        code = str(row['代码'])
        name = row['名称']
        change_pct = row['涨幅%']
        
        if is_jiangyouban(change_pct) and is_valid_a_share(code):
            yesterday_limit_up.append({
                'code': code,
                'name': name,
                'yesterday_change': change_pct
            })
    
    print(f'   ✓ 筛选出 {len(yesterday_limit_up)} 只昨日涨停的A股')
    print()

    if not yesterday_limit_up:
        print('❌ 没有找到符合条件的股票')
        return

    # 3. 获取今日行情并筛选下跌的股票
    print('3. 获取今日行情，筛选下跌的股票...')
    print()

    result = []
    for stock in yesterday_limit_up:
        try:
            quote = get_stock_quote(stock['code'])
            if stock['code'] in quote:
                data = quote[stock['code']]
                today_change = data['change_pct']
                
                if today_change < 0:  # 今日下跌
                    result.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'yesterday_change': stock['yesterday_change'],
                        'today_price': data['price'],
                        'today_change': today_change,
                        'pe': data['pe_ttm'],
                        'pb': data['pb'],
                        'mcap': data['mcap_yi']
                    })
                    print(f'   ✓ {stock["name"]}({stock["code"]}): 昨涨{stock["yesterday_change"]}%, 今跌{today_change}%')
        except Exception as e:
            print(f'   ⚠️  {stock["name"]}({stock["code"]}) 获取行情失败: {e}')

    print()
    print('='*60)
    print(f'🎉 筛选结果：共找到 {len(result)} 只符合条件的股票')
    print('='*60)
    print()

    # 4. 展示结果
    if result:
        print(f'{"代码":<10} {"名称":<10} {"昨涨%":>8} {"今跌%":>8} {"现价":>10} {"PE":>8} {"PB":>6} {"市值亿":>10}')
        print('-'*80)
        for stock in result:
            print(f'{stock["code"]:<10} {stock["name"]:<10} {stock["yesterday_change"]:>8.2f} {stock["today_change"]:>8.2f} {stock["today_price"]:>10.2f} {stock["pe"]:>8.2f} {stock["pb"]:>6.2f} {stock["mcap"]:>10.2f}')
        print()

        # 5. 保存结果
        output_file = '/Users/houpengyuan/Documents/trae_projects/a-stock-data/筛选结果.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'💾 结果已保存到: {output_file}')
    else:
        print('❌ 没有找到昨日涨停、今日下跌的股票')

    print()
    print('✅ 筛选完成！')

if __name__ == '__main__':
    main()