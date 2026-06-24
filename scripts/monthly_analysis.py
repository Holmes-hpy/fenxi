#!/usr/bin/env python3
"""月度数据分析脚本"""

import json
from collections import defaultdict
from datetime import datetime

DATA_DIR = "/Users/houpengyuan/Documents/trae_projects/a-stock-data"

# 读取数据
with open(f"{DATA_DIR}/stock_selection_db/selection_history.json", "r", encoding="utf-8") as f:
    selection_history = json.load(f)

with open(f"{DATA_DIR}/stock_selection_db/analysis_records.json", "r", encoding="utf-8") as f:
    analysis_records = json.load(f)

with open(f"{DATA_DIR}/stock_selection_db/accuracy_stats.json", "r", encoding="utf-8") as f:
    accuracy_stats = json.load(f)

# ============= 5月份选股统计 =============
may_selections = [s for s in selection_history.get("selections", []) 
                  if s.get("selection_date", "").startswith("2026-05")]

print("=" * 60)
print("5月份选股记录统计")
print("=" * 60)
print(f"5月选股总次数: {len(may_selections)}")

# 按策略统计
strategy_counts = defaultdict(int)
for s in may_selections:
    strategy_counts[s.get("strategy", "unknown")] += 1

print("\n按策略分布:")
for strategy, count in sorted(strategy_counts.items(), key=lambda x: -x[1]):
    print(f"  {strategy}: {count}次")

# 按日期统计
date_counts = defaultdict(int)
for s in may_selections:
    date_counts[s.get("selection_date", "unknown")] += 1

print("\n按日期分布:")
for date in sorted(date_counts.keys()):
    print(f"  {date}: {date_counts[date]}次")

# 详细记录
print("\n选股详情:")
for s in may_selections:
    result = s.get("result", "未验证")
    actual = s.get("actual_change_pct", "N/A")
    print(f"  {s['selection_date']} {s['stock_code']} {s.get('stock_name','')} "
          f"策略:{s.get('strategy')} 结果:{result} 实际涨跌:{actual}")

# ============= 验证结果统计 =============
print("\n" + "=" * 60)
print("5月选股验证结果分析")
print("=" * 60)

# 从 selection_history 提取已验证的5月选股
verified_may = [s for s in may_selections if "result" in s]
print(f"已验证的5月选股: {len(verified_may)}次")
for s in verified_may:
    print(f"  {s['stock_code']} 预测结果: {s['result']} 实际涨跌: {s['actual_change_pct']:.4f}%")

# 从 analysis_records 提取成功/失败案例（5月选股的）
success_cases = [c for c in analysis_records.get("success_cases", [])
                 if c.get("selection_date", "").startswith("2026-05")]
failure_cases = [c for c in analysis_records.get("failure_cases", [])
                 if c.get("selection_date", "").startswith("2026-05")]

print(f"\nsuccess_cases中5月选股成功: {len(success_cases)}次")
for c in success_cases:
    print(f"  {c['stock_code']} 预测:{c['prediction']} 实际:{c['actual_change_pct']:.4f}% 策略:{c.get('strategy','')}")

print(f"\nfailure_cases中5月选股失败: {len(failure_cases)}次")
for c in failure_cases:
    print(f"  {c['stock_code']} 预测:{c['prediction']} 实际:{c['actual_change_pct']:.4f}% 策略:{c.get('strategy','')}")

# 去重统计（按股票+日期唯一识别）
def unique_key(c):
    return f"{c.get('stock_code')}_{c.get('selection_date')}"

unique_success = {}
for c in success_cases:
    key = unique_key(c)
    if key not in unique_success:
        unique_success[key] = c

unique_failure = {}
for c in failure_cases:
    key = unique_key(c)
    if key not in unique_failure:
        unique_failure[key] = c

# 同时出现在成功和失败中的需要检查
all_keys = set(list(unique_success.keys()) + list(unique_failure.keys()))
print(f"\n去重后唯一案例数: {len(all_keys)}")
for key in all_keys:
    in_success = key in unique_success
    in_failure = key in unique_failure
    if in_success and in_failure:
        print(f"  {key}: 同时在成功和失败列表中（不同时间窗口的验证）")
    elif in_success:
        print(f"  {key}: 成功")
    else:
        print(f"  {key}: 失败")

# 综合准确率
total_verified = len(all_keys)
correct_count = len(unique_success)
incorrect_count = len(unique_failure)
# 如果有重叠，取最后验证的结果为准
overlap_keys = set(unique_success.keys()) & set(unique_failure.keys())
if overlap_keys:
    print(f"\n⚠️ 注意：有{len(overlap_keys)}条记录同时出现在成功和失败案例中")
    for key in overlap_keys:
        print(f"  - {key}")

# 更准确的计算：取success和failure的并集
# 如果同一股票同时在两个列表，说明是不同时间点的验证，都算一次独立验证
print("\n" + "=" * 60)
print("准确率计算")
print("=" * 60)

# 方法1：基于去重的唯一key（成功案例为主）
total_unique = len(set(list(unique_success.keys()) + list(unique_failure.keys())))
# 计算成功率：成功案例数 / 总验证数（注意去重）
actual_success = len(unique_success) - len(overlap_keys)  # 纯成功
actual_failure = len(unique_failure) - len(overlap_keys)   # 纯失败
mixed = len(overlap_keys)  # 混合（不同时间窗口）

print(f"纯成功: {actual_success}")
print(f"纯失败: {actual_failure}")
print(f"混合验证: {mixed}（同一股票不同时间窗口有不同结果）")
print(f"总验证案例: {actual_success + actual_failure + mixed}")

if (actual_success + actual_failure + mixed) > 0:
    # 混合案例按"部分正确"处理，成功率按50%估算
    # 或者更保守：混合案例算半个成功
    adjusted_correct = actual_success + mixed * 0.5
    accuracy = adjusted_correct / (actual_success + actual_failure + mixed) * 100
    print(f"\n保守估算准确率: {accuracy:.1f}%")
    
    # 另一种算法：纯成功/(纯成功+纯失败)
    if (actual_success + actual_failure) > 0:
        accuracy2 = actual_success / (actual_success + actual_failure) * 100
        print(f"纯成功率（排除混合）: {accuracy2:.1f}%")

# ============= 按策略准确率 =============
print("\n" + "=" * 60)
print("各策略准确率")
print("=" * 60)

strategy_stats = defaultdict(lambda: {"success": 0, "failure": 0})

for c in success_cases:
    strat = c.get("strategy", "unknown")
    strategy_stats[strat]["success"] += 1

for c in failure_cases:
    strat = c.get("strategy", "unknown")
    strategy_stats[strat]["failure"] += 1

for strat, stats in sorted(strategy_stats.items(), key=lambda x: -(x[1]["success"] + x[1]["failure"])):
    total = stats["success"] + stats["failure"]
    acc = stats["success"] / total * 100 if total > 0 else 0
    print(f"  {strat}: 成功{stats['success']}次, 失败{stats['failure']}次, 准确率{acc:.1f}%")

# ============= 预测因子分析 =============
print("\n" + "=" * 60)
print("成功/失败案例预测因子分析")
print("=" * 60)

success_factors = defaultdict(int)
for c in success_cases:
    for factor in c.get("success_factors", []):
        success_factors[factor] += 1

failure_factors = defaultdict(int)
for c in failure_cases:
    for factor in c.get("prediction_factors", []):
        failure_factors[factor] += 1

print("\n成功案例高频因子:")
for factor, count in sorted(success_factors.items(), key=lambda x: -x[1]):
    print(f"  {factor}: {count}次")

print("\n失败案例高频因子:")
for factor, count in sorted(failure_factors.items(), key=lambda x: -x[1]):
    print(f"  {factor}: {count}次")

# ============= 5月分析记录详情 =============
print("\n" + "=" * 60)
print("5月份分析记录详情")
print("=" * 60)

may_analyses = [a for a in analysis_records.get("analyses", [])
                if a.get("analysis_date", "").startswith("2026-05")]

print(f"5月共{len(may_analyses)}条分析记录")
for a in may_analyses:
    pred = a.get("prediction", {})
    print(f"\n  {a['analysis_date']} {a.get('stock_code','')} {a.get('stock_name','')}")
    print(f"    预测方向: {pred.get('direction','')} 分数: {pred.get('score','')} "
          f"预期涨跌: {pred.get('predicted_change_pct','')}%")
    print(f"    预测因子: {pred.get('factors', [])}")

print("\n" + "=" * 60)
print("accuracy_stats.json 当前数据")
print("=" * 60)
print(json.dumps(accuracy_stats, ensure_ascii=False, indent=2))
