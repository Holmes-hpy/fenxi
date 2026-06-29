"""
Serenity每日选股系统 v2.0

核心能力：
1. 策略库管理（多策略并存，支持手动调参）
2. 每日选股（基于Serenity分析框架）
3. 持续验证（T+1开始每日验证，直到止盈/止损/到期）
4. 策略淘汰（连续5次下跌 或 跌幅超10% → 深度复盘→优化→淘汰）
5. 每日复盘（对策略进行深度分析）

数据存储：
- strategies.json         策略库
- selections.json         选股记录
- strategy_performance.json 策略表现统计
- abandoned_strategies.json 已废弃策略（留档+复盘）
- daily_reviews/          每日复盘报告
"""

import sys
import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class StrategyStatus(Enum):
    """策略状态"""
    ACTIVE = "活跃"
    WARNING = "警告"
    PAUSED = "暂停"
    ABANDONED = "废弃"


class SelectionStatus(Enum):
    """选股记录状态"""
    PENDING = "待验证"       # 刚选入，还没到T+1
    VERIFYING = "验证中"     # T+1开始，每日验证
    WIN = "止盈"             # 达到止盈目标
    LOSS = "止损"            # 达到止损线
    EXPIRED = "到期"         # 超过最大持仓天数
    ABANDONED_TRIGGER = "触发淘汰"  # 该选股导致策略被淘汰


# ============================================================
# 数据结构定义
# ============================================================

@dataclass
class StrategyRiskControl:
    """策略风控参数"""
    stop_loss_pct: float = -10.0      # 止损线（%）
    take_profit_pct: float = 20.0     # 止盈线（%）
    max_hold_days: int = 20           # 最大持仓天数
    expected_return_pct: float = 15.0  # 预期涨幅（%）
    position_size_pct: float = 10.0    # 单只仓位（%）


@dataclass
class StrategyPerformance:
    """策略表现统计"""
    total_selections: int = 0         # 总选股次数
    win_count: int = 0                # 盈利次数
    loss_count: int = 0               # 亏损次数
    total_return_pct: float = 0.0     # 总收益（%）
    avg_return_pct: float = 0.0       # 平均收益（%）
    max_return_pct: float = 0.0       # 最大单笔盈利
    min_return_pct: float = 0.0       # 最大单笔亏损
    win_rate: float = 0.0             # 胜率
    profit_loss_ratio: float = 0.0    # 盈亏比
    consecutive_losses: int = 0       # 连续亏损次数
    max_consecutive_losses: int = 0   # 最大连续亏损
    current_streak: int = 0           # 当前连续次数（正=连胜，负=连败）


@dataclass
class Strategy:
    """选股策略"""
    strategy_id: str
    strategy_name: str
    description: str
    serenity_basis: str                # Serenity分析依据
    risk_control: StrategyRiskControl = field(default_factory=StrategyRiskControl)
    status: StrategyStatus = StrategyStatus.ACTIVE
    performance: StrategyPerformance = field(default_factory=StrategyPerformance)
    created_at: str = ""
    last_used_at: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""                   # 备注/优化记录

    def to_dict(self) -> Dict:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "description": self.description,
            "serenity_basis": self.serenity_basis,
            "risk_control": asdict(self.risk_control),
            "status": self.status.value,
            "performance": asdict(self.performance),
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "tags": self.tags,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Strategy':
        rc = StrategyRiskControl(**data.get("risk_control", {}))
        perf = StrategyPerformance(**data.get("performance", {}))
        status = StrategyStatus(data.get("status", "活跃"))
        return cls(
            strategy_id=data["strategy_id"],
            strategy_name=data["strategy_name"],
            description=data.get("description", ""),
            serenity_basis=data.get("serenity_basis", ""),
            risk_control=rc,
            status=status,
            performance=perf,
            created_at=data.get("created_at", ""),
            last_used_at=data.get("last_used_at", ""),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
        )


@dataclass
class StockSelection:
    """选股记录"""
    selection_id: str
    date: str                       # 选股日期（T日）
    stock_code: str
    stock_name: str
    strategy_id: str
    strategy_name: str
    selection_reason: str           # 选股理由（Serenity分析摘要）
    buy_price: float                # 买入参考价
    current_price: float = 0.0      # 当前价
    current_return_pct: float = 0.0 # 当前收益（%）
    max_return_pct: float = 0.0     # 期间最高收益
    min_return_pct: float = 0.0     # 期间最低收益
    status: SelectionStatus = SelectionStatus.PENDING
    hold_days: int = 0              # 已持仓天数
    final_return_pct: float = 0.0   # 最终收益
    closed_at: str = ""             # 平仓日期
    daily_prices: Dict[str, float] = field(default_factory=dict)  # 每日价格 {date: price}

    def to_dict(self) -> Dict:
        return {
            "selection_id": self.selection_id,
            "date": self.date,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "selection_reason": self.selection_reason,
            "buy_price": self.buy_price,
            "current_price": self.current_price,
            "current_return_pct": self.current_return_pct,
            "max_return_pct": self.max_return_pct,
            "min_return_pct": self.min_return_pct,
            "status": self.status.value,
            "hold_days": self.hold_days,
            "final_return_pct": self.final_return_pct,
            "closed_at": self.closed_at,
            "daily_prices": self.daily_prices,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'StockSelection':
        status = SelectionStatus(data.get("status", "待验证"))
        return cls(
            selection_id=data["selection_id"],
            date=data["date"],
            stock_code=data["stock_code"],
            stock_name=data["stock_name"],
            strategy_id=data["strategy_id"],
            strategy_name=data["strategy_name"],
            selection_reason=data.get("selection_reason", ""),
            buy_price=data["buy_price"],
            current_price=data.get("current_price", 0),
            current_return_pct=data.get("current_return_pct", 0),
            max_return_pct=data.get("max_return_pct", 0),
            min_return_pct=data.get("min_return_pct", 0),
            status=status,
            hold_days=data.get("hold_days", 0),
            final_return_pct=data.get("final_return_pct", 0),
            closed_at=data.get("closed_at", ""),
            daily_prices=data.get("daily_prices", {}),
        )


@dataclass
class AbandonedStrategyReview:
    """废弃策略深度复盘"""
    strategy_id: str
    strategy_name: str
    abandoned_date: str
    trigger_reason: str              # 触发淘汰的原因
    total_selections: int
    win_rate: float
    total_return_pct: float
    max_consecutive_losses: int
    cause_analysis: str              # 原因分析
    optimization_suggestions: List[str] = field(default_factory=list)  # 优化建议
    lessons_learned: List[str] = field(default_factory=list)          # 经验教训
    new_strategy_derived: str = ""   # 衍生出的新策略ID


# ============================================================
# 策略库管理模块
# ============================================================

class StrategyManager:
    """
    策略库管理器

    负责策略的增删改查、参数调整、状态管理
    """

    def __init__(self, data_dir: str = "serenity_stock_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.strategies_file = self.data_dir / "strategies.json"
        self.abandoned_file = self.data_dir / "abandoned_strategies.json"
        self.strategies: Dict[str, Strategy] = {}
        self.abandoned_reviews: List[AbandonedStrategyReview] = []
        self._load()

    def _load(self):
        """加载策略库"""
        if self.strategies_file.exists():
            with open(self.strategies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for sid, sdata in data.items():
                    self.strategies[sid] = Strategy.from_dict(sdata)

        if self.abandoned_file.exists():
            with open(self.abandoned_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    review = AbandonedStrategyReview(
                        strategy_id=item["strategy_id"],
                        strategy_name=item["strategy_name"],
                        abandoned_date=item["abandoned_date"],
                        trigger_reason=item["trigger_reason"],
                        total_selections=item.get("total_selections", 0),
                        win_rate=item.get("win_rate", 0),
                        total_return_pct=item.get("total_return_pct", 0),
                        max_consecutive_losses=item.get("max_consecutive_losses", 0),
                        cause_analysis=item.get("cause_analysis", ""),
                        optimization_suggestions=item.get("optimization_suggestions", []),
                        lessons_learned=item.get("lessons_learned", []),
                        new_strategy_derived=item.get("new_strategy_derived", ""),
                    )
                    self.abandoned_reviews.append(review)

        # 如果是空库，初始化默认策略
        if not self.strategies:
            self._init_default_strategies()

    def _save(self):
        """保存策略库"""
        data = {sid: s.to_dict() for sid, s in self.strategies.items()}
        with open(self.strategies_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存废弃策略复盘
        abandoned_data = []
        for review in self.abandoned_reviews:
            abandoned_data.append({
                "strategy_id": review.strategy_id,
                "strategy_name": review.strategy_name,
                "abandoned_date": review.abandoned_date,
                "trigger_reason": review.trigger_reason,
                "total_selections": review.total_selections,
                "win_rate": review.win_rate,
                "total_return_pct": review.total_return_pct,
                "max_consecutive_losses": review.max_consecutive_losses,
                "cause_analysis": review.cause_analysis,
                "optimization_suggestions": review.optimization_suggestions,
                "lessons_learned": review.lessons_learned,
                "new_strategy_derived": review.new_strategy_derived,
            })
        with open(self.abandoned_file, 'w', encoding='utf-8') as f:
            json.dump(abandoned_data, f, ensure_ascii=False, indent=2)

    def _init_default_strategies(self):
        """初始化默认策略"""
        today = datetime.now().strftime('%Y-%m-%d')

        default_strategies = [
            Strategy(
                strategy_id="S001",
                strategy_name="瓶颈选股-等权策略",
                description="基于Serenity物理四问筛选，等权持有",
                serenity_basis="物理四问综合评分≥70分 + 证据强度≥中等",
                risk_control=StrategyRiskControl(
                    stop_loss_pct=-10.0,
                    take_profit_pct=25.0,
                    max_hold_days=30,
                    expected_return_pct=15.0,
                    position_size_pct=10.0,
                ),
                status=StrategyStatus.ACTIVE,
                created_at=today,
                tags=["瓶颈", "等权", "物理四问"],
            ),
            Strategy(
                strategy_id="S002",
                strategy_name="认知差修复策略",
                description="寻找市场认知差较大的标的，等待认知修复",
                serenity_basis="认知差程度≥60分 + 有明确催化剂",
                risk_control=StrategyRiskControl(
                    stop_loss_pct=-12.0,
                    take_profit_pct=30.0,
                    max_hold_days=45,
                    expected_return_pct=20.0,
                    position_size_pct=8.0,
                ),
                status=StrategyStatus.ACTIVE,
                created_at=today,
                tags=["认知差", "修复", "催化剂"],
            ),
            Strategy(
                strategy_id="S003",
                strategy_name="事件驱动策略",
                description="基于重大事件（封锁/政策/订单）驱动的选股",
                serenity_basis="三级证据验证为强 + 事件影响等级高",
                risk_control=StrategyRiskControl(
                    stop_loss_pct=-8.0,
                    take_profit_pct=20.0,
                    max_hold_days=15,
                    expected_return_pct=12.0,
                    position_size_pct=12.0,
                ),
                status=StrategyStatus.ACTIVE,
                created_at=today,
                tags=["事件驱动", "强证据"],
            ),
            Strategy(
                strategy_id="S004",
                strategy_name="产业趋势策略",
                description="基于产业政策和供需缺口的中长期选股",
                serenity_basis="行业政策支持 + 供需缺口扩大 + 国产替代加速",
                risk_control=StrategyRiskControl(
                    stop_loss_pct=-15.0,
                    take_profit_pct=40.0,
                    max_hold_days=60,
                    expected_return_pct=25.0,
                    position_size_pct=10.0,
                ),
                status=StrategyStatus.ACTIVE,
                created_at=today,
                tags=["产业趋势", "政策", "国产替代"],
            ),
            Strategy(
                strategy_id="S005",
                strategy_name="低估值修复策略",
                description="寻找被错杀的低估标的，等待估值修复",
                serenity_basis="PE/PB低于行业均值30% + 基本面稳健",
                risk_control=StrategyRiskControl(
                    stop_loss_pct=-10.0,
                    take_profit_pct=20.0,
                    max_hold_days=30,
                    expected_return_pct=12.0,
                    position_size_pct=10.0,
                ),
                status=StrategyStatus.ACTIVE,
                created_at=today,
                tags=["低估", "修复", "价值"],
            ),
        ]

        for s in default_strategies:
            self.strategies[s.strategy_id] = s

        self._save()

    def get_active_strategies(self) -> List[Strategy]:
        """获取所有活跃策略"""
        return [s for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE]

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """获取指定策略"""
        return self.strategies.get(strategy_id)

    def update_strategy_params(self, strategy_id: str, **params) -> bool:
        """
        手动调整策略参数

        支持调整的参数：
        - stop_loss_pct: 止损线
        - take_profit_pct: 止盈线
        - max_hold_days: 最大持仓天数
        - expected_return_pct: 预期涨幅
        - position_size_pct: 单只仓位
        - description: 描述
        - notes: 备注
        """
        if strategy_id not in self.strategies:
            return False

        strategy = self.strategies[strategy_id]

        # 风控参数
        rc_params = ["stop_loss_pct", "take_profit_pct", "max_hold_days",
                     "expected_return_pct", "position_size_pct"]
        for param in rc_params:
            if param in params:
                setattr(strategy.risk_control, param, params[param])

        # 其他参数
        if "description" in params:
            strategy.description = params["description"]
        if "notes" in params:
            strategy.notes = params["notes"]
        if "tags" in params:
            strategy.tags = params["tags"]

        self._save()
        return True

    def pause_strategy(self, strategy_id: str) -> bool:
        """暂停策略"""
        if strategy_id not in self.strategies:
            return False
        self.strategies[strategy_id].status = StrategyStatus.PAUSED
        self._save()
        return True

    def activate_strategy(self, strategy_id: str) -> bool:
        """激活策略"""
        if strategy_id not in self.strategies:
            return False
        self.strategies[strategy_id].status = StrategyStatus.ACTIVE
        self._save()
        return True

    def add_strategy(self, strategy: Strategy) -> bool:
        """添加新策略"""
        if strategy.strategy_id in self.strategies:
            return False
        self.strategies[strategy.strategy_id] = strategy
        self._save()
        return True

    def get_strategy_list_report(self) -> str:
        """生成策略列表报告"""
        lines = []
        lines.append("【策略库概览】")
        lines.append("-" * 60)
        lines.append("")

        active = [s for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE]
        warning = [s for s in self.strategies.values() if s.status == StrategyStatus.WARNING]
        paused = [s for s in self.strategies.values() if s.status == StrategyStatus.PAUSED]
        abandoned = len(self.abandoned_reviews)

        lines.append(f"策略总数: {len(self.strategies)}")
        lines.append(f"  活跃: {len(active)}")
        lines.append(f"  警告: {len(warning)}")
        lines.append(f"  暂停: {len(paused)}")
        lines.append(f"  已废弃: {abandoned}")
        lines.append("")

        lines.append("活跃策略详情：")
        lines.append("")
        for s in active:
            perf = s.performance
            lines.append(f"  🟢 [{s.strategy_id}] {s.strategy_name}")
            lines.append(f"     描述: {s.description}")
            lines.append(f"     Serenity依据: {s.serenity_basis}")
            lines.append(f"     风控: 止损{s.risk_control.stop_loss_pct}% / 止盈{s.risk_control.take_profit_pct}% / 最多{s.risk_control.max_hold_days}天")
            lines.append(f"     表现: 总选股{perf.total_selections}次 / 胜率{perf.win_rate:.1f}% / 盈亏比{perf.profit_loss_ratio:.2f}")
            if perf.consecutive_losses > 0:
                lines.append(f"     ⚠️  当前连续亏损: {perf.consecutive_losses}次")
            lines.append("")

        if warning:
            lines.append("警告策略：")
            lines.append("")
            for s in warning:
                lines.append(f"  🟡 [{s.strategy_id}] {s.strategy_name}")
                lines.append(f"     连续亏损: {s.performance.consecutive_losses}次")
                lines.append("")

        return "\n".join(lines)


# ============================================================
# 选股记录管理器
# ============================================================

class SelectionManager:
    """
    选股记录管理器

    负责选股记录的存储、查询、更新
    """

    def __init__(self, data_dir: str = "serenity_stock_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.selections_file = self.data_dir / "selections.json"
        self.selections: Dict[str, StockSelection] = {}
        self._load()

    def _load(self):
        """加载选股记录"""
        if self.selections_file.exists():
            with open(self.selections_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for sid, sdata in data.items():
                    self.selections[sid] = StockSelection.from_dict(sdata)

    def _save(self):
        """保存选股记录"""
        data = {sid: s.to_dict() for sid, s in self.selections.items()}
        with open(self.selections_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_selection(self, selection: StockSelection):
        """添加选股记录"""
        self.selections[selection.selection_id] = selection
        self._save()

    def get_pending_selections(self) -> List[StockSelection]:
        """获取待验证的选股（刚选入，还没开始验证）"""
        return [s for s in self.selections.values() if s.status == SelectionStatus.PENDING]

    def get_verifying_selections(self) -> List[StockSelection]:
        """获取验证中的选股"""
        return [s for s in self.selections.values() if s.status == SelectionStatus.VERIFYING]

    def get_active_selections(self) -> List[StockSelection]:
        """获取所有活跃选股（待验证+验证中）"""
        return [s for s in self.selections.values()
                if s.status in (SelectionStatus.PENDING, SelectionStatus.VERIFYING)]

    def get_selections_by_strategy(self, strategy_id: str) -> List[StockSelection]:
        """获取指定策略的所有选股"""
        return [s for s in self.selections.values() if s.strategy_id == strategy_id]

    def update_selection_price(self, selection_id: str, date: str, price: float):
        """更新选股的价格数据"""
        if selection_id not in self.selections:
            return

        sel = self.selections[selection_id]
        sel.daily_prices[date] = price
        sel.current_price = price

        if sel.buy_price > 0:
            sel.current_return_pct = (price / sel.buy_price - 1) * 100

        # 更新最高/最低收益
        if sel.current_return_pct > sel.max_return_pct:
            sel.max_return_pct = sel.current_return_pct
        if sel.current_return_pct < sel.min_return_pct:
            sel.min_return_pct = sel.current_return_pct

        self._save()

    def close_selection(self, selection_id: str, status: SelectionStatus,
                        final_price: float, close_date: str):
        """平仓选股记录"""
        if selection_id not in self.selections:
            return

        sel = self.selections[selection_id]
        sel.status = status
        sel.final_return_pct = (final_price / sel.buy_price - 1) * 100
        sel.closed_at = close_date
        sel.current_price = final_price
        sel.current_return_pct = sel.final_return_pct

        self._save()

    def get_today_selections(self, today: str = None) -> List[StockSelection]:
        """获取今日选股"""
        if today is None:
            today = datetime.now().strftime('%Y-%m-%d')
        return [s for s in self.selections.values() if s.date == today]


# ============================================================
# 每日选股引擎
# ============================================================

class DailyStockPicker:
    """
    每日选股引擎 v2.0

    选股→验证→淘汰→复盘 完整闭环
    """

    def __init__(self, data_dir: str = "serenity_stock_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.review_dir = self.data_dir / "daily_reviews"
        self.review_dir.mkdir(exist_ok=True)

        self.strategy_mgr = StrategyManager(data_dir)
        self.selection_mgr = SelectionManager(data_dir)

        # 淘汰阈值配置
        self.abandon_thresholds = {
            "consecutive_losses": 5,      # 连续5次亏损
            "max_drawdown_pct": -10.0,    # 单只跌幅超10%
            "min_win_rate": 0.3,          # 最低胜率30%
            "min_pl_ratio": 0.5,          # 最低盈亏比0.5
        }

    def generate_selection_id(self, date: str, code: str) -> str:
        """生成选股ID"""
        return f"SEL_{date}_{code}"

    def daily_selection(self, candidates: List[Dict], today: str = None) -> List[StockSelection]:
        """
        每日选股

        Args:
            candidates: 候选股票列表 [{"code":..., "name":..., "reason":..., "strategy_id":...}]
            today: 选股日期

        Returns:
            List[StockSelection]: 今日选股记录
        """
        if today is None:
            today = datetime.now().strftime('%Y-%m-%d')

        selections = []

        for cand in candidates:
            code = cand.get("code", "")
            name = cand.get("name", "")
            strategy_id = cand.get("strategy_id", "S001")
            reason = cand.get("reason", "")
            price = cand.get("price", 0)

            strategy = self.strategy_mgr.get_strategy(strategy_id)
            if not strategy or strategy.status != StrategyStatus.ACTIVE:
                continue

            sel_id = self.generate_selection_id(today, code)

            if sel_id in self.selection_mgr.selections:
                continue  # 今天已经选过了

            selection = StockSelection(
                selection_id=sel_id,
                date=today,
                stock_code=code,
                stock_name=name,
                strategy_id=strategy_id,
                strategy_name=strategy.strategy_name,
                selection_reason=reason,
                buy_price=price,
                current_price=price,
            )

            self.selection_mgr.add_selection(selection)
            selections.append(selection)

            # 更新策略最后使用时间
            strategy.last_used_at = today

        return selections

    def daily_verification(self, price_data: Dict[str, float], today: str = None) -> Dict:
        """
        每日验证（核心：T+1开始每天验证）

        Args:
            price_data: {stock_code: price} 今日收盘价
            today: 验证日期

        Returns:
            Dict: 验证结果
        """
        if today is None:
            today = datetime.now().strftime('%Y-%m-%d')

        result = {
            "date": today,
            "verified_count": 0,
            "new_wins": 0,
            "new_losses": 0,
            "new_expired": 0,
            "warnings": [],
            "abandonments": [],
            "details": [],
        }

        # 1. 处理待验证的选股（T日选的，到了T+1转为验证中）
        pending = self.selection_mgr.get_pending_selections()
        for sel in pending:
            # 如果选股日期不是今天，说明已经过了一天，开始验证
            if sel.date < today:
                sel.status = SelectionStatus.VERIFYING
                sel.hold_days = 1
                if sel.stock_code in price_data:
                    price = price_data[sel.stock_code]
                    self.selection_mgr.update_selection_price(sel.selection_id, today, price)
                result["verified_count"] += 1

        # 2. 处理验证中的选股（每日检查止盈/止损/到期）
        verifying = self.selection_mgr.get_verifying_selections()

        for sel in verifying:
            if sel.stock_code not in price_data:
                continue

            price = price_data[sel.stock_code]
            self.selection_mgr.update_selection_price(sel.selection_id, today, price)
            sel.hold_days += 1

            strategy = self.strategy_mgr.get_strategy(sel.strategy_id)
            if not strategy:
                continue

            rc = strategy.risk_control
            return_pct = sel.current_return_pct

            # 检查止盈
            if return_pct >= rc.take_profit_pct:
                self.selection_mgr.close_selection(
                    sel.selection_id, SelectionStatus.WIN, price, today
                )
                result["new_wins"] += 1
                self._update_strategy_performance(strategy, True, return_pct)
                result["details"].append(f"✅ {sel.stock_name}止盈: +{return_pct:.2f}%")

            # 检查止损
            elif return_pct <= rc.stop_loss_pct:
                self.selection_mgr.close_selection(
                    sel.selection_id, SelectionStatus.LOSS, price, today
                )
                result["new_losses"] += 1
                self._update_strategy_performance(strategy, False, return_pct)
                result["details"].append(f"❌ {sel.stock_name}止损: {return_pct:.2f}%")

                # 检查是否触发策略淘汰
                abandon_result = self._check_strategy_abandonment(strategy, sel)
                if abandon_result:
                    result["abandonments"].append(abandon_result)

            # 检查到期
            elif sel.hold_days >= rc.max_hold_days:
                self.selection_mgr.close_selection(
                    sel.selection_id, SelectionStatus.EXPIRED, price, today
                )
                result["new_expired"] += 1
                is_win = return_pct > 0
                self._update_strategy_performance(strategy, is_win, return_pct)
                result["details"].append(f"⏰ {sel.stock_name}到期: {return_pct:.2f}%")

            result["verified_count"] += 1

        self.selection_mgr._save()
        self.strategy_mgr._save()

        return result

    def _update_strategy_performance(self, strategy: Strategy, is_win: bool, return_pct: float):
        """更新策略表现统计"""
        perf = strategy.performance
        perf.total_selections += 1

        if is_win:
            perf.win_count += 1
            perf.current_streak = max(0, perf.current_streak) + 1
            perf.consecutive_losses = 0
        else:
            perf.loss_count += 1
            perf.current_streak = min(0, perf.current_streak) - 1
            perf.consecutive_losses += 1
            if perf.consecutive_losses > perf.max_consecutive_losses:
                perf.max_consecutive_losses = perf.consecutive_losses

        perf.total_return_pct += return_pct
        perf.avg_return_pct = perf.total_return_pct / perf.total_selections

        if return_pct > perf.max_return_pct:
            perf.max_return_pct = return_pct
        if return_pct < perf.min_return_pct:
            perf.min_return_pct = return_pct

        if perf.total_selections > 0:
            perf.win_rate = perf.win_count / perf.total_selections * 100

            avg_win = perf.total_return_pct / perf.win_count if perf.win_count > 0 else 0
            avg_loss = abs(perf.total_return_pct / perf.loss_count) if perf.loss_count > 0 else 0
            if avg_loss > 0:
                perf.profit_loss_ratio = avg_win / avg_loss

        # 状态检查
        if perf.consecutive_losses >= 3 and strategy.status == StrategyStatus.ACTIVE:
            strategy.status = StrategyStatus.WARNING

    def _check_strategy_abandonment(self, strategy: Strategy, trigger_selection: StockSelection) -> Optional[Dict]:
        """
        检查策略是否需要淘汰

        淘汰条件：
        1. 连续5次下跌
        2. 单只跌幅超10%
        """
        perf = strategy.performance
        should_abandon = False
        reason = ""

        # 条件1：连续5次亏损
        if perf.consecutive_losses >= self.abandon_thresholds["consecutive_losses"]:
            should_abandon = True
            reason = f"连续{perf.consecutive_losses}次亏损"

        # 条件2：单只跌幅超10%
        if trigger_selection.current_return_pct <= self.abandon_thresholds["max_drawdown_pct"]:
            should_abandon = True
            reason = f"单只跌幅达{trigger_selection.current_return_pct:.2f}%"

        if should_abandon and strategy.status != StrategyStatus.ABANDONED:
            # 执行深度复盘
            review = self._deep_review_abandoned_strategy(strategy, reason, trigger_selection)
            strategy.status = StrategyStatus.ABANDONED
            self.strategy_mgr.abandoned_reviews.append(review)
            self.strategy_mgr._save()

            return {
                "strategy_id": strategy.strategy_id,
                "strategy_name": strategy.strategy_name,
                "reason": reason,
                "review": review,
            }

        return None

    def _deep_review_abandoned_strategy(
        self, strategy: Strategy, trigger_reason: str, trigger_selection: StockSelection
    ) -> AbandonedStrategyReview:
        """
        对废弃策略进行深度复盘

        分析内容：
        1. 原因分析
        2. 优化建议
        3. 经验教训
        4. 衍生新策略的方向
        """
        perf = strategy.performance

        # 原因分析
        cause_analysis = f"""
【策略{strategy.strategy_id}深度复盘】

触发原因：{trigger_reason}

历史表现：
- 总选股次数: {perf.total_selections}
- 胜率: {perf.win_rate:.2f}%
- 盈亏比: {perf.profit_loss_ratio:.2f}
- 总收益: {perf.total_return_pct:.2f}%
- 最大连续亏损: {perf.max_consecutive_losses}次
- 最大单笔亏损: {perf.min_return_pct:.2f}%

可能原因分析：
1. 选股逻辑问题：
   - Serenity依据: {strategy.serenity_basis}
   - 可能物理四问评分标准过松
   - 可能证据强度要求太低

2. 风控参数问题：
   - 止损线: {strategy.risk_control.stop_loss_pct}%
   - 止盈线: {strategy.risk_control.take_profit_pct}%
   - 可能止损线太宽，单笔亏损过大
   - 可能止盈线太高，难以达到

3. 市场环境问题：
   - 可能策略与当前市场风格不匹配
   - 可能行业β影响过大

4. 样本量问题：
   - 总样本{perf.total_selections}次，可能样本不足
"""

        # 优化建议
        optimizations = [
            "提高物理四问入选门槛（从70分提高到75分）",
            "加强证据验证要求（至少2个强证据）",
            "收紧止损线（从10%调整为8%）",
            "增加行业分散度，避免单一行业风险",
            "加入市场环境过滤（熊市降低仓位）",
        ]

        # 经验教训
        lessons = [
            "连续亏损是策略失效的重要信号，不应抱有侥幸心理",
            "单只跌幅超过10%说明选股逻辑可能有根本性问题",
            "策略不是一成不变的，需要持续验证和优化",
            "Serenity分析框架需要与市场反馈结合，不能教条主义",
            "样本量不足时不要过度自信，需要更多验证",
        ]

        review = AbandonedStrategyReview(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name,
            abandoned_date=datetime.now().strftime('%Y-%m-%d'),
            trigger_reason=trigger_reason,
            total_selections=perf.total_selections,
            win_rate=perf.win_rate,
            total_return_pct=perf.total_return_pct,
            max_consecutive_losses=perf.max_consecutive_losses,
            cause_analysis=cause_analysis,
            optimization_suggestions=optimizations,
            lessons_learned=lessons,
        )

        return review

    def generate_daily_review(self, today: str = None) -> str:
        """
        生成每日复盘报告

        包含：
        - 今日选股情况
        - 验证结果
        - 策略表现排名
        - 策略预警
        - 深度分析
        """
        if today is None:
            today = datetime.now().strftime('%Y-%m-%d')

        lines = []
        lines.append("=" * 70)
        lines.append("  Serenity每日选股复盘报告")
        lines.append(f"  日期: {today}")
        lines.append("=" * 70)
        lines.append("")

        # ===== 今日选股 =====
        today_selections = self.selection_mgr.get_today_selections(today)
        lines.append("【一、今日选股情况】")
        lines.append("-" * 50)
        lines.append("")

        if today_selections:
            lines.append(f"今日选股数量: {len(today_selections)}只")
            lines.append("")
            for sel in today_selections:
                lines.append(f"  🟢 {sel.stock_name}({sel.stock_code})")
                lines.append(f"     策略: [{sel.strategy_id}] {sel.strategy_name}")
                lines.append(f"     买入价: {sel.buy_price:.2f}元")
                lines.append(f"     理由: {sel.selection_reason[:60]}...")
                lines.append("")
        else:
            lines.append("今日无新选股")
            lines.append("")

        # ===== 验证结果 =====
        verifying = self.selection_mgr.get_verifying_selections()
        lines.append("【二、验证中持仓】")
        lines.append("-" * 50)
        lines.append("")

        if verifying:
            lines.append(f"验证中数量: {len(verifying)}只")
            lines.append("")
            for sel in verifying:
                return_pct = sel.current_return_pct
                icon = "🟢" if return_pct >= 0 else "🔴"
                lines.append(f"  {icon} {sel.stock_name}({sel.stock_code})")
                lines.append(f"     策略: [{sel.strategy_id}] {sel.strategy_name}")
                lines.append(f"     持仓: {sel.hold_days}天 / 收益: {return_pct:+.2f}%")
                lines.append(f"     最高: +{sel.max_return_pct:.2f}% / 最低: {sel.min_return_pct:.2f}%")
                lines.append("")
        else:
            lines.append("暂无验证中持仓")
            lines.append("")

        # ===== 策略表现排名 =====
        lines.append("【三、策略表现排名】")
        lines.append("-" * 50)
        lines.append("")

        strategies = list(self.strategy_mgr.strategies.values())
        # 按胜率+盈亏比综合排序
        strategies.sort(key=lambda s: (s.performance.win_rate + s.performance.profit_loss_ratio * 10), reverse=True)

        for i, s in enumerate(strategies):
            perf = s.performance
            status_icon = "🟢" if s.status == StrategyStatus.ACTIVE else "🟡" if s.status == StrategyStatus.WARNING else "⏸️"
            lines.append(f"  {i+1}. {status_icon} [{s.strategy_id}] {s.strategy_name}")
            lines.append(f"     状态: {s.status.value}")
            lines.append(f"     选股: {perf.total_selections}次 | 胜率: {perf.win_rate:.1f}%")
            lines.append(f"     盈亏比: {perf.profit_loss_ratio:.2f} | 总收益: {perf.total_return_pct:+.2f}%")
            if perf.consecutive_losses > 0:
                lines.append(f"     ⚠️  连续亏损: {perf.consecutive_losses}次")
            lines.append("")

        # ===== 策略预警 =====
        warning_strategies = [s for s in strategies if s.status == StrategyStatus.WARNING]
        if warning_strategies:
            lines.append("【四、策略预警】")
            lines.append("-" * 50)
            lines.append("")
            for s in warning_strategies:
                lines.append(f"  ⚠️  [{s.strategy_id}] {s.strategy_name}")
                lines.append(f"     当前连续亏损: {s.performance.consecutive_losses}次")
                lines.append(f"     距离淘汰还有: {5 - s.performance.consecutive_losses}次")
                lines.append(f"     建议: 关注下一次选股结果，若继续亏损则启动深度复盘")
                lines.append("")

        # ===== 废弃策略复盘 =====
        if self.strategy_mgr.abandoned_reviews:
            lines.append("【五、废弃策略复盘】")
            lines.append("-" * 50)
            lines.append("")
            lines.append(f"已废弃策略: {len(self.strategy_mgr.abandoned_reviews)}个")
            lines.append("")
            # 展示最近1个
            latest = self.strategy_mgr.abandoned_reviews[-1]
            lines.append(f"  最近废弃: [{latest.strategy_id}] {latest.strategy_name}")
            lines.append(f"  废弃日期: {latest.abandoned_date}")
            lines.append(f"  触发原因: {latest.trigger_reason}")
            lines.append(f"  历史胜率: {latest.win_rate:.1f}%")
            lines.append("")
            lines.append("  经验教训:")
            for lesson in latest.lessons_learned[:3]:
                lines.append(f"    • {lesson}")
            lines.append("")

        # ===== 深度分析与建议 =====
        lines.append("【六、深度分析与建议】")
        lines.append("-" * 50)
        lines.append("")

        # 分析当前最佳策略
        best = strategies[0] if strategies else None
        if best and best.performance.total_selections > 0:
            lines.append(f"📈 最佳策略: {best.strategy_name}")
            lines.append(f"   胜率: {best.performance.win_rate:.1f}% | 盈亏比: {best.performance.profit_loss_ratio:.2f}")
            lines.append(f"   建议: 可适当增加该策略权重")
            lines.append("")

        # 分析最差策略
        worst = strategies[-1] if strategies else None
        if worst and worst.performance.total_selections > 0:
            lines.append(f"📉 最弱策略: {worst.strategy_name}")
            lines.append(f"   胜率: {worst.performance.win_rate:.1f}% | 盈亏比: {worst.performance.profit_loss_ratio:.2f}")
            if worst.status == StrategyStatus.WARNING:
                lines.append(f"   ⚠️  已触发警告，密切关注")
            lines.append("")

        # 系统整体评估
        total_selections = sum(s.performance.total_selections for s in strategies)
        if total_selections > 0:
            avg_win_rate = sum(s.performance.win_rate for s in strategies) / len(strategies)
            lines.append(f"📊 系统整体评估:")
            lines.append(f"   总选股次数: {total_selections}")
            lines.append(f"   平均胜率: {avg_win_rate:.1f}%")
            lines.append(f"   活跃策略数: {len(self.strategy_mgr.get_active_strategies())}")
            lines.append("")

        lines.append("💡 每日复盘要点:")
        lines.append("  1. 关注连续亏损的策略，及时干预")
        lines.append("  2. 验证止盈止损是否合理")
        lines.append("  3. 检查选股逻辑是否与市场匹配")
        lines.append("  4. 记录经验教训，持续优化")
        lines.append("")

        lines.append("=" * 70)
        lines.append("  报告结束")
        lines.append("=" * 70)

        # 保存报告
        report_file = self.review_dir / f"daily_review_{today}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return "\n".join(lines)


# ============================================================
# 便捷函数
# ============================================================

_picker_instance = None


def get_daily_picker(data_dir: str = "serenity_stock_data") -> DailyStockPicker:
    """获取选股引擎单例"""
    global _picker_instance
    if _picker_instance is None:
        _picker_instance = DailyStockPicker(data_dir)
    return _picker_instance


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  Serenity每日选股系统 v2.0 - 测试")
    print("=" * 70)
    print()

    picker = DailyStockPicker("serenity_stock_data_test")

    # 1. 查看策略库
    print("【1. 策略库初始化】")
    print(picker.strategy_mgr.get_strategy_list_report())

    # 2. 模拟选股
    print("【2. 模拟选股】")
    test_candidates = [
        {"code": "300655", "name": "晶瑞电材", "strategy_id": "S001",
         "reason": "光刻胶龙头，日本封锁催化，物理四问75分", "price": 18.0},
        {"code": "300346", "name": "南大光电", "strategy_id": "S002",
         "reason": "ArF光刻胶领先，认知差60分", "price": 35.0},
        {"code": "688126", "name": "沪硅产业", "strategy_id": "S004",
         "reason": "国产替代加速，产业趋势明确", "price": 30.0},
    ]
    selections = picker.daily_selection(test_candidates, "2026-06-24")
    print(f"今日选股: {len(selections)}只")
    for s in selections:
        print(f"  {s.stock_name}({s.stock_code}) - {s.strategy_name}")
    print()

    # 3. 模拟T+1验证
    print("【3. 模拟T+1验证】")
    price_data_t1 = {
        "300655": 18.5,   # +2.78%
        "300346": 36.0,   # +2.86%
        "688126": 29.5,   # -1.67%
    }
    result = picker.daily_verification(price_data_t1, "2026-06-25")
    print(f"验证数量: {result['verified_count']}")
    print(f"止盈: {result['new_wins']}")
    print(f"止损: {result['new_losses']}")
    print(f"到期: {result['new_expired']}")
    for d in result["details"]:
        print(f"  {d}")
    print()

    # 4. 模拟多日验证（连续亏损测试淘汰机制）
    print("【4. 模拟连续亏损（测试淘汰机制）】")
    # 给S005策略制造连续5次亏损
    test_dates = ["2026-06-20", "2026-06-19", "2026-06-18", "2026-06-17", "2026-06-16"]
    for i, d in enumerate(test_dates):
        test_sel = [
            {"code": f"60000{i}", "name": f"测试股{i}", "strategy_id": "S005",
             "reason": "测试连续亏损", "price": 10.0},
        ]
        picker.daily_selection(test_sel, d)
        # 次日全部下跌12%（触发止损）
        next_day = (datetime.strptime(d, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        picker.daily_verification({f"60000{i}": 8.8}, next_day)

    print("连续5次亏损测试完成")
    print()

    # 5. 生成复盘报告
    print("【5. 生成每日复盘报告】")
    report = picker.generate_daily_review("2026-06-25")
    print(report[:2000] + "...")
    print()
    print("✅ 测试完成！")
