#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日选股任务执行脚本
基于Serenity瓶颈投资分析框架筛选候选股票，匹配活跃策略，记录选股决策

执行流程：
1. 从产业链数据库获取候选瓶颈环节
2. 执行六步漏斗选股流程（物理四问筛选）
3. 匹配5大活跃投资策略
4. 生成选股决策报告
5. 存储决策到知识库
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from core.chain_database import get_chain_database, ChokepointData
from core.enhanced_analyzer import SerenityEnhancedAnalyzer, VerifiedInfo


class SerenityDailySelection:
    """Serenity每日选股系统"""

    def __init__(self):
        self.db = get_chain_database()
        self.analyzer = SerenityEnhancedAnalyzer()
        self.report_dir = PROJECT_DIR / "data" / "stock" / "daily_reviews"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def run_daily_selection(self) -> dict:
        """
        执行每日选股任务
        返回：选股决策结果
        """
        print("=" * 80)
        print(f"  Serenity每日选股决策系统 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)
        print()

        # Step 1: 获取产业链数据库状态
        print("【步骤1】获取产业链数据库状态")
        print("-" * 50)
        tracks = self.db.get_all_tracks()
        print(f"产业链数据库覆盖赛道: {len(tracks)}个")
        for track in tracks:
            track_data = self.db.get_track(track)
            candidates = track_data.chokepoint_candidates if track_data else []
            print(f"  - {track}: {len(candidates)}个候选瓶颈环节")
        print()

        # Step 2: 执行六步漏斗选股流程
        print("【步骤2】执行六步漏斗选股流程")
        print("-" * 50)

        all_candidates = []
        candidate_count = 0
        stock_count = 0

        for track in tracks:
            track_data = self.db.get_track(track)
            if not track_data:
                continue

            for cp in track_data.chokepoint_candidates:
                candidate_count += 1
                stock_count += len(cp.representative_stocks)

                # 执行物理四问筛选
                physical_score = self._evaluate_physical_questions(cp)

                # 计算供给刚性得分
                supply_score = self._evaluate_supply_rigidness(cp)

                # 计算市场忽视度得分
                market_ignore_score = self._evaluate_market_ignore(cp)

                # 综合评分
                total_score = (
                    physical_score * 0.4 +
                    supply_score * 0.3 +
                    market_ignore_score * 0.3
                )

                # 一票否决检查
                pass_veto = self._check_veto(cp)

                candidate_info = {
                    'track': track,
                    'name': cp.name,
                    'layer_num': cp.layer_num,
                    'chain_position': cp.chain_position,
                    'physical_score': physical_score,
                    'supply_score': supply_score,
                    'market_ignore_score': market_ignore_score,
                    'total_score': total_score,
                    'pass_veto': pass_veto,
                    'localization_rate': cp.localization_rate,
                    'representative_stocks': cp.representative_stocks,
                    'failure_impact': cp.failure_impact,
                }

                all_candidates.append(candidate_info)

        print(f"候选瓶颈环节总数: {candidate_count}个")
        print(f"匹配选股标的数: {stock_count}个")
        print()

        # Step 3: 候选瓶颈环节评分排名
        print("【步骤3】候选瓶颈环节评分排名")
        print("-" * 50)

        # 按综合评分排序（仅显示通过一票否决的）
        qualified_candidates = [c for c in all_candidates if c['pass_veto']]
        qualified_candidates.sort(key=lambda x: -x['total_score'])

        # 展示前5名候选
        for i, candidate in enumerate(qualified_candidates[:5], 1):
            print(f"\n候选{i}: {candidate['name']}")
            print(f"  所属赛道: {candidate['track']}")
            print(f"  产业链位置: 第{candidate['layer_num']}层 - {candidate['chain_position']}")
            print(f"  综合评分: {candidate['total_score']:.1f}分")
            print(f"    - 物理四问: {candidate['physical_score']:.1f}分 {'(一票否决: 通过)' if candidate['pass_veto'] else '(一票否决: 失败)'}")
            print(f"    - 供给刚性: {candidate['supply_score']:.1f}分")
            print(f"    - 市场忽视: {candidate['market_ignore_score']:.1f}分")
            print(f"    - 国产化率: {candidate['localization_rate']}%")
            stocks = candidate['representative_stocks']
            print(f"  代表标的: {', '.join([s['name'] for s in stocks])}")
        print()

        # Step 4: 匹配活跃投资策略
        print("【步骤4】匹配活跃投资策略")
        print("-" * 50)

        strategies = self._match_strategies(qualified_candidates[:5])

        for strategy_code, strategy_info in strategies.items():
            print(f"\n策略 [{strategy_code}] {strategy_info['name']}")
            print(f"  Serenity依据: {strategy_info['rationale']}")
            print(f"  风控参数: 止损{strategy_info['stop_loss']:.1f}% / 止盈{strategy_info['take_profit']:.1f}%")

            for stock in strategy_info['stocks']:
                print(f"  🟢 {stock['name']}({stock['code']})")
                print(f"     瓶颈环节: {stock['bottleneck']}")
                print(f"     匹配理由: {stock['reason']}")
                print(f"     综合评分: {stock['score']:.1f}分")
                print(f"     备注: {stock['note']}")
        print()

        # Step 5: 生成选股决策报告
        print("【步骤5】生成选股决策报告")
        print("-" * 50)

        report_file = self._generate_report(qualified_candidates[:5], strategies)
        print(f"✅ 报告已保存: {report_file}")
        print()

        # Step 6: 存储决策到知识库
        print("【步骤6】存储决策到知识库")
        print("-" * 50)

        self._save_to_knowledge_base(qualified_candidates[:5], strategies)
        print("✅ 决策已存储到知识库")
        print()

        print("=" * 80)
        print("  ✅ 每日选股任务完成!")
        print("=" * 80)

        return {
            'candidates': qualified_candidates[:5],
            'strategies': strategies,
            'report_file': str(report_file),
            'timestamp': datetime.now().isoformat()
        }

    def _evaluate_physical_questions(self, cp: ChokepointData) -> float:
        """物理四问评分（一票否决制）"""
        score = 0.0

        # Q1: 每单位终端产品必需？
        if cp.required_per_unit:
            score += 25.0

        # Q2: 3年内无成熟替代？
        if cp.no_substitute_3y:
            score += 25.0

        # Q3: 缺了会导致产线停摆？
        if "停摆" in cp.failure_impact or "报废" in cp.failure_impact:
            score += 25.0

        # Q4: 成本占比足够重要？
        if cp.cost_ratio >= 1.0:
            score += 25.0

        return score

    def _evaluate_supply_rigidness(self, cp: ChokepointData) -> float:
        """供给刚性评分"""
        score = 50.0  # 基准分

        # 全球供应商数量（越少越刚性）
        if cp.global_suppliers <= 3:
            score += 30.0
        elif cp.global_suppliers <= 5:
            score += 20.0
        elif cp.global_suppliers <= 10:
            score += 10.0

        # 行业CR3（越高越刚性）
        if cp.industry_cr3 >= 90:
            score += 25.0
        elif cp.industry_cr3 >= 80:
            score += 20.0
        elif cp.industry_cr3 >= 70:
            score += 15.0

        # 产能利用率（越高越刚性）
        if cp.capacity_util >= 90:
            score += 20.0
        elif cp.capacity_util >= 85:
            score += 15.0
        elif cp.capacity_util >= 80:
            score += 10.0

        # 设备交付周期（越长越刚性）
        if cp.equipment_lead_time >= 18:
            score += 20.0
        elif cp.equipment_lead_time >= 12:
            score += 15.0
        elif cp.equipment_lead_time >= 9:
            score += 10.0

        # 产能扩张周期（越长越刚性）
        if cp.expansion_cycle >= 24:
            score += 20.0
        elif cp.expansion_cycle >= 18:
            score += 15.0
        elif cp.expansion_cycle >= 12:
            score += 10.0

        return min(score, 125.0)

    def _evaluate_market_ignore(self, cp: ChokepointData) -> float:
        """市场忽视度评分"""
        score = 0.0

        # 市值规模（中小市值优先）
        if cp.mktcap_min <= 50 and cp.mktcap_max <= 200:
            score += 30.0

        # 券商覆盖数（少覆盖优先）
        if cp.covered_brokers <= 5:
            score += 30.0
        elif cp.covered_brokers <= 10:
            score += 20.0
        elif cp.covered_brokers <= 15:
            score += 10.0

        # 机构持仓占比（低持仓优先）
        if cp.fund_holding <= 3:
            score += 20.0
        elif cp.fund_holding <= 5:
            score += 15.0

        # 近期涨幅（低涨幅优先）
        if cp.recent_gain_6m <= 20:
            score += 20.0
        elif cp.recent_gain_6m <= 30:
            score += 15.0

        return score

    def _check_veto(self, cp: ChokepointData) -> bool:
        """一票否决检查"""
        # 必需性检查
        if not cp.required_per_unit:
            return False

        # 替代性检查
        if not cp.no_substitute_3y:
            return False

        # 失效影响检查
        if "停摆" not in cp.failure_impact and "报废" not in cp.failure_impact:
            return False

        # 成本占比检查
        if cp.cost_ratio < 1.0:
            return False

        return True

    def _match_strategies(self, candidates: list) -> dict:
        """匹配投资策略"""
        strategies = {
            'S001': {
                'name': '瓶颈选股-等权策略',
                'rationale': '物理四问综合评分≥70分 + 证据强度≥中等',
                'stop_loss': 10.0,
                'take_profit': 25.0,
                'stocks': []
            },
            'S002': {
                'name': '认知差修复策略',
                'rationale': '认知差程度≥60分 + 有明确催化剂',
                'stop_loss': 12.0,
                'take_profit': 30.0,
                'stocks': []
            },
            'S003': {
                'name': '事件驱动策略',
                'rationale': '三级证据验证为强 + 事件影响等级高',
                'stop_loss': 8.0,
                'take_profit': 20.0,
                'stocks': []
            },
            'S004': {
                'name': '产业趋势策略',
                'rationale': '行业政策支持 + 供需缺口扩大 + 国产替代加速',
                'stop_loss': 15.0,
                'take_profit': 40.0,
                'stocks': []
            },
        }

        # 为每个候选匹配策略
        for candidate in candidates:
            score = candidate['total_score']
            bottleneck = candidate['name']

            # S001: 瓶颈选股策略（高综合评分）
            if score >= 70 and candidate['pass_veto']:
                for stock in candidate['representative_stocks']:
                    strategies['S001']['stocks'].append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'bottleneck': bottleneck,
                        'reason': f"物理四问通过，综合评分{score:.1f}分",
                        'score': score,
                        'note': stock['note']
                    })

            # S002: 认知差修复策略（高市场忽视度）
            if candidate['market_ignore_score'] >= 60:
                for stock in candidate['representative_stocks']:
                    strategies['S002']['stocks'].append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'bottleneck': bottleneck,
                        'reason': f"市场忽视度{candidate['market_ignore_score']:.1f}分，认知差空间大",
                        'score': score,
                        'note': stock['note']
                    })

            # S003: 事件驱动策略（低国产化率）
            if candidate['localization_rate'] <= 20:
                for stock in candidate['representative_stocks']:
                    strategies['S003']['stocks'].append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'bottleneck': bottleneck,
                        'reason': f"国产化率仅{candidate['localization_rate']}%，供给刚性{candidate['supply_score']:.1f}分",
                        'score': score,
                        'note': stock['note']
                    })

            # S004: 产业趋势策略（高国产化空间）
            localization_space = 100 - candidate['localization_rate']
            if localization_space >= 80:
                for stock in candidate['representative_stocks']:
                    strategies['S004']['stocks'].append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'bottleneck': bottleneck,
                        'reason': f"产业确定性高，国产化空间{localization_space}%",
                        'score': score,
                        'note': stock['note']
                    })

        # 限制每策略最多3只标的
        for strategy_code in strategies:
            strategies[strategy_code]['stocks'] = strategies[strategy_code]['stocks'][:3]

        return strategies

    def _generate_report(self, candidates: list, strategies: dict) -> Path:
        """生成选股决策报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        report_file = self.report_dir / f"selection_report_{today}.txt"

        # 统计数据
        tracks_count = len(self.db.get_all_tracks())
        candidate_count = sum(len(self.db.get_track(t).chokepoint_candidates) for t in self.db.get_all_tracks() if self.db.get_track(t))
        stock_count = sum(len(c['representative_stocks']) for c in candidates)

        lines = []
        lines.append("=" * 70)
        lines.append("  Serenity每日选股决策报告")
        lines.append(f"  日期: {today}")
        lines.append("=" * 70)
        lines.append("")
        lines.append("【一、筛选概况】")
        lines.append("-" * 50)
        lines.append("")
        lines.append(f"产业链数据库覆盖赛道: {tracks_count}个")
        lines.append(f"候选瓶颈环节总数: {candidate_count}个")
        lines.append(f"匹配选股标的数: {stock_count}个")
        lines.append("")
        lines.append("【二、候选瓶颈环节评分】")
        lines.append("-" * 50)
        lines.append("")

        for i, candidate in enumerate(candidates, 1):
            lines.append(f"候选{i}: {candidate['name']}")
            lines.append(f"  所属赛道: {candidate['track']}")
            lines.append(f"  产业链位置: 第{candidate['layer_num']}层 - {candidate['chain_position']}")
            lines.append(f"  综合评分: {candidate['total_score']:.1f}分")
            lines.append(f"    - 物理四问: {candidate['physical_score']:.1f}分 {'(一票否决: 通过)' if candidate['pass_veto'] else '(一票否决: 失败)'}")
            lines.append(f"    - 供给刚性: {candidate['supply_score']:.1f}分")
            lines.append(f"    - 市场忽视: {candidate['market_ignore_score']:.1f}分")
            lines.append(f"    - 国产化率: {candidate['localization_rate']}%")
            stocks = candidate['representative_stocks']
            lines.append(f"  代表标的: {', '.join([s['name'] for s in stocks])}")
            lines.append("")

        lines.append("【三、今日选股决策】")
        lines.append("-" * 50)
        lines.append("")

        for strategy_code, strategy_info in strategies.items():
            if not strategy_info['stocks']:
                continue

            lines.append(f"策略 [{strategy_code}] {strategy_info['name']}")
            lines.append(f"  Serenity依据: {strategy_info['rationale']}")
            lines.append(f"  风控参数: 止损{strategy_info['stop_loss']:.1f}% / 止盈{strategy_info['take_profit']:.1f}%")
            lines.append("")

            for stock in strategy_info['stocks']:
                lines.append(f"  🟢 {stock['name']}({stock['code']})")
                lines.append(f"     瓶颈环节: {stock['bottleneck']}")
                lines.append(f"     匹配理由: {stock['reason']}")
                lines.append(f"     综合评分: {stock['score']:.1f}分")
                lines.append(f"     备注: {stock['note']}")
                lines.append("")

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

        report_file.write_text("\n".join(lines), encoding='utf-8')
        return report_file

    def _save_to_knowledge_base(self, candidates: list, strategies: dict):
        """存储决策到知识库"""
        kb_dir = PROJECT_DIR / "knowledge"
        kb_dir.mkdir(exist_ok=True)

        kb_file = kb_dir / "serenity_selection_knowledge.md"

        if not kb_file.exists():
            kb_file.write_text("# Serenity选股知识库\n\n", encoding='utf-8')

        today = datetime.now().strftime('%Y-%m-%d')

        with open(kb_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## 每日选股决策 ({today})\n")
            f.write(f"\n### 候选瓶颈环节\n")
            for i, candidate in enumerate(candidates, 1):
                f.write(f"{i}. **{candidate['name']}** ({candidate['track']})\n")
                f.write(f"   - 综合评分: {candidate['total_score']:.1f}分\n")
                f.write(f"   - 国产化率: {candidate['localization_rate']}%\n")
                stock_names = [s['name'] for s in candidate['representative_stocks']]
                f.write(f"   - 代表标的: {', '.join(stock_names)}\n")

            f.write(f"\n### 策略匹配\n")
            for strategy_code, strategy_info in strategies.items():
                if strategy_info['stocks']:
                    f.write(f"- **{strategy_info['name']}**: {len(strategy_info['stocks'])}只标的\n")

            f.write(f"\n---\n")


def main():
    """主函数"""
    selection_system = SerenityDailySelection()
    result = selection_system.run_daily_selection()

    print("\n" + "=" * 80)
    print("  📊 每日选股任务执行完成")
    print("=" * 80)
    print()
    print(f"报告文件: {result['report_file']}")
    print(f"候选瓶颈: {len(result['candidates'])}个")
    print(f"匹配策略: {len(result['strategies'])}个")
    print()

    return result


if __name__ == '__main__':
    main()