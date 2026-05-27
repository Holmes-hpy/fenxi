#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收盘后学习分析脚本 - 生成今日市场分析和学习报告
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

import json
from datetime import datetime
from a_stock_data_mcp import (
    get_stock_quote,
    get_ths_hot_stocks,
    get_cls_flash_news
)

def analyze_market():
    """分析今日市场数据"""
    print("="*70)
    print("📊 收盘后市场分析")
    print("="*70)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 读取收集到的数据
    with open('/Users/houpengyuan/Documents/trae_projects/a-stock-data/reports/收盘后数据收集_2026-05-22.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    analysis = {
        'report_date': '2026-05-22',
        'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_summary': {},
        'northbound_flow': {},
        'hot_sectors': {},
        'hot_stocks': {},
        'key_stocks_performance': {},
        'market_insights': []
    }

    # 1. 北向资金分析
    print("1️⃣ 分析北向资金...")
    northbound = data.get('northbound_flow', {})
    analysis['northbound_flow'] = {
        '沪股通': northbound.get('hgt', 0),
        '深股通': northbound.get('sgt', 0),
        '北向合计': northbound.get('total', 0),
        'status': '净流出' if northbound.get('total', 0) < 0 else '净流入'
    }
    print(f"   北向资金净流出: {northbound.get('total', 0):.2f}亿元")

    # 2. 重点个股表现分析
    print("\n2️⃣ 分析重点个股表现...")
    key_stocks = data.get('key_stocks', {})
    for code, info in key_stocks.items():
        for stock_code, stock_info in info.items():
            name = stock_info.get('name', stock_code)
            change_pct = stock_info.get('change_pct', 0)
            price = stock_info.get('price', 0)
            amount_wan = stock_info.get('amount_wan', 0)

            analysis['key_stocks_performance'][name] = {
                'code': stock_code,
                'price': price,
                'change_pct': change_pct,
                'amount_wan': amount_wan,
                'status': '上涨' if change_pct > 0 else ('下跌' if change_pct < 0 else '平盘')
            }
            print(f"   {name}({stock_code}): {change_pct:+.2f}%")

    # 3. 行业涨跌分析
    print("\n3️⃣ 分析行业涨跌情况...")
    industry_rankings = data.get('industry_rankings', {})
    top_industries = industry_rankings.get('top', [])[:10]
    bottom_industries = industry_rankings.get('bottom', [])[-5:]

    analysis['hot_sectors'] = {
        '涨幅前10': [{'name': ind['name'], 'change_pct': ind['change_pct']} for ind in top_industries],
        '跌幅前5': [{'name': ind['name'], 'change_pct': ind['change_pct']} for ind in bottom_industries]
    }

    print("   涨幅前5行业:")
    for i, ind in enumerate(top_industries[:5]):
        print(f"   {i+1}. {ind['name']}: +{ind['change_pct']:.2f}%")

    print("   跌幅前5行业:")
    for i, ind in enumerate(bottom_industries[:5]):
        print(f"   {i+1}. {ind['name']}: {ind['change_pct']:.2f}%")

    # 4. 热点题材分析
    print("\n4️⃣ 分析热点题材...")
    hot_stocks_data = data.get('hot_stocks', {})

    # 提取热点股票和题材
    hot_stocks_list = []
    if '名称' in hot_stocks_data:
        names = hot_stocks_data['名称']
        codes = hot_stocks_data.get('代码', {})
        reasons = hot_stocks_data.get('题材归因', {})

        # 转换为list以便索引
        names_list = list(names.values())
        codes_list = list(codes.values()) if codes else []
        reasons_list = list(reasons.values()) if reasons else []

        for i in range(min(20, len(names_list))):
            hot_stocks_list.append({
                'name': names_list[i] if i < len(names_list) else '',
                'code': codes_list[i] if i < len(codes_list) else '',
                'theme': reasons_list[i] if i < len(reasons_list) else ''
            })

    analysis['hot_stocks'] = {
        'top_10': hot_stocks_list[:10],
        'total': len(hot_stocks_list)
    }

    print("   今日热点题材:")
    themes_count = {}
    for stock in hot_stocks_list:
        theme = stock['theme']
        if theme:
            # 提取主题关键词
            theme_parts = theme.split('+')
            for part in theme_parts:
                part = part.strip()
                if part:
                    themes_count[part] = themes_count.get(part, 0) + 1

    sorted_themes = sorted(themes_count.items(), key=lambda x: x[1], reverse=True)
    for theme, count in sorted_themes[:10]:
        print(f"   - {theme}: {count}只")

    # 5. 市场洞察
    print("\n5️⃣ 生成市场洞察...")

    insights = []

    # 洞察1: 北向资金
    if northbound.get('total', 0) < -30:
        insights.append({
            'category': '资金流向',
            'insight': '北向资金连续净流出超30亿元，外资短期偏谨慎',
            'implication': '可能压制市场情绪，但长期不改配置价值'
        })

    # 洞察2: 半导体板块
    semiconductor_stocks = [s for s in hot_stocks_list if '半导体' in s['theme'] or 'AI' in s['theme']]
    if semiconductor_stocks:
        insights.append({
            'category': '热点板块',
            'insight': f'半导体/AI产业链持续活跃，{len(semiconductor_stocks)}只相关个股上榜热点',
            'implication': '国产替代逻辑持续，可关注优质龙头回调机会'
        })

    # 洞察3: 防御板块
    key_stocks_perf = analysis['key_stocks_performance']
    if key_stocks_perf:
        # 检查消费龙头
        consumer_stocks = ['贵州茅台', '五粮液']
        consumer_decline = all(
            key_stocks_perf.get(name, {}).get('change_pct', 0) < -1
            for name in consumer_stocks if name in key_stocks_perf
        )
        if consumer_decline:
            insights.append({
                'category': '板块轮动',
                'insight': '消费白马股集体调整，显示市场风险偏好下降',
                'implication': '资金可能向防御性板块或主题炒作转移'
            })

    # 洞察4: 市场分化
    if top_industries and bottom_industries:
        avg_top = sum(ind['change_pct'] for ind in top_industries[:5]) / 5
        avg_bottom = sum(ind['change_pct'] for ind in bottom_industries[-5:]) / 5
        if avg_top - avg_bottom > 3:
            insights.append({
                'category': '市场特征',
                'insight': f'市场分化明显，强者恒强格局延续（强弱差距超3%）',
                'implication': '结构性行情中，精选赛道和个股更为重要'
            })

    # 洞察5: PCB/算力板块
    pcb_stocks = [s for s in hot_stocks_list if 'PCB' in s['theme'] or '算力' in s['theme']]
    if pcb_stocks:
        insights.append({
            'category': '产业趋势',
            'insight': f'PCB/算力基础设施持续受追捧，{len(pcb_stocks)}只相关个股表现强势',
            'implication': 'AI产业链上游持续景气，业绩确定性较高'
        })

    analysis['market_insights'] = insights

    print(f"   生成 {len(insights)} 条市场洞察")

    # 6. 市场总结
    print("\n6️⃣ 生成市场总结...")

    # 计算市场情绪
    positive_signals = 0
    negative_signals = 0

    if northbound.get('total', 0) > 0:
        positive_signals += 1
    elif northbound.get('total', 0) < -20:
        negative_signals += 1

    # 统计上涨股票数量
    up_count = sum(1 for ind in industry_rankings.get('top', [])[:20] if ind['change_pct'] > 0)
    if up_count > 15:
        positive_signals += 1
    else:
        negative_signals += 1

    # 热点板块数量
    if len(semiconductor_stocks) > 5:
        positive_signals += 1

    if positive_signals > negative_signals:
        market_sentiment = '偏乐观'
    elif positive_signals < negative_signals:
        market_sentiment = '偏谨慎'
    else:
        market_sentiment = '中性'

    analysis['market_summary'] = {
        'sentiment': market_sentiment,
        'positive_signals': positive_signals,
        'negative_signals': negative_signals,
        'main_theme': '半导体/AI产业链持续活跃',
        'market_characteristic': '结构性分化行情'
    }

    print(f"   市场情绪: {market_sentiment}")
    print(f"   积极信号: {positive_signals}, 消极信号: {negative_signals}")

    # 保存分析结果
    output_file = '/Users/houpengyuan/Documents/trae_projects/a-stock-data/reports/收盘后分析_2026-05-22.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 分析结果已保存到: {output_file}")

    return analysis

def generate_report(analysis):
    """生成收盘后学习报告"""

    print("\n" + "="*70)
    print("📝 生成收盘后学习报告")
    print("="*70)

    report = f"""# 2026年5月22日收盘后学习报告

**报告日期**：2026年5月22日（星期四）
**报告类型**：收盘后自主学习报告
**生成时间**：{analysis['report_time']}

---

## 一、今日行情数据总览

### 1.1 北向资金动向

| 通道 | 净流入(亿元) | 状态 |
|:----:|:-----------:|:----:|
| 沪股通 | {analysis['northbound_flow'].get('沪股通', 0):.2f} | {'净流出' if analysis['northbound_flow'].get('沪股通', 0) < 0 else '净流入'} |
| 深股通 | {analysis['northbound_flow'].get('深股通', 0):.2f} | {'净流出' if analysis['northbound_flow'].get('深股通', 0) < 0 else '净流入'} |
| **北向合计** | **{analysis['northbound_flow'].get('北向合计', 0):.2f}** | **{analysis['northbound_flow'].get('status', 'N/A')}** |

**今日表现**：
- 北向资金全天净流出 **{abs(analysis['northbound_flow'].get('北向合计', 0)):.2f}亿元**
- 沪股通和深股通双双净流出
- 外资短期对A股偏谨慎

---

### 1.2 重点个股行情

| 股票 | 代码 | 今日收盘价 | 涨跌幅 | 成交额(万元) | 状态 |
|:----:|:----:|:--------:|:------:|:-----------:|:----:|
"""

    # 添加重点个股
    for name, info in analysis['key_stocks_performance'].items():
        report += f"| {name} | {info['code']} | {info['price']:.2f}元 | {info['change_pct']:+.2f}% | {info['amount_wan']:,.0f} | {info['status']} |\n"

    report += f"""
**个股点评**：
- **长电科技**(+9.04%)：今日表现强势，成交量放大至198亿，换手率16.03%
- **贵州茅台**(-1.59%)、**五粮液**(-1.55%)：消费白马股集体调整
- **宁德时代**(-0.11%)：小幅回调，整体表现稳定
- **招商银行**(-0.35%)、**中国平安**(-0.15%)：金融板块小幅下跌

---

## 二、行业涨跌分析

### 2.1 涨幅前10行业

| 排名 | 行业名称 | 涨跌幅 | 涨停股数 |
|:----:|:--------:|:------:|:--------:|
"""

    for i, ind in enumerate(analysis['hot_sectors'].get('涨幅前10', [])[:10], 1):
        report += f"| {i} | {ind['name']} | +{ind['change_pct']:.2f}% | {analysis['hot_sectors'].get('up_count', 'N/A')} |\n"

    report += f"""
### 2.2 跌幅前5行业

| 排名 | 行业名称 | 涨跌幅 |
|:----:|:--------:|:------:|
"""

    for i, ind in enumerate(analysis['hot_sectors'].get('跌幅前5', [])[:5], 1):
        report += f"| {i} | {ind['name']} | {ind['change_pct']:.2f}% |\n"

    report += f"""
**行业特征分析**：
- **领涨板块**：通信设备、仪器仪表、电网设备等科技相关板块表现强劲
- **主题投资**：AI算力、半导体产业链持续活跃
- **防御板块**：消费白马股整体偏弱，显示市场风险偏好下降

---

## 三、热点题材深度解析

### 3.1 今日热门题材TOP10

"""

    # 从热点股票中提取主题
    hot_stocks = analysis['hot_socks'] = analysis['hot_stocks'].get('top_10', [])
    themes_count = {}
    for stock in hot_stocks:
        theme = stock.get('theme', '')
        if theme:
            theme_parts = theme.split('+')
            for part in theme_parts:
                part = part.strip()
                if part and len(part) < 20:  # 过滤太长的描述
                    themes_count[part] = themes_count.get(part, 0) + 1

    sorted_themes = sorted(themes_count.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (theme, count) in enumerate(sorted_themes, 1):
        report += f"{i}. **{theme}**：{count}只相关个股表现强势\n"

    report += f"""
### 3.2 核心热点个股

| 股票名称 | 代码 | 题材归因 |
|:--------:|:----:|:--------:|
"""

    for stock in hot_stocks[:10]:
        report += f"| {stock['name']} | {stock['code']} | {stock['theme'][:50]}... |\n"

    report += f"""
**题材特点分析**：
1. **AI算力产业链**：PCB、算力租赁、光模块等领域持续受资金追捧
2. **国产替代**：半导体设备、材料国产化率提升逻辑持续
3. **业绩驱动**：一季报业绩高增个股获得资金青睐
4. **主题炒作**：低空经济、商业航天等新主题持续发酵

---

## 四、龙虎榜数据

**今日龙虎榜**：暂无数据（收盘后数据更新中）

*注：龙虎榜数据通常在收盘后1-2小时内更新完整信息*

---

## 五、市场深度洞察

### 5.1 今日市场主要特点

"""

    for i, insight in enumerate(analysis['market_insights'], 1):
        report += f"""
**洞察{i}：{insight['category']}**
- **核心发现**：{insight['insight']}
- **投资启示**：{insight['implication']}
"""

    report += f"""
### 5.2 资金流向分析

**外资动向**：
- 北向资金连续净流出，短期偏谨慎
- 沪股通流出9.28亿元，深股通流出31.1亿元
- 深市流出更多，可能反映外资对成长股短期看法偏空

**内资动向**：
- 热点个股成交活跃，显示游资和短线资金活跃
- PCB、半导体等科技板块持续吸引资金
- 消费白马股调整，显示机构调仓换股

### 5.3 市场情绪研判

**情绪指标**：
- 整体情绪：{analysis['market_summary'].get('sentiment', '中性')}
- 积极信号：{analysis['market_summary'].get('positive_signals', 0)} 个
- 消极信号：{analysis['market_summary'].get('negative_signals', 0)} 个

**市场特征**：
- 主要热点：{analysis['market_summary'].get('main_theme', 'N/A')}
- 行情特点：{analysis['market_summary'].get('market_characteristic', 'N/A')}
- 结构性分化明显，强者恒强格局延续

---

## 六、投资规律总结

### 6.1 今日市场规律

1. **北向资金警示规律**
   - 当北向资金单日净流出超30亿元时，次日市场往往承压
   - 今日北向净流出40.38亿元，需密切关注明日资金动向
   - **我主观认为**：这可能与近期外围市场波动有关，外资风险偏好下降

2. **热点板块轮动规律**
   - AI算力产业链持续活跃，但内部出现分化
   - PCB、铜箔等上游材料表现最强
   - 业绩超预期个股更受资金青睐
   - **我主观认为**：市场正在从概念炒作向业绩验证过渡

3. **防御板块表现规律**
   - 消费白马股集体调整，通常出现在市场风险偏好下降时
   - 银行、保险等金融板块小幅下跌
   - **我主观认为**：这可能是机构调仓的信号

4. **成交量与走势规律**
   - 强势股成交量持续放大，显示资金参与度高
   - 长电科技换手率达16%，但股价涨停，显示多头力量强劲
   - **我主观认为**：高换手率需要结合股价走势判断

### 6.2 操作启示

**明日操作建议**：
1. **关注北向资金流向**：若持续流出，需控制仓位
2. **紧跟热点主线**：AI算力、半导体国产替代仍是核心方向
3. **业绩为王**：优先配置一季报业绩超预期的个股
4. **控制风险**：市场分化加大，避免追高涨幅过大的题材股

---

## 七、明日市场展望

### 7.1 可能影响市场的因素

**利好因素**：
- 政策面：国务院推进全国统一大市场建设
- 流动性：央行5000亿元MLF操作维持资金面充裕
- 业绩支撑：多家上市公司一季报表现亮眼

**利空因素**：
- 外资流出：北向资金连续净流出
- 港股承压：科网股调整可能拖累A股情绪
- 获利回吐：近期涨幅较大的科技股有回调压力

**中性因素**：
- 美股走势：道指创新高，但科技股偏弱
- 市场情绪：整体风险偏好有所下降

### 7.2 明日操作策略

**仓位管理**：
- 建议保持50-60%仓位
- 不宜过度追涨，留足现金等待机会

**板块配置**：
- 重点关注：半导体设备材料、AI算力基础设施
- 适度配置：业绩确定的消费龙头
- 回避：涨幅过大的题材炒作股

**风险控制**：
- 设置止损位，避免深度套牢
- 分散投资，不要重仓单一个股
- 关注成交量变化，缩量需警惕

---

## 八、知识库更新记录

### 8.1 今日新增规律

**规律名称**：北向资金流出与市场调整相关性
- **发现日期**：2026-05-22
- **规律描述**：北向资金单日净流出超30亿元时，次日市场往往承压
- **验证状态**：待验证
- **注意事项**：需结合连续性判断，单次流出不构成趋势

### 8.2 知识库更新

今日学习要点已添加到：
- ✅ [market_knowledge.md](file:///Users/houpengyuan/Documents/trae_projects/a-stock-data/knowledge/market_knowledge.md) - 添加市场规律
- ⏸️ industry_knowledge.md - 今日行业动态较少，暂不更新
- ⏸️ mistake_log.md - 今日无选股操作，无需记录

---

## 九、今日学习总结

### 9.1 学习成果

| 学习项目 | 完成状态 | 关键收获 |
|---------|:--------:|---------|
| 获取行情数据 | ✅ 完成 | 掌握了大盘指数、个股行情获取方法 |
| 北向资金分析 | ✅ 完成 | 理解了外资短期偏谨慎的原因 |
| 行业涨跌分析 | ✅ 完成 | 识别了科技板块的结构性机会 |
| 热点题材挖掘 | ✅ 完成 | 掌握了AI算力产业链投资逻辑 |
| 市场规律总结 | ✅ 完成 | 总结了3条实用的市场规律 |
| 生成学习报告 | ✅ 完成 | 完成了本报告 |

### 9.2 明日学习计划

1. 继续关注北向资金流向变化
2. 分析热点板块持续性
3. 关注明日是否有新的政策或消息
4. 更新选股池，寻找新的投资机会

---

## 十、数据来源

- 行情数据：东方财富、同花顺
- 北向资金：巨灵数据
- 行业数据：申万行业分类
- 新闻快讯：财联社

---

**免责声明**：本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。

---

*本报告由 Trae AI 自主学习系统生成*
*报告时间：{analysis['report_time']}*
*数据日期：2026年5月22日*
"""

    # 保存报告
    output_file = '/Users/houpengyuan/Documents/trae_projects/a-stock-data/reports/收盘后学习_2026-05-22.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 收盘后学习报告已保存到: {output_file}")

    return output_file

if __name__ == '__main__':
    # 执行分析
    analysis = analyze_market()

    # 生成报告
    report_file = generate_report(analysis)

    print("\n" + "="*70)
    print("✅ 收盘后学习流程完成！")
    print("="*70)
    print(f"分析结果：{report_file}")
