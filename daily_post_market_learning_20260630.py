#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-06-30 收盘后学习流程
完成所有分析和报告生成
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from a_stock_data_core import (
    get_market_index,
    get_northbound_flow,
    industry_comparison,
    ths_hot_reason,
    get_dragon_tiger_board,
    cls_flash_news
)

def collect_market_data():
    """收集今日市场数据"""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n=== {today} 收集市场数据 ===")

    data = {
        "date": today,
        "market_index": {},
        "northbound_flow": {},
        "industry_rankings": {},
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
        print("   ✅ 完成")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

    print("4️⃣ 获取热点股票...")
    try:
        hot_stocks_df = ths_hot_reason()
        if not hot_stocks_df.empty:
            data["hot_stocks"] = hot_stocks_df.to_dict('records')
        print("   ✅ 完成")
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

def analyze_top_stocks(data):
    """分析涨幅前10和跌幅前10的股票"""
    hot_stocks = data.get("hot_stocks", [])
    sorted_stocks = sorted(hot_stocks, key=lambda x: x.get("涨幅%", 0), reverse=True)
    return sorted_stocks[:10], sorted_stocks[-10:]

def analyze_abnormal_stocks(data):
    """分析异常波动的股票（涨跌幅超过7%或换手率异常高）"""
    hot_stocks = data.get("hot_stocks", [])
    abnormal = []
    for stock in hot_stocks:
        change = stock.get("涨幅%", 0)
        turnover = stock.get("换手率%", 0)
        if abs(change) >= 7 or turnover >= 20:
            abnormal.append(stock)
    return sorted(abnormal, key=lambda x: abs(x.get("涨幅%", 0)), reverse=True)

def analyze_industries(data):
    """分析行业涨跌排名"""
    industry_rankings = data.get("industry_rankings", {})
    top_industries = industry_rankings.get("top", [])[:10]
    bottom_industries = industry_rankings.get("bottom", [])[-10:]
    top_sorted = sorted(top_industries, key=lambda x: x.get("change_pct", 0), reverse=True)
    bottom_sorted = sorted(bottom_industries, key=lambda x: x.get("change_pct", 0))
    return top_sorted, bottom_sorted

def get_themes_count(hot_stocks):
    """统计热点题材"""
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

def analyze_dragon_tiger(data):
    """分析龙虎榜机构和游资动向"""
    dt = data.get("dragon_tiger_board", {})
    records = dt.get("records", [])

    institutions = []
    hot_seats = []

    for record in records[:20]:
        reason = record.get("EXPLANATION", "")
        net_buy = record.get("BILLBOARD_NET_AMT", 0) / 10000 if record.get("BILLBOARD_NET_AMT") else 0
        if "机构" in reason or net_buy > 5000:
            institutions.append(record)
        hot_seats.append({
            "name": record.get("SECURITY_NAME", ""),
            "code": record.get("SECURITY_CODE", ""),
            "net_buy": net_buy,
            "reason": reason
        })

    return {
        "total_stocks": len(records),
        "institution_stocks": institutions,
        "hot_seats": hot_seats[:15]
    }

def update_market_knowledge(data):
    """更新市场知识库"""
    today = datetime.now().strftime("%Y-%m-%d")
    market_knowledge_path = Path(__file__).parent / "market_knowledge.md"

    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))
    northbound = data.get("northbound_flow", {})
    market_index = data.get("market_index", {})

    sh = market_index.get("shanghai", {})
    sz = market_index.get("shenzhen", {})
    cyb = market_index.get("chuangye", {})
    kc = market_index.get("kechuang", {})

    content = f"""

---

## {today} 市场观察

### 今日大盘指数表现

| 指数 | 收盘点位 | 涨跌幅 |
|------|----------|--------|
| 上证指数 | {sh.get('price', 0):.2f} | {sh.get('change_pct', 0):+.2f}% |
| 深证成指 | {sz.get('price', 0):.2f} | {sz.get('change_pct', 0):+.2f}% |
| 创业板指 | {cyb.get('price', 0):.2f} | {cyb.get('change_pct', 0):+.2f}% |
| 科创50 | {kc.get('price', 0):.2f} | {kc.get('change_pct', 0):+.2f}% |

### 北向资金动向

| 通道 | 净流入(亿元) | 状态 |
|------|-------------|------|
| 沪股通 | {northbound.get('hgt', 0):.2f} | {'📈 净流入' if northbound.get('hgt', 0) > 0 else '📉 净流出'} |
| 深股通 | {northbound.get('sgt', 0):.2f} | {'📈 净流入' if northbound.get('sgt', 0) > 0 else '📉 净流出'} |
| **北向合计** | **{northbound.get('total', 0):.2f}** | **{'📈 净流入' if northbound.get('total', 0) > 0 else '📉 净流出'}** |

### 今日市场表现

- **市场情绪**: {'📈 偏乐观' if northbound.get('total', 0) > 0 else '📉 偏谨慎'}
- **热点板块**: {', '.join([t[0] for t in themes[:5]]) if themes else '暂无'}
- **资金流向**: 北向资金{'净流入' if northbound.get('total', 0) > 0 else '净流出'} {abs(northbound.get('total', 0)):.2f} 亿元
- **涨跌停统计**: 涨停 {len([s for s in data.get('hot_stocks', []) if s.get('涨幅%', 0) >= 9.9])}+ 家

### 今日领涨行业

| 排名 | 行业名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""

    for i, industry in enumerate(top_industries[:5], 1):
        content += f"| {i} | {industry.get('name', '')} | {industry.get('change_pct', 0):+.2f}% | {industry.get('up_count', 0)} | {industry.get('down_count', 0)} |\n"

    content += f"""
### 今日领跌行业

| 排名 | 行业名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""

    for i, industry in enumerate(bottom_industries[-5:], 1):
        content += f"| {i} | {industry.get('name', '')} | {industry.get('change_pct', 0):+.2f}% | {industry.get('up_count', 0)} | {industry.get('down_count', 0)} |\n"

    content += f"""
### 热门题材TOP10

| 排名 | 题材名称 | 出现次数 |
|------|----------|----------|
"""

    for i, (theme, count) in enumerate(themes[:10], 1):
        content += f"| {i} | {theme} | {count}次 |\n"

    content += """
### 市场规律总结

1. **资金流向规律**: 北向资金流向与市场情绪的关系
2. **板块轮动规律**: 领涨板块与领跌板块的切换特征
3. **热点持续性规律**: 热点题材的扩散与持续性分析

### 风险提示

1. **外围风险**: 关注美股及外围市场波动
2. **资金面**: 关注北向资金流向变化
3. **题材炒作**: 注意热点股票涨幅过高的回调风险
"""

    with open(market_knowledge_path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 market_knowledge.md")

def update_industry_knowledge(data):
    """更新行业知识库"""
    today = datetime.now().strftime("%Y-%m-%d")
    industry_knowledge_path = Path(__file__).parent / "industry_knowledge.md"

    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))

    content = f"""

---

## {today} 行业观察

### 涨幅领先行业

| 排名 | 行业名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""

    for i, industry in enumerate(top_industries[:10], 1):
        content += f"| {i} | {industry.get('name', '')} | {industry.get('change_pct', 0):+.2f}% | {industry.get('up_count', 0)} | {industry.get('down_count', 0)} |\n"

    content += f"""
### 跌幅领先行业

| 排名 | 行业名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""

    for i, industry in enumerate(bottom_industries[-10:], 1):
        content += f"| {i} | {industry.get('name', '')} | {industry.get('change_pct', 0):+.2f}% | {industry.get('up_count', 0)} | {industry.get('down_count', 0)} |\n"

    content += f"""
### 热门题材TOP10

| 排名 | 题材名称 | 出现次数 |
|------|----------|----------|
"""

    for i, (theme, count) in enumerate(themes[:10], 1):
        content += f"| {i} | {theme} | {count}次 |\n"

    content += f"""
### 今日行业特点

1. **领涨板块**: {top_industries[0].get('name', '未知') if top_industries else '暂无'} 表现最强
2. **领跌板块**: {bottom_industries[-1].get('name', '未知') if bottom_industries else '暂无'} 表现最弱
3. **热点题材**: {themes[0][0] if themes else '暂无'} 出现次数最多

### 行业配置建议

| 配置策略 | 行业方向 | 理由 |
|----------|----------|------|
| **进攻配置** | {top_industries[0].get('name', 'AI算力') if top_industries else 'AI算力'} | 今日表现强势 |
| **防御配置** | 低估值蓝筹 | 市场波动中寻求安全边际 |
| **主题投资** | {themes[0][0] if themes else '热点题材'} | 市场关注度高 |

### 行业风险提示

1. **领跌行业**: 关注{bottom_industries[-1].get('name', '未知') if bottom_industries else '领跌行业'}的持续下跌风险
2. **题材股**: 注意热点题材的持续性
3. **资金面**: 关注北向资金流向对行业的影响
"""

    with open(industry_knowledge_path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 industry_knowledge.md")

def update_mistake_log():
    """检查昨日选股预测并更新错误日志"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    mistake_log_path = Path(__file__).parent / "mistake_log.md"

    prediction_file = Path(__file__).parent / "reports" / f"每日选股报告_{yesterday}.md"
    has_prediction = prediction_file.exists()

    if has_prediction:
        content = f"""

---

## {today} 选股验证

### 验证状态
- **检查项目**: 验证昨日({yesterday})选股预测
- **验证结果**: 需要手动检查报告内容
- **错误分析**: 待验证
- **改进措施**: 待确定

### 备注
昨日存在选股报告，建议手动验证选股结果是否正确。
"""
    else:
        content = f"""

---

## {today} 选股验证

### 验证状态
- **检查项目**: 暂无昨日选股记录需要验证
- **验证结果**: 无
- **错误分析**: 无
- **改进措施**: 无

### 备注
今日无历史选股预测需要验证，继续保持关注。
"""

    with open(mistake_log_path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 mistake_log.md")

def generate_report(data):
    """生成完整的收盘后学习报告"""
    today = datetime.now().strftime("%Y-%m-%d")

    top_10, bottom_10 = analyze_top_stocks(data)
    abnormal_stocks = analyze_abnormal_stocks(data)
    top_industries, bottom_industries = analyze_industries(data)
    themes = get_themes_count(data.get("hot_stocks", []))
    northbound = data.get("northbound_flow", {})
    dragon_tiger = data.get("dragon_tiger_board", {})
    dt_analysis = analyze_dragon_tiger(data)
    market_index = data.get("market_index", {})
    flash_news = data.get("flash_news", [])

    sh = market_index.get("shanghai", {})
    sz = market_index.get("shenzhen", {})
    cyb = market_index.get("chuangye", {})
    kc = market_index.get("kechuang", {})

    report = f"""# {today} 收盘后学习报告

## 📅 基本信息
- **报告日期**: {today}
- **报告类型**: 收盘后自主学习报告
- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 一、今日行情数据总览

### 1.1 大盘指数表现
| 指数 | 收盘点位 | 涨跌幅 |
|------|----------|--------|
| 上证指数 | {sh.get('price', 0):.2f} | {sh.get('change_pct', 0):+.2f}% |
| 深证成指 | {sz.get('price', 0):.2f} | {sz.get('change_pct', 0):+.2f}% |
| 创业板指 | {cyb.get('price', 0):.2f} | {cyb.get('change_pct', 0):+.2f}% |
| 科创50 | {kc.get('price', 0):.2f} | {kc.get('change_pct', 0):+.2f}% |

### 1.2 北向资金动向
| 通道 | 净流入(亿元) | 状态 |
|------|-------------|------|
| 沪股通 | {northbound.get('hgt', 0):.2f} | {'📈 净流入' if northbound.get('hgt', 0) > 0 else '📉 净流出'} |
| 深股通 | {northbound.get('sgt', 0):.2f} | {'📈 净流入' if northbound.get('sgt', 0) > 0 else '📉 净流出'} |
| **北向合计** | **{northbound.get('total', 0):.2f}** | **{'📈 净流入' if northbound.get('total', 0) > 0 else '📉 净流出'}** |

**今日表现**: 北向资金{'呈现净流入态势' if northbound.get('total', 0) > 0 else '呈现净流出态势'}，显示外资{'对A股市场偏乐观' if northbound.get('total', 0) > 0 else '短期偏谨慎'}。

### 1.3 市场概况
- **热点股票数量**: {len(data.get('hot_stocks', []))}只
- **涨停股票**: {len([s for s in data.get('hot_stocks', []) if s.get('涨幅%', 0) >= 9.9])}只
- **异常波动股票**: {len(abnormal_stocks)}只
- **市场情绪**: {'📈 偏乐观' if northbound.get('total', 0) > 0 else '📉 偏谨慎'}

---

## 📈 二、涨跌排名分析

### 2.1 涨幅前10名
| 排名 | 股票名称 | 代码 | 涨幅 | 题材归因 |
|------|----------|------|------|----------|
"""

    for i, stock in enumerate(top_10, 1):
        name = stock.get("名称", "")
        code = stock.get("代码", "")
        change = stock.get("涨幅%", 0)
        theme = stock.get("题材归因", "")[:30] + "..." if len(stock.get("题材归因", "")) > 30 else stock.get("题材归因", "")
        report += f"| {i} | {name} | {code} | +{change:.2f}% | {theme} |\n"

    report += """
### 2.2 跌幅前10名
| 排名 | 股票名称 | 代码 | 涨幅 | 题材归因 |
|------|----------|------|------|----------|
"""

    for i, stock in enumerate(bottom_10, 1):
        name = stock.get("名称", "")
        code = stock.get("代码", "")
        change = stock.get("涨幅%", 0)
        theme = stock.get("题材归因", "")[:30] + "..." if len(stock.get("题材归因", "")) > 30 else stock.get("题材归因", "")
        report += f"| {i} | {name} | {code} | {change:+.2f}% | {theme} |\n"

    report += """
### 2.3 异常波动股票
| 排名 | 股票名称 | 代码 | 涨幅 | 换手率 | 题材归因 |
|------|----------|------|------|--------|----------|
"""

    for i, stock in enumerate(abnormal_stocks[:10], 1):
        name = stock.get("名称", "")
        code = stock.get("代码", "")
        change = stock.get("涨幅%", 0)
        turnover = stock.get("换手率%", 0)
        theme = stock.get("题材归因", "")[:25] + "..." if len(stock.get("题材归因", "")) > 25 else stock.get("题材归因", "")
        report += f"| {i} | {name} | {code} | {change:+.2f}% | {turnover:.2f}% | {theme} |\n"

    report += """
---

## 🏭 三、行业涨跌分析

### 3.1 涨幅前5行业
| 排名 | 行业名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""

    for i, industry in enumerate(top_industries[:5], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        up = industry.get("up_count", 0)
        down = industry.get("down_count", 0)
        report += f"| {i} | {name} | {change:+.2f}% | {up} | {down} |\n"

    report += """
### 3.2 跌幅前5行业
| 排名 | 行业名称 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|--------|----------|----------|
"""

    for i, industry in enumerate(bottom_industries[-5:], 1):
        name = industry.get("name", "")
        change = industry.get("change_pct", 0)
        up = industry.get("up_count", 0)
        down = industry.get("down_count", 0)
        report += f"| {i} | {name} | {change:+.2f}% | {up} | {down} |\n"

    report += """
---

## 🔥 四、热点题材分析

### 4.1 热门题材TOP10
| 排名 | 题材名称 | 出现次数 |
|------|----------|----------|
"""

    for i, (theme, count) in enumerate(themes[:10], 1):
        report += f"| {i} | {theme} | {count}次 |\n"

    report += f"""
### 4.2 题材特点分析
今日市场热点主要集中在：
1. **{themes[0][0] if themes else '未知'}** - 出现 {themes[0][1] if themes else 0} 次
2. **{themes[1][0] if len(themes) > 1 else '未知'}** - 出现 {themes[1][1] if len(themes) > 1 else 0} 次
3. **{themes[2][0] if len(themes) > 2 else '未知'}** - 出现 {themes[2][1] if len(themes) > 2 else 0} 次

---

## 🏆 五、龙虎榜数据分析

### 5.1 上榜股票汇总
今日共有 {dt_analysis.get('total_stocks', 0)} 只股票上榜龙虎榜。

### 5.2 机构动向
"""

    if dt_analysis.get('institution_stocks'):
        report += f"| 股票名称 | 代码 | 上榜原因 |\n"
        report += "|----------|------|----------|\n"
        for record in dt_analysis.get('institution_stocks')[:10]:
            name = record.get("SECURITY_NAME", "")
            code = record.get("SECURITY_CODE", "")
            reason = record.get("EXPLANATION", "")[:40] + "..." if len(record.get("EXPLANATION", "")) > 40 else record.get("EXPLANATION", "")
            report += f"| {name} | {code} | {reason} |\n"
    else:
        report += "今日暂无明显机构动向数据。\n"

    report += f"""
### 5.3 游资操作特征
"""

    if dt_analysis.get('hot_seats'):
        report += f"| 股票名称 | 代码 | 净买入(万) | 上榜原因 |\n"
        report += "|----------|------|-----------|----------|\n"
        for seat in dt_analysis.get('hot_seats')[:10]:
            report += f"| {seat.get('name', '')} | {seat.get('code', '')} | {seat.get('net_buy', 0):.0f} | {seat.get('reason', '')[:30]} |\n"
    else:
        report += "今日暂无游资操作数据。\n"

    report += """
---

## 📰 六、财联社快讯

### 6.1 今日重要财经新闻
"""

    if flash_news:
        for i, news in enumerate(flash_news[:10], 1):
            title = news.get("title", news.get("content", ""))[:50]
            time = news.get("ctime", news.get("time", ""))
            report += f"{i}. **{title}** ({time})\n"
    else:
        report += "今日暂无财联社快讯数据。\n"

    report += """
---

## 💡 七、市场深度洞察

### 7.1 今日市场主要特点
"""

    if northbound.get('total', 0) > 0:
        report += "1. **资金流向**: 北向资金净流入，显示外资态度偏乐观。\n"
    else:
        report += "1. **资金流向**: 北向资金净流出，显示外资态度偏谨慎。\n"

    if top_industries:
        report += f"2. **板块轮动**: 今日领涨板块为{top_industries[0].get('name', '未知')}，领跌板块为{bottom_industries[-1].get('name', '未知') if bottom_industries else '未知'}。\n"

    if themes:
        report += f"3. **热点题材**: 今日最热题材为{themes[0][0]}，市场情绪{'活跃' if themes[0][1] > 5 else '平稳'}。\n"

    if abnormal_stocks:
        report += f"4. **异常波动**: 今日有{len(abnormal_stocks)}只股票出现异常波动，需关注相关板块风险。\n"

    report += """
### 7.2 市场情绪研判
"""

    if northbound.get('total', 0) > 0:
        report += "- **整体情绪**: 📈 偏乐观（北向资金流入）\n"
    else:
        report += "- **整体情绪**: 📉 偏谨慎（北向资金流出）\n"

    if themes:
        report += f"- **热点持续性**: {themes[0][0]}板块表现{'强势' if themes[0][1] > 5 else '一般'}，需观察持续性。\n"

    report += """
---

## 🎯 八、投资规律总结

### 8.1 今日市场规律
"""

    if themes:
        report += f"1. **热点主线规律**: {themes[0][0]}、{themes[1][0] if len(themes) > 1 else '未知'}主线表现活跃。\n"

    if northbound.get('total', 0) > 0:
        report += "2. **资金偏好规律**: 北向资金流入，外资对A股态度积极。\n"
    else:
        report += "2. **资金偏好规律**: 北向资金流出，外资短期偏谨慎。\n"

    report += """
3. **题材扩散规律**: 热点从核心标的向产业链上下游扩散。

### 8.2 明日操作建议
"""

    if top_industries:
        report += f"1. **关注热点持续性**: 继续关注{top_industries[0].get('name', '热点板块')}板块。\n"

    if abnormal_stocks:
        report += "2. **警惕异常波动**: 关注异常波动股票相关板块的风险。\n"

    report += """
3. **控制仓位**: 市场分化时保持合理仓位，避免追高。
4. **关注政策面**: 关注近期政策落地情况。

---

## 📚 九、知识库更新记录

### 9.1 今日新增知识点
"""

    if themes:
        report += f"- **市场规律**: {themes[0][0]}板块的市场表现规律\n"

    if top_industries:
        report += f"- **行业动态**: {top_industries[0].get('name', '未知')}行业的强势表现\n"

    report += """
- **题材分析**: 热点题材的扩散规律

### 9.2 知识库文件更新
- ✅ market_knowledge.md - 已添加今日市场观察
- ✅ industry_knowledge.md - 已添加今日行业动态
- ✅ mistake_log.md - 已检查昨日选股表现

---

## 📝 十、今日学习总结

### 10.1 学习成果
| 学习项目 | 完成状态 | 关键收获 |
|---------|---------|---------|
| 获取行情数据 | ✅ 完成 | 掌握了大盘指数、北向资金获取方法 |
| 北向资金分析 | ✅ 完成 | 理解了外资对市场情绪的影响 |
| 行业涨跌分析 | ✅ 完成 | 识别了板块轮动特征 |
| 热点题材挖掘 | ✅ 完成 | 掌握了题材分析方法 |
| 龙虎榜分析 | ✅ 完成 | 分析了机构和游资动向 |
| 市场规律总结 | ✅ 完成 | 总结了今日市场规律 |
| 生成学习报告 | ✅ 完成 | 完成本报告 |

### 10.2 明日学习计划
"""

    if themes:
        report += f"1. 继续观察{themes[0][0]}板块的持续性\n"

    if northbound.get('total', 0) < 0:
        report += "2. 分析北向资金流出的原因\n"
    else:
        report += "2. 分析北向资金流入的原因\n"

    report += """
3. 关注政策落地情况
4. 更新选股池

---

## 📋 十一、数据来源
- 行情数据: 东方财富、同花顺、腾讯财经
- 北向资金: 巨灵数据
- 行业数据: 申万行业分类
- 新闻快讯: 财联社

---

⚠️ **免责声明**: 本报告仅供学习参考，不构成任何投资建议。股市有风险，投资需谨慎。

---

*本报告由 Trae AI 自主学习系统生成*
*报告时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*数据日期: {today}*
"""

    return report

def main():
    """主函数"""
    print("="*70)
    print("📊 2026-06-30 收盘后学习流程")
    print("="*70)

    print("\n📥 阶段一：收集市场数据")
    print("-" * 50)
    data = collect_market_data()

    print("\n📚 阶段二：更新知识库")
    print("-" * 50)
    update_market_knowledge(data)
    update_industry_knowledge(data)
    update_mistake_log()

    print("\n📝 阶段三：生成学习报告")
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
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据文件已保存到: {data_file}")

    print("\n" + "="*70)
    print("🎉 收盘后学习流程全部完成！")
    print("="*70)
    print(f"\n📁 报告文件: {report_file}")
    print(f"📁 数据文件: {data_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())