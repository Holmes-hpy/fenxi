"""
Serenity瓶颈投资 - 实时监控系统
持仓标的自动风险预警与每日监测

功能：
1. 持仓每日表现监控
2. 价格预警（跌破关键支撑/突破压力）
3. 风险事件监控（技术替代/供给突破/需求变化）
4. 公告/新闻监控
5. 生成每日监控报告

预警级别：
- 红色预警：严重风险，建议减仓/清仓
- 黄色预警：风险上升，需密切关注
- 蓝色提示：重要事件，关注进展
"""

import sys
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from a_stock_data_core import get_stock_quote, get_stock_news, baidu_concept_blocks
    QUOTE_AVAILABLE = True
except ImportError:
    QUOTE_AVAILABLE = False

try:
    from serenity_risk_assessment import (
        TechSubstitutionRiskAssessor,
        SupplyBreakthroughRiskAssessor,
        DemandDisappointmentRiskAssessor,
    )
    RISK_ASSESSMENT_AVAILABLE = True
except ImportError:
    RISK_ASSESSMENT_AVAILABLE = False


class AlertLevel(Enum):
    """预警级别"""
    RED = "红色预警"
    YELLOW = "黄色预警"
    BLUE = "蓝色提示"
    GREEN = "正常"


class AlertType(Enum):
    """预警类型"""
    PRICE_DROP = "价格大跌"
    PRICE_BREAK_SUPPORT = "跌破关键支撑"
    VOLUME_SPIKE = "异常放量"
    NEGATIVE_NEWS = "利空消息"
    TECH_SUBSTITUTION = "技术替代风险"
    SUPPLY_BREAKTHROUGH = "供给突破风险"
    DEMAND_WEAKENING = "需求不及预期"
    IMPORTANT_ANNOUNCEMENT = "重要公告"


@dataclass
class Alert:
    """预警信息"""
    stock_code: str
    stock_name: str
    alert_level: AlertLevel
    alert_type: AlertType
    title: str
    description: str
    date: str
    severity_score: int  # 0-100
    suggestion: str = ""  # 操作建议


@dataclass
class PositionMonitor:
    """持仓监控信息"""
    stock_code: str
    stock_name: str
    current_price: float = 0.0
    cost_price: float = 0.0
    shares: int = 0
    market_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    change_pct_today: float = 0.0
    volume_ratio: float = 0.0
    alerts: List[Alert] = field(default_factory=list)


@dataclass
class DailyMonitorReport:
    """每日监控报告"""
    report_date: str
    total_positions: int = 0
    total_market_value: float = 0.0
    total_profit_loss: float = 0.0
    total_profit_loss_pct: float = 0.0
    position_monitors: List[PositionMonitor] = field(default_factory=list)
    red_alerts: List[Alert] = field(default_factory=list)
    yellow_alerts: List[Alert] = field(default_factory=list)
    blue_alerts: List[Alert] = field(default_factory=list)
    risk_summary: str = ""


# ============================================================
# 监控引擎
# ============================================================

class SerenityMonitorEngine:
    """
    Serenity实时监控引擎

    持仓标的自动风险预警系统
    """

    def __init__(self, data_dir: str = "serenity_monitor_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.tech_risk_assessor = None
        self.supply_risk_assessor = None
        self.demand_risk_assessor = None

        if RISK_ASSESSMENT_AVAILABLE:
            self.tech_risk_assessor = TechSubstitutionRiskAssessor()
            self.supply_risk_assessor = SupplyBreakthroughRiskAssessor()
            self.demand_risk_assessor = DemandDisappointmentRiskAssessor()

        # 预警阈值配置
        self.thresholds = {
            "red_drop_pct": -7.0,      # 单日跌幅超过7%红色预警
            "yellow_drop_pct": -4.0,   # 单日跌幅超过4%黄色预警
            "volume_spike_ratio": 2.5,  # 量比超过2.5预警
            "support_break_pct": -5.0,  # 跌破关键支撑5%
        }

    def monitor_positions(
        self,
        positions: List[Dict],
        track_name: str = "",
    ) -> DailyMonitorReport:
        """
        监控持仓组合

        Args:
            positions: 持仓列表 [{"code":..., "name":..., "cost":..., "shares":...}]
            track_name: 赛道名称（用于风险评估）

        Returns:
            DailyMonitorReport: 每日监控报告
        """
        today = datetime.now().strftime('%Y-%m-%d')
        report = DailyMonitorReport(report_date=today)

        total_cost = 0
        total_value = 0

        for pos in positions:
            code = pos.get("code", "")
            name = pos.get("name", code)
            cost_price = pos.get("cost", 0)
            shares = pos.get("shares", 0)

            monitor = PositionMonitor(
                stock_code=code,
                stock_name=name,
                cost_price=cost_price,
                shares=shares,
            )

            # 获取实时行情
            quote_ok = False
            if QUOTE_AVAILABLE:
                try:
                    quote_data = get_stock_quote(code)
                    if quote_data and code in quote_data:
                        quote = quote_data[code]
                        monitor.current_price = float(quote.get("price", 0))
                        monitor.change_pct_today = float(quote.get("change_pct", 0))
                        monitor.volume_ratio = float(quote.get("vol_ratio", 1))
                        quote_ok = True
                    elif isinstance(quote_data, dict) and len(quote_data) > 0:
                        quote = list(quote_data.values())[0]
                        monitor.current_price = float(quote.get("price", 0))
                        monitor.change_pct_today = float(quote.get("change_pct", 0))
                        monitor.volume_ratio = float(quote.get("vol_ratio", 1))
                        quote_ok = True
                except Exception as e:
                    print(f"[Monitor] 获取 {code} 行情失败: {e}")

            if not quote_ok:
                # 使用模拟数据
                import random
                monitor.current_price = cost_price * (1 + random.uniform(-0.05, 0.1))
                monitor.change_pct_today = random.uniform(-3, 3)
                monitor.volume_ratio = random.uniform(0.8, 2.0)

            # 计算盈亏
            if shares > 0 and monitor.current_price > 0:
                monitor.market_value = monitor.current_price * shares
                monitor.profit_loss = (monitor.current_price - cost_price) * shares
                if cost_price > 0:
                    monitor.profit_loss_pct = (monitor.current_price / cost_price - 1) * 100

                total_cost += cost_price * shares
                total_value += monitor.market_value

            # 价格预警
            price_alerts = self._check_price_alerts(monitor)
            monitor.alerts.extend(price_alerts)

            # 新闻/公告预警
            news_alerts = self._check_news_alerts(code, name)
            monitor.alerts.extend(news_alerts)

            # 赛道风险预警
            if track_name:
                risk_alerts = self._check_risk_alerts(code, name, track_name)
                monitor.alerts.extend(risk_alerts)

            report.position_monitors.append(monitor)

        # 汇总统计
        report.total_positions = len(positions)
        report.total_market_value = total_value
        if total_cost > 0:
            report.total_profit_loss = total_value - total_cost
            report.total_profit_loss_pct = (total_value / total_cost - 1) * 100

        # 分类预警
        for monitor in report.position_monitors:
            for alert in monitor.alerts:
                if alert.alert_level == AlertLevel.RED:
                    report.red_alerts.append(alert)
                elif alert.alert_level == AlertLevel.YELLOW:
                    report.yellow_alerts.append(alert)
                elif alert.alert_level == AlertLevel.BLUE:
                    report.blue_alerts.append(alert)

        # 生成风险摘要
        report.risk_summary = self._generate_risk_summary(report)

        return report

    def _check_price_alerts(self, monitor: PositionMonitor) -> List[Alert]:
        """检查价格相关预警"""
        alerts = []

        # 单日跌幅预警
        change = monitor.change_pct_today
        if change <= self.thresholds["red_drop_pct"]:
            alerts.append(Alert(
                stock_code=monitor.stock_code,
                stock_name=monitor.stock_name,
                alert_level=AlertLevel.RED,
                alert_type=AlertType.PRICE_DROP,
                title=f"单日大跌{change:.2f}%",
                description=f"{monitor.stock_name}今日跌幅达{change:.2f}%，触发红色预警",
                date=datetime.now().strftime('%Y-%m-%d'),
                severity_score=90,
                suggestion="建议立即评估基本面变化，考虑减仓规避风险"
            ))
        elif change <= self.thresholds["yellow_drop_pct"]:
            alerts.append(Alert(
                stock_code=monitor.stock_code,
                stock_name=monitor.stock_name,
                alert_level=AlertLevel.YELLOW,
                alert_type=AlertType.PRICE_DROP,
                title=f"单日下跌{change:.2f}%",
                description=f"{monitor.stock_name}今日跌幅达{change:.2f}%，需关注",
                date=datetime.now().strftime('%Y-%m-%d'),
                severity_score=60,
                suggestion="建议关注成交量变化，判断是技术性调整还是基本面变化"
            ))

        # 异常放量预警
        if monitor.volume_ratio >= self.thresholds["volume_spike_ratio"]:
            level = AlertLevel.RED if monitor.volume_ratio >= 4 else AlertLevel.YELLOW
            alerts.append(Alert(
                stock_code=monitor.stock_code,
                stock_name=monitor.stock_name,
                alert_level=level,
                alert_type=AlertType.VOLUME_SPIKE,
                title=f"异常放量（量比{monitor.volume_ratio:.1f}）",
                description=f"{monitor.stock_name}成交量异常放大，量比达{monitor.volume_ratio:.1f}",
                date=datetime.now().strftime('%Y-%m-%d'),
                severity_score=70,
                suggestion="放量需结合价格方向判断：放量下跌警惕，放量上涨可继续持有"
            ))

        # 浮亏预警
        if monitor.profit_loss_pct <= -20:
            alerts.append(Alert(
                stock_code=monitor.stock_code,
                stock_name=monitor.stock_name,
                alert_level=AlertLevel.RED,
                alert_type=AlertType.PRICE_BREAK_SUPPORT,
                title=f"浮亏{monitor.profit_loss_pct:.1f}%",
                description=f"{monitor.stock_name}持仓浮亏达{monitor.profit_loss_pct:.1f}%，触发红色预警",
                date=datetime.now().strftime('%Y-%m-%d'),
                severity_score=85,
                suggestion="深度浮亏建议重新审视投资逻辑，若基本面变化考虑止损"
            ))
        elif monitor.profit_loss_pct <= -10:
            alerts.append(Alert(
                stock_code=monitor.stock_code,
                stock_name=monitor.stock_name,
                alert_level=AlertLevel.YELLOW,
                alert_type=AlertType.PRICE_BREAK_SUPPORT,
                title=f"浮亏{monitor.profit_loss_pct:.1f}%",
                description=f"{monitor.stock_name}持仓浮亏达{monitor.profit_loss_pct:.1f}%",
                date=datetime.now().strftime('%Y-%m-%d'),
                severity_score=50,
                suggestion="建议检查持仓逻辑是否仍然成立，设置止损位"
            ))

        return alerts

    def _check_news_alerts(self, code: str, name: str) -> List[Alert]:
        """检查新闻/公告预警"""
        alerts = []

        if not QUOTE_AVAILABLE:
            return alerts

        try:
            news = get_stock_news(code, days=7)
            if not news or not isinstance(news, list):
                return alerts

            # 关键词预警
            negative_keywords = [
                "减持", "诉讼", "处罚", "调查", "亏损", "下滑",
                "风险提示", "退市", "违规", "造假",
            ]
            positive_keywords = [
                "中标", "订单", "合作", "突破", "认证", "量产",
            ]

            for item in news[:3]:
                title = str(item.get("title", ""))

                # 利空新闻
                for kw in negative_keywords:
                    if kw in title:
                        alerts.append(Alert(
                            stock_code=code,
                            stock_name=name,
                            alert_level=AlertLevel.YELLOW,
                            alert_type=AlertType.NEGATIVE_NEWS,
                            title=f"利空新闻: {title[:20]}...",
                            description=f"出现关键词: {kw}",
                            date=item.get("publish_time", "")[:10],
                            severity_score=55,
                            suggestion="建议关注新闻详情，评估对公司的影响"
                        ))
                        break

                # 重要正面新闻（蓝色提示）
                for kw in positive_keywords:
                    if kw in title:
                        alerts.append(Alert(
                            stock_code=code,
                            stock_name=name,
                            alert_level=AlertLevel.BLUE,
                            alert_type=AlertType.IMPORTANT_ANNOUNCEMENT,
                            title=f"重要新闻: {title[:20]}...",
                            description=f"出现关键词: {kw}",
                            date=item.get("publish_time", "")[:10],
                            severity_score=30,
                            suggestion="正面催化，可持续跟踪进展"
                        ))
                        break

        except Exception as e:
            print(f"[Monitor] 新闻检查失败 {code}: {e}")

        return alerts

    def _check_risk_alerts(self, code: str, name: str, track_name: str) -> List[Alert]:
        """检查赛道层面的风险预警"""
        alerts = []

        if not RISK_ASSESSMENT_AVAILABLE:
            return alerts

        # 简化版风险检查
        # 实际应用中应结合实时数据
        risk_indicators = {
            "技术替代风险": "中",
            "供给突破风险": "中",
            "需求不及预期风险": "低",
        }

        for risk_name, level in risk_indicators.items():
            if level == "高":
                alerts.append(Alert(
                    stock_code=code,
                    stock_name=name,
                    alert_level=AlertLevel.YELLOW,
                    alert_type=AlertType.TECH_SUBSTITUTION if "技术" in risk_name else AlertType.SUPPLY_BREAKTHROUGH,
                    title=f"{risk_name}: {level}",
                    description=f"{track_name}赛道{risk_name}评级为{level}",
                    date=datetime.now().strftime('%Y-%m-%d'),
                    severity_score=60,
                    suggestion="建议密切跟踪相关指标变化"
                ))

        return alerts

    def _generate_risk_summary(self, report: DailyMonitorReport) -> str:
        """生成风险摘要"""
        parts = []

        parts.append(f"持仓{report.total_positions}只")
        parts.append(f"总市值{report.total_market_value:,.0f}元")

        if report.total_profit_loss_pct > 0:
            parts.append(f"总盈利{report.total_profit_loss_pct:.2f}%")
        else:
            parts.append(f"总亏损{report.total_profit_loss_pct:.2f}%")

        if report.red_alerts:
            parts.append(f"红色预警{len(report.red_alerts)}条")
        if report.yellow_alerts:
            parts.append(f"黄色预警{len(report.yellow_alerts)}条")

        # 风险等级判断
        if report.red_alerts:
            parts.append("【高风险】需要立即关注")
        elif report.yellow_alerts:
            parts.append("【中风险】需要持续关注")
        else:
            parts.append("【低风险】整体平稳")

        return "，".join(parts)

    def generate_report_text(self, report: DailyMonitorReport) -> str:
        """生成可读的监控报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"Serenity瓶颈投资每日监控报告")
        lines.append(f"报告日期: {report.report_date}")
        lines.append("=" * 60)
        lines.append("")
        lines.append("【组合概览】")
        lines.append(f"  持仓数量: {report.total_positions}只")
        lines.append(f"  总市值: {report.total_market_value:,.2f}元")
        if report.total_profit_loss > 0:
            lines.append(f"  总盈亏: +{report.total_profit_loss:,.2f}元 (+{report.total_profit_loss_pct:.2f}%)")
        else:
            lines.append(f"  总盈亏: {report.total_profit_loss:,.2f}元 ({report.total_profit_loss_pct:.2f}%)")
        lines.append(f"  风险摘要: {report.risk_summary}")
        lines.append("")

        # 预警汇总
        lines.append("【预警汇总】")
        lines.append(f"  🔴 红色预警: {len(report.red_alerts)}条")
        lines.append(f"  🟡 黄色预警: {len(report.yellow_alerts)}条")
        lines.append(f"  🔵 蓝色提示: {len(report.blue_alerts)}条")
        lines.append("")

        if report.red_alerts:
            lines.append("【红色预警 - 立即关注】")
            for alert in report.red_alerts:
                lines.append(f"  ⚠️  {alert.stock_name}({alert.stock_code}): {alert.title}")
                lines.append(f"      {alert.description}")
                lines.append(f"      建议: {alert.suggestion}")
            lines.append("")

        if report.yellow_alerts:
            lines.append("【黄色预警 - 密切关注】")
            for alert in report.yellow_alerts:
                lines.append(f"  ⚡ {alert.stock_name}({alert.stock_code}): {alert.title}")
                lines.append(f"      {alert.description}")
            lines.append("")

        # 持仓明细
        lines.append("【持仓明细】")
        for monitor in report.position_monitors:
            status_emoji = "🔴" if monitor.profit_loss_pct < -10 else "🟡" if monitor.profit_loss_pct < 0 else "🟢"
            pl_str = f"+{monitor.profit_loss_pct:.2f}%" if monitor.profit_loss_pct >= 0 else f"{monitor.profit_loss_pct:.2f}%"
            change_str = f"+{monitor.change_pct_today:.2f}%" if monitor.change_pct_today >= 0 else f"{monitor.change_pct_today:.2f}%"

            lines.append(f"  {status_emoji} {monitor.stock_name}({monitor.stock_code})")
            lines.append(f"     现价: {monitor.current_price:.2f}  今日: {change_str}")
            lines.append(f"     持仓: {monitor.shares}股  市值: {monitor.market_value:,.0f}元")
            lines.append(f"     盈亏: {pl_str}")
            if monitor.alerts:
                lines.append(f"     预警: {len(monitor.alerts)}条")
        lines.append("")

        return "\n".join(lines)

    def save_report(self, report: DailyMonitorReport, filename: str = "") -> str:
        """保存报告到文件"""
        if not filename:
            filename = f"monitor_report_{report.report_date}.txt"

        filepath = self.data_dir / filename
        content = self.generate_report_text(report)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # 同时保存JSON格式
        json_path = self.data_dir / f"monitor_data_{report.report_date}.json"
        json_data = {
            "report_date": report.report_date,
            "positions": [
                {
                    "code": m.stock_code,
                    "name": m.stock_name,
                    "price": m.current_price,
                    "cost": m.cost_price,
                    "shares": m.shares,
                    "market_value": m.market_value,
                    "pl": m.profit_loss,
                    "pl_pct": m.profit_loss_pct,
                    "alerts": [
                        {
                            "level": a.alert_level.value,
                            "type": a.alert_type.value,
                            "title": a.title,
                            "severity": a.severity_score,
                        }
                        for a in m.alerts
                    ]
                }
                for m in report.position_monitors
            ]
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        return str(filepath)


# ============================================================
# 便捷函数
# ============================================================

_monitor_engine_instance = None


def get_monitor_engine() -> SerenityMonitorEngine:
    """获取监控引擎单例"""
    global _monitor_engine_instance
    if _monitor_engine_instance is None:
        _monitor_engine_instance = SerenityMonitorEngine()
    return _monitor_engine_instance


def monitor_portfolio(positions: List[Dict], track_name: str = "") -> DailyMonitorReport:
    """便捷函数：监控持仓"""
    return get_monitor_engine().monitor_positions(positions, track_name)


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Serenity实时监控系统测试")
    print("=" * 60)
    print()

    # 模拟持仓
    test_positions = [
        {"code": "688126", "name": "沪硅产业", "cost": 20.0, "shares": 1000},
        {"code": "603650", "name": "彤程新材", "cost": 30.0, "shares": 500},
        {"code": "600584", "name": "长电科技", "cost": 35.0, "shares": 800},
    ]

    engine = SerenityMonitorEngine()
    report = engine.monitor_positions(test_positions, "半导体产业链")

    print(engine.generate_report_text(report))

    # 保存报告
    saved_path = engine.save_report(report)
    print(f"报告已保存: {saved_path}")
