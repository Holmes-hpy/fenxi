"""
隔夜持股法选股策略
买入时间：14:50
卖出条件：次日涨幅>3%
创建时间：2026-05-26
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from a_stock_data_core import get_stock_quote, get_historical_k_data


def check_buy_signals(stock_code):
    """
    检查是否符合隔夜持股法的买入条件
    返回：(True/False, 评分, 原因列表)
    """
    try:
        # 获取实时数据
        quote = get_stock_quote(stock_code)
        if stock_code not in quote:
            return False, 0, ["获取数据失败"]
        
        stock = quote[stock_code]
        price = stock['price']
        change_pct = stock['change_pct']
        vol_ratio = stock.get('vol_ratio', 1.0)
        turnover = stock['turnover_pct']
        
        # 1. 涨幅检查（3%-8%最佳）
        if change_pct < 3.0 or change_pct > 10.0:
            return False, 0, [f"涨幅{change_pct:.2f}%不在最佳区间(3-8%)"]
        
        # 2. 成交量放大检查
        if vol_ratio < 1.5:
            return False, 0, [f"量比{vol_ratio:.2f}不足1.5"]
        
        # 3. 换手率检查（不能太低）
        if turnover < 2.0:
            return False, 0, [f"换手率{turnover:.2f}%太低"]
        
        # 获取历史数据计算均线
        hist = get_historical_k_data(stock_code, 'daily', 30)
        if len(hist) < 20:
            return False, 0, ["历史数据不足"]
        
        # 计算均线
        hist['MA5'] = hist['close'].rolling(5).mean()
        hist['MA10'] = hist['close'].rolling(10).mean()
        hist['MA20'] = hist['close'].rolling(20).mean()
        
        latest = hist.iloc[-1]
        
        # 4. 均线多头排列
        ma_score = 0
        reasons = []
        
        if latest['MA5'] > latest['MA10']:
            ma_score += 1
        else:
            reasons.append("MA5<MA10")
        
        if latest['MA10'] > latest['MA20']:
            ma_score += 1
        else:
            reasons.append("MA10<MA20")
        
        if ma_score < 2:
            return False, 0, reasons + ["均线未多头排列"]
        
        # 5. 价格位置检查（布林带）
        hist['BOLL_MID'] = hist['close'].rolling(20).mean()
        hist['BOLL_STD'] = hist['close'].rolling(20).std()
        hist['BOLL_UPPER'] = hist['BOLL_MID'] + 2 * hist['BOLL_STD']
        hist['BOLL_LOWER'] = hist['BOLL_MID'] - 2 * hist['BOLL_STD']
        
        latest = hist.iloc[-1]
        price_position = (price - latest['BOLL_LOWER']) / (latest['BOLL_UPPER'] - latest['BOLL_LOWER'])
        
        # 价格不能在布林带下轨以下
        if price < latest['BOLL_LOWER']:
            return False, 0, ["价格跌破布林带下轨"]
        
        # 价格不能太接近布林带上轨（防止追高）
        if price_position > 0.95:
            return False, 0, ["价格接近布林带上轨，风险大"]
        
        # 6. 计算综合评分
        score = 0
        reasons = []
        
        # 涨幅评分（3-5%最佳，给30分；5-8%给25分）
        if 3.0 <= change_pct <= 5.0:
            score += 30
            reasons.append(f"涨幅{change_pct:.2f}%最佳")
        elif 5.0 < change_pct <= 8.0:
            score += 25
            reasons.append(f"涨幅{change_pct:.2f}%良好")
        
        # 成交量评分
        if vol_ratio >= 2.0:
            score += 20
            reasons.append(f"量比{vol_ratio:.2f}优秀")
        elif vol_ratio >= 1.5:
            score += 15
            reasons.append(f"量比{vol_ratio:.2f}良好")
        
        # 均线多头排列
        if latest['MA5'] > latest['MA10'] > latest['MA20']:
            score += 30
            reasons.append("均线多头排列")
        elif latest['MA5'] > latest['MA20']:
            score += 20
            reasons.append("均线部分多头")
        
        # 趋势评分
        if price > latest['BOLL_MID']:
            score += 20
            reasons.append("价格在布林带中轨上方")
        
        return True, score, reasons
        
    except Exception as e:
        return False, 0, [f"检查出错: {str(e)}"]


def screen_stocks():
    """
    筛选符合隔夜持股法的股票
    """
    # 测试股票池（可扩展）
    test_stocks = [
        # 半导体
        ('600584', '长电科技'),
        ('002371', '北方华创'),
        ('688012', '中微公司'),
        # 绿电
        ('300750', '宁德时代'),
        ('002594', '比亚迪'),
        # 消费
        ('000858', '五粮液'),
        ('600519', '贵州茅台'),
        # 银行
        ('600036', '招商银行'),
        ('000001', '平安银行'),
        # 其他热门
        ('300041', '回天新材'),
        ('002415', '海康威视'),
    ]
    
    print("="*60)
    print("隔夜持股法选股筛选")
    print("="*60)
    print(f"筛选时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    
    results = []
    
    for code, name in test_stocks:
        print(f"\n检查 {name}({code})...")
        is_valid, score, reasons = check_buy_signals(code)
        
        if is_valid:
            print(f"  ✅ 符合条件！评分：{score}")
            print(f"  原因：{'，'.join(reasons)}")
            
            quote = get_stock_quote(code)[code]
            results.append({
                '代码': code,
                '名称': name,
                '现价': quote['price'],
                '涨幅': quote['change_pct'],
                '量比': quote.get('vol_ratio', 0),
                '换手率': quote['turnover_pct'],
                '评分': score,
                '理由': '，'.join(reasons)
            })
        else:
            print(f"  ❌ 不符合条件")
            for r in reasons:
                print(f"     - {r}")
    
    # 按评分排序
    results.sort(key=lambda x: x['评分'], reverse=True)
    
    print("\n" + "="*60)
    print("筛选结果（按评分排序）")
    print("="*60)
    
    if len(results) == 0:
        print("今日没有符合条件的股票！")
        print("建议：观望为主，等待更好的机会")
    else:
        for i, r in enumerate(results[:5], 1):
            print(f"\n{i}. {r['名称']}({r['代码']})")
            print(f"   现价：{r['现价']:.2f}元")
            print(f"   涨幅：{r['涨幅']:+.2f}%")
            print(f"   量比：{r['量比']:.2f}")
            print(f"   换手率：{r['换手率']:.2f}%")
            print(f"   评分：{r['评分']}/100")
            print(f"   理由：{r['理由']}")
    
    print("\n" + "="*60)
    
    return results


def generate_trade_plan(stock_code, stock_name, price):
    """
    生成交易计划
    """
    buy_price = price
    target_price = price * 1.03  # 3%止盈
    stop_loss_price = price * 0.97  # 3%止损
    
    print("\n" + "="*60)
    print(f"交易计划：{stock_name}({stock_code})")
    print("="*60)
    print(f"买入价：{buy_price:.2f}元")
    print(f"买入时间：今日14:50")
    print(f"买入数量：100股（可根据资金调整）")
    print(f"\n止盈价：{target_price:.2f}元（+3%）")
    print(f"止损价：{stop_loss_price:.2f}元（-3%）")
    print(f"\n执行时间：明日盘中")
    print("="*60)


if __name__ == "__main__":
    print("隔夜持股法选股系统")
    print("="*60)
    
    # 执行筛选
    results = screen_stocks()
    
    # 如果有符合条件的股票，生成交易计划
    if len(results) > 0:
        print("\n是否生成交易计划？(y/n)")
        # 这里可以添加交互逻辑
        best = results[0]
        generate_trade_plan(best['代码'], best['名称'], best['现价'])
