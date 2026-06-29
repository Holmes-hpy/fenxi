"""
Serenity瓶颈点投资分析Agent
基于紫苏叶理论的科技产业投研专家

核心原则：
1. 约束决定论：产业上限由最薄弱的物理瓶颈决定
2. 紫苏叶准则：专注上游底层瓶颈，放弃终端龙头
3. 一票否决制：任意硬性标准不满足直接淘汰
4. 认知差优先：投资收益来源于供需错配+认知差修复

作者：Serenity Agent
版本：V2.0 (增强版)
- V2.0新增：产业链数据库、真实数据接入、增强风险评估
"""

import json
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# 导入增强模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serenity_chain_database import (
    get_chain_database,
    SerenityChainDatabase,
    TrackDatabase,
    list_all_tracks,
)
from serenity_data_fetcher import (
    get_data_fetcher,
    SerenityDataFetcher,
    ChokepointStockData,
    fetch_stock_data,
    fetch_stocks_data,
)
from serenity_risk_assessment import (
    get_redteam_assessor,
    RedTeamAssessor,
    RedTeamReport,
    RiskAssessmentResult,
    full_redteam_assessment,
)

# ==================== 数据结构定义 ====================

class CertaintyLevel(Enum):
    """确定性等级"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

class EvidenceLevel(Enum):
    """证据等级"""
    STRONG = "强"  # 可重仓
    MEDIUM = "中"  # 可建底仓
    WEAK = "弱"    # 仅参考

class RiskLevel(Enum):
    """风险等级"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

class InvestmentRating(Enum):
    """投资评级"""
    STRONG_BUY = "强烈推荐"
    BUY = "推荐"
    WATCH = "观察"
    ELIMINATE = "淘汰"

class TrendType(Enum):
    """驱动类型"""
    TECH_DRIVEN = "技术驱动"
    POLICY_DRIVEN = "政策驱动"
    DEMAND_DRIVEN = "需求驱动"

@dataclass
class IndustryTrend:
    """产业大趋势"""
    name: str                           # 趋势名称
    certainty: CertaintyLevel           # 确定性等级
    trend_type: TrendType               # 驱动类型
    core_terminal_drivers: List[str]    # 核心终端驱动
    core_capex_entities: List[str]      # 核心资本开支主体
    demand_growth_rate: str             # 需求增速预测
    trend_cycle: str = "3-5年"          # 趋势周期
    verification_data: Dict = field(default_factory=dict)  # 验证数据

@dataclass
class SupplyChainLayer:
    """供应链层级"""
    layer_num: int                      # 层级编号(1-8)
    layer_name: str                     # 层级名称
    core_products: List[str]            # 核心产品
    key_suppliers: List[str]            # 关键供应商
    bottleneck_question: str            # "缺了什么就停摆"

@dataclass
class ChokepointCandidate:
    """瓶颈候选环节"""
    name: str                           # 环节名称
    layer_num: int                      # 所属层级
    chain_position: str                 # 产业链位置
    physical_essential: bool = False    # 物理必需
    supply_rigidity: CertaintyLevel = CertaintyLevel.LOW  # 供给刚性
    market_monopoly: bool = False        # 格局垄断
    market_neglected: bool = False       # 市场忽视
    passed: bool = False                # 是否通过筛选
    elimination_reason: str = ""         # 淘汰原因

    # 详细验证指标
    cost_ratio: float = 0.0            # 成本占比
    global_suppliers_count: int = 0     # 全球供应商数量
    industry_cr3: float = 0.0           # 行业CR3
    capacity_utilization: float = 0.0   # 产能利用率
    capacity_expansion_cycle: int = 0   # 产能扩张周期(月)
    equipment_delivery_cycle: int = 0   # 设备交付周期(月)
    top1_market_share: float = 0.0      # 第一名市占率
    top2_market_share: float = 0.0     # 前两名合计
    new_entrants_2y: int = 0            # 过去2年新进入者
    gross_margin: float = 0.0           # 毛利率
    market_cap_min: float = 0.0         # 最小市值(亿)
    market_cap_max: float = 0.0         # 最大市值(亿)
    covered_broker_count: int = 0        # 覆盖券商数量
    fund_holding_ratio: float = 0.0     # 公募+北向持仓占比
    recent_6m_gain: float = 0.0         # 近6月涨幅

@dataclass
class ChokepointEvidence:
    """商业化落地证据"""
    stock_code: str                     # 股票代码
    stock_name: str                     # 股票名称
    evidence_level: EvidenceLevel        # 证据等级
    core_verification_points: List[str] # 核心验证点
    performance_elasticity: str         # 业绩弹性测算
    market_cap: float = 0.0            # 市值(亿)
    current_price: float = 0.0           # 当前价格
    target_price: float = 0.0           # 目标价格
    upside_ratio: float = 0.0           # 上涨空间

@dataclass
class RiskAssessment:
    """风险评估"""
    risk_type: str                      # 风险类型
    risk_description: str                # 风险描述
    probability: RiskLevel               # 发生概率
    impact: RiskLevel                   # 影响程度
    tracking_indicators: List[str]       # 跟踪指标

@dataclass
class InvestmentDecision:
    """投资决策"""
    stock_code: str                     # 股票代码
    stock_name: str                     # 股票名称
    priority: int                       # 优先级
    rating: InvestmentRating             # 投资评级
    expected_return: str                # 预期收益空间
    suggested_position: str             # 建议仓位
    buy_conditions: List[str]           # 买入条件
    sell_conditions: List[str]          # 卖出条件

@dataclass
class SerenityReport:
    """Serenity分析报告"""
    industry_track: str                  # 赛道名称
    trend_certainty: CertaintyLevel      # 趋势确定性
    drive_type: TrendType               # 驱动类型
    data_date: str                      # 数据日期
    tags: List[str]                     # 标签
    chokepoint_count: int               # 瓶颈数量

    # 核心分析结果
    industry_trend: Optional[IndustryTrend] = None
    supply_chain_layers: List[SupplyChainLayer] = field(default_factory=list)
    chokepoint_candidates: List[ChokepointCandidate] = field(default_factory=list)
    chokepoint_evidences: List[ChokepointEvidence] = field(default_factory=list)
    risk_assessments: List[RiskAssessment] = field(default_factory=list)
    investment_decisions: List[InvestmentDecision] = field(default_factory=list)

# ==================== 核心分析引擎 ====================

class SerenityChokepointAnalyzer:
    """
    Serenity瓶颈点投资分析引擎

    执行六步漏斗式选股流程：
    1. 锚定确定性超级大趋势
    2. 八层逆向产业链深度拆解
    3. 物理四问硬性筛选（一票否决）
    4. 商业化落地验证（三级证据体系）
    5. 红队证伪与风险评估
    6. 投资决策输出
    """

    def __init__(self):
        self.current_report: Optional[SerenityReport] = None
        self.analysis_timestamp = datetime.now().strftime("%Y.%m.%d")
        # 增强模块实例
        self.chain_db: SerenityChainDatabase = get_chain_database()
        self.data_fetcher: SerenityDataFetcher = get_data_fetcher()
        self.redteam: RedTeamAssessor = get_redteam_assessor()
        # 缓存的真实数据
        self._stock_data_cache: Dict[str, ChokepointStockData] = {}
        # 红队报告缓存
        self._redteam_reports: Dict[str, RedTeamReport] = {}

    def analyze_from_database(self, track_name: str) -> SerenityReport:
        """
        从产业链数据库直接分析赛道

        Args:
            track_name: 赛道名称

        Returns:
            SerenityReport: 完整分析报告
        """
        track = self.chain_db.get_track(track_name)
        if not track:
            raise ValueError(f"未找到赛道: {track_name}。可用赛道: {', '.join(self.chain_db.get_all_tracks())}")

        # 组装趋势数据
        trend_data = self.chain_db.get_trend_data(track_name)
        trend_data["chain_breakdown"] = self.chain_db.get_chain_layers_for_analysis(track_name)
        trend_data["candidates"] = self.chain_db.get_candidates_for_analysis(track_name)

        return self.analyze(track_name, trend_data)

    def list_available_tracks(self) -> List[str]:
        """列出所有可用赛道"""
        return self.chain_db.get_all_tracks()

    def analyze(self, industry_track: str, trend_data: Dict) -> SerenityReport:
        """
        执行完整的Serenity瓶颈分析

        Args:
            industry_track: 赛道名称
            trend_data: 趋势数据字典

        Returns:
            SerenityReport: 完整的分析报告
        """
        print(f"[Serenity] 开始分析赛道：{industry_track}")

        # 初始化报告
        self.current_report = SerenityReport(
            industry_track=industry_track,
            trend_certainty=CertaintyLevel.MEDIUM,
            drive_type=TrendType.TECH_DRIVEN,
            data_date=datetime.now().strftime("%Y-%m"),
            tags=["瓶颈投资", "紫苏叶理论"],
            chokepoint_count=0
        )

        # 第一步：锚定确定性超级大趋势
        print("[Step 1/6] 锚定产业大趋势...")
        self._step1_trend_validation(trend_data)

        # 第二步：八层逆向产业链拆解
        print("[Step 2/6] 逆向产业链深度拆解...")
        self._step2_supply_chain_breakdown(trend_data.get("chain_breakdown", []))

        # 第三步：物理四问硬性筛选
        print("[Step 3/6] 物理四问硬性筛选...")
        self._step3_chokepoint_screening(trend_data.get("candidates", []))

        # 第四步：商业化落地验证
        print("[Step 4/6] 商业化落地证据验证...")
        self._step4_evidence_verification()

        # 第五步：红队证伪与风险评估
        print("[Step 5/6] 红队证伪与风险评估...")
        self._step5_risk_assessment()

        # 第六步：投资决策输出
        print("[Step 6/6] 输出投资决策...")
        self._step6_investment_decision()

        return self.current_report

    def _step1_trend_validation(self, trend_data: Dict):
        """第一步：锚定确定性超级大趋势"""
        # 验证标准检查
        capex_verified = trend_data.get("has_capex_plan", False)
        data_verified = trend_data.get("has_real_data", False)
        irreversible = trend_data.get("is_irreversible", False)

        certainty = CertaintyLevel.HIGH
        if not all([capex_verified, data_verified, irreversible]):
            certainty = CertaintyLevel.LOW if not capex_verified else CertaintyLevel.MEDIUM

        self.current_report.trend_certainty = certainty
        self.current_report.industry_trend = IndustryTrend(
            name=trend_data.get("trend_name", ""),
            certainty=certainty,
            trend_type=TrendType.TECH_DRIVEN if trend_data.get("is_tech_driven") else TrendType.POLICY_DRIVEN,
            core_terminal_drivers=trend_data.get("terminal_drivers", []),
            core_capex_entities=trend_data.get("capex_entities", []),
            demand_growth_rate=trend_data.get("growth_rate", ""),
            trend_cycle=trend_data.get("trend_cycle", "3-5年"),
            verification_data={
                "capex_verified": capex_verified,
                "data_verified": data_verified,
                "irreversible": irreversible
            }
        )

    def _step2_supply_chain_breakdown(self, chain_data: List[Dict]):
        """第二步：八层逆向产业链深度拆解"""
        for layer_info in chain_data:
            layer = SupplyChainLayer(
                layer_num=layer_info.get("layer_num", 0),
                layer_name=layer_info.get("layer_name", ""),
                core_products=layer_info.get("core_products", []),
                key_suppliers=layer_info.get("key_suppliers", []),
                bottleneck_question=layer_info.get("bottleneck_question", "")
            )
            self.current_report.supply_chain_layers.append(layer)

    def _step3_chokepoint_screening(self, candidates: List[Dict]):
        """第三步：物理四问硬性筛选（一票否决）"""
        for candidate_data in candidates:
            candidate = ChokepointCandidate(
                name=candidate_data.get("name", ""),
                layer_num=candidate_data.get("layer_num", 0),
                chain_position=candidate_data.get("chain_position", "")
            )

            # 一问：物理绝对必需
            physical_pass = (
                candidate_data.get("required_per_unit", True) and
                candidate_data.get("no_substitute_3y", True) and
                candidate_data.get("cost_ratio", 0) <= 5
            )
            candidate.physical_essential = physical_pass

            # 二问：供给足够刚性
            supply_pass = (
                candidate_data.get("global_suppliers", 0) <= 5 and
                candidate_data.get("cr3", 0) >= 80 and
                candidate_data.get("capacity_util", 0) >= 80 and
                candidate_data.get("expansion_cycle", 0) >= 18
            )
            candidate.supply_rigidity = CertaintyLevel.HIGH if supply_pass else CertaintyLevel.LOW

            # 三问：格局足够垄断
            monopoly_pass = (
                candidate_data.get("top1_share", 0) >= 40 and
                candidate_data.get("top2_sum", 0) >= 70 and
                candidate_data.get("new_entrants_2y", 0) == 0 and
                candidate_data.get("gross_margin", 0) >= 40
            )
            candidate.market_monopoly = monopoly_pass

            # 四问：市场足够忽视
            neglected_pass = (
                candidate_data.get("mktcap_min", 30) >= 30 and
                candidate_data.get("mktcap_max", 200) <= 200 and
                candidate_data.get("covered_brokers", 0) <= 10 and
                candidate_data.get("fund_holding", 0) <= 5 and
                candidate_data.get("recent_gain_6m", 0) < 100
            )
            candidate.market_neglected = neglected_pass

            # 一票否决判定
            candidate.passed = all([physical_pass, supply_pass, monopoly_pass, neglected_pass])

            if not candidate.passed:
                reasons = []
                if not physical_pass:
                    reasons.append("物理非必需或存在替代方案")
                if not supply_pass:
                    reasons.append("供给刚性不足")
                if not monopoly_pass:
                    reasons.append("市场格局不够垄断")
                if not neglected_pass:
                    reasons.append("已被市场充分认知")
                candidate.elimination_reason = "; ".join(reasons)

            # 详细指标
            candidate.global_suppliers_count = candidate_data.get("global_suppliers", 0)
            candidate.industry_cr3 = candidate_data.get("cr3", 0)
            candidate.capacity_utilization = candidate_data.get("capacity_util", 0)
            candidate.capacity_expansion_cycle = candidate_data.get("expansion_cycle", 0)
            candidate.top1_market_share = candidate_data.get("top1_share", 0)
            candidate.top2_market_share = candidate_data.get("top2_sum", 0)
            candidate.gross_margin = candidate_data.get("gross_margin", 0)
            candidate.market_cap_min = candidate_data.get("mktcap_min", 0)
            candidate.market_cap_max = candidate_data.get("mktcap_max", 0)
            candidate.covered_broker_count = candidate_data.get("covered_brokers", 0)
            candidate.fund_holding_ratio = candidate_data.get("fund_holding", 0)
            candidate.recent_6m_gain = candidate_data.get("recent_gain_6m", 0)

            self.current_report.chokepoint_candidates.append(candidate)

        # 更新瓶颈数量
        passed_count = sum(1 for c in self.current_report.chokepoint_candidates if c.passed)
        self.current_report.chokepoint_count = passed_count

    def _step4_evidence_verification(self):
        """第四步：商业化落地验证（三级证据体系）- 使用真实数据"""
        # 获取候选环节对应的代表标的
        track = self.chain_db.get_track(self.current_report.industry_track)
        track_candidates = {}
        if track:
            for cp in track.chokepoint_candidates:
                track_candidates[cp.name] = cp

        for candidate in self.current_report.chokepoint_candidates:
            if not candidate.passed:
                continue

            # 从数据库获取对应候选的标的列表
            cp_data = track_candidates.get(candidate.name)
            if not cp_data or not cp_data.representative_stocks:
                continue

            # 对每个代表标的进行证据验证
            for stock_info in cp_data.representative_stocks:
                stock_code = stock_info.get("code", "")
                if not stock_code:
                    continue

                try:
                    # 获取真实数据
                    stock_data = self.data_fetcher.get_stock_full_data(stock_code)
                    self._stock_data_cache[stock_code] = stock_data

                    # 基于真实数据评估证据等级
                    evidence = self._verify_evidence_from_data(candidate, stock_data, stock_info)
                    if evidence:
                        self.current_report.chokepoint_evidences.append(evidence)
                except Exception as e:
                    print(f"[Serenity Step4] 获取 {stock_code} 数据失败: {e}")

    def _step5_risk_assessment(self):
        """第五步：红队证伪与风险评估 - 使用增强风险评估"""
        track = self.chain_db.get_track(self.current_report.industry_track)
        trend_data = {}
        if track:
            trend_data = self.chain_db.get_trend_data(self.current_report.industry_track)

        track_candidates = {}
        if track:
            for cp in track.chokepoint_candidates:
                track_candidates[cp.name] = cp

        # 只对第一个通过筛选的候选环节做整体行业风险评估
        first_candidate = None
        for c in self.current_report.chokepoint_candidates:
            if c.passed:
                first_candidate = c
                break

        if not first_candidate:
            self._add_basic_risks()
            return

        cp_name = first_candidate.name
        cp_data_dict = {}
        if cp_name in track_candidates:
            cp = track_candidates[cp_name]
            cp_data_dict = {
                "expansion_cycle": cp.expansion_cycle,
                "capacity_util": cp.capacity_util,
                "new_entrants_2y": cp.new_entrants_2y,
                "top1_share": cp.top1_share,
                "gross_margin": cp.gross_margin,
                "cr3": cp.industry_cr3,
                "localization_rate": cp.localization_rate,
                "equipment_lead_time": cp.equipment_lead_time,
            }

        # 使用增强红队评估（整个赛道只做一次综合风险评估）
        try:
            redteam_report = self.redteam.full_assessment(
                chokepoint_name=cp_name,
                chokepoint_data=cp_data_dict,
                track_name=self.current_report.industry_track,
                trend_data=trend_data,
            )
            # 缓存到第一个标的
            if self.current_report.chokepoint_evidences:
                first_evidence = self.current_report.chokepoint_evidences[0]
                self._redteam_reports[first_evidence.stock_code] = redteam_report

            # 添加整体风险评估
            if redteam_report.tech_risk:
                self.current_report.risk_assessments.append(RiskAssessment(
                    risk_type="技术替代风险",
                    risk_description=f"综合风险评分: {redteam_report.tech_risk.risk_score:.1f}。{redteam_report.tech_risk.rating_adjustment}",
                    probability=self._risk_level_convert(redteam_report.tech_risk.overall_probability),
                    impact=self._risk_level_convert(redteam_report.tech_risk.overall_impact),
                    tracking_indicators=redteam_report.tech_risk.tracking_metrics
                ))
            if redteam_report.supply_risk:
                self.current_report.risk_assessments.append(RiskAssessment(
                    risk_type="供给突破风险",
                    risk_description=f"综合风险评分: {redteam_report.supply_risk.risk_score:.1f}。{redteam_report.supply_risk.rating_adjustment}",
                    probability=self._risk_level_convert(redteam_report.supply_risk.overall_probability),
                    impact=self._risk_level_convert(redteam_report.supply_risk.overall_impact),
                    tracking_indicators=redteam_report.supply_risk.tracking_metrics
                ))
            if redteam_report.demand_risk:
                self.current_report.risk_assessments.append(RiskAssessment(
                    risk_type="需求不及预期风险",
                    risk_description=f"综合风险评分: {redteam_report.demand_risk.risk_score:.1f}。{redteam_report.demand_risk.rating_adjustment}",
                    probability=self._risk_level_convert(redteam_report.demand_risk.overall_probability),
                    impact=self._risk_level_convert(redteam_report.demand_risk.overall_impact),
                    tracking_indicators=redteam_report.demand_risk.tracking_metrics
                ))
        except Exception as e:
            print(f"[Serenity Step5] 红队评估失败: {e}")
            # 降级：使用简单评估
            self._add_basic_risks()

    def _risk_level_convert(self, level) -> RiskLevel:
        """风险等级转换"""
        level_str = str(level.value) if hasattr(level, 'value') else str(level)
        if level_str == "高":
            return RiskLevel.HIGH
        elif level_str == "中":
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _add_basic_risks(self):
        """添加基础风险（降级方案）"""
        base_risks = [
            ("技术替代风险", "存在可绕过瓶颈的新技术路线可能性", RiskLevel.MEDIUM, RiskLevel.HIGH,
             ["技术路线专利", "竞品研发进展", "学术论文发表"]),
            ("供给突破风险", "潜在新玩家可能快速突破壁垒", RiskLevel.MEDIUM, RiskLevel.MEDIUM,
             ["新进入者产能规划", "设备交付周期变化", "原材料供应"]),
            ("需求不及预期风险", "下游大趋势可能证伪或资本开支砍单", RiskLevel.LOW, RiskLevel.HIGH,
             ["下游CAPEX计划", "月度出货数据", "政策变化"]),
        ]
        for rtype, rdesc, rprob, rimpact, rindicators in base_risks:
            self.current_report.risk_assessments.append(RiskAssessment(
                risk_type=rtype,
                risk_description=rdesc,
                probability=rprob,
                impact=rimpact,
                tracking_indicators=rindicators
            ))

    def _step6_investment_decision(self):
        """第六步：投资决策输出 - 考虑风险评估结果"""
        for i, evidence in enumerate(self.current_report.chokepoint_evidences):
            # 基础评级
            if evidence.evidence_level == EvidenceLevel.STRONG:
                rating = InvestmentRating.STRONG_BUY
            elif evidence.evidence_level == EvidenceLevel.MEDIUM:
                rating = InvestmentRating.BUY
            else:
                rating = InvestmentRating.WATCH

            # 根据风险评估调整评级
            redteam = self._redteam_reports.get(evidence.stock_code)
            if redteam and redteam.overall_risk_score >= 60:
                if rating == InvestmentRating.STRONG_BUY:
                    rating = InvestmentRating.BUY
                elif rating == InvestmentRating.BUY:
                    rating = InvestmentRating.WATCH

            # 计算预期收益（基于估值和增长）
            stock_data = self._stock_data_cache.get(evidence.stock_code)
            upside_str = "待测算"
            if stock_data and stock_data.quote and stock_data.quote.pe_ttm > 0:
                # 简单估算：PEG估值法
                growth = stock_data.financial.profit_growth if stock_data.financial else 30
                peg = stock_data.quote.pe_ttm / growth if growth > 0 else 1
                if peg < 1:
                    upside_str = f"{int((1/peg - 1) * 100)}%+"
                elif peg < 1.5:
                    upside_str = "20-50%"
                else:
                    upside_str = "估值偏高"

            # 仓位建议
            if rating == InvestmentRating.STRONG_BUY:
                position = "重仓（10-15%）"
            elif rating == InvestmentRating.BUY:
                position = "标准仓（5-10%）"
            elif rating == InvestmentRating.WATCH:
                position = "底仓（2-5%）"
            else:
                position = "0%（淘汰）"

            decision = InvestmentDecision(
                stock_code=evidence.stock_code,
                stock_name=evidence.stock_name,
                priority=i + 1,
                rating=rating,
                expected_return=upside_str,
                suggested_position=position,
                buy_conditions=[
                    "股价回调至关键支撑位（如20/60日均线）",
                    "成交量显著放大，资金进场信号",
                    "催化剂事件落地（订单/认证/政策）",
                ],
                sell_conditions=[
                    "核心投资逻辑被证伪",
                    "股价达到目标价或充分定价",
                    "关键里程碑未按期兑现",
                    "红队风险指标触发预警",
                ]
            )
            self.current_report.investment_decisions.append(decision)

    def _verify_evidence_from_data(
        self,
        candidate: ChokepointCandidate,
        stock_data: ChokepointStockData,
        stock_info: Dict,
    ) -> Optional[ChokepointEvidence]:
        """基于真实数据验证商业化落地证据"""
        stock_code = stock_info.get("code", "")
        stock_name = stock_info.get("name", stock_data.name or stock_info.get("name", ""))

        # 收集验证点
        verification_points = []
        strong_evidence_count = 0
        medium_evidence_count = 0

        # 1. 检查公告中的订单/合作信息
        if stock_data.announcements:
            order_keywords = ["订单", "合同", "合作", "定点", "中标", "签约", "量产"]
            for ann in stock_data.announcements:
                title = str(ann.get("ann_title", "") + ann.get("title", ""))
                for kw in order_keywords:
                    if kw in title:
                        verification_points.append(f"公告利好: {title[:30]}")
                        strong_evidence_count += 1
                        break

        # 2. 检查业绩增长
        if stock_data.financial:
            if stock_data.financial.profit_growth > 50:
                verification_points.append(f"净利润增速{stock_data.financial.profit_growth:.1f}%")
                strong_evidence_count += 1
            elif stock_data.financial.profit_growth > 20:
                verification_points.append(f"净利润增速{stock_data.financial.profit_growth:.1f}%")
                medium_evidence_count += 1

            if stock_data.financial.revenue_growth > 30:
                verification_points.append(f"营收增速{stock_data.financial.revenue_growth:.1f}%")
                medium_evidence_count += 1

            if stock_data.financial.gross_margin > 40:
                verification_points.append(f"毛利率{stock_data.financial.gross_margin:.1f}%")
                medium_evidence_count += 1

        # 3. 检查研报覆盖
        if stock_data.research and stock_data.research.report_count_3m > 10:
            verification_points.append(f"近3月{stock_data.research.report_count_3m}篇研报覆盖")
            medium_evidence_count += 1

        # 确定证据等级
        if strong_evidence_count >= 2:
            evidence_level = EvidenceLevel.STRONG
            elasticity = "业绩弹性3-5倍"
        elif strong_evidence_count >= 1 or medium_evidence_count >= 3:
            evidence_level = EvidenceLevel.MEDIUM
            elasticity = "业绩弹性1-2倍"
        else:
            evidence_level = EvidenceLevel.WEAK
            elasticity = "业绩弹性待验证"

        # 计算上涨空间（简单估算）
        upside_ratio = 0
        if stock_data.quote and stock_data.quote.price > 0:
            # 基于市场忽视度和供给刚性的粗略估算
            neglect_factor = stock_data.market_neglect_score / 50
            upside_ratio = int(neglect_factor * 50)

        return ChokepointEvidence(
            stock_code=stock_code,
            stock_name=stock_name,
            evidence_level=evidence_level,
            core_verification_points=verification_points if verification_points else ["待深入验证"],
            performance_elasticity=elasticity,
            market_cap=stock_data.quote.mcap_yi if stock_data.quote else 0,
            current_price=stock_data.quote.price if stock_data.quote else 0,
            target_price=stock_data.quote.price * (1 + upside_ratio / 100) if stock_data.quote else 0,
            upside_ratio=upside_ratio
        )

    def _verify_evidence(self, candidate: ChokepointCandidate) -> Optional[ChokepointEvidence]:
        """
        兼容旧接口的证据验证方法（已升级为_verify_evidence_from_data）
        """
        return None

    # ==================== 报告输出 ====================

    def generate_human_readable_report(self) -> str:
        """
        生成人读版分析报告

        Returns:
            str: Markdown格式的报告
        """
        if not self.current_report:
            return "请先执行analyze()方法"

        report = self.current_report
        lines = []

        # 报告标题
        lines.append(f"# 【{report.industry_track}】Serenity瓶颈投资分析报告")
        lines.append(f"**分析日期**：{self.analysis_timestamp}")
        lines.append(f"**赛道确定性评级**：{report.trend_certainty.value}")
        lines.append(f"**核心终端驱动**：{', '.join(report.industry_trend.core_terminal_drivers) if report.industry_trend else '待分析'}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 一、产业大趋势验证
        lines.append("## 一、产业大趋势验证")
        if report.industry_trend:
            lines.append("### 1.1 趋势核心逻辑")
            lines.append(f"{report.industry_trend.name}")
            lines.append("")
            lines.append("### 1.2 资本开支与落地数据验证")
            vd = report.industry_trend.verification_data
            lines.append(f"- 头部企业资本开支计划：{'✅ 已验证' if vd.get('capex_verified') else '❌ 未验证'}")
            lines.append(f"- 月度/季度真实数据：{'✅ 已验证' if vd.get('data_verified') else '❌ 未验证'}")
            lines.append(f"- 趋势不可逆性：{'✅ 已验证' if vd.get('irreversible') else '❌ 未验证'}")
            lines.append("")
            lines.append("### 1.3 趋势确定性结论")
            lines.append(f"**确定性等级**：{report.trend_certainty.value}")
            lines.append(f"**核心驱动因子**：{', '.join(report.industry_trend.core_terminal_drivers)}")
            lines.append(f"**需求增速预测**：{report.industry_trend.demand_growth_rate}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 二、八层逆向产业链拆解
        lines.append("## 二、八层逆向产业链拆解")
        lines.append("### 2.1 完整逆向拆解链条")
        for layer in report.supply_chain_layers:
            lines.append(f"**第{layer.layer_num}层 - {layer.layer_name}**")
            lines.append(f"- 核心产品：{', '.join(layer.core_products)}")
            lines.append(f"- 关键供应商：{', '.join(layer.key_suppliers)}")
            lines.append(f"- 瓶颈问题：{layer.bottleneck_question}")
            lines.append("")
        lines.append("")

        # 三、物理四问硬性筛选结果
        lines.append("## 三、物理四问硬性筛选结果")
        lines.append("| 候选环节 | 物理必需 | 供给刚性 | 格局垄断 | 市场忽视 | 是否通过 | 淘汰原因 |")
        lines.append("|----------|----------|----------|----------|----------|----------|----------|")
        for c in report.chokepoint_candidates:
            lines.append(f"| {c.name} | {'✅' if c.physical_essential else '❌'} | "
                       f"{c.supply_rigidity.value} | {'✅' if c.market_monopoly else '❌'} | "
                       f"{'✅' if c.market_neglected else '❌'} | {'是' if c.passed else '否'} | "
                       f"{c.elimination_reason} |")
        lines.append("")
        lines.append("### 3.1 通过筛选的核心瓶颈环节详解")
        passed_candidates = [c for c in report.chokepoint_candidates if c.passed]
        for c in passed_candidates:
            lines.append(f"**{c.name}**（第{c.layer_num}层）")
            lines.append(f"- 成本占比：{c.cost_ratio}%")
            lines.append(f"- 全球供应商数：{c.global_suppliers_count}家")
            lines.append(f"- 行业CR3：{c.industry_cr3}%")
            lines.append(f"- 产能扩张周期：{c.capacity_expansion_cycle}个月")
            lines.append("")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 四、商业化落地证据验证
        lines.append("## 四、商业化落地证据验证")
        lines.append("| 对应标的 | 证据等级 | 核心验证点 | 业绩弹性测算 |")
        lines.append("|----------|----------|------------|--------------|")
        if report.chokepoint_evidences:
            for e in report.chokepoint_evidences:
                lines.append(f"| {e.stock_name}({e.stock_code}) | {e.evidence_level.value} | "
                           f"{', '.join(e.core_verification_points)} | {e.performance_elasticity} |")
        else:
            lines.append("| - | - | 待深入验证 | - |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 五、红队证伪与风险清单
        lines.append("## 五、红队证伪与风险清单")
        lines.append("| 风险类型 | 风险描述 | 发生概率 | 影响程度 | 核心跟踪指标 |")
        lines.append("|----------|----------|----------|----------|--------------|")
        if report.risk_assessments:
            for r in report.risk_assessments:
                lines.append(f"| {r.risk_type} | {r.risk_description} | "
                           f"{r.probability.value} | {r.impact.value} | "
                           f"{', '.join(r.tracking_indicators)} |")
        else:
            lines.append("| - | - | - | - | - |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 六、最终投资决策
        lines.append("## 六、最终投资决策")
        lines.append("### 6.1 标的投资优先级排序")
        lines.append("| 优先级 | 标的名称 | 投资评级 | 预期赔率 | 建议仓位 |")
        lines.append("|--------|----------|----------|----------|----------|")
        if report.investment_decisions:
            for d in report.investment_decisions:
                lines.append(f"| {d.priority} | {d.stock_name}({d.stock_code}) | "
                           f"{d.rating.value} | {d.expected_return} | {d.suggested_position} |")
        else:
            lines.append("| - | - | - | - | - |")
        lines.append("")
        lines.append("### 6.2 买入与卖出纪律")
        if report.investment_decisions:
            for d in report.investment_decisions:
                lines.append(f"**{d.stock_name}**")
                lines.append(f"- 核心买入条件：{', '.join(d.buy_conditions)}")
                lines.append(f"- 核心卖出条件：{', '.join(d.sell_conditions)}")
                lines.append("")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 第二部分：知识库存储版（分隔输出）
        lines.append("# ========================================")
        lines.append("# 第二部分：知识库存储版")
        lines.append("# ========================================")
        lines.append("")
        lines.append(self._generate_knowledge_base_section())

        return "\n".join(lines)

    def _generate_knowledge_base_section(self) -> str:
        """生成知识库存储版"""
        report = self.current_report
        if not report:
            return ""

        lines = []
        lines.append("---")
        lines.append(f"industry_track: {report.industry_track}")
        lines.append(f"trend_certainty: {report.trend_certainty.value}")
        lines.append(f"drive_type: {report.industry_trend.trend_type.value if report.industry_trend else '待分析'}")
        lines.append(f"data_date: {report.data_date}")
        lines.append(f'tags: ["瓶颈投资", "紫苏叶理论"]')
        lines.append(f"chokepoint_count: {report.chokepoint_count}")
        lines.append("---")
        lines.append("")
        lines.append("# 趋势基础信息")
        if report.industry_trend:
            lines.append(f"- 核心终端驱动：{', '.join(report.industry_trend.core_terminal_drivers)}")
            lines.append(f"- 核心资本开支主体：{', '.join(report.industry_trend.core_capex_entities)}")
            lines.append(f"- 需求增速预测：{report.industry_trend.demand_growth_rate}")
            lines.append(f"- 趋势周期：{report.industry_trend.trend_cycle}")
        lines.append("")
        lines.append("## 核心瓶颈环节清单")
        for c in report.chokepoint_candidates:
            if c.passed:
                lines.append(f"### {c.name}")
                lines.append(f"- 所属产业链层级：第{c.layer_num}层")
                lines.append(f"- 核心产品：{c.chain_position}")
                lines.append(f"- 物理必需性：{'是' if c.physical_essential else '否'}")
                lines.append(f"- 供给刚性等级：{c.supply_rigidity.value}")
                lines.append(f"- 行业CR3：{c.industry_cr3}%")
                lines.append(f"- 产能释放周期：{c.capacity_expansion_cycle}个月")
                lines.append(f"- 国产替代率：待评估")
                lines.append(f"- 代表标的：待确认")
                lines.append(f"- 标的市值：{c.market_cap_min}-{c.market_cap_max}亿")
                evidence = self._get_evidence_for_candidate(c.name)
                lines.append(f"- 证据等级：{evidence.evidence_level.value if evidence else '待验证'}")
                lines.append(f"- 市场认知度：{'低' if c.market_neglected else '高'}")
                lines.append(f"- 投资评级：{self._get_rating_for_candidate(c.name)}")
                lines.append("")
        lines.append("")
        lines.append("## 核心风险")
        for r in report.risk_assessments[:3]:  # 只取前3个主要风险
            lines.append(f"- {r.risk_type}：{r.risk_description}（概率:{r.probability.value}，影响:{r.impact.value}）")
        lines.append("")
        lines.append("## 交易关键节点")
        if report.investment_decisions:
            for d in report.investment_decisions:
                lines.append(f"- **{d.stock_name}**")
                lines.append(f"  - 买入触发条件：{', '.join(d.buy_conditions)}")
                lines.append(f"  - 卖出触发条件：{', '.join(d.sell_conditions)}")
                lines.append(f"  - 核心跟踪指标：待设定")
        return "\n".join(lines)

    def _get_evidence_for_candidate(self, candidate_name: str) -> Optional[ChokepointEvidence]:
        """获取候选环节的证据"""
        for e in self.current_report.chokepoint_evidences:
            if candidate_name in e.stock_name:
                return e
        return None

    def _get_rating_for_candidate(self, candidate_name: str) -> str:
        """获取候选环节的评级"""
        for d in self.current_report.investment_decisions:
            if candidate_name in d.stock_name:
                return d.rating.value
        return "待评估"

    def generate_knowledge_base_only(self) -> str:
        """
        仅生成知识库存储版

        Returns:
            str: Markdown格式的知识库文件
        """
        return self._generate_knowledge_base_section()

    def save_report(self, filepath: str, include_human_readable: bool = True):
        """
        保存报告到文件

        Args:
            filepath: 文件路径
            include_human_readable: 是否包含人读版
        """
        content = self.generate_human_readable_report() if include_human_readable else self.generate_knowledge_base_only()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[Serenity] 报告已保存至：{filepath}")

    def get_summary(self) -> Dict[str, Any]:
        """
        获取分析摘要

        Returns:
            Dict: 摘要信息
        """
        if not self.current_report:
            return {}

        report = self.current_report
        return {
            "赛道": report.industry_track,
            "趋势确定性": report.trend_certainty.value,
            "瓶颈环节数量": report.chokepoint_count,
            "通过筛选数量": len([c for c in report.chokepoint_candidates if c.passed]),
            "投资机会数量": len(report.investment_decisions),
            "强烈推荐数量": len([d for d in report.investment_decisions if d.rating == InvestmentRating.STRONG_BUY])
        }


# ==================== 便捷函数 ====================

def analyze_chokepoint(industry_track: str, trend_data: Dict) -> SerenityReport:
    """
    便捷函数：执行瓶颈点分析

    Args:
        industry_track: 赛道名称
        trend_data: 趋势数据

    Returns:
        SerenityReport: 分析报告
    """
    analyzer = SerenityChokepointAnalyzer()
    return analyzer.analyze(industry_track, trend_data)


def analyze_track(track_name: str) -> SerenityReport:
    """
    便捷函数：从产业链数据库直接分析赛道

    Args:
        track_name: 赛道名称

    Returns:
        SerenityReport: 分析报告
    """
    analyzer = SerenityChokepointAnalyzer()
    return analyzer.analyze_from_database(track_name)


def list_tracks() -> List[str]:
    """便捷函数：列出所有可用赛道"""
    return list_all_tracks()


def generate_sample_report() -> str:
    """
    生成示例报告（用于测试）

    Returns:
        str: 示例报告内容
    """
    sample_data = {
        "trend_name": "AI算力需求爆发",
        "has_capex_plan": True,
        "has_real_data": True,
        "is_irreversible": True,
        "is_tech_driven": True,
        "terminal_drivers": ["大模型训练", "AI推理应用", "数据中心扩张"],
        "capex_entities": ["微软", "谷歌", "亚马逊", "Meta"],
        "growth_rate": "年复合增速50%+",
        "trend_cycle": "3-5年",
        "chain_breakdown": [
            {
                "layer_num": 1,
                "layer_name": "终端需求",
                "core_products": ["AI服务器", "GPU集群"],
                "key_suppliers": ["英伟达", "AMD"],
                "bottleneck_question": "缺了GPU算力，整个AI产业就无法运转"
            },
            {
                "layer_num": 2,
                "layer_name": "系统集成/OEM整机",
                "core_products": ["AI服务器整机"],
                "key_suppliers": ["浪潮信息", "戴尔", "HPE"],
                "bottleneck_question": "缺了特定规格的服务器，数据中心建设就延期"
            },
            {
                "layer_num": 3,
                "layer_name": "模块与子系统",
                "core_products": ["GPU模块", "高速互联模块"],
                "key_suppliers": ["英伟达", "富士康"],
                "bottleneck_question": "缺了NVLink互联技术，多GPU协作效率大幅下降"
            },
            {
                "layer_num": 4,
                "layer_name": "核心芯片与元器件",
                "core_products": ["GPU", "CPU", "FPGA"],
                "key_suppliers": ["英伟达", "英特尔", "AMD"],
                "bottleneck_question": "缺了HBM显存，GPU性能将大幅下滑"
            },
            {
                "layer_num": 5,
                "layer_name": "封装/组装/测试",
                "core_products": ["先进封装", "CoWoS"],
                "key_suppliers": ["台积电", "日月光"],
                "bottleneck_question": "缺了CoWoS封装，HBM无法与GPU集成"
            },
            {
                "layer_num": 6,
                "layer_name": "生产设备与计量仪器",
                "core_products": ["光刻机", "刻蚀机", "镀膜设备"],
                "key_suppliers": ["ASML", "应用材料", "东京电子"],
                "bottleneck_question": "缺了EUV光刻机，先进制程就无法生产"
            },
            {
                "layer_num": 7,
                "layer_name": "核心材料与耗材",
                "core_products": ["光刻胶", "硅片", "电子特气"],
                "key_suppliers": ["信越化学", "陶氏", "信义玻璃"],
                "bottleneck_question": "缺了特定规格的光刻胶，晶圆良率大幅下降"
            },
            {
                "layer_num": 8,
                "layer_name": "物理基础设施",
                "core_products": ["工业冷水", "电力设施", "洁净室"],
                "key_suppliers": ["各地能源公司"],
                "bottleneck_question": "缺了足够电力供应，超算中心无法满载运行"
            }
        ],
        "candidates": [
            {
                "name": "HBM内存",
                "layer_num": 7,
                "chain_position": "核心材料/存储芯片",
                "required_per_unit": True,
                "no_substitute_3y": True,
                "cost_ratio": 2.5,
                "global_suppliers": 3,
                "cr3": 95,
                "capacity_util": 90,
                "expansion_cycle": 24,
                "top1_share": 50,
                "top2_sum": 90,
                "new_entrants_2y": 0,
                "gross_margin": 55,
                "mktcap_min": 50,
                "mktcap_max": 150,
                "covered_brokers": 5,
                "fund_holding": 2,
                "recent_gain_6m": 30
            },
            {
                "name": "CoWoS封装",
                "layer_num": 5,
                "chain_position": "先进封装",
                "required_per_unit": True,
                "no_substitute_3y": True,
                "cost_ratio": 3,
                "global_suppliers": 2,
                "cr3": 90,
                "capacity_util": 85,
                "expansion_cycle": 20,
                "top1_share": 60,
                "top2_sum": 85,
                "new_entrants_2y": 0,
                "gross_margin": 45,
                "mktcap_min": 30,
                "mktcap_max": 100,
                "covered_brokers": 8,
                "fund_holding": 3,
                "recent_gain_6m": 50
            },
            {
                "name": "EUV光刻机",
                "layer_num": 6,
                "chain_position": "核心设备",
                "required_per_unit": True,
                "no_substitute_3y": True,
                "cost_ratio": 1,
                "global_suppliers": 1,
                "cr3": 100,
                "capacity_util": 95,
                "expansion_cycle": 36,
                "top1_share": 100,
                "top2_sum": 100,
                "new_entrants_2y": 0,
                "gross_margin": 65,
                "mktcap_min": 500,
                "mktcap_max": 2000,
                "covered_brokers": 20,
                "fund_holding": 8,
                "recent_gain_6m": 80
            },
            {
                "name": "光刻胶",
                "layer_num": 7,
                "chain_position": "关键材料",
                "required_per_unit": True,
                "no_substitute_3y": True,
                "cost_ratio": 0.5,
                "global_suppliers": 5,
                "cr3": 75,
                "capacity_util": 80,
                "expansion_cycle": 18,
                "top1_share": 35,
                "top2_sum": 65,
                "new_entrants_2y": 1,
                "gross_margin": 38,
                "mktcap_min": 20,
                "mktcap_max": 80,
                "covered_brokers": 12,
                "fund_holding": 6,
                "recent_gain_6m": 20
            }
        ]
    }

    analyzer = SerenityChokepointAnalyzer()
    analyzer.analyze("AI算力产业链", sample_data)

    # 添加模拟证据
    from dataclasses import replace
    analyzer.current_report.chokepoint_evidences = [
        ChokepointEvidence(
            stock_code="001896",
            stock_name="某封装龙头",
            evidence_level=EvidenceLevel.STRONG,
            core_verification_points=["收到英伟达正式订单", "产能持续爬坡", "毛利率连续两季度上升"],
            performance_elasticity="业绩弹性3-5倍",
            market_cap=80,
            current_price=45,
            target_price=90,
            upside_ratio=100
        ),
        ChokepointEvidence(
            stock_code="002371",
            stock_name="某特种气体",
            evidence_level=EvidenceLevel.MEDIUM,
            core_verification_points=["通过台积电认证", "小批量供货"],
            performance_elasticity="业绩弹性1-2倍",
            market_cap=50,
            current_price=25,
            target_price=40,
            upside_ratio=60
        )
    ]

    # 添加模拟投资决策
    analyzer.current_report.investment_decisions = [
        InvestmentDecision(
            stock_code="001896",
            stock_name="某封装龙头",
            priority=1,
            rating=InvestmentRating.STRONG_BUY,
            expected_return="100%+",
            suggested_position="重仓",
            buy_conditions=["回调至40元以下", "成交量放大", "英伟达新订单公告"],
            sell_conditions=["达到目标价90元", "逻辑证伪", "封装技术被绕过"]
        ),
        InvestmentDecision(
            stock_code="002371",
            stock_name="某特种气体",
            priority=2,
            rating=InvestmentRating.BUY,
            expected_return="60%",
            suggested_position="底仓",
            buy_conditions=["回调至20元以下", "机构进场"],
            sell_conditions=["达到目标价40元", "新进入者量产"]
        )
    ]

    return analyzer.generate_human_readable_report()


# ==================== 主入口 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Serenity瓶颈点投资分析系统 v2.0 (增强版)")
    print("=" * 60)
    print()

    # 列出可用赛道
    tracks = list_tracks()
    print(f"可用赛道数量：{len(tracks)}")
    for i, t in enumerate(tracks, 1):
        print(f"  {i}. {t}")
    print()

    # 选择一个赛道进行分析（使用第一个赛道）
    test_track = tracks[0]  # AI算力产业链
    print(f"正在分析赛道：{test_track}")
    print("-" * 60)

    try:
        # 执行分析
        report = analyze_track(test_track)
        analyzer = SerenityChokepointAnalyzer()
        analyzer.current_report = report

        # 生成报告
        print("\n正在生成分析报告...")
        full_report = analyzer.generate_human_readable_report()

        # 保存报告
        output_path = f"/Users/houpengyuan/Documents/trae_projects/a-stock-data/serenity_{test_track}_report.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        print(f"报告已保存至：{output_path}")

        # 打印摘要
        print()
        print("=" * 60)
        print("分析摘要")
        print("=" * 60)
        summary = analyzer.get_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"分析出错: {e}")
        import traceback
        traceback.print_exc()