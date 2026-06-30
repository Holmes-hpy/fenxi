import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serenity_monitor_engine import SerenityMonitorEngine, AlertLevel


def main():
    print("=" * 60)
    print("晶瑞电材(300655)每日监控任务执行中...")
    print("=" * 60)
    print()

    engine = SerenityMonitorEngine(data_dir="serenity_monitor_data")

    jingrui_positions = [
        {"code": "300655", "name": "晶瑞电材", "cost": 18.07, "shares": 1000},
    ]

    report = engine.monitor_positions(jingrui_positions, "光刻胶产业链")

    today = datetime.now().strftime('%Y-%m-%d')
    txt_filename = f"jingrui_monitor_{today}.txt"
    json_filename = f"jingrui_monitor_{today}.json"

    report_text = engine.generate_report_text(report)
    print(report_text)

    txt_path = os.path.join("serenity_monitor_data", txt_filename)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n📄 报告已保存: {txt_path}")

    json_data = {
        "report_date": report.report_date,
        "generated_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_positions": report.total_positions,
        "total_market_value": report.total_market_value,
        "total_profit_loss": report.total_profit_loss,
        "total_profit_loss_pct": report.total_profit_loss_pct,
        "risk_summary": report.risk_summary,
        "red_alerts_count": len(report.red_alerts),
        "yellow_alerts_count": len(report.yellow_alerts),
        "blue_alerts_count": len(report.blue_alerts),
        "positions": [
            {
                "code": m.stock_code,
                "name": m.stock_name,
                "current_price": m.current_price,
                "cost_price": m.cost_price,
                "shares": m.shares,
                "market_value": m.market_value,
                "profit_loss": m.profit_loss,
                "profit_loss_pct": m.profit_loss_pct,
                "change_pct_today": m.change_pct_today,
                "volume_ratio": m.volume_ratio,
                "alerts": [
                    {
                        "level": a.alert_level.value,
                        "type": a.alert_type.value,
                        "title": a.title,
                        "description": a.description,
                        "severity_score": a.severity_score,
                        "suggestion": a.suggestion,
                    }
                    for a in m.alerts
                ]
            }
            for m in report.position_monitors
        ],
        "red_alerts": [
            {
                "stock_code": a.stock_code,
                "stock_name": a.stock_name,
                "title": a.title,
                "description": a.description,
                "severity_score": a.severity_score,
                "suggestion": a.suggestion,
            }
            for a in report.red_alerts
        ],
        "yellow_alerts": [
            {
                "stock_code": a.stock_code,
                "stock_name": a.stock_name,
                "title": a.title,
                "description": a.description,
                "severity_score": a.severity_score,
                "suggestion": a.suggestion,
            }
            for a in report.yellow_alerts
        ],
        "blue_alerts": [
            {
                "stock_code": a.stock_code,
                "stock_name": a.stock_name,
                "title": a.title,
                "description": a.description,
                "severity_score": a.severity_score,
                "suggestion": a.suggestion,
            }
            for a in report.blue_alerts
        ],
    }

    json_path = os.path.join("serenity_monitor_data", json_filename)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"📊 JSON数据已保存: {json_path}")

    if report.red_alerts:
        print("\n" + "=" * 60)
        print("🔴🔴🔴 红色预警特别提醒 🔴🔴🔴")
        print("=" * 60)
        for alert in report.red_alerts:
            print(f"\n⚠️  {alert.stock_name}({alert.stock_code}): {alert.title}")
            print(f"   描述: {alert.description}")
            print(f"   严重程度: {alert.severity_score}/100")
            print(f"   建议: {alert.suggestion}")
        print("\n" + "=" * 60)
        print("请立即关注红色预警标的！")
        print("=" * 60)

    print("\n✅ 监控任务执行完成")
    return report


if __name__ == "__main__":
    main()