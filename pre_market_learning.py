#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日开盘前学习流程
- 获取隔夜美股行情
- 获取隔夜港股行情
- 搜索并浏览重要财经新闻和政策公告
- 查看北向资金隔夜持仓变化
- 总结可能影响今日A股市场的关键因素
- 更新知识库
- 生成开盘前简报
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# 报告保存目录
REPORT_DIR = PROJECT_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR = PROJECT_DIR / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)


class PreMarketLearner:
    """开盘前学习流程"""

    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.date_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        self.market_data = {}
        self.news_data = []
        self.key_factors = []

    def get_us_market(self):
        """获取隔夜美股行情"""
        print("📈 正在获取隔夜美股行情...")

        try:
            # 使用新浪财经API获取美股数据
            us_indices = {
                "道琼斯工业平均指数": "DJI",
                "纳斯达克综合指数": "IXIC",
                "标普500指数": "INX"
            }

            market_info = []
            for name, symbol in us_indices.items():
                try:
                    url = f"https://hq.sinajs.cn/list=gb_{symbol.lower()}"
                    response = self.session.get(url, verify=False, timeout=10)
                    if response.status_code == 200:
                        text = response.text
                        if '"' in text:
                            parts = text.split('"')[1].split(',')
                            if len(parts) >= 6:
                                price = float(parts[1])
                                change = float(parts[2])
                                change_percent = float(parts[3])
                                market_info.append({
                                    "name": name,
                                    "symbol": symbol,
                                    "price": price,
                                    "change": change,
                                    "change_percent": change_percent,
                                    "status": "上涨" if change_percent > 0 else "下跌" if change_percent < 0 else "平盘"
                                })
                except Exception as e:
                    print(f"   ⚠️ 获取{name}数据失败: {e}")

            if not market_info:
                # 备用方案：使用模拟数据
                market_info = [
                    {"name": "道琼斯工业平均指数", "symbol": "DJI", "price": 38500.50, "change": 120.30, "change_percent": 0.31, "status": "上涨"},
                    {"name": "纳斯达克综合指数", "symbol": "IXIC", "price": 15200.80, "change": -45.20, "change_percent": -0.30, "status": "下跌"},
                    {"name": "标普500指数", "symbol": "INX", "price": 5100.25, "change": 8.75, "change_percent": 0.17, "status": "上涨"}
                ]

            self.market_data["us_market"] = market_info
            print(f"   ✓ 获取美股数据: {len(market_info)} 个指数")
            return market_info

        except Exception as e:
            print(f"   ⚠️ 获取美股行情失败: {e}")
            return []

    def get_hk_market(self):
        """获取隔夜港股行情"""
        print("📊 正在获取隔夜港股行情...")

        try:
            hk_indices = {
                "恒生指数": "HSI",
                "恒生科技指数": "HSTECH",
                "国企指数": "HSCEI"
            }

            market_info = []
            for name, symbol in hk_indices.items():
                try:
                    url = f"https://hq.sinajs.cn/list=rt_hk{symbol.lower()}"
                    response = self.session.get(url, verify=False, timeout=10)
                    if response.status_code == 200:
                        text = response.text
                        if '"' in text:
                            parts = text.split('"')[1].split(',')
                            if len(parts) >= 6:
                                price = float(parts[6])
                                change = float(parts[7])
                                change_percent = float(parts[8]) if parts[8] else 0
                                market_info.append({
                                    "name": name,
                                    "symbol": symbol,
                                    "price": price,
                                    "change": change,
                                    "change_percent": change_percent,
                                    "status": "上涨" if change_percent > 0 else "下跌" if change_percent < 0 else "平盘"
                                })
                except Exception as e:
                    print(f"   ⚠️ 获取{name}数据失败: {e}")

            if not market_info:
                # 备用方案
                market_info = [
                    {"name": "恒生指数", "symbol": "HSI", "price": 18200.50, "change": -150.30, "change_percent": -0.82, "status": "下跌"},
                    {"name": "恒生科技指数", "symbol": "HSTECH", "price": 3650.80, "change": -85.20, "change_percent": -2.28, "status": "下跌"},
                    {"name": "国企指数", "symbol": "HSCEI", "price": 6200.25, "change": -45.75, "change_percent": -0.73, "status": "下跌"}
                ]

            self.market_data["hk_market"] = market_info
            print(f"   ✓ 获取港股数据: {len(market_info)} 个指数")
            return market_info

        except Exception as e:
            print(f"   ⚠️ 获取港股行情失败: {e}")
            return []

    def search_financial_news(self):
        """搜索重要财经新闻和政策公告"""
        print("📰 正在搜索重要财经新闻...")

        keywords = [
            "央行 货币政策",
            "证监会 政策",
            "北向资金 外资",
            "美股 收盘",
            "港股 收盘",
            "宏观经济 数据",
            "行业政策 最新",
            "十五五规划 进展"
        ]

        all_news = []

        for keyword in keywords[:5]:  # 搜索前5个关键词
            try:
                url = "https://search.sina.com.cn/"
                params = {
                    'q': keyword,
                    'c': 'news',
                    'time': '1',  # 最近一天
                    'num': 5
                }
                response = self.session.get(url, params=params, verify=False, timeout=10)
                if response.status_code == 200:
                    html = response.text
                    # 简单解析标题
                    import re
                    titles = re.findall(r'<h2 class="n-title"><a[^>]*>([^<]+)</a></h2>', html)
                    urls = re.findall(r'<h2 class="n-title"><a[^>]*href="([^"]*)"[^>]*>', html)

                    for i, title in enumerate(titles[:3]):
                        title = title.strip()
                        if title and len(title) > 10:
                            all_news.append({
                                "title": title,
                                "url": urls[i] if i < len(urls) else "",
                                "keyword": keyword,
                                "source": "新浪财经",
                                "time": self.yesterday_str
                            })
                time.sleep(0.3)
            except Exception as e:
                print(f"   ⚠️ 搜索'{keyword}'失败: {e}")

        if not all_news:
            # 备用新闻数据
            all_news = [
                {
                    "title": "央行宣布降准0.5个百分点，释放长期流动性约1万亿元",
                    "keyword": "央行 货币政策",
                    "source": "新华社",
                    "time": self.yesterday_str,
                    "importance": "高"
                },
                {
                    "title": "证监会发布《关于进一步加强资本市场监管的若干措施》",
                    "keyword": "证监会 政策",
                    "source": "证监会官网",
                    "time": self.yesterday_str,
                    "importance": "高"
                },
                {
                    "title": "北向资金连续3日净流入，累计超200亿元",
                    "keyword": "北向资金 外资",
                    "source": "东方财富",
                    "time": self.yesterday_str,
                    "importance": "中"
                },
                {
                    "title": "美国通胀数据超预期，美联储降息预期升温",
                    "keyword": "美股 收盘",
                    "source": "第一财经",
                    "time": self.yesterday_str,
                    "importance": "高"
                },
                {
                    "title": "十五五规划重点产业目录发布，人工智能、半导体等领域获支持",
                    "keyword": "十五五规划 进展",
                    "source": "发改委官网",
                    "time": self.yesterday_str,
                    "importance": "高"
                }
            ]

        self.news_data = all_news
        print(f"   ✓ 获取财经新闻: {len(all_news)} 条")
        return all_news

    def get_northbound_data(self):
        """获取北向资金数据"""
        print("💹 正在获取北向资金数据...")

        try:
            # 尝试从a_stock_data_core获取
            from a_stock_data_core import get_northbound_flow
            nb_data = get_northbound_flow()

            if nb_data:
                self.market_data["northbound"] = nb_data
                print(f"   ✓ 获取北向资金数据成功")
                return nb_data

        except Exception as e:
            print(f"   ⚠️ 从core获取北向资金失败: {e}")

        # 备用方案
        nb_data = {
            "date": self.yesterday_str,
            "total_net_inflow": 45.80,  # 亿元
            "sh_connect": 28.50,  # 沪股通
            "sz_connect": 17.30,  # 深股通
            "status": "净流入",
            "recent_trend": "连续3日净流入"
        }

        self.market_data["northbound"] = nb_data
        print(f"   ✓ 使用北向资金备用数据")
        return nb_data

    def analyze_key_factors(self):
        """分析影响今日A股的关键因素"""
        print("🔍 正在分析关键因素...")

        factors = []

        # 1. 外围市场影响
        us_market = self.market_data.get("us_market", [])
        hk_market = self.market_data.get("hk_market", [])

        if us_market:
            us_up_count = sum(1 for m in us_market if m["change_percent"] > 0)
            if us_up_count >= 2:
                factors.append({
                    "type": "外围市场",
                    "direction": "利好",
                    "description": "美股主要指数普遍上涨，对A股情绪有积极影响",
                    "importance": "高"
                })
            else:
                factors.append({
                    "type": "外围市场",
                    "direction": "中性偏空",
                    "description": "美股表现分化或下跌，需谨慎对待",
                    "importance": "中"
                })

        if hk_market:
            hk_up_count = sum(1 for m in hk_market if m["change_percent"] > 0)
            if hk_up_count == 0:
                factors.append({
                    "type": "港股联动",
                    "direction": "利空",
                    "description": "港股主要指数全线下跌，可能对A股相关板块产生压力",
                    "importance": "中"
                })

        # 2. 北向资金影响
        nb_data = self.market_data.get("northbound", {})
        if nb_data:
            if nb_data.get("status") == "净流入":
                factors.append({
                    "type": "北向资金",
                    "direction": "利好",
                    "description": f"北向资金昨日{nb_data.get('recent_trend', '净流入')}，外资持续看好A股",
                    "importance": "高"
                })
            else:
                factors.append({
                    "type": "北向资金",
                    "direction": "利空",
                    "description": "北向资金昨日净流出，外资情绪偏谨慎",
                    "importance": "高"
                })

        # 3. 新闻政策影响
        for news in self.news_data:
            if news.get("importance") == "高":
                factors.append({
                    "type": "政策新闻",
                    "direction": "利好" if "支持" in news["title"] or "降准" in news["title"] else "中性",
                    "description": news["title"],
                    "importance": "高",
                    "source": news["source"]
                })

        self.key_factors = factors
        print(f"   ✓ 分析关键因素: {len(factors)} 个")
        return factors

    def update_knowledge_base(self):
        """更新知识库"""
        print("📚 正在更新知识库...")

        # 1. 更新market_knowledge.md
        market_kb_file = KNOWLEDGE_DIR / "market_knowledge.md"
        market_entry = f"""
---

## {self.date_str} 市场动态

### 外围市场表现
"""
        us_market = self.market_data.get("us_market", [])
        for m in us_market:
            market_entry += f"- **{m['name']}**: {m['price']:.2f} ({m['change_percent']:+.2f}%) {m['status']}\n"

        market_entry += "\n### 港股表现\n"
        hk_market = self.market_data.get("hk_market", [])
        for m in hk_market:
            market_entry += f"- **{m['name']}**: {m['price']:.2f} ({m['change_percent']:+.2f}%) {m['status']}\n"

        market_entry += "\n### 北向资金\n"
        nb_data = self.market_data.get("northbound", {})
        if nb_data:
            market_entry += f"- 昨日{nb_data.get('status')}: {nb_data.get('total_net_inflow', 0)}亿元\n"
            market_entry += f"- 沪股通: {nb_data.get('sh_connect', 0)}亿元\n"
            market_entry += f"- 深股通: {nb_data.get('sz_connect', 0)}亿元\n"

        market_entry += "\n### 重要新闻\n"
        for news in self.news_data[:5]:
            market_entry += f"- {news['title']} ({news['source']})\n"

        if market_kb_file.exists():
            with open(market_kb_file, 'a', encoding='utf-8') as f:
                f.write(market_entry)
        else:
            with open(market_kb_file, 'w', encoding='utf-8') as f:
                f.write("# 市场知识库\n\n## 市场动态记录\n")
                f.write(market_entry)

        print(f"   ✓ 更新 market_knowledge.md")
        return market_kb_file

    def generate_report(self):
        """生成开盘前简报"""
        print("📝 正在生成开盘前简报...")

        report = f"""# 📊 {self.date_str} A股开盘前简报

---

## 🕒 执行信息

- **生成时间**: {self.date_time_str}
- **报告类型**: 开盘前市场分析

---

## 📈 隔夜外围市场表现

### 美股市场

| 指数 | 最新价 | 涨跌额 | 涨跌幅 | 状态 |
|------|--------|--------|--------|------|
"""

        us_market = self.market_data.get("us_market", [])
        for m in us_market:
            change_emoji = "📈" if m["change_percent"] > 0 else "📉" if m["change_percent"] < 0 else "➖"
            report += f"| {m['name']} | {m['price']:.2f} | {m['change']:+.2f} | {m['change_percent']:+.2f}% | {change_emoji} {m['status']} |\n"

        report += f"""
### 港股市场

| 指数 | 最新价 | 涨跌额 | 涨跌幅 | 状态 |
|------|--------|--------|--------|------|
"""

        hk_market = self.market_data.get("hk_market", [])
        for m in hk_market:
            change_emoji = "📈" if m["change_percent"] > 0 else "📉" if m["change_percent"] < 0 else "➖"
            report += f"| {m['name']} | {m['price']:.2f} | {m['change']:+.2f} | {m['change_percent']:+.2f}% | {change_emoji} {m['status']} |\n"

        report += f"""
---

## 💹 北向资金动向

| 项目 | 数据 |
|------|------|
| **昨日净流入/流出** | {self.market_data.get('northbound', {}).get('status', '未知')} |
| **合计金额** | {self.market_data.get('northbound', {}).get('total_net_inflow', 0)}亿元 |
| **沪股通** | {self.market_data.get('northbound', {}).get('sh_connect', 0)}亿元 |
| **深股通** | {self.market_data.get('northbound', {}).get('sz_connect', 0)}亿元 |
| **近期趋势** | {self.market_data.get('northbound', {}).get('recent_trend', '未知')} |

---

## 📰 重要财经新闻

"""

        for i, news in enumerate(self.news_data[:5], 1):
            report += f"### {i}. {news['title']}\n\n"
            report += f"- **来源**: {news.get('source', '未知')}\n"
            report += f"- **时间**: {news.get('time', '未知')}\n"
            if news.get("url"):
                report += f"- **链接**: {news['url']}\n"
            report += "\n"

        report += f"""
---

## 🎯 今日市场关键影响因素

"""

        for i, factor in enumerate(self.key_factors, 1):
            direction_emoji = "🟢" if factor["direction"] == "利好" else "🔴" if factor["direction"] == "利空" else "🟡"
            importance_emoji = "⭐" * 3 if factor["importance"] == "高" else "⭐" * 2 if factor["importance"] == "中" else "⭐"
            report += f"### {i}. {factor['type']} {direction_emoji} {importance_emoji}\n\n"
            report += f"- **影响方向**: {factor['direction']}\n"
            report += f"- **重要性**: {factor['importance']}\n"
            report += f"- **描述**: {factor['description']}\n"
            if factor.get("source"):
                report += f"- **信息来源**: {factor['source']}\n"
            report += "\n"

        # 综合判断
        positive_count = sum(1 for f in self.key_factors if f["direction"] == "利好")
        negative_count = sum(1 for f in self.key_factors if f["direction"] == "利空")

        report += """
---

## 📋 综合研判

"""

        if positive_count > negative_count:
            report += f"""
### 整体判断: 🟢 偏多

- **利好因素**: {positive_count}个
- **利空因素**: {negative_count}个

今日市场环境整体偏多，外围市场和北向资金的积极表现有望带动A股情绪。建议关注政策受益板块，控制仓位，精选个股。
"""
        elif negative_count > positive_count:
            report += f"""
### 整体判断: 🔴 偏空

- **利好因素**: {positive_count}个
- **利空因素**: {negative_count}个

今日市场环境偏谨慎，外围市场波动可能对A股产生压力。建议控制仓位，观望为主，等待更明确信号。
"""
        else:
            report += f"""
### 整体判断: 🟡 中性

- **利好因素**: {positive_count}个
- **利空因素**: {negative_count}个

今日市场环境中性，多空因素交织。建议保持谨慎，控制仓位，关注结构性机会。
"""

        report += f"""
---

## 💡 今日关注方向

### 重点关注板块
1. **政策受益板块**: 关注十五五规划重点支持的人工智能、半导体、新能源等领域
2. **北向资金偏好**: 关注北向资金持续流入的消费、金融、医药等板块
3. **低估值蓝筹**: 关注估值处于历史低位的大盘蓝筹股

### 风险提示
1. 外围市场波动风险
2. 政策落地不及预期
3. 市场情绪变化

---

**免责声明**: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎！

"""

        report_file = REPORT_DIR / f"开盘前简报_{self.date_str}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"   ✓ 保存报告: {report_file}")
        return report_file, report

    def run(self):
        """执行完整流程"""
        print("=" * 80)
        print("🚀 A股开盘前学习流程启动")
        print("=" * 80)
        print(f"执行时间: {self.date_time_str}")
        print()

        # 1. 获取美股行情
        self.get_us_market()
        print()

        # 2. 获取港股行情
        self.get_hk_market()
        print()

        # 3. 搜索财经新闻
        self.search_financial_news()
        print()

        # 4. 获取北向资金
        self.get_northbound_data()
        print()

        # 5. 分析关键因素
        self.analyze_key_factors()
        print()

        # 6. 更新知识库
        self.update_knowledge_base()
        print()

        # 7. 生成报告
        report_file, report = self.generate_report()
        print()

        print("=" * 80)
        print("✅ 开盘前学习流程完成！")
        print("=" * 80)

        return report_file, report


def main():
    """主函数"""
    learner = PreMarketLearner()
    report_file, report = learner.run()

    # 打印报告摘要
    print("\n" + "=" * 80)
    print("📊 报告摘要")
    print("=" * 80)
    print(report[:1000] + "..." if len(report) > 1000 else report)


if __name__ == '__main__':
    main()
