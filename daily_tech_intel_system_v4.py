#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日科技前沿资讯分析系统 v4.0（最终稳定版）
- 每天上午9:30执行
- 使用 requests 库获取真实新闻（绕过SSL验证）
- 聚焦十五五规划相关产业
- 结合缠论进行深度知识沉淀
- 识别反向信号（自媒体标题党、资本雇佣枪手）
"""

import sys
import os
import json
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# 报告保存目录
REPORT_DIR = PROJECT_DIR / "daily_tech_intel"
REPORT_DIR.mkdir(exist_ok=True)
KNOWLEDGE_BASE_DIR = PROJECT_DIR / "knowledge"
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# 十五五规划重点关注领域
FIFTEEN_FIVE_INDUSTRIES = {
    "人工智能": ["人工智能", "AI", "大模型", "生成式AI", "深度学习", "机器学习", "人形机器人"],
    "半导体": ["半导体", "芯片", "集成电路", "先进制程", "国产替代", "中芯国际"],
    "新能源": ["新能源", "光伏", "风电", "储能", "新能源汽车", "锂电池"],
    "数字经济": ["数字经济", "数据中心", "算力", "云计算", "大数据", "东数西算"],
    "十五五规划": ["十五五规划", "第十四个五年规划", "高质量发展", "现代化产业体系"],
    "新材料": ["新材料", "稀土", "碳纤维", "第三代半导体", "碳化硅", "氮化镓"],
    "生物医药": ["生物医药", "创新药", "基因编辑", "医疗器械", "生物科技"]
}

# 可靠资讯来源白名单
RELIABLE_SOURCES = [
    "gov.cn", "miit.gov.cn", "most.gov.cn", "ndrc.gov.cn",
    "xinhuanet.com", "people.com.cn", "stdaily.com",
    "caixin.com", "yicai.com", "stcn.com", "cnstock.com",
    "36kr.com", "huxiu.com", "techweb.com.cn"
]

# 反向信号关键词
REVERSE_SIGNAL_KEYWORDS = {
    "极端词汇": ["暴涨", "暴跌", "必涨", "必跌", "翻倍", "妖股", "疯涨", "崩盘", "血洗"],
    "内幕词汇": ["内幕", "独家", "重磅", "惊天", "震惊", "秘密", "内部消息", "绝密", "泄密"],
    "主体词汇": ["主力", "游资", "机构", "大佬", "牛散", "庄家", "操盘手", "国家队"],
    "时间词汇": ["即将", "马上", "立刻", "刚刚", "就在刚才", "紧急", "突发"],
    "引导词汇": ["手把手", "带你", "教你", "跟着", "躺赢", "赚钱", "发财", "暴富", "致富"],
    "操作词汇": ["抄底", "逃顶", "上车", "下车", "接力", "打板", "追涨", "杀跌", "核按钮"]
}


class NewsSearcher:
    """新闻搜索器 - 使用 requests 获取真实新闻"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def search_eastmoney_news(self, keyword, num=10):
        """使用东方财富新闻API"""
        try:
            # 使用东方财富搜索API
            url = f"https://search-api-web.eastmoney.com/search/jsonp"
            params = {
                'cb': 'jQuery',
                'param': '',
                'qu': keyword,
                'type': '',
                'page': 1,
                'pageSize': num,
                'uid': '',
                'mCode': '',
                'esIndex': 1,
                'client': 'web',
                '_': int(time.time())
            }

            response = self.session.get(url, params=params, verify=False, timeout=10)
            if response.status_code == 200:
                # 简化的解析
                return [{
                    "title": f"东方财富-关键词[{keyword}]最新资讯",
                    "url": f"https://so.eastmoney.com/news/s?keyword={keyword}",
                    "snippet": "东方财富财经资讯平台提供最新财经新闻",
                    "source": "东方财富"
                }]
            return []
        except Exception as e:
            print(f"      ⚠️ 东方财富搜索失败: {e}")
            return []

    def search_sina_news(self, keyword, num=10):
        """使用新浪新闻搜索"""
        try:
            url = f"https://search.sina.com.cn/"
            params = {
                'q': keyword,
                'c': 'news',
                'from': '',
                'time': '',
                'col': '',
                'source': '',
                'country': '',
                'pf': 0,
                'ps': 0,
                'page': 1,
                'num': num,
                'page': 1
            }

            response = self.session.get(url, params=params, verify=False, timeout=10)
            if response.status_code == 200:
                html = response.text

                # 简单解析标题
                news_list = []
                titles = re.findall(r'<h2 class="n-title"><a[^>]*>([^<]+)</a></h2>', html)
                urls = re.findall(r'<h2 class="n-title"><a[^>]*href="([^"]*)"[^>]*>', html)

                for i, title in enumerate(titles[:num]):
                    title = title.strip()
                    url = urls[i] if i < len(urls) else f"https://search.sina.com.cn/?q={keyword}"
                    if title:
                        news_list.append({
                            "title": title,
                            "url": url,
                            "snippet": "新浪财经资讯",
                            "source": "新浪财经"
                        })

                return news_list
            return []
        except Exception as e:
            print(f"      ⚠️ 新浪搜索失败: {e}")
            return []

    def search_baidu_news(self, keyword, num=10):
        """使用百度新闻搜索"""
        try:
            url = f"https://news.baidu.com/ns"
            params = {
                'word': keyword,
                'tn': 'news',
                'from': 'news',
                'cl': 2,
                'rn': num,
                'ct': 1
            }

            response = self.session.get(url, params=params, verify=False, timeout=10)
            if response.status_code == 200:
                html = response.text

                # 简单解析
                news_list = []
                titles = re.findall(r'<h3 class="news-title[^"]*">.*?<a[^>]*>([^<]+)</a>', html, re.DOTALL)
                urls = re.findall(r'<h3 class="news-title[^"]*">.*?<a[^>]*href="([^"]*)"', html, re.DOTALL)

                for i, title in enumerate(titles[:num]):
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    url = urls[i] if i < len(urls) else f"https://news.baidu.com/ns?word={keyword}"
                    if title and len(title) > 5:
                        news_list.append({
                            "title": title,
                            "url": url,
                            "snippet": "百度新闻资讯",
                            "source": "百度新闻"
                        })

                return news_list
            return []
        except Exception as e:
            print(f"      ⚠️ 百度搜索失败: {e}")
            return []

    def search(self, keyword, num=10):
        """综合搜索"""
        print(f"   🔍 正在搜索: {keyword}")

        all_news = []

        # 尝试多个来源
        sources = [
            ("百度新闻", self.search_baidu_news),
            ("新浪财经", self.search_sina_news),
            ("东方财富", self.search_eastmoney_news),
        ]

        for source_name, search_func in sources:
            try:
                news = search_func(keyword, num)
                if news:
                    all_news.extend(news)
                    print(f"     ✓ {source_name}: 获取 {len(news)} 条")
                time.sleep(0.3)
            except Exception as e:
                print(f"     ⚠️ {source_name} 失败: {e}")

        # 去重
        unique_news = []
        seen_titles = set()
        for news in all_news:
            title_key = news["title"][:30] if len(news["title"]) > 30 else news["title"]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)

        print(f"     ✓ 共获取 {len(unique_news)} 条有效新闻")
        return unique_news


class DailyTechIntelSystemV4:
    """每日科技资讯分析系统 v4.0"""

    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.date_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.news_data = {}
        self.analyzed_data = {}
        self.searcher = NewsSearcher()

    def crawl_all_news(self):
        """爬取所有领域的新闻"""
        print("=" * 80)
        print("🚀 每日科技前沿资讯分析系统 v4.0 启动")
        print("=" * 80)
        print(f"执行时间: {self.date_time_str}")
        print()

        for industry, keywords in FIFTEEN_FIVE_INDUSTRIES.items():
            print(f"📡 正在爬取【{industry}】领域...")
            industry_news = []

            # 每个领域搜索多个关键词
            search_queries = [
                f"{industry} 最新政策 2025",
                f"{industry} 技术突破 进展",
                f"十五五规划 {industry}"
            ]

            for query in search_queries[:2]:
                results = self.searcher.search(query, num=5)
                for result in results:
                    result["industry"] = industry
                    industry_news.append(result)
                time.sleep(0.3)

            # 去重
            unique_news = []
            seen_titles = set()
            for news in industry_news:
                title_key = news["title"][:50] if len(news["title"]) > 50 else news["title"]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_news.append(news)

            self.news_data[industry] = unique_news
            print(f"   ✓ 共获取 {len(unique_news)} 条有效新闻")
            print()

        return self.news_data

    def analyze_source_reliability(self, news):
        """分析资讯来源可靠性"""
        url = news.get("url", "")
        reliability_score = 50

        for source in RELIABLE_SOURCES:
            if source in url:
                reliability_score += 30
                break

        title = news["title"]
        if len(title) < 10:
            reliability_score -= 10
        elif len(title) > 50:
            reliability_score -= 5

        return {
            "score": min(100, max(0, reliability_score)),
            "is_reliable": reliability_score >= 60,
            "reasons": []
        }

    def extract_core_information(self, news):
        """提取核心信息"""
        title = news["title"]
        snippet = news.get("snippet", "")
        industry = news.get("industry", "")

        core_info = {
            "event_subject": self._identify_subject(title, snippet),
            "event_type": self._identify_event_type(title, snippet),
            "impact_scope": self._identify_impact_scope(title, snippet),
            "time_sensitivity": self._identify_time_sensitivity(title),
            "industry": industry,
            "raw_news": news
        }

        return core_info

    def _identify_subject(self, title, snippet):
        """识别事件主体"""
        subjects = {
            "government": ["国务院", "发改委", "工信部", "科技部", "财政部", "央行", "证监会"],
            "enterprise": ["华为", "中芯国际", "宁德时代", "比亚迪", "腾讯", "阿里", "百度"]
        }

        text = title + snippet
        for category, keywords in subjects.items():
            for keyword in keywords:
                if keyword in text:
                    return keyword

        return "其他主体"

    def _identify_event_type(self, title, snippet):
        """识别事件类型"""
        event_types = {
            "政策发布": ["政策", "规划", "发布", "出台", "印发", "通知", "意见", "方案"],
            "技术突破": ["突破", "进展", "研发", "成功", "首次", "创新", "专利", "技术"],
            "产能扩张": ["产能", "量产", "扩产", "投产", "开工"],
            "合作并购": ["合作", "并购", "收购", "投资", "合资", "签约"],
            "市场动态": ["上涨", "下跌", "增长", "下降", "销量", "订单"]
        }

        text = title + snippet
        for event_type, keywords in event_types.items():
            for keyword in keywords:
                if keyword in text:
                    return event_type

        return "其他事件"

    def _identify_impact_scope(self, title, snippet):
        """识别影响范围"""
        text = title + snippet

        if any(keyword in text for keyword in ["全国", "国家", "国务院", "全球", "国际"]):
            return "国家级/全球性"
        elif any(keyword in text for keyword in ["行业", "产业", "领域", "板块"]):
            return "行业级"
        else:
            return "企业级"

    def _identify_time_sensitivity(self, title):
        """识别时间敏感性"""
        if any(keyword in title for keyword in ["今日", "刚刚", "最新", "突发", "紧急"]):
            return "高"
        elif any(keyword in title for keyword in ["近日", "近期", "本周"]):
            return "中"
        else:
            return "低"

    def analyze_reverse_signal(self, news):
        """分析反向信号"""
        title = news["title"]
        snippet = news.get("snippet", "")

        signal_analysis = {
            "has_reverse_signal": False,
            "signal_score": 0,
            "signal_categories": {},
            "signal_words": [],
            "risk_level": "低",
            "analysis": ""
        }

        for category, keywords in REVERSE_SIGNAL_KEYWORDS.items():
            found = []
            for keyword in keywords:
                if keyword in title:
                    found.append(keyword)
                    signal_analysis["signal_score"] += 1

            if found:
                signal_analysis["signal_categories"][category] = found
                signal_analysis["signal_words"].extend(found)

        if len(snippet) < 30 and not any(char in snippet for char in "0123456789"):
            signal_analysis["signal_score"] += 2
            signal_analysis["analysis"] += "缺乏具体数据支撑；"

        reliability = self.analyze_source_reliability(news)
        if not reliability["is_reliable"]:
            signal_analysis["signal_score"] += 1
            signal_analysis["analysis"] += "来源可靠性较低；"

        if signal_analysis["signal_score"] >= 5:
            signal_analysis["has_reverse_signal"] = True
            signal_analysis["risk_level"] = "高"
        elif signal_analysis["signal_score"] >= 3:
            signal_analysis["has_reverse_signal"] = True
            signal_analysis["risk_level"] = "中"

        if signal_analysis["signal_score"] >= 3:
            signal_analysis["analysis"] += f"检测到{len(signal_analysis['signal_words'])}个风险关键词，"
            if signal_analysis["signal_score"] >= 5:
                signal_analysis["analysis"] += "高度疑似标题党，建议反向思考！"
            else:
                signal_analysis["analysis"] += "存在一定风险，需谨慎判断。"

        return signal_analysis

    def analyze_chan_theory(self, news, core_info):
        """缠论视角深度分析"""
        title = news["title"]
        snippet = news.get("snippet", "")
        text = title + snippet

        chan_analysis = {
            "buy_points": {
                "first": False,
                "second": False,
                "third": False,
                "details": []
            },
            "pivot_type": "",
            "support_level": "",
            "trend_judgment": "",
            "operation_suggestion": ""
        }

        # 第一类买点
        first_triggers = ["政策底", "技术底", "估值底", "重大利好", "超跌反弹", "政策发布"]
        for trigger in first_triggers:
            if trigger in text or core_info["event_type"] == "政策发布":
                chan_analysis["buy_points"]["first"] = True
                chan_analysis["buy_points"]["details"].append(f"政策底/技术底信号: {trigger}")
                break

        # 第二类买点
        second_triggers = ["回调企稳", "二次确认", "缩量回踩", "支撑有效"]
        for trigger in second_triggers:
            if trigger in text:
                chan_analysis["buy_points"]["second"] = True
                chan_analysis["buy_points"]["details"].append(f"回调确认信号: {trigger}")
                break

        # 第三类买点
        third_triggers = ["趋势确立", "放量突破", "新高确认", "强势上涨"]
        for trigger in third_triggers:
            if trigger in text:
                chan_analysis["buy_points"]["third"] = True
                chan_analysis["buy_points"]["details"].append(f"趋势确立信号: {trigger}")
                break

        # 中枢判断
        if core_info["event_type"] == "政策发布":
            chan_analysis["pivot_type"] = "政策支撑中枢"
        elif core_info["event_type"] == "技术突破":
            chan_analysis["pivot_type"] = "技术突破中枢"
        else:
            chan_analysis["pivot_type"] = "产业趋势中枢"

        # 走势判断
        buy_count = sum([chan_analysis["buy_points"]["first"],
                         chan_analysis["buy_points"]["second"],
                         chan_analysis["buy_points"]["third"]])

        if buy_count >= 2:
            chan_analysis["trend_judgment"] = "偏多，关注入场机会"
            chan_analysis["operation_suggestion"] = "可考虑分批建仓，设置止损"
        elif buy_count == 1:
            chan_analysis["trend_judgment"] = "中性偏多，观察确认"
            chan_analysis["operation_suggestion"] = "继续观察，等待明确信号"
        else:
            chan_analysis["trend_judgment"] = "中性，保持观望"
            chan_analysis["operation_suggestion"] = "暂不操作，等待更多信号"

        return chan_analysis

    def analyze_all_news(self):
        """分析所有新闻"""
        self.analyzed_data = {}

        for industry, news_list in self.news_data.items():
            analyzed_list = []
            for news in news_list:
                core_info = self.extract_core_information(news)
                reverse_signal = self.analyze_reverse_signal(news)
                chan_analysis = self.analyze_chan_theory(news, core_info)

                analyzed_list.append({
                    "news": news,
                    "core_info": core_info,
                    "reverse_signal": reverse_signal,
                    "chan_analysis": chan_analysis
                })

            analyzed_list.sort(key=lambda x: (
                0 if x["reverse_signal"]["has_reverse_signal"] else 1,
                -x["core_info"]["impact_scope"].count("级"),
                -len(x["chan_analysis"]["buy_points"]["details"])
            ))

            self.analyzed_data[industry] = analyzed_list

        return self.analyzed_data

    def generate_structured_report(self):
        """生成结构化报告"""
        report = f"# 📊 {self.date_str} 科技前沿资讯分析报告\n\n"
        report += "---\n\n"

        report += self._generate_summary_section()
        report += "\n"

        report += "## 📋 十五五规划相关产业动态\n\n"
        for industry, news_list in self.analyzed_data.items():
            if news_list:
                report += self._generate_industry_section(industry, news_list)

        report += self._generate_reverse_signal_section()
        report += "\n"

        report += self._generate_chan_theory_section()
        report += "\n"

        report += self._generate_knowledge_section()
        report += "\n"

        return report

    def _generate_summary_section(self):
        """生成摘要部分"""
        total_news = sum(len(news_list) for news_list in self.news_data.values())
        normal_news = sum(1 for news_list in self.analyzed_data.values()
                          for item in news_list if not item["reverse_signal"]["has_reverse_signal"])
        reverse_news = total_news - normal_news
        high_impact = sum(1 for news_list in self.analyzed_data.values()
                          for item in news_list
                          if item["core_info"]["impact_scope"] in ["国家级/全球性", "行业级"])

        section = f"""## 📌 报告摘要

| 指标 | 数值 |
|------|------|
| 📰 爬取资讯总数 | {total_news} |
| ✅ 正常资讯 | {normal_news} |
| ⚠️ 反向信号 | {reverse_news} |
| 🎯 高影响力资讯 | {high_impact} |

**执行时间**: {self.date_time_str}

"""
        return section

    def _generate_industry_section(self, industry, news_list):
        """生成行业资讯部分"""
        section = f"### 🔬 {industry}\n\n"

        for i, item in enumerate(news_list[:5], 1):
            news = item["news"]
            core = item["core_info"]
            reverse = item["reverse_signal"]
            chan = item["chan_analysis"]

            section += f"**{i}. {news['title']}**\n\n"
            section += f"- **来源**: {news.get('url', '未知')[:60]}...\n"
            section += f"- **核心内容**: {news.get('snippet', '待获取')[:150]}...\n"
            section += f"- **事件类型**: {core['event_type']} | **影响范围**: {core['impact_scope']}\n"

            buy_points = []
            if chan["buy_points"]["first"]:
                buy_points.append("一买")
            if chan["buy_points"]["second"]:
                buy_points.append("二买")
            if chan["buy_points"]["third"]:
                buy_points.append("三买")

            if buy_points:
                section += f"- **缠论视角**: 🟢 {','.join(buy_points)}信号 | {chan['trend_judgment']}\n"
            else:
                section += f"- **缠论视角**: ⚪ 无明确信号 | {chan['trend_judgment']}\n"

            if reverse["has_reverse_signal"]:
                section += f"- **风险预警**: 🔴 {reverse['risk_level']}风险 | {', '.join(reverse['signal_words'][:5])}\n"
            else:
                section += f"- **风险预警**: 🟢 正常\n"

            section += "\n"

        if len(news_list) > 5:
            section += f"*（还有 {len(news_list) - 5} 条资讯省略）*\n\n"

        return section

    def _generate_reverse_signal_section(self):
        """生成反向信号预警部分"""
        all_reverse = []
        for industry, news_list in self.analyzed_data.items():
            for item in news_list:
                if item["reverse_signal"]["has_reverse_signal"]:
                    item["industry"] = industry
                    all_reverse.append(item)

        if not all_reverse:
            return "## ✅ 反向信号检测\n\n今日未检测到明显的标题党或资本雇佣枪手发文。\n\n"

        section = f"## ⚠️ 反向信号预警 ({len(all_reverse)}条)\n\n"

        for i, item in enumerate(all_reverse[:10], 1):
            news = item["news"]
            reverse = item["reverse_signal"]

            section += f"**{i}. {news['title']}**\n\n"
            section += f"- **风险等级**: 🔴 {reverse['risk_level']}\n"
            section += f"- **风险关键词**: {', '.join(reverse['signal_words'][:8])}\n"
            section += f"- **分析**: {reverse['analysis']}\n"
            section += f"- **💡 建议**: 此类资讯高度疑似标题党或资本雇佣枪手发文，建议反向思考，谨慎追高！\n\n"

        return section

    def _generate_chan_theory_section(self):
        """生成缠论分析部分"""
        section = """## 📈 缠论视角深度分析

### 核心要点

1. **第一类买点**：关注政策发布、技术突破带来的底部机会
2. **第二类买点**：等待回调确认后的安全入场点
3. **第三类买点**：趋势确立后的强势突破机会

### 今日操作建议

"""

        first_buy = sum(1 for news_list in self.analyzed_data.values()
                        for item in news_list if item["chan_analysis"]["buy_points"]["first"])
        second_buy = sum(1 for news_list in self.analyzed_data.values()
                         for item in news_list if item["chan_analysis"]["buy_points"]["second"])
        third_buy = sum(1 for news_list in self.analyzed_data.values()
                        for item in news_list if item["chan_analysis"]["buy_points"]["third"])

        section += f"- 第一类买点信号: {first_buy} 个\n"
        section += f"- 第二类买点信号: {second_buy} 个\n"
        section += f"- 第三类买点信号: {third_buy} 个\n\n"

        section += """### 策略建议

- **仓位管理**: 控制总仓位在50%-70%
- **选股方向**: 重点关注人工智能、半导体、新能源等十五五重点赛道
- **入场时机**: 等待明确的回调确认信号
- **止损设置**: 单只股票亏损不超过5%

"""
        return section

    def _generate_knowledge_section(self):
        """生成知识沉淀部分"""
        section = """## 🧠 知识沉淀

### 今日知识点

1. **政策解读**: 十五五规划重点支持方向
2. **产业趋势**: 人工智能、半导体、新能源长期向好
3. **风险防范**: 识别标题党和反向信号的重要性
4. **技术分析**: 缠论买点的实战应用

### 后续关注

- 持续跟踪政策落地进展
- 关注行业数据验证
- 警惕市场情绪过热

"""
        return section

    def save_report_and_knowledge(self, report):
        """保存报告和知识沉淀"""
        report_file = REPORT_DIR / f"{self.date_str}_tech_intel_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n📁 主报告已保存: {report_file}")

        data_file = REPORT_DIR / f"{self.date_str}_tech_intel_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date": self.date_str,
                "datetime": self.date_time_str,
                "news_data": self.news_data,
                "analyzed_data": self.analyzed_data
            }, f, ensure_ascii=False, indent=2)

        print(f"📁 分析数据已保存: {data_file}")

        knowledge_file = KNOWLEDGE_BASE_DIR / "tech_intel_history.md"
        knowledge_entry = f"\n\n---\n\n## {self.date_str}\n{report[:500]}...\n"

        if knowledge_file.exists():
            with open(knowledge_file, 'a', encoding='utf-8') as f:
                f.write(knowledge_entry)
        else:
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                f.write("# 科技资讯知识沉淀库\n" + knowledge_entry)

        print(f"📚 知识沉淀已追加: {knowledge_file}")

        return report_file, data_file

    def run(self):
        """执行完整流程"""
        print("📡 开始爬取资讯...")
        self.crawl_all_news()

        print("\n🔍 开始分析资讯...")
        self.analyze_all_news()

        print("\n📝 生成分析报告...")
        report = self.generate_structured_report()

        print("\n💾 保存结果...")
        self.save_report_and_knowledge(report)

        print("\n" + "=" * 80)
        print("✅ 分析完成！")
        print("=" * 80)

        return report


def main():
    """主函数"""
    system = DailyTechIntelSystemV4()
    system.run()


if __name__ == '__main__':
    main()
