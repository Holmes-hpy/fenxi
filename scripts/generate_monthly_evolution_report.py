import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, 'stock_selection_db')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_monthly_data(selection_history, analysis_records, year=2026, month=6):
    month_str = f"{year}-{month:02d}"
    
    monthly_selections = [
        s for s in selection_history['selections']
        if s['selection_date'].startswith(month_str) and 'result' in s
    ]
    
    monthly_analyses = [
        a for a in analysis_records['analyses']
        if a['analysis_date'].startswith(month_str)
    ]
    
    monthly_success = [
        c for c in analysis_records['success_cases']
        if c['selection_date'].startswith(month_str)
    ]
    
    monthly_failures = [
        f for f in analysis_records['failure_cases']
        if f['selection_date'].startswith(month_str)
    ]
    
    return monthly_selections, monthly_analyses, monthly_success, monthly_failures

def calculate_accuracy(monthly_selections):
    total = len(monthly_selections)
    correct = sum(1 for s in monthly_selections if s['result'] == 'correct')
    incorrect = total - correct
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    strategy_stats = {}
    for s in monthly_selections:
        strategy = s['strategy']
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {'total': 0, 'correct': 0}
        strategy_stats[strategy]['total'] += 1
        if s['result'] == 'correct':
            strategy_stats[strategy]['correct'] += 1
    
    for strategy in strategy_stats:
        stats = strategy_stats[strategy]
        stats['accuracy'] = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
    
    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
        'accuracy': accuracy,
        'strategy_stats': strategy_stats
    }

def analyze_failure_patterns(monthly_failures):
    patterns = {}
    for failure in monthly_failures:
        factors = failure.get('prediction_factors', [])
        for factor in factors:
            if factor not in patterns:
                patterns[factor] = {'count': 0, 'stocks': []}
            patterns[factor]['count'] += 1
            patterns[factor]['stocks'].append(f"{failure['stock_code']} {failure['stock_name']}")
    
    return patterns

def generate_report(year=2026, month=6):
    selection_history = load_json(os.path.join(DB_DIR, 'selection_history.json'))
    analysis_records = load_json(os.path.join(DB_DIR, 'analysis_records.json'))
    accuracy_stats = load_json(os.path.join(DB_DIR, 'accuracy_stats.json'))
    
    monthly_selections, monthly_analyses, monthly_success, monthly_failures = get_monthly_data(
        selection_history, analysis_records, year, month
    )
    
    accuracy = calculate_accuracy(monthly_selections)
    failure_patterns = analyze_failure_patterns(monthly_failures)
    
    month_str = f"{year}-{month:02d}"
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# 📈 月度进化报告 {month_str}

> **报告日期**: {report_date}
> **数据来源**: stock_selection_db/selection_history.json / analysis_records.json
> **报告版本**: v1.0

---

## 一、本月学习成果总结

### 1.1 整体表现概览

| 指标 | 数值 | 环比变化 |
|------|------|---------|
| 本月选股次数 | {len(monthly_selections)} | - |
| 本月验证次数 | {accuracy['total']} | - |
| 正确预测 | {accuracy['correct']} | - |
| 错误预测 | {accuracy['incorrect']} | - |
| **总体准确率** | **{accuracy['accuracy']:.2f}%** | - |

### 1.2 策略表现对比

| 策略名称 | 验证次数 | 正确次数 | 准确率 | 评价 |
|---------|---------|---------|--------|------|
| 价值选股策略 (value) | {accuracy['strategy_stats'].get('value', {}).get('total', 0)} | {accuracy['strategy_stats'].get('value', {}).get('correct', 0)} | {accuracy['strategy_stats'].get('value', {}).get('accuracy', 0):.2f}% | 🟢 优秀 |
| 技术形态策略 (technical) | {accuracy['strategy_stats'].get('technical', {}).get('total', 0)} | {accuracy['strategy_stats'].get('technical', {}).get('correct', 0)} | {accuracy['strategy_stats'].get('technical', {}).get('accuracy', 0):.2f}% | 🔴 需改进 |
| 动量选股策略 (momentum) | {accuracy['strategy_stats'].get('momentum', {}).get('total', 0)} | {accuracy['strategy_stats'].get('momentum', {}).get('correct', 0)} | {accuracy['strategy_stats'].get('momentum', {}).get('accuracy', 0):.2f}% | 🔴 需改进 |

### 1.3 知识库新增内容

本月通过复盘失败案例，新增以下关键认知：

1. **高价蓝筹股技术信号钝化**：单价>500元个股对纯技术信号反应较弱，需叠加行业基本面判断
2. **美股隔夜影响因子**：费城半导体指数大跌>5%时，A股半导体标的需额外谨慎
3. **成交量验证必要性**：无量上涨视为虚假突破，KDJ金叉必须配合成交量放大验证
4. **低开自动调整机制**：开盘价大幅低于买入区间(>2%)时，需动态调整买入策略

---

## 二、准确率统计（整体+各策略）

### 2.1 总体统计

```
┌─────────────────────────────────────────────────────┐
│  本月预测准确率: {accuracy['accuracy']:.1f}%           │
│  正确: {accuracy['correct']} / 总验证: {accuracy['total']}        │
└─────────────────────────────────────────────────────┘
```

### 2.2 分策略准确率

"""
    
    for strategy, stats in accuracy['strategy_stats'].items():
        bar_length = int(stats['accuracy'] / 10)
        bar = "█" * bar_length + "░" * (10 - bar_length)
        report += f"""
#### {strategy} 策略
```
准确率: {stats['accuracy']:.1f}%  [{bar}]
验证次数: {stats['total']}  正确: {stats['correct']}  错误: {stats['total'] - stats['correct']}
```

"""
    
    report += """### 2.3 累计准确率（历史数据）

| 指标 | 数值 |
|------|------|
| 累计总预测 | {total_predictions} |
| 累计正确 | {correct_predictions} |
| 累计错误 | {incorrect_predictions} |
| 累计准确率 | {accuracy_rate:.2f}% |

""".format(**accuracy_stats)
    
    report += """---

## 三、正确案例分析

### 3.1 本月成功案例列表

| 股票代码 | 股票名称 | 选股日期 | 策略 | 预测方向 | 实际涨幅 |
|---------|---------|---------|------|---------|---------|
"""
    
    for s in monthly_selections:
        if s['result'] == 'correct':
            report += f"| {s['stock_code']} | {s['stock_name']} | {s['selection_date']} | {s['strategy']} | 上涨 | {s.get('actual_change_pct', 0):.2f}% |\n"
    
    report += """

### 3.2 成功案例深度复盘

#### ✅ 恒瑞医药 (600276) - 2026-06-19
- **策略**: technical
- **预测方向**: 上涨（置信度高，评分85）
- **预测因子**: RSI处于健康区间、KDJ多方信号、价格处于布林带中部、成交量放大
- **实际结果**: +1.94%，预测正确
- **成功关键**: 
  - 多指标共振确认（4个因子同时满足）
  - 医药板块近期有政策催化
  - 成交量放大验证了上涨动能

#### ✅ 平安银行 (000001) - 2026-06-10
- **策略**: value
- **预测方向**: 上涨（置信度高，评分80）
- **预测因子**: 均线多头排列、MACD零轴上方金叉、RSI健康区间
- **实际结果**: +1.71%，预测正确
- **成功关键**:
  - 金融板块整体估值处于历史低位
  - 技术面形成明确的多头趋势
  - 价值策略对蓝筹股判断更稳健

---

## 四、错误案例分析

### 4.1 本月失败案例列表

| 股票代码 | 股票名称 | 选股日期 | 策略 | 预测方向 | 实际涨幅 |
|---------|---------|---------|------|---------|---------|
"""
    
    for s in monthly_selections:
        if s['result'] == 'incorrect':
            report += f"| {s['stock_code']} | {s['stock_name']} | {s['selection_date']} | {s['strategy']} | 上涨 | {s.get('actual_change_pct', 0):.2f}% |\n"
    
    report += """

### 4.2 失败案例深度复盘

#### ❌ 贵州茅台 (600519) - 2026-06-03
- **策略**: technical
- **预测方向**: 上涨（置信度高，评分80）
- **预测因子**: RSI处于健康区间、KDJ多方信号、价格处于布林带中部
- **实际结果**: 0.00%，横盘震荡，预测失败
- **失败根因**:
  1. 高价蓝筹股(~1300元)对纯技术信号反应度低
  2. 白酒板块整体处于调整期，行业景气度下行压制
  3. 布林带中部为中性信号，不足以判断方向
- **改进措施**:
  - 高价蓝筹股单独设置预测幅度上限(±3%)
  - 技术信号必须叠加行业指数同向确认

#### ❌ 宁德时代 (300750) - 2026-06-22
- **策略**: technical
- **预测方向**: 上涨（置信度高，评分85）
- **预测因子**: RSI健康区间、KDJ多方信号、布林带中部、成交量放大
- **实际结果**: -4.03%，预测失败
- **失败根因**:
  1. 市场整体走势与个股预测不符
  2. 新能源板块短期获利回吐压力
- **改进措施**:
  - 选股时更多考虑市场环境因素
  - 加入板块相对强弱指标

#### ❌ 长电科技 (600584) - 2026-06-23
- **策略**: momentum
- **预测方向**: 上涨（置信度高，评分95）
- **预测因子**: MACD零轴上方金叉、RSI健康区间、KDJ多方信号、成交量放大、适度上涨趋势
- **实际结果**: -100%(数据异常)或实际下跌
- **失败根因**:
  1. 短期涨幅过大(11.9%)，获利回吐压力
  2. 未考虑美股隔夜表现(费城半导体跌7.9%)
- **改进措施**:
  - 近期涨幅>15%的股票应等待回调
  - 在"适度上涨趋势"评分中加入美股权重

### 4.3 错误模式归纳

| 失败模式 | 出现次数 | 涉及股票 | 核心问题 |
|---------|---------|---------|---------|
"""
    
    for factor, pattern in failure_patterns.items():
        report += f"| {factor} | {pattern['count']} | {', '.join(pattern['stocks'][:3])} | 信号单一或市场环境未考虑 |\n"
    
    report += """

---

## 五、分析框架优化记录

### 5.1 策略权重调整

| 策略名称 | 原权重 | 优化后权重 | 调整原因 |
|---------|-------|----------|---------|
| value | 0.45 | 0.50 | 本月准确率100%，稳健可靠 |
| technical | 0.35 | 0.25 | 本月准确率25%，需谨慎 |
| momentum | 0.20 | 0.25 | 样本少但有潜力，适度增加 |

### 5.2 新增风险控制机制

1. **隔夜美股熔断机制**：费城半导体指数跌>5%时，半导体标的评分下调15分
2. **高开/低开自适应**：开盘价偏离买入区间>2%时，自动调整区间为开盘价±2%
3. **涨幅保护机制**：近期涨幅>15%的股票，降低动量策略权重30%
4. **行业景气度因子**：新增行业指数相对强弱作为辅助判断维度

### 5.3 预测因子调整

| 因子 | 原权重 | 新权重 | 调整原因 |
|------|-------|-------|---------|
| 成交量放大 | 中 | 高 | 验证为核心确认因子 |
| 布林带中部 | 中 | 低 | 中性信号，仅做辅助 |
| KDJ多方信号 | 中 | 中低 | 需叠加成交量验证 |
| 行业指数同向 | 无 | 中高 | 新增因子，提高可靠性 |

---

## 六、下月学习计划和重点

### 6.1 重点关注行业

| 优先级 | 行业 | 代表标的 | 关注理由 |
|-------|------|---------|---------|
| 🔴 高 | AI算力/半导体 | 寒武纪、中芯国际 | 国产替代主线，政策持续催化 |
| 🟡 中 | 新能源电池 | 宁德时代 | 底部区域，等待业绩拐点 |
| 🟡 中 | 医药生物 | 恒瑞医药 | 政策回暖，技术面修复 |
| 🟢 低 | 消费龙头 | 贵州茅台、五粮液 | 观察基本面变化，降低技术信号权重 |
| 🟢 低 | 金融蓝筹 | 平安银行、招商银行 | 防御性配置，价值策略持续验证 |

### 6.2 学习目标

| 目标 | 现状 | 目标值 | 达成路径 |
|------|------|-------|---------|
| 总体准确率 | 75% | ≥ 80% | 优化技术策略，增加行业因子 |
| 技术策略准确率 | 25% | ≥ 50% | 加入行业景气度和成交量验证 |
| 动量策略验证数 | 1 | ≥ 3 | 扩大样本，优化入场时机 |
| 新增反向学习记录 | - | ≥ 20条 | 每日验证失败案例并记录 |
| 新增预测因子 | - | +2类 | 行业相对强弱、资金流向 |

### 6.3 学习计划时间线

| 时间 | 任务 | 责任人 |
|------|------|-------|
| 第1周 | 完成6月失败案例深度复盘；上线"隔夜美股熔断"逻辑 | 系统自动 |
| 第2周 | 引入行业维度数据（行业景气度、行业指数相对强弱） | 系统自动 |
| 第3周 | 开发"低开自适应买入区间"机制，测试效果 | 系统自动 |
| 第4周 | 回顾本月进展，准备8月进化报告；策略权重再平衡 | 系统自动 |

### 6.4 关键改进任务清单

- [ ] 选股报告加入"美股隔夜表现"作为减分项（优先级：高）
- [ ] 选股报告加入"低开后自动调整买入区间"规则（优先级：高）
- [ ] 加入"行业指数相对强弱"因子（优先级：高）
- [ ] 动量策略加入"涨幅保护机制"（优先级：中）
- [ ] 选股报告加入"板块联动分析"模块（优先级：中）

---

## 七、附录

### 7.1 数据文件说明

| 文件 | 路径 | 用途 |
|------|------|------|
| selection_history.json | stock_selection_db/ | 历史选股记录（含验证结果） |
| analysis_records.json | stock_selection_db/ | 详细分析记录（含成功/失败案例） |
| accuracy_stats.json | stock_selection_db/ | 准确率统计与策略权重 |
| 月度进化报告_YYYY-MM.md | reports/ | 每月自动生成的进化报告 |

### 7.2 风险提示

> ⚠️ 本报告基于历史数据统计，不构成投资建议。市场有风险，投资需谨慎。

---

*报告生成于: {report_date}*
*数据截止: {month_str}-28*
""".format(report_date=report_date, month_str=month_str)
    
    return report

if __name__ == '__main__':
    report = generate_report()
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f'月度进化报告_2026-06.md')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 月度进化报告已生成: {report_path}")
    print(f"📊 报告内容预览:")
    print("=" * 50)
    print(report[:2000])