# -*- coding: utf-8 -*-
"""
每日自动选股与涨幅监测系统
- 每日执行BOM产业链选股
- 跟踪选股组合的每日表现
- 生成监测报告
"""

import sys
import json
import time
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from three_high_engine import ThreeHighEngine, StockEvaluation


# 数据存储目录
DATA_DIR = PROJECT_DIR / "bom_stock_data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class DailySelection:
    """每日选股记录"""
    date: str
    selections: List[StockEvaluation]
    performance: List[Dict] = field(default_factory=list)

    def to_dict(self):
        return {
            "date": self.date,
            "selections": [
                {
                    "code": s.code, "name": s.name, "node_name": s.node_name,
                    "category": s.category, "level": s.level,
                    "barrier_score": round(s.barrier_score, 2),
                    "growth_score": round(s.growth_score, 2),
                    "profit_score": round(s.profit_score, 2),
                    "supply_demand_score": round(s.supply_demand_score, 2),
                    "total_score": round(s.total_score, 2),
                    "reason": s.reason,
                    "price_on_selection": s.quote.get("price", 0) if s.quote else 0,
                    "pe_ttm": s.quote.get("pe_ttm", 0) if s.quote else 0,
                }
                for s in self.selections
            ],
            "performance": self.performance,
        }


class DailyMonitoringSystem:
    """每日监测系统"""

    def __init__(self):
        self.engine = ThreeHighEngine()
        self.tracking_file = DATA_DIR / "tracking_history.json"
        self.load_history()

    def load_history(self):
        """加载历史选股记录"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = data.get("history", [])
                self.all_tracking_stocks = data.get("tracking_stocks", {})
        else:
            self.history = []
            self.all_tracking_stocks = {}

    def save_history(self):
        """保存历史记录"""
        data = {
            "history": self.history[-90:],  # 保留近90天
            "tracking_stocks": self.all_tracking_stocks,
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run_daily_selection(self, top_n: int = 15) -> DailySelection:
        """执行每日选股"""
        print("\n" + "#"*80)
        print(f"#  📊 BOM产业链每日选股 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("#"*80)

        # 执行三高筛选
        selections = self.engine.run_screening(top_n=top_n)
        today = datetime.now().strftime('%Y-%m-%d')

        daily_sel = DailySelection(
            date=today,
            selections=selections,
            performance=[]
        )

        # 记录到追踪库
        for s in selections:
            if s.code not in self.all_tracking_stocks:
                self.all_tracking_stocks[s.code] = {
                    "name": s.name,
                    "node_name": s.node_name,
                    "first_selected_date": today,
                    "total_score": s.total_score,
                    "tracking_days": 0,
                    "total_return": 0.0,
                    "selection_price": s.quote.get("price", 0) if s.quote else 0,
                }

        # 保存
        self.history.append(daily_sel.to_dict())
        self.save_history()

        return daily_sel

    def monitor_daily_performance(self):
        """监测今日表现（所有历史选股的表现）"""
        print("\n" + "="*80)
        print("📈 今日涨幅监测 - 所有追踪股票")
        print("="*80)

        if not self.all_tracking_stocks:
            print("  暂无追踪数据，先执行每日选股")
            return []

        codes = list(self.all_tracking_stocks.keys())
        quotes = self.engine.fetch_real_time_quotes(codes)

        # 计算今日表现
        today_results = []
        total_up = 0
        total_down = 0
        total_avg = 0.0

        print(f"\n{'代码':<12}{'名称':<12}{'入选日期':<14}{'入选价':<10}{'现价':<10}{'累计':<10}{'今日':<10}")
        print("-" * 80)

        for code, info in self.all_tracking_stocks.items():
            quote = quotes.get(code, {})
            if not quote:
                continue

            current_price = quote.get('price', 0)
            selection_price = info.get('selection_price', 0)
            daily_change = quote.get('change_pct', 0)

            # 累计收益
            if selection_price > 0:
                cumulative = ((current_price - selection_price) / selection_price) * 100
            else:
                cumulative = 0

            total_avg += daily_change
            if daily_change > 0:
                total_up += 1
            elif daily_change < 0:
                total_down += 1

            info['tracking_days'] += 1
            info['total_return'] = round(cumulative, 2)
            info['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            info['current_price'] = current_price
            info['daily_change'] = daily_change

            today_results.append({
                "code": code,
                "name": info.get('name', ''),
                "node_name": info.get('node_name', ''),
                "selection_date": info.get('first_selected_date', ''),
                "selection_price": selection_price,
                "current_price": current_price,
                "cumulative_return": round(cumulative, 2),
                "daily_change": round(daily_change, 2),
            })

            line = f"{code:<12}{info.get('name',''):<12}{info.get('first_selected_date',''):<14}{selection_price:<10.2f}{current_price:<10.2f}{cumulative:>+.2f}%   {daily_change:>+.2f}%"
            print(line)

        # 汇总
        print("\n" + "-" * 80)
        n = len(today_results)
        if n > 0:
            avg = total_avg / n
            print(f"📊 汇总: {n}只股票 | 上涨{total_up}只 | 下跌{total_down}只 | 平均涨跌幅 {avg:+.2f}%")

            # 计算胜率
            win_count = sum(1 for r in today_results if r['cumulative_return'] > 0)
            win_rate = (win_count / n) * 100
            print(f"🎯 累计胜率: {win_rate:.1f}% ({win_count}/{n})")

            # TOP 3 表现
            sorted_results = sorted(today_results, key=lambda x: x['cumulative_return'], reverse=True)
            print(f"\n🏆 最佳3只:")
            for r in sorted_results[:3]:
                print(f"   {r['name']}({r['code']}) +{r['cumulative_return']:.1f}%")

            print(f"📉 最差3只:")
            for r in sorted_results[-3:]:
                print(f"   {r['name']}({r['code']}) {r['cumulative_return']:+.1f}%")

        self.save_history()
        return today_results

    def generate_report(self) -> str:
        """生成完整报告"""
        report_lines = []
        report_lines.append("#"*80)
        report_lines.append(f"#  BOM产业链选股系统 - 每日监测报告")
        report_lines.append(f"#  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("#"*80)

        # 今日选股
        if self.history:
            latest = self.history[-1]
            report_lines.append("\n## 🎯 今日选股")
            for i, s in enumerate(latest.get('selections', []), 1):
                report_lines.append(
                    f"{i}. {s['name']}({s['code']}) | {s['node_name']} | "
                    f"壁垒{s['barrier_score']:.0f}·增长{s['growth_score']:.0f}·"
                    f"利润{s['profit_score']:.0f}·供需{s['supply_demand_score']:.0f}·"
                    f"总分{s['total_score']:.0f}"
                )

        # 历史表现
        if self.all_tracking_stocks:
            report_lines.append("\n## 📊 历史表现追踪")
            codes = list(self.all_tracking_stocks.keys())
            quotes = self.engine.fetch_real_time_quotes(codes)

            total_returns = []
            for code, info in self.all_tracking_stocks.items():
                quote = quotes.get(code, {})
                if quote:
                    selection_price = info.get('selection_price', 0)
                    current_price = quote.get('price', 0)
                    if selection_price > 0:
                        ret = ((current_price - selection_price) / selection_price) * 100
                        total_returns.append((code, info.get('name',''), ret))

            total_returns.sort(key=lambda x: x[2], reverse=True)

            if total_returns:
                avg = sum(r[2] for r in total_returns) / len(total_returns)
                win_rate = sum(1 for r in total_returns if r[2] > 0) / len(total_returns) * 100
                report_lines.append(f"平均收益: {avg:+.2f}% | 胜率: {win_rate:.1f}%")

        report = "\n".join(report_lines)
        print(report)
        return report

    def run_full_workflow(self):
        """执行完整工作流: 选股 + 监测 + 报告"""
        print("\n" + "🚀"*40)
        print("🚀 BOM产业链自动选股系统启动")
        print("🚀"*40)

        # Step 1: 选股
        self.run_daily_selection(top_n=15)

        # Step 2: 监测
        self.monitor_daily_performance()

        # Step 3: 报告
        self.generate_report()

        print("\n✅ 完整工作流执行完毕！")


def main():
    system = DailyMonitoringSystem()
    system.run_full_workflow()


if __name__ == "__main__":
    main()
