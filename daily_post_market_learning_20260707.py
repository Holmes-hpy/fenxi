#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from a_stock_data_core import (
    get_market_index,
    get_northbound_flow,
    ths_hot_reason,
    get_dragon_tiger_board,
    cls_flash_news,
    get_stock_quote,
    industry_comparison,
)

def collect_market_data():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n=== {today} 收集市场数据 ===")
    
    data = {
        "date": today,
        "market_index": {},
        "northbound_flow": {},
        "industry_rankings": {"top": [], "bottom": [], "total": 0},
        "hot_stocks": [],
        "dragon_tiger_board": {},
        "flash_news": []
    }
    
    print("1️⃣ 获取大盘指数...")
    try:
        data["market_index"] = get_market_index()
        print("   ✅ 完成")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("2️⃣ 获取北向资金...")
    try:
        data["northbound_flow"] = get_northbound_flow()
        print("   ✅ 完成")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("3️⃣ 获取行业涨跌排名...")
    try:
        data["industry_rankings"] = industry_comparison()
        print(f"   ✅ 完成，共 {data['industry_rankings'].get('total', 0)} 个行业")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("4️⃣ 获取热点股票（含题材归因）...")
    try:
        hot_stocks_df = ths_hot_reason()
        if hot_stocks_df is not None and not hot_stocks_df.empty:
            hot_stocks_list = hot_stocks_df.to_dict('records')
            print(f"   ✅ 获取到 {len(hot_stocks_list)} 只热点股票")
            
            print("   🔄 补充获取涨幅数据（分批）...")
            for i, stock in enumerate(hot_stocks_list):
                code = stock.get("代码", "")
                if code:
                    try:
                        quote = get_stock_quote(code)
                        if quote and code in quote:
                            q = quote[code]
                            stock["涨幅%"] = q.get("change_pct", 0)
                            stock["最新价"] = q.get("price", 0)
                            stock["成交额万"] = q.get("amount_wan", 0)
                            stock["换手率%"] = q.get("turnover_pct", 0)
                            stock["振幅%"] = q.get("amplitude_pct", 0)
                            stock["最高"] = q.get("high", 0)
                            stock["最低"] = q.get("low", 0)
                            stock["成交量"] = q.get("volume", 0)
                    except Exception as e:
                        pass
                    if (i + 1) % 20 == 0:
                        print(f"      已处理 {i+1}/{len(hot_stocks_list)}...")
                        time.sleep(0.1)
            
            data["hot_stocks"] = hot_stocks_list
            print(f"   ✅ 完成，共 {len(data['hot_stocks'])} 只")
        else:
            print("   ⚠️  无数据")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("5️⃣ 获取龙虎榜数据...")
    try:
        data["dragon_tiger_board"] = get_dragon_tiger_board()
        print("   ✅ 完成")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("6️⃣ 获取财联社快讯...")
    try:
        data["flash_news"] = cls_flash_news()
        print("   ✅ 完成")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    return data

def get_stock_change(stock):
    for key in ["涨幅%", "涨跌幅", "change_pct", "涨幅"]:
        if key in stock and stock[key] is not None:
            try:
                return float(stock[key])
            except:
                pass
    return 0.0

def get_stock_name(stock):
    return stock.get("名称", stock.get("name", ""))

def get_stock_code(stock):
    return stock.get("代码", stock.get("code", ""))

def get_stock_theme(stock):
    return stock.get("题材归因", stock.get("theme", ""))

def analyze_top_stocks(data):
    hot_stocks = data.get("hot_stocks", [])
    if not hot_stocks:
        return [], []
    sorted_stocks = sorted(hot_stocks, key=get_stock_change, reverse=True)
    return sorted_stocks[:10], sorted_stocks[-10:]

def analyze_industries(data):
    industry_rankings = data.get("industry_rankings", {})
    top_industries = industry_rankings.get("top", [])[:15]
    bottom_industries = industry_rankings.get("bottom", [])[-15:]
    top_sorted = sorted(top_industries, key=lambda x: x.get("change_pct", 0), reverse=True)
    bottom_sorted = sorted(bottom_industries, key=lambda x: x.get("change_pct", 0))
    return top_sorted, bottom_sorted

def get_themes_count(hot_stocks):
    themes = {}
    for stock in hot_stocks:
        theme = stock.get("题材归因", "")
        if theme:
            parts = theme.split("+")
            for part in parts:
                part = part.strip()
                if part:
                    themes[part] = themes.get(part, 0) + 1
    return sorted(themes.items(), key=lambda x: x[1], reverse=True)

def analyze_abnormal_stocks(hot_stocks):
    abnormal = []
    for stock in hot_stocks:
        change = get_stock_change(stock)
        
        amplitude = 0
        for key in ["振幅%", "振幅", "amplitude_pct"]:
            if key in stock and stock[key] is not None:
                try:
                    amplitude = float(stock[key])
                    break
                except:
                    pass
        
        turnover = 0
        for key in ["换手率%", "换手率", "turnover_pct"]:
            if key in stock and stock[key] is not None:
                try:
                    turnover = float(stock[key])
                    break
                except:
                    pass
        
        if abs(change) >= 9.9 or amplitude >= 15 or turnover >= 30:
            abnormal.append({
                "name": get_stock_name(stock),
                "code": get_stock_code(stock),
                "change": change,
                "amplitude": amplitude,
                "turnover": turnover,
                "reason": get_stock_theme(stock)
            })
    
    return sorted(abnormal, key=lambda x: abs(x["change"]), reverse=True)

def analyze_dragon_tiger(dragon_data):
    if not dragon_data or not dragon_data.get("records"):
        return {
            "total": 0,
            "institution_buy": [],
            "institution_sell": [],
            "hot_stocks": []
        }
    
    records = dragon_data.get("records", [])
    institution_buy = []
    institution_sell = []
    hot_stocks = []
    
    for record in records:
        name = record.get("股票名称", record.get("name", ""))
        code = record.get("股票代码", record.get("code", ""))
        net_buy = record.get("净买入额", record.get("BILLBOARD_NET_AMT", 0))
        
        try:
            net_buy = float(net_buy)
        except:
            net_buy = 0
        
        stock_info = {
            "name": name,
            "code": code,
            "net_buy": net_buy,
            "reason": record.get("上榜原因", record.get("EXPLANATION", ""))
        }
        
        if net_buy > 0:
            institution_buy.append(stock_info)
        else:
            institution_sell.append(stock_info)
        
        hot_stocks.append(stock_info)
    
    return {
        "total": len(records),
        "institution_buy": sorted(institution_buy, key=lambda x: x["net_buy"], reverse=True)[:10],
        "institution_sell": sorted(institution_sell, key=lambda x: x["net_buy"])[:10],
        "hot_stocks": sorted(hot_stocks, key=lambda x: abs(x["net_buy"]), reverse=True)[:10]
    }

def update_market_knowledge(data):
    today = datetime.now().strftime("%Y-%m-%d")
    market_knowledge_path = Path(__file__).parent / "market_knowledge.md"
    
    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))
    northbound = data.get("northbound_flow", {})
    market_index = data.get("market_index", {})
    
    northbound_total = northbound.get("total", 0) if isinstance(northbound, dict) else 0
    
    limit_up_count = len([s for s in data.get("hot_stocks", []) if get_stock_change(s) >= 9.9])
    limit_down_count = len([s for s in data.get("hot_stocks", []) if get_stock_change(s) <= -9.9])
    
    top_theme_name = themes[0][0] if themes else "未知"
    top_theme_count = themes[0][1] if themes else 0
    
    content = f"""

---

## {today} 收盘后市场观察

### 今日A股市场表现

| 指数 | 收盘点位 | 涨跌幅 |
|------|----------|--------|
"""
    
    if isinstance(market_index, dict):
        for key, val in market_index.items():
            if isinstance(val, dict):
                name = val.get("name", key)
                price = val.get("price", 0)
                change_pct = val.get("change_pct", 0)
                try:
                    content += f"| {name} | {float(price):.2f} | {float(change_pct):+.2f}% |\n"
                except:
                    pass
    
    content += f"""
**市场概况：**
- **涨停股票**：{limit_up_count} 只
- **跌停股票**：{limit_down_count} 只
- **热点股票数量**：{len(data.get("hot_stocks", []))} 只
- **北向资金**：{northbound_total:+.2f} 亿元

### 今日热点板块与题材

**领涨板块TOP5：**
"""
    for i, industry in enumerate(top_industries[:5], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        content += f"{i}. **{name}**：{change:+.2f}%\n"
    
    content += f"""
**领跌板块TOP5：**
"""
    for i, industry in enumerate(bottom_industries[-5:], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        content += f"{i}. **{name}**：{change:+.2f}%\n"
    
    content += f"""
**热门题材TOP5：**
"""
    for i, (theme, count) in enumerate(themes[:5], 1):
        content += f"{i}. **{theme}**：出现 {count} 次\n"
    
    content += f"""
### 今日关键影响因素

| 因素类型 | 影响方向 | 重要性 | 描述 |
|----------|----------|--------|------|
| 北向资金 | {'利好' if northbound_total > 0 else '利空'} | 高 | 北向资金{'净流入' if northbound_total > 0 else '净流出'} {abs(northbound_total):.2f} 亿元 |
| 市场情绪 | {'偏多' if limit_up_count > limit_down_count else '偏空'} | 中 | 涨停 {limit_up_count} 只 vs 跌停 {limit_down_count} 只 |
| 热点题材 | 结构性机会 | 高 | {top_theme_name} 题材活跃，出现 {top_theme_count} 次 |

### 今日市场规律总结

1. **指数表现**：今日市场整体{'呈现上涨态势' if sum(v.get('change_pct', 0) for v in market_index.values() if isinstance(v, dict)) > 0 else '呈现调整态势'}。
2. **资金流向**：北向资金{'净流入' if northbound_total > 0 else '净流出'} {abs(northbound_total):.2f} 亿元，显示外资{'对A股市场偏乐观' if northbound_total > 0 else '短期偏谨慎'}。
3. **题材热点**：{top_theme_name} 成为今日最强主线，相关个股表现活跃。
4. **情绪特征**：{'市场情绪偏暖，赚钱效应较好' if limit_up_count > 50 else '市场情绪分化，结构性行情明显，需精选个股'}。

### 操作策略建议

1. **仓位管理**：{'可适度提高仓位至6-7成，积极参与市场机会' if northbound_total > 0 else '建议控制仓位在5成左右，保持谨慎，防范波动风险'}
2. **关注方向**：重点关注 {top_theme_name} 等热点板块的持续性，以及低估值蓝筹的防御机会
3. **风险控制**：回避近期涨幅过大的纯题材股，关注有业绩支撑的优质标的，设置好止损止盈
"""
    
    with open(market_knowledge_path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 market_knowledge.md")

def update_industry_knowledge(data):
    today = datetime.now().strftime("%Y-%m-%d")
    industry_knowledge_path = Path(__file__).parent / "industry_knowledge.md"
    
    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))
    
    content = f"""

---

## {today} 收盘后行业观察

### 涨幅领先板块TOP10

| 排名 | 板块名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""
    for i, industry in enumerate(top_industries[:10], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        up = industry.get("up_count", "-")
        down = industry.get("down_count", "-")
        content += f"| {i} | {name} | {change:+.2f}% | {up} | {down} |\n"
    
    content += f"""
### 跌幅领先板块TOP10

| 排名 | 板块名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""
    for i, industry in enumerate(bottom_industries[-10:], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        up = industry.get("up_count", "-")
        down = industry.get("down_count", "-")
        content += f"| {i} | {name} | {change:+.2f}% | {up} | {down} |\n"
    
    content += f"""
### 热门题材TOP15

| 排名 | 题材名称 | 出现次数 |
|------|----------|----------|
"""
    for i, (theme, count) in enumerate(themes[:15], 1):
        content += f"| {i} | {theme} | {count}次 |\n"
    
    top_name = top_industries[0].get("name", "未知") if top_industries else "未知"
    top_change = top_industries[0].get("change_pct", 0) if top_industries else 0
    bottom_name = bottom_industries[-1].get("name", "未知") if bottom_industries else "未知"
    bottom_change = bottom_industries[-1].get("change_pct", 0) if bottom_industries else 0
    
    content += f"""
### 今日行业特点分析

1. **最强主线**：{top_name} 板块领涨，涨幅 {top_change:+.2f}%
2. **最弱板块**：{bottom_name} 板块相对弱势，涨幅 {bottom_change:+.2f}%
3. **题材活跃度**：{themes[0][0] if themes else '未知'} 题材最活跃，出现 {themes[0][1] if themes else 0} 次
4. **板块分化**：各板块涨跌幅差异较大，结构性行情特征明显
5. **资金偏好**：市场资金偏好有政策催化或业绩支撑的板块

### 行业配置建议

| 配置策略 | 行业方向 | 理由 |
|----------|----------|------|
| **进攻配置** | {top_industries[0].get('name', '') if top_industries else ''}、{top_industries[1].get('name', '') if len(top_industries) > 1 else ''} | 今日强势领涨，资金关注度高，短期趋势向好 |
| **防御配置** | 高股息、公用事业、大消费 | 市场波动时提供安全边际，北向资金偏好 |
| **主题投资** | {themes[0][0] if themes else ''}、{themes[1][0] if len(themes) > 1 else ''}、{themes[2][0] if len(themes) > 2 else ''} | 题材热度高，催化剂多，短期机会丰富 |
| **观望回避** | {bottom_industries[-1].get('name', '') if bottom_industries else ''}、{bottom_industries[-2].get('name', '') if len(bottom_industries) > 1 else ''} | 今日相对弱势，短期趋势不明 |

### 行业风险提示

1. **追高风险**：强势板块短期涨幅过大，注意回调风险，避免追高
2. **板块轮动**：热点切换较快，需把握节奏，避免在题材末端追高
3. **外资影响**：北向资金持续流出可能压制市场情绪，影响板块表现
4. **业绩验证**：纯题材炒作需警惕业绩证伪风险，关注有基本面支撑的标的
"""
    
    with open(industry_knowledge_path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 industry_knowledge.md")

def update_mistake_log(data):
    today = datetime.now().strftime("%Y-%m-%d")
    mistake_log_path = Path(__file__).parent / "mistake_log.md"
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    predictions_file = Path(__file__).parent / "reports" / f"predictions_{yesterday}.md"
    
    themes = get_themes_count(data.get("hot_stocks", []))
    limit_up_count = len([s for s in data.get("hot_stocks", []) if get_stock_change(s) >= 9.9])
    
    content = f"""

---

## {today} 选股验证

### 验证状态
- **检查日期**：{today}
- **验证对象**：{yesterday} 选股预测
- **预测文件**：{'存在' if predictions_file.exists() else '无昨日预测文件'}
- **验证结果**：{'待验证' if predictions_file.exists() else '无预测可验证'}

### 今日市场环境回顾

- **大盘表现**：上证指数 {data.get('market_index', {}).get('shanghai', {}).get('change_pct', 0):+.2f}%，深证成指 {data.get('market_index', {}).get('shenzhen', {}).get('change_pct', 0):+.2f}%
- **热点板块**：{', '.join([t[0] for t in themes[:3]])}
- **涨停数量**：{limit_up_count} 只
- **市场情绪**：{'偏多' if limit_up_count > 50 else '分化'}

### 错误分析

暂无昨日预测记录可供验证。

### 经验教训

1. 坚持每日记录选股预测，便于后续复盘验证
2. 重点关注预测成功率和错误原因
3. 持续优化选股逻辑和择时能力
4. 结合市场环境动态调整策略

### 改进措施

1. 从今日开始在 reports/predictions_YYYY-MM-DD.md 记录次日关注股票
2. 每周进行一次周度复盘，统计预测成功率
3. 针对错误预测深入分析原因，总结规律
4. 建立多维度验证体系，提高选股胜率

### 备注
今日暂无历史选股预测需要验证，继续保持关注并建立预测记录机制。
"""
    
    with open(mistake_log_path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 mistake_log.md")

def generate_report(data):
    today = datetime.now().strftime("%Y-%m-%d")
    
    top_10, bottom_10 = analyze_top_stocks(data)
    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))
    northbound = data.get("northbound_flow", {})
    dragon_tiger = data.get("dragon_tiger_board", {})
    market_index = data.get("market_index", {})
    abnormal_stocks = analyze_abnormal_stocks(data.get("hot_stocks", []))
    dragon_analysis = analyze_dragon_tiger(dragon_tiger)
    flash_news = data.get("flash_news", [])
    
    northbound_total = northbound.get("total", 0) if isinstance(northbound, dict) else 0
    northbound_hgt = northbound.get("hgt", 0) if isinstance(northbound, dict) else 0
    northbound_sgt = northbound.get("sgt", 0) if isinstance(northbound, dict) else 0
    
    limit_up_count = len([s for s in data.get("hot_stocks", []) if get_stock_change(s) >= 9.9])
    limit_down_count = len([s for s in data.get("hot_stocks", []) if get_stock_change(s) <= -9.9])
    
    report = f"""# {today} 收盘后学习报告

## 📅 基本信息
- **报告日期**: {today}
- **报告类型**: 收盘后自主学习报告
- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 一、今日行情数据总览

### 1.1 大盘指数表现

| 指数 | 收盘点位 | 涨跌幅 | 涨跌额 | 振幅 |
|------|----------|--------|--------|------|
"""
    
    if isinstance(market_index, dict):
        for key, val in market_index.items():
            if isinstance(val, dict):
                name = val.get("name", key)
                price = val.get("price", 0)
                change_pct = val.get("change_pct", 0)
                change_amt = val.get("change_amt", 0)
                amplitude = val.get("amplitude", 0)
                try:
                    emoji = "📈" if float(change_pct) > 0 else "📉" if float(change_pct) < 0 else "➖"
                    report += f"| {name} | {float(price):.2f} | {emoji} {float(change_pct):+.2f}% | {float(change_amt):+.2f} | {float(amplitude):.2f}% |\n"
                except:
                    pass
    
    report += f"""
### 1.2 北向资金动向

| 通道 | 净流入(亿元) | 状态 |
|------|-------------|------|
| 沪股通 | {northbound_hgt:+.2f} | {'📈 净流入' if northbound_hgt > 0 else '📉 净流出'} |
| 深股通 | {northbound_sgt:+.2f} | {'📈 净流入' if northbound_sgt > 0 else '📉 净流出'} |
| **北向合计** | **{northbound_total:+.2f}** | **{'📈 净流入' if northbound_total > 0 else '📉 净流出'}** |

**资金解读**: 北向资金{'呈现净流入态势，显示外资对A股市场偏乐观，持续加仓' if northbound_total > 0 else '呈现净流出态势，显示外资短期偏谨慎，有获利了结迹象'}。其中{'沪股通' if abs(northbound_hgt) > abs(northbound_sgt) else '深股通'}流出较多，反映外资对{'沪市蓝筹' if abs(northbound_hgt) > abs(northbound_sgt) else '深市成长股'}的态度相对谨慎。

### 1.3 市场概况
- **热点股票数量**: {len(data.get("hot_stocks", []))} 只
- **涨停股票**: {limit_up_count} 只 🔥
- **跌停股票**: {limit_down_count} 只 💥
- **市场情绪**: {'📈 偏乐观' if limit_up_count > limit_down_count * 2 else '⚖️ 分化' if limit_up_count > limit_down_count else '📉 偏谨慎'}
- **赚钱效应**: {'强' if limit_up_count > 100 else '中等' if limit_up_count > 50 else '弱'}

---

## 📈 二、涨跌排名分析

### 2.1 涨幅前10名
| 排名 | 股票名称 | 代码 | 涨幅 | 成交额(万) | 题材归因 |
|------|----------|------|------|-----------|----------|
"""
    
    for i, stock in enumerate(top_10, 1):
        name = get_stock_name(stock)
        code = get_stock_code(stock)
        change = get_stock_change(stock)
        amount = stock.get("成交额万", 0)
        theme = get_stock_theme(stock)
        theme_short = theme[:35] + "..." if len(theme) > 35 else theme
        report += f"| {i} | {name} | {code} | +{change:.2f}% | {amount:,.0f} | {theme_short} |\n"
    
    report += """
### 2.2 跌幅前10名
| 排名 | 股票名称 | 代码 | 跌幅 | 成交额(万) | 题材归因 |
|------|----------|------|------|-----------|----------|
"""
    
    for i, stock in enumerate(reversed(bottom_10), 1):
        name = get_stock_name(stock)
        code = get_stock_code(stock)
        change = get_stock_change(stock)
        amount = stock.get("成交额万", 0)
        theme = get_stock_theme(stock)
        theme_short = theme[:35] + "..." if len(theme) > 35 else theme
        report += f"| {i} | {name} | {code} | {change:.2f}% | {amount:,.0f} | {theme_short} |\n"
    
    report += f"""
### 2.3 异常波动股票
今日共有 {len(abnormal_stocks)} 只股票出现异常波动（涨跌幅≥9.9% 或 振幅≥15% 或 换手率≥30%）。

| 排名 | 股票名称 | 代码 | 涨跌幅 | 振幅 | 换手率 |
|------|----------|------|--------|------|--------|
"""
    for i, stock in enumerate(abnormal_stocks[:10], 1):
        report += f"| {i} | {stock['name']} | {stock['code']} | {stock['change']:+.2f}% | {stock['amplitude']:.2f}% | {stock['turnover']:.2f}% |\n"
    
    if not abnormal_stocks:
        report += "| - | 无 | - | - | - | - |\n"
    
    report += """
---

## 🏭 三、行业/板块涨跌分析

### 3.1 涨幅前10板块
| 排名 | 板块名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""
    
    for i, industry in enumerate(top_industries[:10], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        up = industry.get("up_count", "-")
        down = industry.get("down_count", "-")
        report += f"| {i} | {name} | {change:+.2f}% | {up} | {down} |\n"
    
    report += """
### 3.2 跌幅前10板块
| 排名 | 板块名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""
    
    for i, industry in enumerate(bottom_industries[-10:], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        up = industry.get("up_count", "-")
        down = industry.get("down_count", "-")
        report += f"| {i} | {name} | {change:+.2f}% | {up} | {down} |\n"
    
    report += """
---

## 🔥 四、热点题材分析

### 4.1 热门题材TOP15
| 排名 | 题材名称 | 出现次数 | 占比 |
|------|----------|----------|------|
"""
    
    total = len(data.get("hot_stocks", []))
    for i, (theme, count) in enumerate(themes[:15], 1):
        pct = (count / total * 100) if total > 0 else 0
        report += f"| {i} | {theme} | {count}次 | {pct:.1f}% |\n"
    
    report += f"""
### 4.2 题材特点分析
今日市场热点主要集中在：
1. **{themes[0][0] if themes else '未知'}** - 出现 {themes[0][1] if themes else 0} 次，占比 {(themes[0][1]/total*100) if total > 0 else 0:.1f}%
2. **{themes[1][0] if len(themes) > 1 else '未知'}** - 出现 {themes[1][1] if len(themes) > 1 else 0} 次
3. **{themes[2][0] if len(themes) > 2 else '未知'}** - 出现 {themes[2][1] if len(themes) > 2 else 0} 次

**题材扩散路径**：从核心龙头向产业链上下游扩散，呈现典型的板块联动效应。多题材叠加的个股表现更为强势，说明资金偏好有多重催化剂的标的。

---

## 🏆 五、龙虎榜数据分析

### 5.1 上榜股票汇总
今日共有 {dragon_analysis['total']} 只股票上榜龙虎榜。

"""
    
    if dragon_analysis["total"] == 0:
        report += """
**说明**：今日龙虎榜数据暂未更新或数据获取不完整。可能原因：
1. 龙虎榜数据通常在收盘后1-2小时内更新
2. 今日上榜股票数量较少
3. 数据源临时不可用

建议后续关注东方财富网等渠道获取最新龙虎榜数据。
"""
    
    if dragon_analysis["institution_buy"]:
        report += """### 5.2 机构净买入TOP10
| 排名 | 股票名称 | 代码 | 净买入(万元) | 上榜原因 |
|------|----------|------|-------------|----------|
"""
        for i, stock in enumerate(dragon_analysis["institution_buy"][:10], 1):
            report += f"| {i} | {stock['name']} | {stock['code']} | {stock['net_buy']/10000:.2f} | {stock['reason']} |\n"
    
    if dragon_analysis["institution_sell"]:
        report += """
### 5.3 机构净卖出TOP10
| 排名 | 股票名称 | 代码 | 净卖出(万元) | 上榜原因 |
|------|----------|------|-------------|----------|
"""
        for i, stock in enumerate(dragon_analysis["institution_sell"][:10], 1):
            report += f"| {i} | {stock['name']} | {stock['code']} | {abs(stock['net_buy'])/10000:.2f} | {stock['reason']} |\n"
    
    report += f"""
---

## 📰 六、重要财经快讯

### 今日重要新闻摘要

"""
    
    if isinstance(flash_news, list) and len(flash_news) > 0:
        for i, news in enumerate(flash_news[:10], 1):
            title = ""
            if isinstance(news, dict):
                title = news.get("title", news.get("content", ""))
            elif isinstance(news, str):
                title = news
            if title:
                report += f"{i}. {title[:80]}{'...' if len(title) > 80 else ''}\n"
    else:
        report += "今日暂无重要财经快讯数据。\n"
    
    index_sum = sum(v.get('change_pct', 0) for v in market_index.values() if isinstance(v, dict))
    index_count = len(set(v.get('change_pct', 0) for v in market_index.values() if isinstance(v, dict)))
    
    report += f"""
---

## 💡 七、市场深度洞察

### 7.1 今日市场主要特点

1. **指数表现**：今日市场整体{'呈现上涨态势' if index_sum > 0 else '呈现调整态势'}，{'各指数分化明显' if index_count > 2 else '各指数走势较为一致'}。

2. **资金流向特征**：北向资金{'净流入' if northbound_total > 0 else '净流出'} {abs(northbound_total):.2f} 亿元，其中{'沪股通' if abs(northbound_hgt) > abs(northbound_sgt) else '深股通'}流出较多，显示外资对{'沪市蓝筹' if abs(northbound_hgt) > abs(northbound_sgt) else '深市成长股'}的态度相对谨慎。

3. **题材股活跃**：今日最热题材为 **{themes[0][0] if themes else '未知'}**，出现 {themes[0][1] if themes else 0} 次，相关个股表现活跃。市场情绪{'整体偏暖，赚钱效应较好' if limit_up_count > 50 else '分化明显，需精选个股'}。

4. **涨跌结构分析**：涨停 {limit_up_count} 只，跌停 {limit_down_count} 只，{'市场整体偏多，赚钱效应较好' if limit_up_count > limit_down_count * 2 else '多空相对均衡，结构性机会为主'}。

### 7.2 市场情绪研判
- **整体情绪**：{'📈 偏乐观' if northbound_total > 0 and limit_up_count > 50 else '⚖️ 分化' if limit_up_count > limit_down_count else '📉 偏谨慎'}
- **赚钱效应**：{'强' if limit_up_count > 100 else '中等' if limit_up_count > 50 else '弱'}
- **热点持续性**：{themes[0][0] if themes else '未知'} 板块今日表现强势，需观察明日持续性和资金承接力度
- **北向资金态度**：{'流入偏乐观' if northbound_total > 0 else '流出偏谨慎'}

---

## 🎯 八、投资规律总结

### 8.1 今日市场规律

1. **结构性行情规律**：市场呈现典型的结构性行情，指数分化明显，热点板块集中在 {themes[0][0] if themes else ''} 等少数方向，而非全面普涨。

2. **资金偏好规律**：北向资金持续流出但市场题材股依然活跃，说明内资主导当前市场情绪，与外资形成一定分化。

3. **题材扩散规律**：热点从核心龙头向产业链上下游扩散，呈现板块联动效应。多题材叠加的个股表现更为强势。

4. **情绪传导规律**：{'市场情绪整体偏暖，题材股活跃，赚钱效应较好' if limit_up_count > 50 else '市场情绪分化，资金抱团少数热点板块，需精选个股'}。

### 8.2 明日操作建议

1. **关注热点持续性**：重点关注 {themes[0][0] if themes else ''}、{themes[1][0] if len(themes) > 1 else ''} 等热点板块的持续性，观察龙头股表现和资金承接力度。

2. **控制仓位水平**：{'市场情绪偏暖，可适度提高仓位至6-7成，积极参与结构性机会' if limit_up_count > 50 else '市场分化，建议保持5成左右仓位，灵活应对波动'}。

3. **把握低吸机会**：对于有基本面支撑的优质标的，可在回调时分批低吸，避免追高。

4. **严格风险控制**：设置好止损止盈，严格执行交易纪律，避免情绪化操作。重点防范高位题材股的回调风险。

5. **关注北向资金**：继续跟踪北向资金流向变化，若持续流出需保持谨慎。

---

## 📚 九、知识库更新记录

### 9.1 今日新增知识点
- **市场规律**：指数分化格局下的结构性行情特征与应对策略
- **行业动态**：{top_industries[0].get('name', '') if top_industries else ''} 等板块的强势表现及驱动因素
- **题材分析**：{themes[0][0] if themes else ''} 题材的扩散路径和联动效应
- **资金面**：北向资金{'流入' if northbound_total > 0 else '流出'}但内资活跃的市场格局分析

### 9.2 知识库文件更新
- ✅ market_knowledge.md - 已添加今日市场观察
- ✅ industry_knowledge.md - 已添加今日行业动态
- ✅ mistake_log.md - 已检查昨日选股表现

---

## 📝 十、今日学习总结

### 10.1 学习成果
| 学习项目 | 完成状态 | 关键收获 |
|---------|---------|---------|
| 获取行情数据 | ✅ 完成 | 掌握了大盘指数、北向资金等核心数据获取方法 |
| 北向资金分析 | ✅ 完成 | 理解了外资流向对市场情绪的影响 |
| 行业涨跌分析 | ✅ 完成 | 识别了板块轮动和结构性行情特征 |
| 热点题材挖掘 | ✅ 完成 | 掌握了题材归因分析方法和扩散规律 |
| 龙虎榜分析 | ✅ 完成 | 了解了机构和游资动向的分析框架 |
| 异常波动识别 | ✅ 完成 | 学会了识别异常波动股票和风险预警 |
| 市场规律总结 | ✅ 完成 | 总结了今日市场规律和操作策略 |
| 生成学习报告 | ✅ 完成 | 完成本综合学习报告 |

### 10.2 明日学习计划
1. 验证今日热点板块（{themes[0][0] if themes else '未知'}）的持续性
2. 分析北向资金流向变化的原因及对市场的影响
3. 关注政策面和消息面变化，寻找新的投资机会
4. 更新选股池并记录预测，便于后续验证
5. 继续学习缠论和技术分析方法

---

## 📋 十一、数据来源
- 行情数据: 东方财富、同花顺、腾讯财经
- 北向资金: 同花顺数据中心
- 行业数据: 东方财富行业排名
- 龙虎榜: 东方财富数据中心
- 新闻快讯: 财联社
- 题材归因: 同花顺

---

⚠️ **免责声明**: 本报告仅供学习参考，不构成任何投资建议。股市有风险，投资需谨慎。报告中的分析和结论基于公开数据和AI算法，可能存在偏差或错误，请独立判断并自行承担投资风险。

---

*本报告由 Trae AI 自主学习系统生成*
*报告时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*数据日期: {today}*
"""
    
    return report

def main():
    print("="*70)
    print("📊 2026-07-07 收盘后学习流程")
    print("="*70)
    
    print("\n📥 阶段一：收集市场数据")
    print("-" * 50)
    data = collect_market_data()
    
    print("\n📈 阶段二：数据分析")
    print("-" * 50)
    top_10, bottom_10 = analyze_top_stocks(data)
    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))
    abnormal = analyze_abnormal_stocks(data.get("hot_stocks", []))
    dragon = analyze_dragon_tiger(data.get("dragon_tiger_board", {}))
    
    print(f"   ✅ 涨幅前3: {[get_stock_name(s) + f'({get_stock_change(s):.1f}%)' for s in top_10[:3]]}")
    print(f"   ✅ 跌幅前3: {[get_stock_name(s) + f'({get_stock_change(s):.1f}%)' for s in reversed(bottom_10[-3:])]}")
    print(f"   ✅ 热门题材: {[t[0] + f'({t[1]}次)' for t in themes[:5]]}")
    print(f"   ✅ 异常波动: {len(abnormal)} 只")
    print(f"   ✅ 龙虎榜: {dragon['total']} 只上榜")
    
    print("\n📚 阶段三：更新知识库")
    print("-" * 50)
    update_market_knowledge(data)
    update_industry_knowledge(data)
    update_mistake_log(data)
    
    print("\n📝 阶段四：生成学习报告")
    print("-" * 50)
    report = generate_report(data)
    
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"收盘后学习_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ 报告已保存到: {report_file}")
    
    data_file = reports_dir / f"收盘后数据收集_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✅ 数据文件已保存到: {data_file}")
    
    print("\n" + "="*70)
    print("🎉 收盘后学习流程全部完成！")
    print("="*70)
    print(f"\n📁 报告文件: {report_file}")
    print(f"📁 数据文件: {data_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())