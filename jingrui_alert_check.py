#!/usr/bin/env python3
"""
晶瑞电材(300655) 盘前盘后风险预警检查
执行时间：盘前9:00 / 盘后15:00
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入数据模块
try:
    from a_stock_data_core import (
        get_stock_quote,
        get_stock_news,
        cninfo_announcements,
    )
    DATA_AVAILABLE = True
except ImportError as e:
    print(f"[警告] 数据模块导入失败: {e}")
    DATA_AVAILABLE = False

# 晶瑞电材持仓配置
POSITION = {
    "code": "300655",
    "name": "晶瑞电材",
    "shares": 1000,
    "cost": 18.07,  # 持仓成本
}

# 预警阈值
THRESHOLDS = {
    "yellow_drop_pct": -5.0,   # 单日涨跌超±5% → 黄色预警
    "red_drop_pct": -8.0,      # 单日涨跌超±8% → 红色预警
    "volume_ratio_alert": 3.0, # 量比超3倍 → 关注
    "support_yellow": 16.0,    # 跌破16元（成本-10%）→ 黄色预警
    "support_red": 14.5,       # 跌破14.5元（成本-20%）→ 红色预警
}

# 关键词配置
POSITIVE_KEYWORDS = ["量产", "认证", "订单", "突破", "扩产", "中标", "合作", "断供", "替代", "重组"]
NEGATIVE_KEYWORDS = ["减持", "诉讼", "调查", "处罚", "业绩下滑", "亏损", "风险", "退市"]


def get_realtime_data(code: str) -> dict:
    """获取实时行情数据"""
    if not DATA_AVAILABLE:
        return {}

    try:
        quote_data = get_stock_quote(code)
        if quote_data and code in quote_data:
            return quote_data[code]
        elif isinstance(quote_data, dict) and len(quote_data) > 0:
            # 尝试第一个值
            first_key = list(quote_data.keys())[0]
            return quote_data[first_key]
    except Exception as e:
        print(f"[错误] 获取行情失败: {e}")

    return {}


def check_news_keywords(code: str, days: int = 7) -> dict:
    """检查新闻关键词"""
    result = {
        "positive": [],
        "negative": [],
        "all_news": []
    }

    if not DATA_AVAILABLE:
        return result

    try:
        news = get_stock_news(code, days=days)
        if news and isinstance(news, list):
            for item in news[:20]:
                title = str(item.get("title", ""))
                result["all_news"].append({
                    "title": title,
                    "time": item.get("publish_time", "")[:10] if item.get("publish_time") else "",
                    "url": item.get("url", "")
                })

                for kw in POSITIVE_KEYWORDS:
                    if kw in title and title not in [n["title"] for n in result["positive"]]:
                        result["positive"].append(title)

                for kw in NEGATIVE_KEYWORDS:
                    if kw in title and title not in [n["title"] for n in result["negative"]]:
                        result["negative"].append(title)
    except Exception as e:
        print(f"[错误] 获取新闻失败: {e}")

    return result


def check_announcements(code: str, days: int = 7) -> dict:
    """检查公告关键词"""
    result = {
        "positive": [],
        "negative": [],
        "all": []
    }

    if not DATA_AVAILABLE:
        return result

    try:
        anns = cninfo_announcements(code, days=days)
        if anns and isinstance(anns, list):
            for ann in anns[:10]:
                title = str(ann.get("ann_title", "") or ann.get("title", ""))
                result["all"].append(title)

                for kw in POSITIVE_KEYWORDS:
                    if kw in title and title not in result["positive"]:
                        result["positive"].append(title)

                for kw in NEGATIVE_KEYWORDS:
                    if kw in title and title not in result["negative"]:
                        result["negative"].append(title)
    except Exception as e:
        print(f"[错误] 获取公告失败: {e}")

    return result


def generate_alert_report():
    """生成预警报告"""
    today = datetime.now()
    report_date = today.strftime("%Y-%m-%d")
    report_time = today.strftime("%Y-%m-%d %H:%M")
    is_pre_market = today.hour < 12  # 12点前为盘前

    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("         晶瑞电材(300655) 盘前盘后风险预警简报")
    report_lines.append(f"                    报告日期: {report_date}")
    report_lines.append(f"                    生成时间: {report_time}")
    report_lines.append("=" * 70)
    report_lines.append("")

    # ===== 获取实时数据 =====
    quote = get_realtime_data(POSITION["code"])
    news_data = check_news_keywords(POSITION["code"], days=7)
    ann_data = check_announcements(POSITION["code"], days=7)

    # ===== 行情数据解析 =====
    current_price = 0.0
    change_pct = 0.0
    change_amt = 0.0
    high_price = 0.0
    low_price = 0.0
    open_price = 0.0
    last_close = 0.0
    vol_ratio = 0.0
    volume = 0.0
    turnover_pct = 0.0

    if quote:
        current_price = float(quote.get("price", 0) or 0)
        change_pct = float(quote.get("change_pct", 0) or 0)
        change_amt = float(quote.get("change_amt", 0) or 0)
        high_price = float(quote.get("high", 0) or 0)
        low_price = float(quote.get("low", 0) or 0)
        open_price = float(quote.get("open", 0) or 0)
        last_close = float(quote.get("last_close", 0) or 0)
        vol_ratio = float(quote.get("vol_ratio", 0) or 0)
        volume = float(quote.get("volume", 0) or 0) / 1000000  # 转换为万手
        turnover_pct = float(quote.get("turnover_pct", 0) or 0)

    # 计算持仓盈亏
    shares = POSITION["shares"]
    cost = POSITION["cost"]
    market_value = current_price * shares if current_price > 0 else 0
    profit_loss = (current_price - cost) * shares if current_price > 0 else 0
    profit_loss_pct = (current_price / cost - 1) * 100 if cost > 0 and current_price > 0 else 0

    # ===== 第一节：当前价格与盈亏状态 =====
    report_lines.append("【一、当前价格与盈亏状态】")
    report_lines.append("")
    report_lines.append(f"  标的名称: {POSITION['name']}({POSITION['code']})")

    if current_price > 0:
        report_lines.append(f"  最新价格: {current_price:.2f}元")
    else:
        report_lines.append(f"  最新价格: 数据获取中...")

    report_lines.append(f"  持仓数量: {shares:,}股")

    if current_price > 0:
        report_lines.append(f"  持仓市值: {market_value:,.2f}元")
        report_lines.append(f"  持仓成本: {cost:.2f}元")
        report_lines.append(f"  持仓盈亏: {profit_loss:+,.2f}元 ({profit_loss_pct:+.2f}%)")
        report_lines.append("")
        report_lines.append("  预警阈值参考:")
        report_lines.append(f"    - 成本-10% ({THRESHOLDS['support_yellow']:.2f}元) → 黄色预警")
        report_lines.append(f"    - 成本-20% ({THRESHOLDS['support_red']:.2f}元) → 红色预警")
    else:
        report_lines.append(f"  持仓成本: {cost:.2f}元")
        report_lines.append(f"  持仓盈亏: 数据获取中...")

    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("")

    # ===== 第二节：盘前/盘后检查 =====
    if is_pre_market:
        report_lines.append("【二、盘前检查（9:00）】")
    else:
        report_lines.append("【二、盘后检查（15:00）】")

    report_lines.append("")

    # 1. 当日行情数据（盘后）
    if not is_pre_market:
        report_lines.append("  1️⃣ 当日行情数据")
        report_lines.append("  " + "━" * 40)
        if current_price > 0:
            report_lines.append(f"  ┌────────────────┬────────────┐")
            report_lines.append(f"  │   行情指标     │   数值      │")
            report_lines.append(f"  ├────────────────┼────────────┤")
            report_lines.append(f"  │ 涨跌幅         │  {change_pct:+.2f}%    │")
            report_lines.append(f"  │ 今日最高价     │  {high_price:.2f}元   │")
            report_lines.append(f"  │ 今日最低价     │  {low_price:.2f}元   │")
            report_lines.append(f"  │ 换手率         │  {turnover_pct:.2f}%    │")
            report_lines.append(f"  │ 量比           │  {vol_ratio:.2f}     │")
            report_lines.append(f"  │ 成交量         │  {volume:.2f}万手   │")
            report_lines.append(f"  └────────────────┴────────────┘")
        else:
            report_lines.append("  ⚠️ 暂无当日交易数据（停牌或未交易）")
        report_lines.append("")

    # 2. 异常波动预警
    report_lines.append("  2️⃣ 异常波动预警")
    report_lines.append("  " + "━" * 40)

    alerts = []

    # 价格涨跌预警
    if abs(change_pct) >= THRESHOLDS["red_drop_pct"]:
        alerts.append(("🔴", "红色预警", f"单日涨跌{change_pct:+.2f}%，已触发±8%红色预警线"))
    elif abs(change_pct) >= THRESHOLDS["yellow_drop_pct"]:
        alerts.append(("🟡", "黄色预警", f"单日涨跌{change_pct:+.2f}%，已触发±5%黄色预警线"))

    # 量比预警
    if vol_ratio >= THRESHOLDS["volume_ratio_alert"]:
        alerts.append(("🟡", "量比异常", f"量比{vOL_ratio:.2f}，超过3倍阈值，关注是否有重大消息"))

    # 关键技术位预警
    if current_price > 0:
        if current_price <= THRESHOLDS["support_red"]:
            alerts.append(("🔴", "红色预警", f"价格{current_price:.2f}元，跌破成本-20%（{THRESHOLDS['support_red']}元），建议减仓"))
        elif current_price <= THRESHOLDS["support_yellow"]:
            alerts.append(("🟡", "黄色预警", f"价格{current_price:.2f}元，跌破成本-10%（{THRESHOLDS['support_yellow']}元），关注支撑"))

    if alerts:
        for level, alert_type, desc in alerts:
            report_lines.append(f"  {level} {alert_type}: {desc}")
    else:
        report_lines.append("  ✅ 无异常波动预警")

    report_lines.append("")

    # 3. 盘前外围市场（9:00检查）
    if is_pre_market:
        report_lines.append("  3️⃣ 隔夜外围市场")
        report_lines.append("  " + "━" * 40)
        report_lines.append("  ⚠️ 盘前外围市场数据（参考）:")
        report_lines.append("  • 美股费城半导体指数：关注今晚表现")
        report_lines.append("  • 日经225半导体板块：日本光刻胶巨头动态")
        report_lines.append("  • 港股科技股：A股开盘参考")
        report_lines.append("")
        report_lines.append("  📋 持续跟踪要点:")
        report_lines.append("  • 日本东京应化(TOK)、JSR等光刻胶巨头股价")
        report_lines.append("  • 美股半导体设备股（应用材料、科磊等）")
        report_lines.append("  • 国产替代进度和政策支持力度")
        report_lines.append("")

    # ===== 第三节：公告/新闻关键词检查 =====
    report_lines.append("【三、公告/新闻关键词检查】")
    report_lines.append("")

    report_lines.append("  📰 利空关键词监控:")
    if ann_data["negative"] or news_data["negative"]:
        for kw in ann_data["negative"][:3]:
            report_lines.append(f"    ❌ 公告: {kw[:40]}...")
        for kw in news_data["negative"][:3]:
            report_lines.append(f"    ❌ 新闻: {kw[:40]}...")
    else:
        report_lines.append("    ✅ 未检测到利空关键词")

    report_lines.append("")
    report_lines.append("  📋 利好关键词监控:")
    if ann_data["positive"] or news_data["positive"]:
        for kw in ann_data["positive"][:5]:
            report_lines.append(f"    ✅ 公告: {kw[:40]}...")
        for kw in news_data["positive"][:5]:
            report_lines.append(f"    ✅ 新闻: {kw[:40]}...")
    else:
        report_lines.append("    ℹ️ 未检测到特定利好关键词")

    # 最新新闻摘要
    if news_data["all_news"]:
        report_lines.append("")
        report_lines.append("  📢 最新新闻（5条）:")
        for i, news in enumerate(news_data["all_news"][:5], 1):
            time_str = f"[{news['time']}]" if news['time'] else ""
            report_lines.append(f"    {i}. {time_str} {news['title'][:35]}...")

    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("")

    # ===== 第四节：预警状态汇总 =====
    report_lines.append("【四、涨跌预警状态汇总】")
    report_lines.append("")

    if current_price > 0:
        report_lines.append("  ┌────────────────────┬──────────┬──────────────┐")
        report_lines.append("  │   预警类型         │   阈值   │   当前状态    │")
        report_lines.append("  ├────────────────────┼──────────┼──────────────┤")

        # 单日涨跌
        if change_pct >= 8:
            status = "🔴 触发红色"
        elif change_pct >= 5:
            status = "🟡 触发黄色"
        elif change_pct <= -8:
            status = "🔴 触发红色"
        elif change_pct <= -5:
            status = "🟡 触发黄色"
        else:
            status = f"  {change_pct:+.2f}%"
        report_lines.append(f"  │ 单日涨跌           │   ±5%/±8% │ {status}     │")

        # 量比
        if vol_ratio >= 3:
            status = "🟡 异常放量"
        else:
            status = f"  {vol_ratio:.2f}"
        report_lines.append(f"  │ 量比               │   3.0     │ {status}     │")

        # 支撑位
        if current_price <= THRESHOLDS["support_red"]:
            status = "🔴 跌破-20%"
        elif current_price <= THRESHOLDS["support_yellow"]:
            status = "🟡 跌破-10%"
        else:
            status = "✅ 正常"
        report_lines.append(f"  │ 关键技术位        │ 16/14.5元 │ {status}     │")

        report_lines.append("  └────────────────────┴──────────┴──────────────┘")
    else:
        report_lines.append("  ⚠️ 暂无交易数据，无法判断预警状态")

    report_lines.append("")

    # ===== 第五节：操作建议 =====
    report_lines.append("【五、操作建议】")
    report_lines.append("")

    if current_price > 0:
        # 根据价格区间给出建议
        if profit_loss_pct >= 10:
            level = "【盈利持有】"
        elif profit_loss_pct >= 0:
            level = "【小幅盈利】"
        elif profit_loss_pct >= -10:
            level = "【轻度浮亏】"
        else:
            level = "【深度浮亏】"

        report_lines.append(f"  当前评级: {level}")
        report_lines.append("")
        report_lines.append("  关键价位操作参考:")
        report_lines.append(f"    ┌──────────────┬─────────────────────────┐")
        report_lines.append(f"    │   价格区间    │        操作建议          │")
        report_lines.append(f"    ├──────────────┼─────────────────────────┤")
        report_lines.append(f"    │ 20元以上      │ 考虑减仓1/3，锁定利润    │")
        report_lines.append(f"    │ 18.5-20元     │ 持有观察                 │")
        report_lines.append(f"    │ {THRESHOLDS['support_yellow']:.1f}-{THRESHOLDS['support_yellow']+2.5}元  │ 正常持有区间             │")
        report_lines.append(f"    │ 16元以下      │ 触发黄色预警，关注减仓   │")
        report_lines.append(f"    │ 14.5元以下    │ 触发红色预警，建议减仓   │")
        report_lines.append(f"    └──────────────┴─────────────────────────┘")
    else:
        report_lines.append("  ⚠️ 当前无交易数据，建议关注复牌公告")

    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("")
    report_lines.append(f"  生成时间: {report_time}")
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append("                    Serenity瓶颈投资监控系统")
    report_lines.append("                         晶瑞电材持仓监测")
    report_lines.append("=" * 70)

    return "\n".join(report_lines), report_lines


def save_report(content: str, report_date: str):
    """保存报告到文件"""
    output_dir = Path(__file__).parent / "serenity_monitor_data"
    output_dir.mkdir(exist_ok=True)

    filename = f"jingrui_alert_{report_date}.txt"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return str(filepath)


if __name__ == "__main__":
    print("=" * 60)
    print("晶瑞电材(300655) 风险预警检查")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 生成报告
    content, lines = generate_alert_report()

    # 保存报告
    report_date = datetime.now().strftime("%Y-%m-%d")
    saved_path = save_report(content, report_date)

    # 输出报告
    print(content)
    print()
    print(f"[完成] 报告已保存: {saved_path}")