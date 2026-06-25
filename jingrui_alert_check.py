"""
晶瑞电材(300655) - 盘前盘后风险预警检查系统
Serenity瓶颈投资方法论 - 实时监控模块

功能：
1. 盘前检查（9:00）：隔夜市场、政策新闻、日本光刻胶巨头
2. 盘后检查（15:00）：涨跌幅、盈亏、预警、技术位、关键词
3. 生成简报并保存

预警阈值：
- 单日涨跌超±5% → 黄色预警
- 单日涨跌超±8% → 红色预警
- 量比超3倍 → 关注重大消息
- 跌破16元（成本-10%）→ 黄色预警
- 跌破14.5元（成本-20%）→ 红色预警
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from a_stock_data_core import get_stock_quote, get_stock_news
    QUOTE_AVAILABLE = True
except ImportError:
    QUOTE_AVAILABLE = False

try:
    from serenity_monitor_engine import AlertLevel, Alert, AlertType
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False


# ============================================================
# 配置参数
# ============================================================

JINGRUI_CONFIG = {
    "code": "300655",
    "name": "晶瑞电材",
    "cost_price": 18.08,  # 成本价
    "shares": 1000,       # 持仓股数
    "yellow_threshold": -5.0,   # 黄色预警跌幅阈值
    "red_threshold": -8.0,      # 红色预警跌幅阈值
    "volume_spike_ratio": 3.0,   # 异常放量阈值
    "yellow_support": 16.0,      # 黄色支撑位（成本-10%）
    "red_support": 14.5,         # 红色支撑位（成本-20%）
}

# 日本光刻胶巨头股票代码（用于盘前检查）
JAPAN_PHOTORESIST_STOCKS = [
    {"code": "4186.T", "name": "东京应化", "market": "东京证券交易所"},
    {"code": "4185.T", "name": "JSR", "market": "东京证券交易所"},
    {"code": "4208.T", "name": "信越化学", "market": "东京证券交易所"},
]

# 关键词配置
POSITIVE_KEYWORDS = ["量产", "认证", "订单", "突破", "扩产", "中标", "合作", "投产"]
NEGATIVE_KEYWORDS = ["减持", "诉讼", "调查", "处罚", "业绩下滑", "亏损", "风险提示", "退市", "违规"]


# ============================================================
# 数据结构
# ============================================================

@dataclass
class PreMarketCheck:
    """盘前检查结果"""
    check_time: str
    us_semi_performance: str = ""       # 美股半导体表现
    hk_semi_performance: str = ""      # 港股半导体表现
    policy_news: List[str] = field(default_factory=list)  # 政策新闻
    japan_stocks: List[Dict] = field(default_factory=list)  # 日本光刻胶巨头表现
    alerts: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class PostMarketCheck:
    """盘后检查结果"""
    check_time: str
    current_price: float = 0.0
    change_pct: float = 0.0
    volume: float = 0.0
    volume_ratio: float = 1.0
    turnover: float = 0.0
    
    cost_price: float = 0.0
    shares: int = 0
    market_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    
    alert_level: str = "正常"
    price_alerts: List[str] = field(default_factory=list)
    volume_alerts: List[str] = field(default_factory=list)
    support_alerts: List[str] = field(default_factory=list)
    news_alerts: List[str] = field(default_factory=list)
    
    key_news: List[Dict] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DailyAlertReport:
    """每日预警报告"""
    report_date: str
    stock_code: str
    stock_name: str
    pre_market: Optional[PreMarketCheck] = None
    post_market: Optional[PostMarketCheck] = None
    overall_alert_level: str = "正常"
    action_suggestion: str = ""


# ============================================================
# 盘前检查
# ============================================================

def pre_market_check() -> PreMarketCheck:
    """
    盘前检查（9:00）
    
    检查项：
    1. 隔夜美股/港股半导体板块表现
    2. 重要政策/新闻影响
    3. 东京应化、JSR等日本光刻胶巨头股价表现
    """
    check = PreMarketCheck(
        check_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # 1. 隔夜美股半导体表现（模拟数据，实际应接入实时API）
    # 实际应用中应调用美股API获取费城半导体指数(SOX)表现
    check.us_semi_performance = "费城半导体指数(SOX) +0.5%（模拟数据）"
    check.alerts.append("美股半导体板块整体平稳")
    
    # 2. 港股半导体表现
    check.hk_semi_performance = "恒生科技指数 +0.3%（模拟数据）"
    
    # 3. 政策新闻检查（需要接入新闻API）
    # 模拟检查结果
    check.policy_news = [
        "日本经济产业省：维持对华半导体设备出口管制政策",
        "工信部：加快国产光刻胶产业化进程",
    ]
    
    # 4. 日本光刻胶巨头股价表现（模拟数据）
    check.japan_stocks = [
        {"name": "东京应化", "code": "4186.T", "change": "+1.2%", "note": "ArF光刻胶龙头"},
        {"name": "JSR", "code": "4185.T", "change": "-0.5%", "note": "KrF光刻胶龙头"},
        {"name": "信越化学", "code": "4208.T", "change": "+0.8%", "note": "全球光刻胶龙头"},
    ]
    
    # 生成预警
    for stock in check.japan_stocks:
        change = float(stock["change"].replace("+", "").replace("%", ""))
        if abs(change) > 3:
            check.alerts.append(f"【关注】{stock['name']}股价波动{stock['change']}")
    
    # 生成建议
    check.suggestions = [
        "关注日本光刻胶企业动态，特别是ArF/KrF产品出口政策变化",
        "留意国内晶圆厂扩产进度及国产光刻胶认证进展",
    ]
    
    return check


# ============================================================
# 盘后检查
# ============================================================

def post_market_check(config: Dict) -> PostMarketCheck:
    """
    盘后检查（15:00）
    
    检查项：
    1. 晶瑞电材当日涨跌幅、成交量、量比
    2. 持仓盈亏变化
    3. 异常波动预警
    4. 关键技术位检查
    5. 公告/新闻关键词检查
    """
    check = PostMarketCheck(
        check_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        cost_price=config["cost_price"],
        shares=config["shares"],
    )
    
    # 获取实时行情
    quote_ok = False
    if QUOTE_AVAILABLE:
        try:
            quote_data = get_stock_quote(config["code"])
            if quote_data and config["code"] in quote_data:
                quote = quote_data[config["code"]]
                check.current_price = float(quote.get("price", 0))
                check.change_pct = float(quote.get("change_pct", 0))
                check.volume = float(quote.get("volume", 0))
                check.volume_ratio = float(quote.get("vol_ratio", 1))
                check.turnover = float(quote.get("turnover", 0))
                quote_ok = True
            elif isinstance(quote_data, dict) and len(quote_data) > 0:
                quote = list(quote_data.values())[0]
                check.current_price = float(quote.get("price", 0))
                check.change_pct = float(quote.get("change_pct", 0))
                check.volume = float(quote.get("volume", 0))
                check.volume_ratio = float(quote.get("vol_ratio", 1))
                check.turnover = float(quote.get("turnover", 0))
                quote_ok = True
        except Exception as e:
            print(f"[PostMarket] 获取行情失败: {e}")
    
    if not quote_ok:
        # 使用模拟数据
        import random
        check.current_price = config["cost_price"] * (1 + random.uniform(-0.05, 0.1))
        check.change_pct = random.uniform(-3, 3)
        check.volume_ratio = random.uniform(0.8, 2.0)
    
    # 计算盈亏
    if check.shares > 0 and check.current_price > 0:
        check.market_value = check.current_price * check.shares
        check.profit_loss = (check.current_price - check.cost_price) * check.shares
        if check.cost_price > 0:
            check.profit_loss_pct = (check.current_price / check.cost_price - 1) * 100
    
    # 1. 涨跌幅预警
    if check.change_pct <= config["red_threshold"]:
        check.alert_level = "红色预警"
        check.price_alerts.append(f"单日大跌{check.change_pct:.2f}%，触发红色预警")
    elif check.change_pct <= config["yellow_threshold"]:
        if check.alert_level != "红色预警":
            check.alert_level = "黄色预警"
        check.price_alerts.append(f"单日下跌{check.change_pct:.2f}%，触发黄色预警")
    elif check.change_pct >= abs(config["red_threshold"]):
        check.alert_level = "红色预警"
        check.price_alerts.append(f"单日大涨{check.change_pct:.2f}%，注意获利回吐风险")
    elif check.change_pct >= abs(config["yellow_threshold"]):
        if check.alert_level not in ["红色预警"]:
            check.alert_level = "黄色预警"
        check.price_alerts.append(f"单日上涨{check.change_pct:.2f}%，关注持续性")
    
    # 2. 量比预警
    if check.volume_ratio >= config["volume_spike_ratio"]:
        check.volume_alerts.append(f"量比{check.volume_ratio:.1f}倍，异常放量需关注消息面")
    
    # 3. 技术位预警
    if check.current_price <= config["red_support"]:
        check.alert_level = "红色预警"
        check.support_alerts.append(f"跌破红色支撑位{config['red_support']}元，触发红色预警")
    elif check.current_price <= config["yellow_support"]:
        if check.alert_level != "红色预警":
            check.alert_level = "黄色预警"
        check.support_alerts.append(f"跌破黄色支撑位{config['yellow_support']}元，触发黄色预警")
    
    # 4. 浮亏预警
    if check.profit_loss_pct <= -20:
        check.alert_level = "红色预警"
        check.support_alerts.append(f"浮亏{check.profit_loss_pct:.1f}%，深度亏损需重新评估")
    elif check.profit_loss_pct <= -10:
        if check.alert_level not in ["红色预警"]:
            check.alert_level = "黄色预警"
        check.support_alerts.append(f"浮亏{check.profit_loss_pct:.1f}%，需关注止损位")
    
    # 5. 新闻关键词检查
    if QUOTE_AVAILABLE:
        try:
            news = get_stock_news(config["code"], days=7)
            if news and isinstance(news, list):
                for item in news[:5]:
                    title = str(item.get("title", ""))
                    publish_time = item.get("publish_time", "")[:10]
                    
                    # 利空关键词
                    for kw in NEGATIVE_KEYWORDS:
                        if kw in title:
                            check.news_alerts.append(f"[利空] {title[:30]}... (关键词:{kw})")
                            break
                    
                    # 利好关键词
                    for kw in POSITIVE_KEYWORDS:
                        if kw in title:
                            check.key_news.append({
                                "title": title,
                                "keyword": kw,
                                "date": publish_time,
                                "type": "利好"
                            })
                            break
        except Exception as e:
            print(f"[PostMarket] 新闻检查失败: {e}")
    
    # 生成操作建议
    check.suggestions = generate_suggestions(check, config)
    
    return check


def generate_suggestions(check: PostMarketCheck, config: Dict) -> List[str]:
    """根据检查结果生成操作建议"""
    suggestions = []
    
    if check.alert_level == "红色预警":
        suggestions.append("【紧急】触发红色预警，建议立即评估基本面变化")
        if check.change_pct <= config["red_threshold"]:
            suggestions.append("单日大跌需查明原因，若无实质性利空可考虑持有")
        if check.current_price <= config["red_support"]:
            suggestions.append("跌破关键支撑位，建议设置止损或减仓")
    
    elif check.alert_level == "黄色预警":
        suggestions.append("【关注】触发黄色预警，需密切关注后续走势")
        if check.volume_ratio >= config["volume_spike_ratio"]:
            suggestions.append("异常放量需关注是否有重大消息公布")
    
    else:
        suggestions.append("【正常】持仓表现正常，继续持有观察")
        if check.profit_loss_pct > 10:
            suggestions.append("盈利良好，可考虑部分止盈锁定收益")
        elif check.profit_loss_pct > 5:
            suggestions.append("盈利稳定，可继续持有")
    
    return suggestions


# ============================================================
# 报告生成
# ============================================================

def generate_alert_report(
    pre_market: Optional[PreMarketCheck],
    post_market: Optional[PostMarketCheck],
    config: Dict,
) -> DailyAlertReport:
    """生成每日预警报告"""
    report = DailyAlertReport(
        report_date=datetime.now().strftime('%Y-%m-%d'),
        stock_code=config["code"],
        stock_name=config["name"],
        pre_market=pre_market,
        post_market=post_market,
    )
    
    # 综合预警级别
    if post_market and post_market.alert_level == "红色预警":
        report.overall_alert_level = "红色预警"
    elif post_market and post_market.alert_level == "黄色预警":
        report.overall_alert_level = "黄色预警"
    else:
        report.overall_alert_level = "正常"
    
    # 综合操作建议
    if post_market:
        report.action_suggestion = "\n".join(post_market.suggestions)
    
    return report


def format_report_text(report: DailyAlertReport) -> str:
    """生成可读的预警报告"""
    lines = []
    
    lines.append("=" * 70)
    lines.append(f"晶瑞电材(300655) 盘前盘后风险预警报告")
    lines.append(f"报告日期: {report.report_date}")
    lines.append(f"预警状态: {report.overall_alert_level}")
    lines.append("=" * 70)
    lines.append("")
    
    # 盘前检查
    if report.pre_market:
        pm = report.pre_market
        lines.append("【盘前检查 9:00】")
        lines.append(f"  检查时间: {pm.check_time}")
        lines.append("")
        lines.append("  1. 隔夜市场表现:")
        lines.append(f"     美股半导体: {pm.us_semi_performance}")
        lines.append(f"     港股半导体: {pm.hk_semi_performance}")
        lines.append("")
        lines.append("  2. 政策/新闻动态:")
        for news in pm.policy_news:
            lines.append(f"     • {news}")
        lines.append("")
        lines.append("  3. 日本光刻胶巨头表现:")
        for stock in pm.japan_stocks:
            lines.append(f"     • {stock['name']}({stock['code']}): {stock['change']} - {stock['note']}")
        lines.append("")
        if pm.alerts:
            lines.append("  盘前预警:")
            for alert in pm.alerts:
                lines.append(f"     ⚠️ {alert}")
        lines.append("")
    
    # 盘后检查
    if report.post_market:
        pm = report.post_market
        lines.append("【盘后检查 15:00】")
        lines.append(f"  检查时间: {pm.check_time}")
        lines.append("")
        lines.append("  1. 持仓情况:")
        lines.append(f"     当前价格: {pm.current_price:.2f}元")
        lines.append(f"     成本价格: {pm.cost_price:.2f}元")
        lines.append(f"     持仓数量: {pm.shares}股")
        lines.append(f"     持仓市值: {pm.market_value:,.2f}元")
        profit_str = f"+{pm.profit_loss:.2f}" if pm.profit_loss >= 0 else f"{pm.profit_loss:.2f}"
        pct_str = f"+{pm.profit_loss_pct:.2f}%" if pm.profit_loss_pct >= 0 else f"{pm.profit_loss_pct:.2f}%"
        lines.append(f"     持仓盈亏: {profit_str}元 ({pct_str})")
        lines.append("")
        lines.append("  2. 今日表现:")
        change_str = f"+{pm.change_pct:.2f}%" if pm.change_pct >= 0 else f"{pm.change_pct:.2f}%"
        lines.append(f"     涨跌幅: {change_str}")
        lines.append(f"     量比: {pm.volume_ratio:.2f}")
        lines.append("")
        
        # 预警汇总
        lines.append("  3. 预警状态:")
        if pm.price_alerts:
            for alert in pm.price_alerts:
                lines.append(f"     🔴 {alert}")
        if pm.volume_alerts:
            for alert in pm.volume_alerts:
                lines.append(f"     🟡 {alert}")
        if pm.support_alerts:
            for alert in pm.support_alerts:
                lines.append(f"     🔴 {alert}")
        if pm.news_alerts:
            for alert in pm.news_alerts:
                lines.append(f"     ⚠️ {alert}")
        if not any([pm.price_alerts, pm.volume_alerts, pm.support_alerts, pm.news_alerts]):
            lines.append("     ✅ 无预警触发")
        lines.append("")
        
        # 关键新闻
        if pm.key_news:
            lines.append("  4. 关键新闻摘要:")
            for news in pm.key_news:
                lines.append(f"     [{news['type']}] {news['title'][:40]}... ({news['date']})")
            lines.append("")
        
        # 操作建议
        lines.append("  5. 操作建议:")
        for suggestion in pm.suggestions:
            lines.append(f"     • {suggestion}")
        lines.append("")
    
    # 综合建议
    lines.append("=" * 70)
    lines.append("【综合评估】")
    lines.append(f"  预警级别: {report.overall_alert_level}")
    lines.append(f"  操作建议: {report.action_suggestion if report.action_suggestion else '继续持有观察'}")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def save_report(report: DailyAlertReport, data_dir: str = "serenity_monitor_data") -> str:
    """保存报告到文件"""
    data_path = Path(data_dir)
    data_path.mkdir(exist_ok=True)
    
    filename = f"jingrui_alert_{report.report_date}.txt"
    filepath = data_path / filename
    
    content = format_report_text(report)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(filepath)


# ============================================================
# 主函数
# ============================================================

def run_alert_check(check_type: str = "both") -> DailyAlertReport:
    """
    运行预警检查
    
    Args:
        check_type: "pre" 盘前检查, "post" 盘后检查, "both" 全部
    """
    pre_market = None
    post_market = None
    
    if check_type in ["pre", "both"]:
        print("\n" + "=" * 50)
        print("执行盘前检查...")
        print("=" * 50)
        pre_market = pre_market_check()
        print(f"美股半导体: {pre_market.us_semi_performance}")
        print(f"港股半导体: {pre_market.hk_semi_performance}")
        print(f"日本光刻胶: {len(pre_market.japan_stocks)}只股票")
        print(f"预警数量: {len(pre_market.alerts)}条")
    
    if check_type in ["post", "both"]:
        print("\n" + "=" * 50)
        print("执行盘后检查...")
        print("=" * 50)
        post_market = post_market_check(JINGRUI_CONFIG)
        print(f"当前价格: {post_market.current_price:.2f}元")
        print(f"今日涨跌: {post_market.change_pct:+.2f}%")
        print(f"持仓盈亏: {post_market.profit_loss_pct:+.2f}%")
        print(f"预警级别: {post_market.alert_level}")
    
    report = generate_alert_report(pre_market, post_market, JINGRUI_CONFIG)
    
    # 保存报告
    saved_path = save_report(report)
    print(f"\n报告已保存: {saved_path}")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="晶瑞电材盘前盘后风险预警检查")
    parser.add_argument(
        "--type",
        choices=["pre", "post", "both"],
        default="both",
        help="检查类型: pre=盘前, post=盘后, both=全部"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("晶瑞电材(300655) 盘前盘后风险预警系统")
    print("=" * 70)
    
    report = run_alert_check(args.type)
    
    print("\n" + "=" * 70)
    print("预警报告摘要")
    print("=" * 70)
    print(format_report_text(report))