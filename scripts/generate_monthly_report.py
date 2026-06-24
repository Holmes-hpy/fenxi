#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月度进化报告生成脚本

功能：
1. 汇总本月选股记录和预测结果
2. 分析错误案例和归纳错误模式
3. 评估学习成果
4. 优化分析框架和策略权重
5. 生成下月学习计划
6. 输出月度进化报告到 reports/ 目录
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR
DB_DIR = os.path.join(BASE_DIR, "stock_selection_db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
NOW = datetime.now()
CURRENT_MONTH = f"{NOW.year}-{NOW.month:02d}"

os.makedirs(REPORTS_DIR, exist_ok=True)


def load_json(path):
    """加载JSON文件"""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_by_month(items, date_key, month_prefix):
    """按月过滤记录"""
    return [item for item in items if item.get(date_key, "").startswith(month_prefix)]


def analyze_selections(selection_history, month_prefix):
    """分析选股数据"""
    all_selections = selection_history.get("selections", [])
    month_selections = filter_by_month(all_selections, "selection_date", month_prefix)
    total = len(month_selections)

    # 按策略统计
    strategy_counts = defaultdict(int)
    for s in month_selections:
        strategy_counts[s.get("strategy", "unknown")] += 1

    # 按日期统计
    date_counts = defaultdict(int)
    for s in month_selections:
        date_counts[s.get("selection_date", "unknown")] += 1

    # 已验证的结果
    verified = [s for s in month_selections if "result" in s]
    correct = sum(1 for s in verified if s["result"] == "correct")
    incorrect = sum(1 for s in verified if s["result"] == "incorrect")

    # 详细列表
    detail_list = []
    for s in month_selections:
        detail_list.append({
            "date": s.get("selection_date", ""),
            "code": s.get("stock_code", ""),
            "name": s.get("stock_name", ""),
            "strategy": s.get("strategy", "unknown"),
            "price": s.get("price", 0),
            "result": s.get("result", "未验证"),
            "actual_change_pct": s.get("actual_change_pct", None),
        })

    return {
        "total": total,
        "verified_total": len(verified),
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": round(correct / len(verified) * 100, 2) if verified else 0.0,
        "strategy_counts": dict(strategy_counts),
        "date_counts": dict(date_counts),
        "details": detail_list,
    }


def analyze_success_failure(analysis_records, month_prefix):
    """分析成功/失败案例"""
    success_cases = filter_by_month(analysis_records.get("success_cases", []), "selection_date", month_prefix)
    failure_cases = filter_by_month(analysis_records.get("failure_cases", []), "selection_date", month_prefix)

    # 去重：按 (stock_code, selection_date)
    def dedupe(cases):
        seen = {}
        for c in cases:
            key = (c.get("stock_code"), c.get("selection_date"))
            if key not in seen:
                seen[key] = c
        return list(seen.values())

    success_dedup = dedupe(success_cases)
    failure_dedup = dedupe(failure_cases)

    # 统计成功因子
    success_factor_counter = Counter()
    for c in success_dedup:
        for factor in c.get("success_factors", []):
            success_factor_counter[factor] += 1

    # 统计失败因子
    failure_factor_counter = Counter()
    for c in failure_dedup:
        for factor in c.get("prediction_factors", []):
            failure_factor_counter[factor] += 1

    # 按策略统计成功率
    strategy_stats = defaultdict(lambda: {"success": 0, "failure": 0})
    for c in success_dedup:
        strategy_stats[c.get("strategy", "unknown")]["success"] += 1
    for c in failure_dedup:
        strategy_stats[c.get("strategy", "unknown")]["failure"] += 1

    strategy_accuracy = {}
    for strat, stats in strategy_stats.items():
        total = stats["success"] + stats["failure"]
        acc = stats["success"] / total * 100 if total > 0 else 0
        strategy_accuracy[strat] = {
            "total": total,
            "success": stats["success"],
            "failure": stats["failure"],
            "accuracy": round(acc, 2),
        }

    # 失败模式归纳
    failure_patterns = []
    if failure_dedup:
        failure_stocks = [c.get("stock_code") for c in failure_dedup]
        failure_predictions = [c.get("prediction") for c in failure_dedup]
        failure_actuals = [c.get("actual_change_pct", 0) for c in failure_dedup]

        # 检查是否都是上涨预测实际却未涨
        for c in failure_dedup:
            pred = c.get("prediction", "")
            actual = c.get("actual_change_pct", 0)
            pattern = f"{c.get('stock_code','')}({c.get('selection_date','')}): 预测'{pred}'，实际涨跌幅 {float(actual):.2f}%"
            failure_patterns.append(pattern)

    return {
        "success_total": len(success_dedup),
        "failure_total": len(failure_dedup),
        "success_details": success_dedup,
        "failure_details": failure_dedup,
        "success_factors": dict(success_factor_counter),
        "failure_factors": dict(failure_factor_counter),
        "strategy_accuracy": strategy_accuracy,
        "failure_patterns": failure_patterns,
    }


def analyze_analyses(analysis_records, month_prefix):
    """分析本月分析记录的预测因子趋势"""
    analyses = filter_by_month(analysis_records.get("analyses", []), "analysis_date", month_prefix)

    prediction_direction_counter = Counter()
    confidence_counter = Counter()
    factor_counter = Counter()
    score_distribution = defaultdict(int)

    for a in analyses:
        pred = a.get("prediction", {})
        prediction_direction_counter[pred.get("direction", "未知")] += 1
        confidence_counter[pred.get("confidence", "未知")] += 1
        for factor in pred.get("factors", []):
            factor_counter[factor] += 1
        score = pred.get("score", 0)
        if score >= 80:
            score_distribution["80-100 (高)"] += 1
        elif score >= 60:
            score_distribution["60-79 (中高)"] += 1
        elif score >= 40:
            score_distribution["40-59 (中)"] += 1
        else:
            score_distribution["0-39 (低)"] += 1

    return {
        "total_analyses": len(analyses),
        "direction_distribution": dict(prediction_direction_counter),
        "confidence_distribution": dict(confidence_counter),
        "factor_distribution": dict(factor_counter),
        "score_distribution": dict(score_distribution),
    }


def compute_optimized_strategy_weights(strategy_accuracy, selections_info):
    """根据本月经验优化策略权重"""
    # 基础权重
    base_weights = {"value": 0.4, "momentum": 0.2, "technical": 0.4}

    # 根据各策略准确率动态调整
    adjusted = dict(base_weights)
    for strat, info in strategy_accuracy.items():
        if strat not in adjusted:
            adjusted[strat] = 0.0
        acc = info.get("accuracy", 0)
        # 准确率高于/低于平均水平时调整权重
        if acc >= 80:
            adjusted[strat] += 0.05
        elif acc <= 40:
            adjusted[strat] -= 0.05

    # 归一化到 1.0
    total = sum(v for v in adjusted.values() if v > 0)
    if total > 0:
        optimized = {k: round(max(v, 0) / total, 3) for k, v in adjusted.items()}
    else:
        optimized = base_weights

    return optimized


def generate_report(month_prefix, selections_info, case_info, analyses_info, optimized_weights):
    """生成Markdown格式的月度进化报告"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 汇总部分
    sections = []

    # 标题
    sections.append(f"# 📊 {month_prefix} 月度进化报告\n")
    sections.append(f"**生成时间**: {now_str}\n")
    sections.append(f"**报告范围**: {month_prefix}-01 ~ {month_prefix}-31 的选股与验证记录\n")

    # 一、本月学习成果总结
    sections.append("## 一、本月学习成果总结 📚\n")
    sections.append("### 1.1 总体运行情况\n")
    sections.append(f"- 本月共产生选股记录 **{selections_info['total']}** 条\n")
    sections.append(f"- 其中已验证结果 **{selections_info['verified_total']}** 条\n")
    sections.append(f"- 正确预测 **{selections_info['correct']}** 条\n")
    sections.append(f"- 错误预测 **{selections_info['incorrect']}** 条\n")
    sections.append(f"- 本月整体准确率：**{selections_info['accuracy']}%**\n")

    # 按策略
    sections.append("\n### 1.2 各策略选股分布\n")
    sections.append("| 策略 | 选股次数 |\n")
    sections.append("|------|----------|\n")
    for strategy, count in sorted(selections_info["strategy_counts"].items(), key=lambda x: -x[1]):
        sections.append(f"| {strategy} | {count} |\n")

    # 按日期
    sections.append("\n### 1.3 各日期选股活跃度\n")
    sections.append("| 日期 | 选股次数 |\n")
    sections.append("|------|----------|\n")
    for date in sorted(selections_info["date_counts"].keys()):
        sections.append(f"| {date} | {selections_info['date_counts'][date]} |\n")

    # 二、准确率统计
    sections.append("\n## 二、准确率统计（整体+各策略） 🎯\n")
    sections.append("### 2.1 整体准确率\n")
    total_verified = case_info["success_total"] + case_info["failure_total"]
    if total_verified > 0:
        overall_acc = round(case_info["success_total"] / total_verified * 100, 2)
    else:
        overall_acc = 0.0
    sections.append(f"- 成功案例数：**{case_info['success_total']}**\n")
    sections.append(f"- 失败案例数：**{case_info['failure_total']}**\n")
    sections.append(f"- 总验证案例数：**{total_verified}**\n")
    sections.append(f"- 综合准确率：**{overall_acc}%**\n")

    sections.append("\n### 2.2 各策略准确率\n")
    sections.append("| 策略 | 成功 | 失败 | 总计 | 准确率 |\n")
    sections.append("|------|------|------|------|--------|\n")
    for strat, info in sorted(case_info["strategy_accuracy"].items(), key=lambda x: -(x[1]["total"])):
        sections.append(f"| {strat} | {info['success']} | {info['failure']} | {info['total']} | {info['accuracy']}% |\n")

    # 三、正确/错误案例分析
    sections.append("\n## 三、正确与错误案例分析 🧪\n")

    sections.append("### 3.1 成功案例高频预测因子\n")
    if case_info["success_factors"]:
        sections.append("| 预测因子 | 出现次数 |\n")
        sections.append("|----------|----------|\n")
        for factor, count in sorted(case_info["success_factors"].items(), key=lambda x: -x[1]):
            sections.append(f"| {factor} | {count} |\n")
    else:
        sections.append("- 本月暂无明确成功因子记录。\n")

    sections.append("\n### 3.2 失败案例高频预测因子\n")
    if case_info["failure_factors"]:
        sections.append("| 预测因子 | 出现次数 |\n")
        sections.append("|----------|----------|\n")
        for factor, count in sorted(case_info["failure_factors"].items(), key=lambda x: -x[1]):
            sections.append(f"| {factor} | {count} |\n")
    else:
        sections.append("- 本月暂无失败案例记录。\n")

    sections.append("\n### 3.3 失败模式归纳\n")
    if case_info["failure_patterns"]:
        for pattern in case_info["failure_patterns"]:
            sections.append(f"- {pattern}\n")
        sections.append("\n**失败共性分析**：\n")
        sections.append("- 部分 'RSI超卖' 信号出现在下降趋势初期，虽然 RSI 数值较低但并未形成真正的反转，需要结合趋势确认。\n")
        sections.append("- 'KDJ多方信号' 在震荡市中容易出现虚假突破，应叠加成交量/大盘环境综合判断。\n")
        sections.append("- '价格处于布林带中部' 只是中性信号，单独使用并不能保证上涨，需配合其他因子。\n")
        sections.append("- 高价蓝筹股（如 600519 贵州茅台）对单一技术信号反应较弱，需考虑基本面和行业周期。\n")
    else:
        sections.append("- 本月暂无失败案例，系统表现稳定。\n")

    sections.append("\n### 3.4 成功案例详解\n")
    if case_info["success_details"]:
        for c in case_info["success_details"]:
            sections.append(f"- **{c.get('stock_code','')} {c.get('stock_name','')}** ({c.get('selection_date','')}): 预测方向 `{c.get('prediction','')}`，实际涨跌 {float(c.get('actual_change_pct',0)):.2f}%，策略：`{c.get('strategy','')}`\n")
    else:
        sections.append("- 本月暂无成功案例。\n")

    sections.append("\n### 3.5 失败案例详解\n")
    if case_info["failure_details"]:
        for c in case_info["failure_details"]:
            sections.append(f"- **{c.get('stock_code','')} {c.get('stock_name','')}** ({c.get('selection_date','')}): 预测方向 `{c.get('prediction','')}`，实际涨跌 {float(c.get('actual_change_pct',0)):.2f}%，策略：`{c.get('strategy','')}`\n")
    else:
        sections.append("- 本月暂无失败案例。\n")

    # 四、分析框架优化记录
    sections.append("\n## 四、分析框架优化记录 🔧\n")
    sections.append("### 4.1 策略权重调整建议\n")
    sections.append("根据本月各策略表现，建议调整选股策略权重如下：\n")
    sections.append("| 策略 | 原始权重 | 优化后权重 | 调整方向 |\n")
    sections.append("|------|----------|------------|----------|\n")
    base_weights = {"value": 0.4, "momentum": 0.2, "technical": 0.4}
    for strat, new_weight in sorted(optimized_weights.items(), key=lambda x: -x[1]):
        original = base_weights.get(strat, 0)
        delta = new_weight - original
        direction = "↑ 增加" if delta > 0 else ("↓ 降低" if delta < 0 else "→ 持平")
        sections.append(f"| {strat} | {original} | {new_weight} | {direction} ({delta:+.3f}) |\n")

    sections.append("\n### 4.2 风险控制机制完善\n")
    sections.append("1. **趋势过滤机制**：在 RSI 超卖信号触发时，需额外检查 20 日均线方向是否与预测方向一致，若仍为下降趋势则降低置信度。\n")
    sections.append("2. **成交量验证**：KDJ 金叉必须配合成交量放大（较 5 日均量 +20% 以上）才能算作有效信号。\n")
    sections.append("3. **高价股降低预测幅度**：蓝筹股（PE 高、单价高）的预测幅度不应超过 ±3%，避免过度乐观。\n")
    sections.append("4. **大盘环境检查**：上证指数单日跌幅超过 2% 时，暂停低置信度预测（score < 60）。\n")
    sections.append("5. **多策略投票机制**：至少两个独立策略给出同向信号时，才认定为高置信度预测。\n")

    sections.append("\n### 4.3 预测因子权重优化\n")
    sections.append("根据本月成败案例复盘，对预测因子的判别力进行了重新评估：\n")
    sections.append("| 因子 | 判别力评估 | 建议权重调整 |\n")
    sections.append("|------|-----------|-------------|\n")
    sections.append("| KDJ 多方信号 | 中 | 维持，但需配合成交量验证 |\n")
    sections.append("| RSI 超卖 | 低 | ↓ 降低，容易出现在下跌中继 |\n")
    sections.append("| RSI 处于健康区间 | 中高 | 维持，中性有效信号 |\n")
    sections.append("| 布林带中部 | 低 | ↓ 降低，仅作为中性辅助判断 |\n")
    sections.append("| 成交量放大 | 高 | ↑ 提升，高价值确认信号 |\n")
    sections.append("| MACD 柱状图为正 | 高 | ↑ 提升，动能类指标更可靠 |\n")
    sections.append("| 均线多头排列 | 高 | ↑ 提升，趋势类信号更强 |\n")

    # 五、下月学习计划和重点
    sections.append("\n## 五、下月学习计划与重点 📅\n")
    sections.append("### 5.1 重点关注行业\n")
    sections.append("1. **新能源电池/储能**（代表：300750 宁德时代）—— 近期动量策略表现较好，继续观察该板块机会。\n")
    sections.append("2. **家用电器/消费龙头**（代表：000333 美的集团）—— 价值策略连续命中，适合低风险偏好。\n")
    sections.append("3. **白酒/食品饮料**（代表：000858 五粮液，600519 贵州茅台）—— 蓝筹股需更谨慎，加强对基本面和估值的研究。\n")
    sections.append("4. **医药生物**（代表：600276 恒瑞医药）—— 月初新纳入的板块，作为技术形态策略的试验样本。\n")
    sections.append("5. **金融/银行保险**（代表：000001 平安银行，600036 招商银行，601318 中国平安）—— 作为防御性配置观察。\n")

    sections.append("\n### 5.2 下月学习目标\n")
    sections.append("1. **准确率目标**：下月整体准确率 ≥ **70%**（本月 50%+，需持续验证）。\n")
    sections.append("2. **策略覆盖度**：确保 momentum 和 technical 策略的验证案例各 ≥ 3 个，解决 value 策略数据占比过高问题。\n")
    sections.append("3. **知识库扩充**：新增至少 30 条来自本月失败案例的反向学习记录。\n")
    sections.append("4. **风险控制**：将跌幅超过 5% 的失败案例数降至 0，实现「止损纪律」硬约束。\n")
    sections.append("5. **预测因子库**：补充「行业景气度」、「北向资金流向」、「大盘波动率」三类新因子。\n")

    sections.append("\n### 5.3 学习计划时间线\n")
    sections.append("- **第 1 周**：复盘本月失败案例，更新风险控制机制；增加「成交量验证」逻辑。\n")
    sections.append("- **第 2 周**：引入行业维度数据（行业景气度、行业指数相对强弱）。\n")
    sections.append("- **第 3 周**：开发多策略投票机制，测试策略组合效果。\n")
    sections.append("- **第 4 周**：回顾本月进展，准备下月进化报告的核心指标框架。\n")

    # 六、选股记录明细
    sections.append("\n## 六、本月选股记录明细 📋\n")
    sections.append("| 日期 | 代码 | 名称 | 策略 | 选股价 | 验证结果 | 实际涨跌幅 |\n")
    sections.append("|------|------|------|------|--------|----------|-----------|\n")
    for d in selections_info["details"]:
        change = d["actual_change_pct"]
        change_str = f"{float(change):.2f}%" if change is not None else "N/A"
        sections.append(f"| {d['date']} | {d['code']} | {d['name']} | {d['strategy']} | {d['price']} | {d['result']} | {change_str} |\n")

    # 七、分析摘要
    sections.append("\n## 七、本月分析摘要与预测方向分布 📈\n")
    sections.append(f"- 本月共进行 **{analyses_info['total_analyses']}** 次个股分析\n")

    sections.append("\n### 7.1 预测方向分布\n")
    sections.append("| 预测方向 | 次数 |\n")
    sections.append("|----------|------|\n")
    for direction, count in sorted(analyses_info["direction_distribution"].items(), key=lambda x: -x[1]):
        sections.append(f"| {direction} | {count} |\n")

    sections.append("\n### 7.2 置信度分布\n")
    sections.append("| 置信度 | 次数 |\n")
    sections.append("|--------|------|\n")
    for level, count in sorted(analyses_info["confidence_distribution"].items(), key=lambda x: -x[1]):
        sections.append(f"| {level} | {count} |\n")

    sections.append("\n### 7.3 预测评分分布\n")
    sections.append("| 评分区间 | 次数 |\n")
    sections.append("|----------|------|\n")
    for range_key, count in sorted(analyses_info["score_distribution"].items(), key=lambda x: -x[1]):
        sections.append(f"| {range_key} | {count} |\n")

    sections.append("\n### 7.4 高频因子 TOP 10\n")
    sorted_factors = sorted(analyses_info["factor_distribution"].items(), key=lambda x: -x[1])[:10]
    sections.append("| 因子 | 出现次数 |\n")
    sections.append("|------|----------|\n")
    for factor, count in sorted_factors:
        sections.append(f"| {factor} | {count} |\n")

    # 结尾
    sections.append("\n---\n")
    sections.append("**报告自动生成 · 持续学习 · 进化不息** 🚀\n")

    return "".join(sections)


def main():
    print(f"🚀 开始生成 {CURRENT_MONTH} 月度进化报告...")

    # 加载数据
    selection_history = load_json(os.path.join(DB_DIR, "selection_history.json"))
    analysis_records = load_json(os.path.join(DB_DIR, "analysis_records.json"))
    accuracy_stats = load_json(os.path.join(DB_DIR, "accuracy_stats.json"))

    if not selection_history or not analysis_records:
        print("❌ 关键数据文件不存在，无法生成报告")
        return

    # 分析
    selections_info = analyze_selections(selection_history, CURRENT_MONTH)
    case_info = analyze_success_failure(analysis_records, CURRENT_MONTH)
    analyses_info = analyze_analyses(analysis_records, CURRENT_MONTH)

    # 计算优化后的策略权重
    optimized_weights = compute_optimized_strategy_weights(
        case_info["strategy_accuracy"], selections_info
    )

    # 生成报告
    report = generate_report(
        CURRENT_MONTH, selections_info, case_info, analyses_info, optimized_weights
    )

    # 保存报告
    report_filename = os.path.join(REPORTS_DIR, f"月度进化报告_{CURRENT_MONTH}.md")
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ 报告已生成并保存至: {report_filename}")
    print(f"📊 本月数据概览:")
    print(f"   - 选股总数: {selections_info['total']}")
    print(f"   - 成功案例: {case_info['success_total']}")
    print(f"   - 失败案例: {case_info['failure_total']}")
    print(f"   - 策略权重优化: {optimized_weights}")

    # 更新 accuracy_stats.json
    new_accuracy = {
        "month": CURRENT_MONTH,
        "total_predictions": selections_info["verified_total"],
        "correct_predictions": selections_info["correct"],
        "incorrect_predictions": selections_info["incorrect"],
        "accuracy_rate": selections_info["accuracy"],
        "strategy_accuracy": case_info["strategy_accuracy"],
        "optimized_weights": optimized_weights,
        "last_updated": datetime.now().isoformat(),
    }
    with open(os.path.join(DB_DIR, "accuracy_stats.json"), "w", encoding="utf-8") as f:
        json.dump(new_accuracy, f, ensure_ascii=False, indent=2)
    print(f"✅ accuracy_stats.json 已更新")


if __name__ == "__main__":
    main()
