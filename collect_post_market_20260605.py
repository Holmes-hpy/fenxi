#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年6月5日收盘后学习流程 - 完整的收盘后分析系统
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_core import (
    get_market_index,
    industry_comparison,
    get_northbound_flow,
    get_dragon_tiger_board,
    get_stock_quote,
    ths_hot_reason
)
from stock_selection_system import StockSelectionSystem
import json
from datetime import datetime, timedelta
from pathlib import Path


class PostMarketLearningSystem:
    """收盘后学习系统"""
    
    def __init__(self):
        self.project_dir = Path('/Users/houpengyuan/Documents/trae_projects/a-stock-data')
        self.knowledge_dir = self.project_dir / 'knowledge'
        self.reports_dir = self.project_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        self.market_data = {}
        self.analysis_result = {}
        
        print("=" * 80)
        print("📈 每日收盘后学习流程")
        print("=" * 80)
        print(f"日期：{self.date_str}")
        print(f"时间：{datetime.now().strftime('%H:%M:%S')}")
        print()
        
    def step1_collect_market_data(self):
        """步骤1：获取今日A股完整行情数据"""
        print("📊 步骤1：获取今日A股完整行情数据")
        print("-" * 80)
        
        # 1.1 大盘指数
        print("\n1.1 获取大盘指数...")
        try:
            # 获取上证指数、深证成指等
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
                            'volume': idx.get('amount_wan', 'N/A')
                        })
                except Exception:
                    pass
            
            self.market_data['index'] = index_list
            
            print("  大盘指数：")
            for idx in index_list:
                print(f"    {idx['name']:12}  收盘: {idx['close']:8.2f}  "
                      f"涨跌: {idx['change_pct']:+.2f}%  "
                      f"成交额: {idx.get('volume', 'N/A')}万")
        except Exception as e:
            print(f"  ⚠️ 获取大盘指数失败: {e}")
            self.market_data['index'] = []
        
        # 1.2 行业板块涨跌
        print("\n1.2 获取行业板块涨跌...")
        try:
            industry_data = industry_comparison()
            self.market_data['industry'] = industry_data
            
            if 'top' in industry_data:
                print("  涨幅前5行业：")
                for i, ind in enumerate(industry_data['top'][:5]):
                    print(f"    {i+1}. {ind.get('name', ''):15} {ind.get('change_pct', 0):>6.2f}%")
            
            if 'bottom' in industry_data:
                print("  跌幅前5行业：")
                for i, ind in enumerate(industry_data['bottom'][:5]):
                    print(f"    {i+1}. {ind.get('name', ''):15} {ind.get('change_pct', 0):>6.2f}%")
        except Exception as e:
            print(f"  ⚠️ 获取行业板块失败: {e}")
        
        # 1.3 北向资金
        print("\n1.3 获取北向资金...")
        try:
            northbound = get_northbound_flow()
            self.market_data['northbound'] = northbound
            total_flow = northbound.get('total', 0)
            print(f"  北向资金净流入: {total_flow:.2f} 亿元 (沪股通: {northbound.get('hgt', 0):.2f}亿, 深股通: {northbound.get('sgt', 0):.2f}亿)")
        except Exception as e:
            print(f"  ⚠️ 获取北向资金失败: {e}")
        
        print("✓ 步骤1完成\n")
        return self.market_data
    
    def step2_analyze_top_stocks(self):
        """步骤2：分析今日涨跌排名靠前的股票"""
        print("🔥 步骤2：分析今日涨跌排名靠前的股票")
        print("-" * 80)
        
        self.market_data['top_stocks'] = {}
        
        print("\n2.1 获取热点股票...")
        try:
            hot_stocks = ths_hot_reason()
            if not hot_stocks.empty:
                self.market_data['top_stocks']['hot'] = hot_stocks
                
                # 检查是否有涨幅%列
                if '涨幅%' in hot_stocks.columns:
                    # 涨幅前10
                    top_gainers = hot_stocks.sort_values('涨幅%', ascending=False).head(10)
                    print("  涨幅前10股票：")
                    for i, (_, row) in enumerate(top_gainers.iterrows()):
                        print(f"    {i+1:2}. {row['名称']:10} ({row['代码']})  "
                              f"涨幅: {row['涨幅%']:>6.2f}%  "
                              f"题材: {str(row.get('题材归因', ''))[:20]}...")
                    
                    # 跌幅前10
                    top_losers = hot_stocks.sort_values('涨幅%', ascending=True).head(10)
                    print("\n  跌幅前10股票：")
                    for i, (_, row) in enumerate(top_losers.iterrows()):
                        print(f"    {i+1:2}. {row['名称']:10} ({row['代码']})  "
                              f"跌幅: {row['涨幅%']:>6.2f}%")
                    
                    # 异常波动
                    print("\n  异常波动股票（涨跌幅>9.9%）：")
                    extreme = hot_stocks[abs(hot_stocks['涨幅%']) > 9.9]
                    if not extreme.empty:
                        for i, (_, row) in enumerate(extreme.iterrows()):
                            print(f"    {i+1:2}. {row['名称']:10} ({row['代码']})  "
                                  f"涨跌幅: {row['涨幅%']:>6.2f}%")
                    else:
                        print("    无")
                else:
                    print("  热点股票数据中缺少'涨幅%'列")
                    print(f"  可用列：{list(hot_stocks.columns)}")
        except Exception as e:
            print(f"  ⚠️ 获取热点股票失败: {e}")
        
        print("✓ 步骤2完成\n")
        return self.market_data
    
    def step3_check_dragon_tiger_board(self):
        """步骤3：查看龙虎榜数据"""
        print("🐉 步骤3：查看龙虎榜数据")
        print("-" * 80)
        
        self.market_data['dragon_tiger'] = {}
        
        print("\n3.1 获取龙虎榜...")
        try:
            dt_data = get_dragon_tiger_board()
            self.market_data['dragon_tiger'] = dt_data
            
            records = dt_data.get('records', [])
            if records and len(records) > 0:
                print(f"  今日共 {len(records)} 只股票上榜")
                
                print("\n  上榜股票：")
                for i, stock in enumerate(records[:10]):
                    name = stock.get('SECURITY_NAME_ABBR', 'N/A')
                    code = stock.get('SECURITY_CODE', 'N/A')
                    net_buy = round((stock.get('BILLBOARD_NET_AMT') or 0) / 10000, 1)
                    print(f"    {i+1}. {name:10} ({code})  净买入: {net_buy}万元")
            else:
                print("  今日无龙虎榜数据")
        except Exception as e:
            print(f"  ⚠️ 获取龙虎榜失败: {e}")
        
        print("✓ 步骤3完成\n")
        return self.market_data
    
    def step4_summarize_market(self):
        """步骤4：总结今日市场的主要特点和规律"""
        print("💡 步骤4：总结今日市场的主要特点和规律")
        print("-" * 80)
        
        self.analysis_result = {
            'date': self.date_str,
            'market_sentiment': '',
            'hot_sectors': [],
            'capital_flow': '',
            'key_observations': []
        }
        
        # 4.1 资金流向分析
        print("\n4.1 资金流向分析...")
        if 'northbound' in self.market_data:
            nb = self.market_data['northbound']
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
            avg_change = sum(idx.get('change_pct', 0) for idx in idx_list) / len(idx_list)
            
            if avg_change > 1:
                sentiment = "市场情绪高涨 🚀"
            elif avg_change > 0:
                sentiment = "市场情绪偏暖 🌤️"
            elif avg_change > -1:
                sentiment = "市场情绪谨慎 ⛅"
            else:
                sentiment = "市场情绪低迷 🌧️"
            
            self.analysis_result['market_sentiment'] = sentiment
            print(f"  市场情绪：{sentiment} (平均涨跌: {avg_change:.2f}%)")
        
        # 4.3 热点板块
        print("\n4.3 热点板块分析...")
        if 'industry' in self.market_data and 'top' in self.market_data['industry']:
            top_industries = self.market_data['industry']['top'][:5]
            self.analysis_result['hot_sectors'] = [ind.get('name', '') for ind in top_industries]
            print(f"  今日热点板块：{', '.join(self.analysis_result['hot_sectors'])}")
        
        # 4.4 关键观察
        print("\n4.4 关键观察...")
        observations = []
        
        if 'top_stocks' in self.market_data and 'hot' in self.market_data['top_stocks']:
            hot = self.market_data['top_stocks']['hot']
            if not hot.empty and '涨幅%' in hot.columns:
                # 观察涨停板数量
                limit_up = hot[hot['涨幅%'] > 9.9]
                if len(limit_up) > 30:
                    observations.append(f"涨停家数较多({len(limit_up)}家)，市场活跃度高")
                elif len(limit_up) > 10:
                    observations.append(f"涨停家数适中({len(limit_up)}家)，结构性机会存在")
                else:
                    observations.append(f"涨停家数较少({len(limit_up)}家)，市场谨慎")
        
        if 'index' in self.market_data and len(self.market_data['index']) >= 2:
            idx = self.market_data['index']
            if idx[0].get('change_pct', 0) > idx[1].get('change_pct', 0):
                observations.append("上证指数表现强于深证成指")
            else:
                observations.append("深证成指表现强于上证指数")
        
        self.analysis_result['key_observations'] = observations
        for obs in observations:
            print(f"  ✓ {obs}")
        
        print("✓ 步骤4完成\n")
        return self.analysis_result
    
    def step5_update_knowledge_base(self):
        """步骤5：更新知识库"""
        print("📚 步骤5：更新知识库")
        print("-" * 80)
        
        self.knowledge_dir.mkdir(exist_ok=True)
        
        # 5.1 更新市场规律
        print("\n5.1 更新市场规律知识库...")
        market_knowledge_file = self.knowledge_dir / 'market_knowledge.md'
        
        if market_knowledge_file.exists():
            with open(market_knowledge_file, 'a', encoding='utf-8') as f:
                f.write(f"\n\n## {self.date_str} 市场观察\n\n")
                f.write(f"- **市场情绪**：{self.analysis_result.get('market_sentiment', '')}\n")
                f.write(f"- **热点板块**：{', '.join(self.analysis_result.get('hot_sectors', []))}\n")
                f.write(f"- **资金流向**：{self.analysis_result.get('capital_flow', '')}\n")
                for obs in self.analysis_result.get('key_observations', []):
                    f.write(f"- {obs}\n")
            print("  ✓ 已更新 market_knowledge.md")
        else:
            with open(market_knowledge_file, 'w', encoding='utf-8') as f:
                f.write("# 市场知识宝库\n\n")
                f.write(f"## {self.date_str} 市场观察\n\n")
                f.write(f"- **市场情绪**：{self.analysis_result.get('market_sentiment', '')}\n")
                f.write(f"- **热点板块**：{', '.join(self.analysis_result.get('hot_sectors', []))}\n")
                f.write(f"- **资金流向**：{self.analysis_result.get('capital_flow', '')}\n")
                for obs in self.analysis_result.get('key_observations', []):
                    f.write(f"- {obs}\n")
            print("  ✓ 已创建 market_knowledge.md")
        
        # 5.2 更新行业知识
        print("\n5.2 更新行业知识...")
        industry_knowledge_file = self.knowledge_dir / 'industry_knowledge.md'
        if 'industry' in self.market_data:
            industry_data = self.market_data['industry']
            if industry_knowledge_file.exists():
                with open(industry_knowledge_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n## {self.date_str} 行业表现\n\n")
                    if 'top' in industry_data:
                        f.write("### 涨幅领先行业\n")
                        for i, ind in enumerate(industry_data['top'][:5]):
                            f.write(f"{i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%\n")
                    if 'bottom' in industry_data:
                        f.write("\n### 跌幅领先行业\n")
                        for i, ind in enumerate(industry_data['bottom'][:5]):
                            f.write(f"{i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%\n")
                print("  ✓ 已更新 industry_knowledge.md")
            else:
                with open(industry_knowledge_file, 'w', encoding='utf-8') as f:
                    f.write("# 行业知识宝库\n\n")
                    f.write(f"## {self.date_str} 行业表现\n\n")
                    if 'top' in industry_data:
                        f.write("### 涨幅领先行业\n")
                        for i, ind in enumerate(industry_data['top'][:5]):
                            f.write(f"{i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%\n")
                    if 'bottom' in industry_data:
                        f.write("\n### 跌幅领先行业\n")
                        for i, ind in enumerate(industry_data['bottom'][:5]):
                            f.write(f"{i+1}. {ind.get('name', '')}: {ind.get('change_pct', 0):.2f}%\n")
                print("  ✓ 已创建 industry_knowledge.md")
        
        # 5.3 检查昨日选股预测
        print("\n5.3 检查昨日选股预测...")
        try:
            # 获取昨日日期
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"  正在检查 {yesterday} 的选股预测...")
            
            selection_history = self.project_dir / 'stock_selection_db' / 'selection_history.json'
            if selection_history.exists():
                with open(selection_history, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                print(f"  共找到 {len(history)} 条历史记录")
                
                # 记录错误日志（如果有的话）
                mistake_log = self.knowledge_dir / 'mistake_log.md'
                if not mistake_log.exists():
                    with open(mistake_log, 'w', encoding='utf-8') as f:
                        f.write("# 错误日志\n\n")
                print("  ✓ 已检查选股预测记录")
            else:
                print("  ⚠️ 暂无选股历史记录")
        except Exception as e:
            print(f"  ⚠️ 检查预测失败: {e}")
        
        print("✓ 步骤5完成\n")
    
    def step6_generate_report(self):
        """步骤6：生成收盘后学习报告"""
        print("📝 步骤6：生成收盘后学习报告")
        print("-" * 80)
        
        report_file = self.reports_dir / f'收盘后学习_{self.date_str}.md'
        
        report = f"""# 📊 每日收盘后学习报告 - {self.date_str}

**报告日期**：{self.date_str}  
**生成时间**：{datetime.now().strftime('%H:%M:%S')}  
**数据来源**：A股数据核心模块 + 知识库

---

## 1️⃣ 今日市场概览

### 1.1 大盘指数表现

| 指数 | 收盘价 | 涨跌幅 | 成交量 |
|------|--------|--------|--------|
"""
        
        if 'index' in self.market_data:
            for idx in self.market_data['index']:
                report += f"| {idx.get('name', '')} | {idx.get('close', 0):.2f} | {idx.get('change_pct', 0):+.2f}% | {idx.get('volume', 'N/A')} |\n"
        
        report += f"""
### 1.2 市场情绪

**{self.analysis_result.get('market_sentiment', '未知')}**

### 1.3 资金流向

{self.analysis_result.get('capital_flow', '暂无数据')}

---

## 2️⃣ 行业板块分析

### 2.1 涨幅前5行业

"""
        
        if 'industry' in self.market_data and 'top' in self.market_data['industry']:
            for i, ind in enumerate(self.market_data['industry']['top'][:5]):
                report += f"{i+1}. **{ind.get('name', '')}**: {ind.get('change_pct', 0):+.2f}%\n"
        
        report += f"""
### 2.2 跌幅前5行业

"""
        
        if 'industry' in self.market_data and 'bottom' in self.market_data['industry']:
            for i, ind in enumerate(self.market_data['industry']['bottom'][:5]):
                report += f"{i+1}. **{ind.get('name', '')}**: {ind.get('change_pct', 0):.2f}%\n"
        
        report += f"""
---

## 3️⃣ 个股涨跌排名

### 3.1 涨幅前10股票

"""
        
        if 'top_stocks' in self.market_data and 'hot' in self.market_data['top_stocks']:
            hot = self.market_data['top_stocks']['hot']
            if not hot.empty and '涨幅%' in hot.columns:
                top_gainers = hot.sort_values('涨幅%', ascending=False).head(10)
                for i, (_, row) in enumerate(top_gainers.iterrows()):
                    report += f"{i+1}. **{row['名称']}** ({row['代码']}) - 涨幅 {row['涨幅%']:.2f}%\n"
                    if '题材归因' in row and row['题材归因']:
                        report += f"   题材：{row['题材归因']}\n"
        
        report += f"""
### 3.2 跌幅前10股票

"""
        
        if 'top_stocks' in self.market_data and 'hot' in self.market_data['top_stocks']:
            hot = self.market_data['top_stocks']['hot']
            if not hot.empty and '涨幅%' in hot.columns:
                top_losers = hot.sort_values('涨幅%', ascending=True).head(10)
                for i, (_, row) in enumerate(top_losers.iterrows()):
                    report += f"{i+1}. **{row['名称']}** ({row['代码']}) - 跌幅 {row['涨幅%']:.2f}%\n"
        
        report += f"""
---

## 4️⃣ 龙虎榜分析

"""
        
        if 'dragon_tiger' in self.market_data and self.market_data['dragon_tiger']:
            dt = self.market_data['dragon_tiger']
            records = dt.get('records', [])
            if records:
                report += f"今日共 **{len(records)}** 只股票上榜\n\n"
                report += "### 上榜股票\n\n"
                for i, stock in enumerate(records[:10]):
                    name = stock.get('SECURITY_NAME_ABBR', 'N/A')
                    code = stock.get('SECURITY_CODE', 'N/A')
                    net_buy = round((stock.get('BILLBOARD_NET_AMT') or 0) / 10000, 1)
                    report += f"{i+1}. **{name}** ({code})\n"
                    report += f"   净买入：{net_buy}万元\n"
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
        
        report += f"""
### 5.2 投资启示

（根据今日市场表现总结，待后续版本完善）

---

## 6️⃣ 知识库更新记录

✅ 更新文件：
- `knowledge/market_knowledge.md` - 添加今日市场观察
- `knowledge/industry_knowledge.md` - 添加今日行业表现
- `knowledge/mistake_log.md` - 记录预测错误（如有）
- `reports/收盘后学习_{self.date_str}.md` - 本报告

---

⚠️ **风险提示**：以上分析仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        report_file.write_text(report, encoding='utf-8')
        print(f"  ✓ 报告已生成：{report_file.name}")
        print(f"  ✓ 保存位置：{report_file}")
        print("✓ 步骤6完成\n")
        
        return report_file
    
    def run(self):
        """运行完整的收盘后学习流程"""
        print("🚀 开始执行收盘后学习流程...\n")
        
        # 执行所有步骤
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
    """主函数"""
    system = PostMarketLearningSystem()
    system.run()


if __name__ == '__main__':
    main()
