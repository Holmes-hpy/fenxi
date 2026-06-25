"""
Serenity每日选股执行脚本
基于Serenity瓶颈投资分析框架进行系统化选股

执行流程：
1. 从产业链数据库筛选候选瓶颈环节
2. 对候选环节进行物理四问评分
3. 匹配活跃策略并确定选股标的
4. 记录选股决策并生成报告
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serenity_chain_database import get_chain_database, ChokepointData
from serenity_daily_stock_picker import DailyStockPicker, StrategyStatus
from serenity_enhanced_analyzer import SerenityEnhancedAnalyzer


class SerenityDailyStockSelection:
    """Serenity每日选股执行引擎"""

    def __init__(self):
        self.chain_db = get_chain_database()
        self.picker = DailyStockPicker()
        self.analyzer = SerenityEnhancedAnalyzer()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def calculate_physical_four_questions_score(self, chokepoint: ChokepointData) -> dict:
        """
        计算物理四问评分

        物理四问（一票否决制）：
        Q1: 是否每单位终端产品必需？
        Q2: 3年内是否有成熟替代？
        Q3: 缺了是否会导致产线停摆？
        Q4: 成本占比是否足够重要？

        每问通过得25分，总分100分
        """
        scores = {}

        # Q1: 每单位必需性
        q1_score = 25 if chokepoint.required_per_unit else 0
        scores["Q1_每单位必需"] = {
            "score": q1_score,
            "passed": chokepoint.required_per_unit,
            "reason": f"必需性={chokepoint.required_per_unit}"
        }

        # Q2: 替代可能性
        q2_score = 25 if chokepoint.no_substitute_3y else 0
        scores["Q2_无成熟替代"] = {
            "score": q2_score,
            "passed": chokepoint.no_substitute_3y,
            "reason": f"3年内无替代={chokepoint.no_substitute_3y}"
        }

        # Q3: 失效影响（产线停摆）
        # 根据failure_impact判断是否导致产线停摆
        critical_keywords = ["停摆", "报废", "无法", "完全"]
        is_critical = any(kw in chokepoint.failure_impact for kw in critical_keywords)
        q3_score = 25 if is_critical else 15
        scores["Q3_失效影响"] = {
            "score": q3_score,
            "passed": is_critical,
            "reason": chokepoint.failure_impact[:50]
        }

        # Q4: 成本占比
        # 成本占比>=2%为重要
        q4_score = 25 if chokepoint.cost_ratio >= 2.0 else 15
        scores["Q4_成本占比"] = {
            "score": q4_score,
            "passed": chokepoint.cost_ratio >= 2.0,
            "reason": f"成本占比={chokepoint.cost_ratio}%"
        }

        # 总分
        total_score = sum(s["score"] for s in scores.values())

        # 一票否决检查
        veto_failed = [q for q, s in scores.items() if not s["passed"]]
        is_veto_passed = len(veto_failed) == 0

        return {
            "chokepoint_name": chokepoint.name,
            "scores": scores,
            "total_score": total_score,
            "is_veto_passed": is_veto_passed,
            "veto_failed": veto_failed,
            "chain_position": chokepoint.chain_position,
            "layer_num": chokepoint.layer_num,
        }

    def calculate_supply_rigidity_score(self, chokepoint: ChokepointData) -> dict:
        """
        计算供给刚性评分

        供给刚性维度：
        - 全球合格供应商数量（越少越好）
        - 行业CR3集中度（越高越好）
        - 产能利用率（越高越好）
        - 产能扩张周期（越长越好）
        - 设备交付周期（越长越好）
        """
        scores = {}

        # 供应商数量评分（<5个=高分）
        supplier_score = 25 if chokepoint.global_suppliers <= 5 else 15 if chokepoint.global_suppliers <= 10 else 5
        scores["供应商稀缺度"] = {
            "score": supplier_score,
            "value": chokepoint.global_suppliers,
            "reason": f"全球合格供应商={chokepoint.global_suppliers}个"
        }

        # CR3集中度评分（>=80%=高分）
        cr3_score = 25 if chokepoint.industry_cr3 >= 80 else 15 if chokepoint.industry_cr3 >= 60 else 5
        scores["行业集中度"] = {
            "score": cr3_score,
            "value": chokepoint.industry_cr3,
            "reason": f"CR3={chokepoint.industry_cr3}%"
        }

        # 产能利用率评分（>=85%=高分）
        util_score = 25 if chokepoint.capacity_util >= 85 else 15 if chokepoint.capacity_util >= 70 else 5
        scores["产能利用率"] = {
            "score": util_score,
            "value": chokepoint.capacity_util,
            "reason": f"产能利用率={chokepoint.capacity_util}%"
        }

        # 扩张周期评分（>=18个月=高分）
        expansion_score = 25 if chokepoint.expansion_cycle >= 18 else 15 if chokepoint.expansion_cycle >= 12 else 5
        scores["扩张周期"] = {
            "score": expansion_score,
            "value": chokepoint.expansion_cycle,
            "reason": f"产能扩张周期={chokepoint.expansion_cycle}月"
        }

        # 设备交付周期评分（>=12个月=高分）
        equipment_score = 25 if chokepoint.equipment_lead_time >= 12 else 15 if chokepoint.equipment_lead_time >= 6 else 5
        scores["设备交付周期"] = {
            "score": equipment_score,
            "value": chokepoint.equipment_lead_time,
            "reason": f"设备交付周期={chokepoint.equipment_lead_time}月"
        }

        total_score = sum(s["score"] for s in scores.values())

        return {
            "chokepoint_name": chokepoint.name,
            "scores": scores,
            "total_score": total_score,
            "avg_score": total_score / 5,
        }

    def calculate_market_neglect_score(self, chokepoint: ChokepointData) -> dict:
        """
        计算市场忽视度评分

        市场忽视维度：
        - 市值区间（中小市值=被忽视）
        - 券商覆盖数（少=被忽视）
        - 机构持仓占比（低=被忽视）
        - 近期涨幅（低=未被炒作）
        """
        scores = {}

        # 市值评分（30-200亿=中等关注度）
        avg_mktcap = (chokepoint.mktcap_min + chokepoint.mktcap_max) / 2
        mktcap_score = 25 if avg_mktcap <= 100 else 15 if avg_mktcap <= 200 else 5
        scores["市值规模"] = {
            "score": mktcap_score,
            "value": avg_mktcap,
            "reason": f"市值区间={chokepoint.mktcap_min}-{chokepoint.mktcap_max}亿"
        }

        # 券商覆盖评分（<10家=被忽视）
        broker_score = 25 if chokepoint.covered_brokers <= 10 else 15 if chokepoint.covered_brokers <= 20 else 5
        scores["券商覆盖"] = {
            "score": broker_score,
            "value": chokepoint.covered_brokers,
            "reason": f"近3月覆盖券商={chokepoint.covered_brokers}家"
        }

        # 机构持仓评分（<5%=被忽视）
        fund_score = 25 if chokepoint.fund_holding <= 5 else 15 if chokepoint.fund_holding <= 10 else 5
        scores["机构持仓"] = {
            "score": fund_score,
            "value": chokepoint.fund_holding,
            "reason": f"公募+北向持仓={chokepoint.fund_holding}%"
        }

        # 近期涨幅评分（<30%=未被炒作）
        gain_score = 25 if chokepoint.recent_gain_6m <= 30 else 15 if chokepoint.recent_gain_6m <= 50 else 5
        scores["近期涨幅"] = {
            "score": gain_score,
            "value": chokepoint.recent_gain_6m,
            "reason": f"近6月涨幅={chokepoint.recent_gain_6m}%"
        }

        total_score = sum(s["score"] for s in scores.values())

        return {
            "chokepoint_name": chokepoint.name,
            "scores": scores,
            "total_score": total_score,
            "avg_score": total_score / 4,
        }

    def calculate_comprehensive_score(self, chokepoint: ChokepointData) -> dict:
        """
        计算综合评分

        综合评分 = 物理四问(40%) + 供给刚性(30%) + 市场忽视(20%) + 国产化空间(10%)
        """
        physical = self.calculate_physical_four_questions_score(chokepoint)
        supply = self.calculate_supply_rigidity_score(chokepoint)
        neglect = self.calculate_market_neglect_score(chokepoint)

        # 国产化空间评分（国产化率越低=空间越大）
        localization_score = 25 if chokepoint.localization_rate <= 10 else 15 if chokepoint.localization_rate <= 30 else 5

        # 综合评分
        comprehensive_score = (
            physical["total_score"] * 0.4 +
            supply["total_score"] * 0.3 +
            neglect["total_score"] * 0.2 +
            localization_score * 0.1
        )

        return {
            "chokepoint_name": chokepoint.name,
            "chain_position": chokepoint.chain_position,
            "layer_num": chokepoint.layer_num,
            "physical_score": physical["total_score"],
            "physical_veto_passed": physical["is_veto_passed"],
            "supply_score": supply["total_score"],
            "neglect_score": neglect["total_score"],
            "localization_rate": chokepoint.localization_rate,
            "localization_score": localization_score,
            "comprehensive_score": comprehensive_score,
            "representative_stocks": chokepoint.representative_stocks,
            "failure_impact": chokepoint.failure_impact,
            "physical_details": physical,
            "supply_details": supply,
            "neglect_details": neglect,
        }

    def screen_candidates(self, min_score: float = 70.0) -> list:
        """
        筛选候选瓶颈环节

        筛选条件：
        1. 物理四问一票否决必须通过
        2. 综合评分>=70分
        """
        candidates = []

        # 从所有赛道获取候选
        for track_name in self.chain_db.get_all_tracks():
            track = self.chain_db.get_track(track_name)
            if not track:
                continue

            for chokepoint in track.chokepoint_candidates:
                score_result = self.calculate_comprehensive_score(chokepoint)

                # 一票否决检查
                if not score_result["physical_veto_passed"]:
                    continue

                # 综合评分检查
                if score_result["comprehensive_score"] >= min_score:
                    score_result["track_name"] = track_name
                    score_result["track_trend_type"] = track.trend_type
                    score_result["track_certainty"] = track.certainty
                    candidates.append(score_result)

        # 按综合评分排序
        candidates.sort(key=lambda x: -x["comprehensive_score"])

        return candidates

    def match_strategies(self, candidates: list) -> list:
        """
        匹配活跃策略

        策略匹配逻辑：
        - S001 瓶颈选股-等权策略：物理四问>=70 + 综合评分>=70
        - S002 认知差修复策略：市场忽视度>=60 + 有催化剂
        - S003 事件驱动策略：重大事件驱动 + 供给刚性高
        - S004 产业趋势策略：产业趋势明确 + 国产化空间大
        - S005 低估值修复策略：市值中等 + 涨幅低
        """
        matched_selections = []

        active_strategies = self.picker.strategy_mgr.get_active_strategies()

        for candidate in candidates:
            matched_strategies = []

            # S001: 瓶颈选股-等权策略
            if candidate["comprehensive_score"] >= 70:
                matched_strategies.append({
                    "strategy_id": "S001",
                    "strategy_name": "瓶颈选股-等权策略",
                    "match_reason": f"物理四问通过，综合评分{candidate['comprehensive_score']:.1f}分",
                    "priority": 1,
                })

            # S002: 认知差修复策略
            if candidate["neglect_score"] >= 60:
                matched_strategies.append({
                    "strategy_id": "S002",
                    "strategy_name": "认知差修复策略",
                    "match_reason": f"市场忽视度{candidate['neglect_score']:.1f}分，认知差空间大",
                    "priority": 2,
                })

            # S003: 事件驱动策略（假设有重大事件，如日本封锁）
            # 根据国产化率判断是否有外部驱动
            if candidate["localization_rate"] <= 20 and candidate["supply_score"] >= 80:
                matched_strategies.append({
                    "strategy_id": "S003",
                    "strategy_name": "事件驱动策略",
                    "match_reason": f"国产化率仅{candidate['localization_rate']}%，供给刚性{candidate['supply_score']:.1f}分",
                    "priority": 3,
                })

            # S004: 产业趋势策略
            if candidate["track_certainty"] == "高" and candidate["localization_rate"] <= 30:
                matched_strategies.append({
                    "strategy_id": "S004",
                    "strategy_name": "产业趋势策略",
                    "match_reason": f"产业确定性高，国产化空间{100-candidate['localization_rate']}%",
                    "priority": 4,
                })

            # 为每个代表股票创建选股候选
            for stock in candidate["representative_stocks"]:
                for strategy in matched_strategies:
                    matched_selections.append({
                        "stock_code": stock["code"],
                        "stock_name": stock["name"],
                        "strategy_id": strategy["strategy_id"],
                        "strategy_name": strategy["strategy_name"],
                        "match_reason": strategy["match_reason"],
                        "chokepoint_name": candidate["chokepoint_name"],
                        "chain_position": candidate["chain_position"],
                        "track_name": candidate["track_name"],
                        "comprehensive_score": candidate["comprehensive_score"],
                        "physical_score": candidate["physical_score"],
                        "supply_score": candidate["supply_score"],
                        "neglect_score": candidate["neglect_score"],
                        "localization_rate": candidate["localization_rate"],
                        "note": stock.get("note", ""),
                        "priority": strategy["priority"],
                    })

        # 按优先级和综合评分排序
        matched_selections.sort(key=lambda x: (x["priority"], -x["comprehensive_score"]))

        return matched_selections

    def generate_selection_report(self, candidates: list, matched_selections: list) -> str:
        """生成选股决策报告"""
        lines = []
        lines.append("=" * 70)
        lines.append("  Serenity每日选股决策报告")
        lines.append(f"  日期: {self.today}")
        lines.append("=" * 70)
        lines.append("")

        # 一、筛选概况
        lines.append("【一、筛选概况】")
        lines.append("-" * 50)
        lines.append("")
        lines.append(f"产业链数据库覆盖赛道: {len(self.chain_db.get_all_tracks())}个")
        lines.append(f"候选瓶颈环节总数: {len(candidates)}个")
        lines.append(f"匹配选股标的数: {len(matched_selections)}个")
        lines.append("")

        # 二、候选瓶颈环节评分
        lines.append("【二、候选瓶颈环节评分】")
        lines.append("-" * 50)
        lines.append("")

        for i, cand in enumerate(candidates[:10]):  # 只展示前10个
            lines.append(f"候选{i+1}: {cand['chokepoint_name']}")
            lines.append(f"  所属赛道: {cand['track_name']}")
            lines.append(f"  产业链位置: 第{cand['layer_num']}层 - {cand['chain_position']}")
            lines.append(f"  综合评分: {cand['comprehensive_score']:.1f}分")
            lines.append(f"    - 物理四问: {cand['physical_score']:.1f}分 (一票否决: {'通过' if cand['physical_veto_passed'] else '未通过'})")
            lines.append(f"    - 供给刚性: {cand['supply_score']:.1f}分")
            lines.append(f"    - 市场忽视: {cand['neglect_score']:.1f}分")
            lines.append(f"    - 国产化率: {cand['localization_rate']}%")
            lines.append(f"  代表标的: {', '.join([s['name'] for s in cand['representative_stocks']])}")
            lines.append("")

        # 三、今日选股决策
        lines.append("【三、今日选股决策】")
        lines.append("-" * 50)
        lines.append("")

        # 按策略分组展示
        strategy_groups = {}
        for sel in matched_selections:
            sid = sel["strategy_id"]
            if sid not in strategy_groups:
                strategy_groups[sid] = []
            strategy_groups[sid].append(sel)

        for sid, selections in strategy_groups.items():
            strategy = self.picker.strategy_mgr.get_strategy(sid)
            if not strategy:
                continue

            lines.append(f"策略 [{sid}] {strategy.strategy_name}")
            lines.append(f"  Serenity依据: {strategy.serenity_basis}")
            lines.append(f"  风控参数: 止损{strategy.risk_control.stop_loss_pct}% / 止盈{strategy.risk_control.take_profit_pct}%")
            lines.append("")

            for sel in selections[:3]:  # 每策略最多3只
                lines.append(f"  🟢 {sel['stock_name']}({sel['stock_code']})")
                lines.append(f"     瓶颈环节: {sel['chokepoint_name']}")
                lines.append(f"     匹配理由: {sel['match_reason']}")
                lines.append(f"     综合评分: {sel['comprehensive_score']:.1f}分")
                lines.append(f"     备注: {sel['note']}")
                lines.append("")

        # 四、选股逻辑说明
        lines.append("【四、选股逻辑说明】")
        lines.append("-" * 50)
        lines.append("")
        lines.append("本次选股基于Serenity瓶颈投资分析框架：")
        lines.append("")
        lines.append("1. 物理四问筛选（一票否决制）：")
        lines.append("   Q1: 是否每单位终端产品必需？")
        lines.append("   Q2: 3年内是否有成熟替代？")
        lines.append("   Q3: 缺了是否会导致产线停摆？")
        lines.append("   Q4: 成本占比是否足够重要？")
        lines.append("")
        lines.append("2. 供给刚性评估：")
        lines.append("   - 全球合格供应商数量")
        lines.append("   - 行业CR3集中度")
        lines.append("   - 产能利用率")
        lines.append("   - 产能扩张周期")
        lines.append("   - 设备交付周期")
        lines.append("")
        lines.append("3. 市场忽视度评估：")
        lines.append("   - 市值规模（中小市值优先）")
        lines.append("   - 券商覆盖数（少覆盖优先）")
        lines.append("   - 机构持仓占比（低持仓优先）")
        lines.append("   - 近期涨幅（低涨幅优先）")
        lines.append("")
        lines.append("4. 策略匹配：")
        lines.append("   - 根据评分结果匹配5大活跃策略")
        lines.append("   - 每策略最多推荐3只标的")
        lines.append("")

        # 五、风险提示
        lines.append("【五、风险提示】")
        lines.append("-" * 50)
        lines.append("")
        lines.append("⚠️  本次选股为理论筛选结果，实际投资需考虑：")
        lines.append("   1. 实时行情数据验证")
        lines.append("   2. 最新公告和新闻核实")
        lines.append("   3. 个人风险承受能力")
        lines.append("   4. 市场整体环境")
        lines.append("")
        lines.append("💡 建议：")
        lines.append("   - 对候选标的进行深度分析后再决策")
        lines.append("   - 使用Serenity增强版分析框架核实信息")
        lines.append("   - 关注产业链动态变化")
        lines.append("")

        lines.append("=" * 70)
        lines.append("  报告结束")
        lines.append("=" * 70)

        return "\n".join(lines)

    def execute_daily_selection(self) -> dict:
        """执行完整的每日选股流程"""
        print("=" * 60)
        print("  Serenity每日选股执行")
        print(f"  日期: {self.today}")
        print("=" * 60)
        print()

        # Step 1: 筛选候选瓶颈环节
        print("【Step 1】筛选候选瓶颈环节...")
        candidates = self.screen_candidates(min_score=70.0)
        print(f"  筛选出 {len(candidates)} 个候选瓶颈环节")
        print()

        # Step 2: 匹配策略
        print("【Step 2】匹配活跃策略...")
        matched_selections = self.match_strategies(candidates)
        print(f"  匹配出 {len(matched_selections)} 个选股候选")
        print()

        # Step 3: 生成报告
        print("【Step 3】生成选股决策报告...")
        report = self.generate_selection_report(candidates, matched_selections)

        # 保存报告
        report_dir = Path("serenity_stock_data/daily_reviews")
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"selection_report_{self.today}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  报告已保存: {report_file}")
        print()

        # Step 4: 记录选股决策（JSON格式）
        selection_data = {
            "date": self.today,
            "candidates_count": len(candidates),
            "matched_count": len(matched_selections),
            "candidates": candidates,
            "matched_selections": matched_selections,
        }

        data_file = report_dir / f"selection_data_{self.today}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(selection_data, f, ensure_ascii=False, indent=2)
        print(f"  数据已保存: {data_file}")
        print()

        return {
            "report": report,
            "candidates": candidates,
            "matched_selections": matched_selections,
            "report_file": str(report_file),
            "data_file": str(data_file),
        }


def main():
    """主函数"""
    selector = SerenityDailyStockSelection()
    result = selector.execute_daily_selection()

    print(result["report"])

    print()
    print("✅ 每日选股任务执行完成！")
    print()
    print("下一步建议：")
    print("  1. 对候选标的进行实时行情验证")
    print("  2. 使用serenity_enhanced_analyzer进行深度分析")
    print("  3. 关注产业链动态和重大事件")


if __name__ == "__main__":
    main()