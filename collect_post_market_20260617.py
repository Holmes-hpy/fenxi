#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年6月17日收盘后学习流程 - 完整的收盘后分析系统
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_core import (
    get_market_index,
    industry_comparison,
    get_northbound_flow,
    get_dragon_tiger_board,
    get_stock_quote,
    ths_hot_reason,
)
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd


class PostMarketLearningSystem:
    """收盘后学习系统（2026-06-17 版）"""

    def __init__(self):
        self.project_dir = Path('/Users/houpengyuan/Documents/trae_projects/a-stock-data')
        self.reports_dir = self.project_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)

        self.date_str = '2026-06-17'
        self.market_data = {}
        self.analysis_result = {}

        print("=" * 80)
        print("📈 每日收盘后学习流程 -", self.date_str)
        print("=" * 80)
        print(f"时间：{datetime.now().strftime('%H:%M:%S')}")
        print()

    # ==================== 步骤1：行情数据 ====================
    def step1_collect_market_data(self):
        print("📊 步骤1：获取今日A股完整行情数据")
        print("-" * 80)

        # 1.1 大盘指数
        print("\n1.1 获取大盘指数...")
        try:
            index_codes = ["000001", "399001", "399006", "000688"]
            index_names = ["上证指数", "深证成指", "创业板指", "科创50"]
            index_list = []

            for code, name in zip(index_codes, index_names):
                try:
                    quote_data = get_stock_quote(code)
                    if code in quote_data:
                        idx = quote_data[code]
                        index_list.append({
                            'name': name,
                            'code': code,
                            'close': idx.get('price', 0),
                            'change_pct': idx.get('change_pct', 0),
                            'change': idx.get('change', 0),
                            'volume': idx.get('vol', 0),
                            'amount_wan': idx.get('amount_wan', 0)
                        })
                except Exception as e:
                    print(f"    ⚠️ 获取{name}({code})失败: {e}")

            self.market_data['index'] = index_list

            print("  大盘指数：")
            for idx in index_list:
                print(f"    {idx['name']:12}  收盘: {idx['close']:8.2f}  "
                      f"涨跌: {idx['change_pct']:+.2f}%  "
                      f"成交额: {idx.get('amount_wan', 0):.0f}万")
        except Exception as e:
            print(f"  ⚠️ 获取大盘指数失败: {e}")
            traceback.print_exc()
            self.market_data['index'] = []

        # 1.2 行业板块涨跌
        print("\n1.2 获取行业板块涨跌...")
        try:
            industry_data = industry_comparison()
            self.market_data['industry'] = industry_data

            if isinstance(industry_data, dict):
                if 'top' in industry_data:
                    print("  涨幅前5行业：")
                    top_list = industry_data['top']
                    if isinstance(top_list, pd.DataFrame):
                        top_list = top_list.to_dict('records')
                    for i, ind in enumerate(top_list[:5]):
                        if isinstance(ind, dict):
                            print(f"    {i+1}. {ind.get('name', ''):15} {ind.get('change_pct', 0):>+6.2f}%")
                        else:
                            print(f"    {i+1}. {ind}")

                if 'bottom' in industry_data:
                    print("  跌幅前5行业：")
                    bottom_list = industry_data['bottom']
                    if isinstance(bottom_list, pd.DataFrame):
                        bottom_list = bottom_list.to_dict('records')
                    for i, ind in enumerate(bottom_list[:5]):
                        if isinstance(ind, dict):
                            print(f"    {i+1}. {ind.get('name', ''):15} {ind.get('change_pct', 0):>6.2f}%")
                        else:
                            print(f"    {i+1}. {ind}")
            else:
                print(f"  行业数据类型: {type(industry_data)}")
                print(f"  内容: {str(industry_data)[:300]}")
        except Exception as e:
            print(f"  ⚠️ 获取行业板块失败: {e}")
            traceback.print_exc()

        # 1.3 北向资金
        print("\n1.3 获取北向资金...")
        try:
            northbound = get_northbound_flow()
            self.market_data['northbound'] = northbound

            if isinstance(northbound, dict):
                total_flow = northbound.get('total', 0)
                hgt = northbound.get('hgt', 0)
                sgt = northbound.get('sgt', 0)
                print(f"  北向资金: 合计 {total_flow:+.2f} 亿元 (沪股通: {hgt:+.2f}亿, 深股通: {sgt:+.2f}亿)")
            else:
                print(f"  北向资金数据: {northbound}")
        except Exception as e:
            print(f"  ⚠️ 获取北向资金失败: {e}")
            traceback.print_exc()

        print("\n✓ 步骤1完成\n")
        return self.market_data

    # ==================== 步骤2：个股排名 ====================
    def step2_analyze_top_stocks(self):
        print("🔥 步骤2：分析今日涨跌排名靠前的股票")
        print("-" * 80)

        self.market_data['top_stocks'] = {}

        print("\n2.1 获取热点股票...")
        try:
            hot_stocks = ths_hot_reason()
            self.market_data['top_stocks']['hot'] = hot_stocks

            if isinstance(hot_stocks, pd.DataFrame) and not hot_stocks.empty:
                print(f"  共获取到 {len(hot_stocks)} 只热点股票")
                print(f"  可用列: {list(hot_stocks.columns)}")

                change_col = None
                for col in ['涨幅%', '涨幅', '涨跌幅', 'change_pct', 'pct_chg']:
                    if col in hot_stocks.columns:
                        change_col = col
                        break

                name_col = None
                for col in ['名称', '股票名称', 'name', 'SECURITY_NAME_ABBR']:
                    if col in hot_stocks.columns:
                        name_col = col
                        break

                code_col = None
                for col in ['代码', '股票代码', 'code', 'SECURITY_CODE']:
                    if col in hot_stocks.columns:
                        code_col = col
                        break

                theme_col = None
                for col in ['题材归因', '题材', '概念', 'theme']:
                    if col in hot_stocks.columns:
                        theme_col = col
                        break

                if change_col:
                    top_gainers = hot_stocks.sort_values(change_col, ascending=False).head(10)
                    print("\n  涨幅前10股票：")
                    for i, (_, row) in enumerate(top_gainers.iterrows()):
                        name = row[name_col] if name_col else 'N/A'
                        code = row[code_col] if code_col else ''
                        change = row[change_col]
                        theme = str(row[theme_col])[:30] if theme_col and pd.notna(row[theme_col]) else ''
                        print(f"    {i+1:2}. {str(name):10} ({code})  "
                              f"涨幅: {change:>6.2f}%  题材: {theme}")

                    top_losers = hot_stocks.sort_values(change_col, ascending=True).head(10)
                    print("\n  跌幅前10股票：")
                    for i, (_, row) in enumerate(top_losers.iterrows()):
                        name = row[name_col] if name_col else 'N/A'
                        code = row[code_col] if code_col else ''
                        change = row[change_col]
                        print(f"    {i+1:2}. {str(name):10} ({code})  跌幅: {change:>6.2f}%")

                    print("\n  异常波动股票（涨跌幅>9.9%）：")
                    extreme = hot_stocks[abs(hot_stocks[change_col]) > 9.9]
                    if not extreme.empty:
                        for i, (_, row) in enumerate(extreme.iterrows()):
                            name = row[name_col] if name_col else 'N/A'
                            code = row[code_col] if code_col else ''
                            change = row[change_col]
                            print(f"    {i+1:2}. {str(name):10} ({code})  涨跌幅: {change:>6.2f}%")
                    else:
                        print("    无")

                    self.market_data['top_stocks']['top_gainers'] = top_gainers
                    self.market_data['top_stocks']['top_losers'] = top_losers
                    self.market_data['top_stocks']['extreme'] = extreme
                else:
                    print("  未找到涨幅列，跳过涨跌排名分析")
            elif isinstance(hot_stocks, list):
                print(f"  热点股票为列表格式，共 {len(hot_stocks)} 项")
                if len(hot_stocks) > 0:
                    print(f"  第一项: {str(hot_stocks[0])[:300]}")
            else:
                print(f"  热点股票数据类型: {type(hot_stocks)}, 内容: {str(hot_stocks)[:300]}")
        except Exception as e:
            print(f"  ⚠️ 获取热点股票失败: {e}")
            traceback.print_exc()

        print("\n✓ 步骤2完成\n")
        return self.market_data

    # ==================== 步骤3：龙虎榜 ====================
    def step3_check_dragon_tiger_board(self):
        print("🐉 步骤3：查看龙虎榜数据")
        print("-" * 80)

        self.market_data['dragon_tiger'] = {}

        print("\n3.1 获取龙虎榜...")
        try:
            dt_data = get_dragon_tiger_board()
            self.market_data['dragon_tiger'] = dt_data

            if isinstance(dt_data, dict):
                records = dt_data.get('records', [])
                if isinstance(records, pd.DataFrame):
                    records = records.to_dict('records')
                if records and len(records) > 0:
                    print(f"  今日共 {len(records)} 只股票上榜")

                    print("\n  上榜股票（前10）：")
                    for i, stock in enumerate(records[:10]):
                        if isinstance(stock, dict):
                            name = stock.get('SECURITY_NAME_ABBR', stock.get('name', 'N/A'))
                            code = stock.get('SECURITY_CODE', stock.get('code', 'N/A'))
                            net_buy_raw = stock.get('BILLBOARD_NET_AMT', stock.get('net_buy', 0))
                            net_buy = round((net_buy_raw or 0) / 10000, 1) if net_buy_raw else 0
                            print(f"    {i+1}. {str(name):10} ({code})  净买入: {net_buy}万元")
                else:
                    print("  今日无龙虎榜数据")
            else:
                print(f"  龙虎榜数据类型: {type(dt_data)}")
                print(f"  内容: {str(dt_data)[:400]}")
        except Exception as e:
            print(f"  ⚠️ 获取龙虎榜失败: {e}")
            traceback.print_exc()

        print("\n✓ 步骤3完成\n")
        return self.market_data

    # ==================== 步骤4：市场总结 ====================
    def step4_summarize_market(self):
        print("💡 步骤4：总结今日市场的主要特点和规律")
        print("-" * 80)

        self.analysis_result = {
            'date': self.date_str,
            'market_sentiment': '',
            'hot_sectors': [],
            'capital_flow': '',
            'key_observations': [],
            'limit_up_count': 0,
            'limit_down_count': 0,
        }

        # 4.1 资金流向
        print("\n4.1 资金流向分析...")
        if 'northbound' in self.market_data:
            nb = self.market_data['northbound']
            if isinstance(nb, dict):
                total_flow = nb.get('total', 0)
                if isinstance(total_flow, (int, float)):
                    if total_flow > 0:
                        self.analysis_result['capital_flow'] = f"北向资金净流入 {total_flow:.2f} 亿元，外资持续买入"
                    else:
                        self.analysis_result['capital_flow'] = f"北向资金净流出 {abs(total_flow):.2f} 亿元，外资流出"
                    print(f"  {self.analysis_result['capital_flow']}")

        # 4.2 市场情绪
        print("\n4.2 市场情绪分析...")
        if 'index' in self.market_data and len(self.market_data['index']) > 0:
            idx_list = self.market_data['index']
            valid_changes = [idx.get('change_pct', 0) for idx in idx_list if isinstance(idx.get('change_pct', 0), (int, float))]
            avg_change = sum(valid_changes) / len(valid_changes) if valid_changes else 0

            if avg_change > 1:
                sentiment = "市场情绪高涨"
            elif avg_change > 0:
                sentiment = "市场情绪偏暖"
            elif avg_change > -1:
                sentiment = "市场情绪谨慎"
            else:
                sentiment = "市场情绪低迷"

            self.analysis_result['market_sentiment'] = sentiment
            print(f"  市场情绪：{sentiment} (平均涨跌: {avg_change:.2f}%)")

        # 4.3 热点板块
        print("\n4.3 热点板块分析...")
        if 'industry' in self.market_data:
            industry_data = self.market_data['industry']
            if isinstance(industry_data, dict) and 'top' in industry_data:
                top_list = industry_data['top']
                if isinstance(top_list, pd.DataFrame):
                    top_list = top_list.to_dict('records')
                hot_sectors = []
                for ind in top_list[:5]:
                    if isinstance(ind, dict):
                        hot_sectors.append(ind.get('name', ''))
                    else:
                        hot_sectors.append(str(ind))
                self.analysis_result['hot_sectors'] = hot_sectors
                print(f"  今日热点板块：{', '.join(hot_sectors)}")

        # 4.4 关键观察
        print("\n4.4 关键观察...")
        observations = []

        if 'top_stocks' in self.market_data and 'hot' in self.market_data['top_stocks']:
            hot = self.market_data['top_stocks']['hot']
            if isinstance(hot, pd.DataFrame) and not hot.empty:
                change_col = None
                for col in ['涨幅%', '涨幅', '涨跌幅']:
                    if col in hot.columns:
                        change_col = col
                        break
                if change_col:
                    limit_up = hot[hot[change_col] > 9.9]
                    limit_down = hot[hot[change_col] < -9.9]
                    self.analysis_result['limit_up_count'] = len(limit_up)
                    self.analysis_result['limit_down_count'] = len(limit_down)

                    if len(limit_up) > 30:
                        observations.append(f"涨停家数较多({len(limit_up)}家)，市场活跃度高")
                    elif len(limit_up) > 10:
                        observations.append(f"涨停家数适中({len(limit_up)}家)，结构性机会存在")
                    else:
                        observations.append(f"涨停家数较少({len(limit_up)}家)，市场谨慎")
                    if len(limit_down) > 10:
                        observations.append(f"跌停家数较多({len(limit_down)}家)，需注意风险")

        if 'index' in self.market_data and len(self.market_data['index']) >= 2:
            idx = self.market_data['index']
            if idx[0].get('change_pct', 0) > idx[1].get('change_pct', 0):
                observations.append("上证指数表现强于深证成指，大盘蓝筹相对强势")
            else:
                observations.append("深证成指表现强于上证指数，中小盘成长相对活跃")

        self.analysis_result['key_observations'] = observations
        for obs in observations:
            print(f"  ✓ {obs}")

        print("\n✓ 步骤4完成\n")
        return self.analysis_result

    # ==================== 步骤5：知识库 ====================
    def step5_update_knowledge_base(self):
        print("📚 步骤5：更新知识库")
        print("-" * 80)

        # 5.1 更新市场规律 - 根目录 market_knowledge.md
        print("\n5.1 更新市场规律知识库 (market_knowledge.md)...")
        market_knowledge_file = self.project_dir / 'market_knowledge.md'

        market_content = f"\n\n---\n\n## {self.date_str} 市场观察\n\n"
        market_content += f"- **市场情绪**：{self.analysis_result.get('market_sentiment', '')}\n"
        market_content += f"- **热点板块**：{', '.join(self.analysis_result.get('hot_sectors', []))}\n"
        market_content += f"- **资金流向**：{self.analysis_result.get('capital_flow', '')}\n"
        lu = self.analysis_result.get('limit_up_count', 0)
        ld = self.analysis_result.get('limit_down_count', 0)
        market_content += f"- **涨跌停统计**：涨停 {lu} 家，跌停 {ld} 家\n"
        for obs in self.analysis_result.get('key_observations', []):
            market_content += f"- {obs}\n"

        if market_knowledge_file.exists():
            with open(market_knowledge_file, 'a', encoding='utf-8') as f:
                f.write(market_content)
            print("  ✓ 已更新 market_knowledge.md")
        else:
            with open(market_knowledge_file, 'w', encoding='utf-8') as f:
                f.write("# 市场知识库\n\n" + market_content)
            print("  ✓ 已创建 market_knowledge.md")

        # 5.2 更新行业知识 - 根目录 industry_knowledge.md
        print("\n5.2 更新行业知识 (industry_knowledge.md)...")
        industry_knowledge_file = self.project_dir / 'industry_knowledge.md'

        industry_content = f"\n\n---\n\n## {self.date_str} 行业表现\n\n"
        if 'industry' in self.market_data:
            industry_data = self.market_data['industry']
            if isinstance(industry_data, dict):
                if 'top' in industry_data:
                    industry_content += "### 涨幅领先行业\n"
                    top_list = industry_data['top']
                    if isinstance(top_list, pd.DataFrame):
                        top_list = top_list.to_dict('records')
                    for i, ind in enumerate(top_list[:5]):
                        if isinstance(ind, dict):
                            industry_content += f"{i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):+.2f}%\n"
                        else:
                            industry_content += f"{i+1}. {ind}\n"
                if 'bottom' in industry_data:
                    industry_content += "\n### 跌幅领先行业\n"
                    bottom_list = industry_data['bottom']
                    if isinstance(bottom_list, pd.DataFrame):
                        bottom_list = bottom_list.to_dict('records')
                    for i, ind in enumerate(bottom_list[:5]):
                        if isinstance(ind, dict):
                            industry_content += f"{i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%\n"
                        else:
                            industry_content += f"{i+1}. {ind}\n"

        if industry_knowledge_file.exists():
            with open(industry_knowledge_file, 'a', encoding='utf-8') as f:
                f.write(industry_content)
            print("  ✓ 已更新 industry_knowledge.md")
        else:
            with open(industry_knowledge_file, 'w', encoding='utf-8') as f:
                f.write("# 行业知识库\n\n" + industry_content)
            print("  ✓ 已创建 industry_knowledge.md")

        # 5.3 检查昨日选股预测 - 根目录 mistake_log.md
        print("\n5.3 检查昨日选股预测 (mistake_log.md)...")
        mistake_log_file = self.project_dir / 'mistake_log.md'

        try:
            yesterday = (datetime.strptime(self.date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"  检查日期: {yesterday}")

            selection_history = self.project_dir / 'stock_selection_db' / 'selection_history.json'
            if selection_history.exists():
                with open(selection_history, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                print(f"  共找到 {len(history)} 条历史记录")

                yesterday_selections = [h for h in history if isinstance(h, dict) and h.get('date') == yesterday]
                if yesterday_selections:
                    print(f"  找到 {len(yesterday_selections)} 条昨日选股记录")

                    # 检查每只股票的实际表现
                    mistake_content = f"\n\n---\n\n## {self.date_str} - 检查 {yesterday} 选股预测\n\n"
                    correct = 0
                    wrong = 0

                    for sel in yesterday_selections:
                        code = sel.get('code', '')
                        name = sel.get('name', '')
                        pred_change = sel.get('predicted_change', 'N/A')
                        actual_change = 'N/A'

                        # 获取实际表现
                        try:
                            if code:
                                quote = get_stock_quote(code)
                                if code in quote and 'change_pct' in quote[code]:
                                    actual_change = f"{quote[code]['change_pct']:+.2f}%"
                                    chg = quote[code]['change_pct']
                                    if (isinstance(pred_change, str) and '涨' in pred_change and chg > 0) or \
                                       (isinstance(pred_change, str) and '跌' in pred_change and chg < 0):
                                        correct += 1
                                    else:
                                        wrong += 1
                        except Exception:
                            pass

                        mistake_content += f"- **{name}({code})**: 预测 {pred_change}，实际 {actual_change}\n"

                    mistake_content += f"\n> 预测准确率：{correct}/{correct+wrong}（{correct/(correct+wrong)*100:.1f}%）\n" if (correct+wrong) > 0 else "\n> 无可量化预测数据\n"

                    if not mistake_log_file.exists():
                        with open(mistake_log_file, 'w', encoding='utf-8') as f:
                            f.write("# 错误日志\n\n记录选股预测与实际表现的差异，用于反思和改进\n\n")
                    with open(mistake_log_file, 'a', encoding='utf-8') as f:
                        f.write(mistake_content)
                    print(f"  ✓ 已记录到 mistake_log.md（正确 {correct}，错误 {wrong}）")
                else:
                    print(f"  未找到 {yesterday} 的选股记录")
                    if not mistake_log_file.exists():
                        with open(mistake_log_file, 'w', encoding='utf-8') as f:
                            f.write("# 错误日志\n\n记录选股预测与实际表现的差异，用于反思和改进\n\n")
            else:
                print("  ⚠️ 暂无选股历史记录文件 (stock_selection_db/selection_history.json)")
                if not mistake_log_file.exists():
                    with open(mistake_log_file, 'w', encoding='utf-8') as f:
                        f.write("# 错误日志\n\n")
        except Exception as e:
            print(f"  ⚠️ 检查预测失败: {e}")
            if not mistake_log_file.exists():
                with open(mistake_log_file, 'w', encoding='utf-8') as f:
                    f.write("# 错误日志\n\n")

        print("\n✓ 步骤5完成\n")

    # ==================== 步骤6：生成报告 ====================
    def step6_generate_report(self):
        print("📝 步骤6：生成收盘后学习报告")
        print("-" * 80)

        report_file = self.reports_dir / f'收盘后学习_{self.date_str}.md'

        report = f"""# 📊 每日收盘后学习报告 - {self.date_str}

**报告日期**：{self.date_str}
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据来源**：A股数据核心模块 (a_stock_data_core.py) + 同花顺热点 + 东方财富龙虎榜

---

## 1️⃣ 今日市场概览

### 1.1 大盘指数表现

| 指数 | 收盘价 | 涨跌幅 | 成交额(万) |
|------|--------|--------|-----------|
"""

        if 'index' in self.market_data:
            for idx in self.market_data['index']:
                report += f"| {idx.get('name', '')} | {idx.get('close', 0):.2f} | {idx.get('change_pct', 0):+.2f}% | {idx.get('amount_wan', 0):.0f} |\n"

        report += f"""
### 1.2 市场情绪

**{self.analysis_result.get('market_sentiment', '暂无数据')}**

### 1.3 资金流向

{self.analysis_result.get('capital_flow', '暂无数据')}

---

## 2️⃣ 行业板块分析

### 2.1 涨幅前5行业

"""

        if 'industry' in self.market_data and isinstance(self.market_data['industry'], dict):
            industry_data = self.market_data['industry']
            if 'top' in industry_data:
                top_list = industry_data['top']
                if isinstance(top_list, pd.DataFrame):
                    top_list = top_list.to_dict('records')
                for i, ind in enumerate(top_list[:5]):
                    if isinstance(ind, dict):
                        report += f"{i+1}. **{ind.get('name', '')}**: {ind.get('change_pct', 0):+.2f}%\n"
                    else:
                        report += f"{i+1}. {ind}\n"

        report += f"""
### 2.2 跌幅前5行业

"""

        if 'industry' in self.market_data and isinstance(self.market_data['industry'], dict):
            industry_data = self.market_data['industry']
            if 'bottom' in industry_data:
                bottom_list = industry_data['bottom']
                if isinstance(bottom_list, pd.DataFrame):
                    bottom_list = bottom_list.to_dict('records')
                for i, ind in enumerate(bottom_list[:5]):
                    if isinstance(ind, dict):
                        report += f"{i+1}. **{ind.get('name', '')}**: {ind.get('change_pct', 0):.2f}%\n"
                    else:
                        report += f"{i+1}. {ind}\n"

        report += f"""
---

## 3️⃣ 个股涨跌排名

### 3.1 涨幅前10股票

"""

        if 'top_stocks' in self.market_data and 'top_gainers' in self.market_data['top_stocks']:
            top_gainers = self.market_data['top_stocks']['top_gainers']
            if isinstance(top_gainers, pd.DataFrame) and not top_gainers.empty:
                change_col = None
                for col in ['涨幅%', '涨幅', '涨跌幅']:
                    if col in top_gainers.columns:
                        change_col = col
                        break
                name_col = None
                for col in ['名称', '股票名称']:
                    if col in top_gainers.columns:
                        name_col = col
                        break
                code_col = None
                for col in ['代码', '股票代码']:
                    if col in top_gainers.columns:
                        code_col = col
                        break
                theme_col = None
                for col in ['题材归因', '题材']:
                    if col in top_gainers.columns:
                        theme_col = col
                        break

                for i, (_, row) in enumerate(top_gainers.iterrows()):
                    name = row[name_col] if name_col else 'N/A'
                    code = row[code_col] if code_col else ''
                    change = row[change_col] if change_col else 0
                    report += f"{i+1}. **{name}** ({code}) - 涨幅 {change:.2f}%\n"
                    if theme_col and pd.notna(row[theme_col]):
                        report += f"   题材：{row[theme_col]}\n"

        report += f"""
### 3.2 跌幅前10股票

"""

        if 'top_stocks' in self.market_data and 'top_losers' in self.market_data['top_stocks']:
            top_losers = self.market_data['top_stocks']['top_losers']
            if isinstance(top_losers, pd.DataFrame) and not top_losers.empty:
                change_col = None
                for col in ['涨幅%', '涨幅', '涨跌幅']:
                    if col in top_losers.columns:
                        change_col = col
                        break
                name_col = None
                for col in ['名称', '股票名称']:
                    if col in top_losers.columns:
                        name_col = col
                        break
                code_col = None
                for col in ['代码', '股票代码']:
                    if col in top_losers.columns:
                        code_col = col
                        break

                for i, (_, row) in enumerate(top_losers.iterrows()):
                    name = row[name_col] if name_col else 'N/A'
                    code = row[code_col] if code_col else ''
                    change = row[change_col] if change_col else 0
                    report += f"{i+1}. **{name}** ({code}) - 跌幅 {change:.2f}%\n"

        report += f"""
---

## 4️⃣ 龙虎榜分析

"""

        if 'dragon_tiger' in self.market_data:
            dt = self.market_data['dragon_tiger']
            if isinstance(dt, dict):
                records = dt.get('records', [])
                if isinstance(records, pd.DataFrame):
                    records = records.to_dict('records')
                if records and len(records) > 0:
                    report += f"今日共 **{len(records)}** 只股票上榜\n\n"
                    report += "### 上榜股票（前10）\n\n"
                    for i, stock in enumerate(records[:10]):
                        if isinstance(stock, dict):
                            name = stock.get('SECURITY_NAME_ABBR', stock.get('name', 'N/A'))
                            code = stock.get('SECURITY_CODE', stock.get('code', 'N/A'))
                            net_buy_raw = stock.get('BILLBOARD_NET_AMT', stock.get('net_buy', 0))
                            net_buy = round((net_buy_raw or 0) / 10000, 1) if net_buy_raw else 0
                            report += f"{i+1}. **{name}** ({code})\n"
                            report += f"   净买入：{net_buy}万元\n"
                else:
                    report += "今日无龙虎榜数据（或数据尚未更新）\n"
            else:
                report += "今日无龙虎榜数据\n"
        else:
            report += "今日无龙虎榜数据\n"

        report += f"""
---

## 5️⃣ 市场规律总结

### 5.1 关键观察

"""

        for obs in self.analysis_result.get('key_observations', []):
            report += f"- {obs}\n"

        if not self.analysis_result.get('key_observations'):
            report += "- 今日暂无特别明显的市场规律特征\n"

        report += f"""
### 5.2 涨跌停统计

- **涨停家数**：{self.analysis_result.get('limit_up_count', 0)} 家
- **跌停家数**：{self.analysis_result.get('limit_down_count', 0)} 家

### 5.3 投资启示

- 关注今日热点板块的持续性
- 留意北向资金动向作为外资情绪的参考
- 观察涨停板数量变化判断市场活跃度
- 注意板块轮动带来的结构性机会

---

## 6️⃣ 知识库更新记录

✅ 更新文件：
- `market_knowledge.md` - 添加今日市场观察
- `industry_knowledge.md` - 添加今日行业表现
- `mistake_log.md` - 检查并记录预测差异（如有）
- `reports/收盘后学习_{self.date_str}.md` - 本报告

---

⚠️ **风险提示**：以上分析仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*报告版本：v1.0 (2026-06-17)*
"""

        report_file.write_text(report, encoding='utf-8')
        print(f"  ✓ 报告已生成：{report_file.name}")
        print(f"  ✓ 保存位置：{report_file}")

        # 保存原始数据
        data_file = self.reports_dir / f'收盘后数据_{self.date_str}.json'
        try:
            serializable_data = {}
            for key, value in self.market_data.items():
                if isinstance(value, pd.DataFrame):
                    serializable_data[key] = value.to_dict('records')
                elif isinstance(value, dict):
                    inner = {}
                    for k, v in value.items():
                        if isinstance(v, pd.DataFrame):
                            inner[k] = v.to_dict('records')
                        else:
                            inner[k] = str(v) if not isinstance(v, (int, float, str, list, dict)) else v
                    serializable_data[key] = inner
                else:
                    serializable_data[key] = str(value)
            serializable_data['analysis_result'] = self.analysis_result

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"  ✓ 原始数据已保存：{data_file.name}")
        except Exception as e:
            print(f"  ⚠️ 原始数据保存失败: {e}")

        print("\n✓ 步骤6完成\n")
        return report_file

    # ==================== 主流程 ====================
    def run(self):
        print("🚀 开始执行收盘后学习流程...\n")

        self.step1_collect_market_data()
        self.step2_analyze_top_stocks()
        self.step3_check_dragon_tiger_board()
        self.step4_summarize_market()
        self.step5_update_knowledge_base()
        report_file = self.step6_generate_report()

        print("=" * 80)
        print("✅ 收盘后学习流程完成！")
        print("=" * 80)
        print()
        print("📊 学习成果总结：")
        print("   ✓ 收集了完整的市场行情数据")
        print("   ✓ 分析了涨跌排名和异常波动")
        print("   ✓ 查看了龙虎榜数据")
        print("   ✓ 总结了市场特点和规律")
        print("   ✓ 更新了知识库文件")
        print("   ✓ 生成了完整的学习报告")
        print()
        print(f"📄 报告位置：{report_file}")
        print()

        return report_file


def main():
    system = PostMarketLearningSystem()
    system.run()


if __name__ == '__main__':
    main()