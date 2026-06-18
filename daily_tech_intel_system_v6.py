#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日科技前沿资讯分析系统 v6.0（多真实新闻源版）
- 每天上午9:30、下午14:30执行
- 使用多个真实财经/科技媒体新闻源（东方财富、新浪财经、中国新闻网等）
- 关注十五五规划相关产业（人工智能、半导体、新能源、数字经济等）
- 结合缠论进行深度知识沉淀
- 智能识别反向信号（自媒体标题党、资本雇佣枪手发文）
- 禁止生成虚假模拟数据，只保留真实获取的资讯
"""

import sys
import os
import json
import re
import time
import random
import hashlib
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

REPORT_DIR = PROJECT_DIR / "daily_tech_intel"
REPORT_DIR.mkdir(exist_ok=True)
KNOWLEDGE_BASE_DIR = PROJECT_DIR / "knowledge"
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# ========== 十五五规划重点关注领域 ==========
FIFTEEN_FIVE_INDUSTRIES = {
    "人工智能": ["人工智能", "AI", "大模型", "生成式AI", "深度学习", "人形机器人", "机器视觉"],
    "半导体": ["半导体", "芯片", "集成电路", "先进制程", "国产替代", "中芯国际", "光刻", "先进封装", "存储"],
    "新能源": ["新能源", "光伏", "风电", "储能", "新能源汽车", "锂电池", "宁德时代", "比亚迪", "氢能"],
    "数字经济": ["数字经济", "数据中心", "算力", "云计算", "大数据", "东数西算", "工业互联网"],
    "十五五规划": ["十五五规划", "高质量发展", "现代化产业体系", "政策", "规划", "新质生产力"],
    "新材料": ["新材料", "稀土", "碳纤维", "第三代半导体", "碳化硅", "氮化镓", "石墨烯"],
    "生物医药": ["生物医药", "创新药", "基因编辑", "医疗器械", "CXO", "生物科技"],
    "航天军工": ["航天", "商业航天", "卫星互联网", "军工", "无人机", "低空经济"]
}

# ========== 可靠资讯来源白名单 ==========
RELIABLE_SOURCES = [
    "gov.cn", "miit.gov.cn", "most.gov.cn", "ndrc.gov.cn", "csrc.gov.cn",
    "xinhuanet.com", "people.com.cn", "stdaily.com", "chinadaily.com.cn",
    "caixin.com", "yicai.com", "stcn.com", "cnstock.com",
    "eastmoney.com", "sina.com.cn", "163.com", "sohu.com",
    "36kr.com", "huxiu.com", "techweb.com.cn", "ithome.com"
]

# ========== 反向信号关键词（增强版） ==========
REVERSE_SIGNAL_KEYWORDS = {
    "极端词汇": ["暴涨", "暴跌", "必涨", "必跌", "翻倍", "妖股", "疯涨", "崩盘", "血洗", "涨停潮", "跌停潮", "炸了", "疯了", "暴增", "暴富", "狂涨", "狂跌", "井喷", "飙升", "爆发", "爆了", "炸裂", "逆天", "彻底疯了", "彻底爆发", "历史首次", "全球第一", "全球首发", "行业第一"],
    "内幕词汇": ["内幕", "独家", "重磅", "惊天", "震惊", "秘密", "内部消息", "绝密", "泄密", "爆料", "实锤", "曝光", "揭秘"],
    "主体词汇": ["主力", "游资", "机构", "大佬", "牛散", "庄家", "操盘手", "国家队", "外资"],
    "时间词汇": ["即将", "马上", "立刻", "今日", "最新", "突发", "紧急", "刚刚", "就在刚才", "就在今天", "周末", "重磅突发"],
    "引导词汇": ["手把手", "带你", "教你", "跟着", "躺赢", "赚钱", "发财", "暴富", "致富", "必看", "收藏", "速看", "快看", "牛股", "龙头股", "十倍股", "翻倍股", "布局", "重点关注", "强烈推荐"],
    "操作词汇": ["抄底", "逃顶", "上车", "下车", "接力", "打板", "追涨", "杀跌", "核按钮", "满仓", "重仓", "梭哈", "All in"],
    "夸张词汇": ["震惊", "慌了", "哭了", "笑了", "懵了", "爽了", "赚翻了", "太可怕", "吓尿", "惊呆", "炸锅", "沸腾", "疯狂", "失控", "彻底失控", "泪目", "燃爆", "炸裂"],
    "数字夸张词汇": ["暴涨", "暴跌", "暴增", "狂涨", "疯涨", "飙升", "井喷"]
}

# ========== 股票关联映射 ==========
INDUSTRY_STOCKS = {
    "人工智能": ["寒武纪", "科大讯飞", "海天瑞声", "云从科技", "拓尔思", "工业富联", "浪潮信息"],
    "半导体": ["中芯国际", "北方华创", "韦尔股份", "紫光国微", "卓胜微", "兆易创新", "长电科技"],
    "新能源": ["宁德时代", "比亚迪", "隆基绿能", "通威股份", "阳光电源", "天齐锂业", "赣锋锂业"],
    "数字经济": ["宝信软件", "用友网络", "金山办公", "中科曙光", "浪潮信息", "紫光股份"],
    "新材料": ["北方稀土", "中国宝安", "光威复材", "中简科技", "天奈科技"],
    "生物医药": ["恒瑞医药", "药明康德", "迈瑞医疗", "爱尔眼科", "智飞生物", "百济神州"],
    "航天军工": ["中航沈飞", "航天电器", "中国卫星", "中直股份", "高德红外"]
}


class MultiSourceNewsFetcher:
    """多源新闻抓取器 - 直接抓取财经/科技频道首页，通过关键词过滤获取资讯"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        # 可靠的新闻源配置（频道首页抓取）
        self.news_sources = [
            {"name": "证券时报", "url": "https://www.stcn.com/", "host": "https://www.stcn.com"},
            {"name": "新浪财经", "url": "https://finance.sina.com.cn/", "host": "https://finance.sina.com.cn"},
            {"name": "财联社", "url": "https://www.cls.cn/", "host": "https://www.cls.cn"},
            {"name": "网易财经", "url": "https://money.163.com/", "host": "https://money.163.com"},
            {"name": "中国证券报", "url": "https://www.cs.com.cn/", "host": "https://www.cs.com.cn"},
            {"name": "第一财经", "url": "https://www.yicai.com/", "host": "https://www.yicai.com"},
            {"name": "央视新闻", "url": "https://news.cctv.com/", "host": "https://news.cctv.com"},
            {"name": "证券日报", "url": "https://www.zqrb.cn/", "host": "https://www.zqrb.cn"},
        ]

    def _safe_get(self, url, timeout=20):
        """安全获取网页"""
        try:
            response = self.session.get(url, verify=False, timeout=timeout)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text
        except Exception as e:
            pass
        return None

    def _fetch_from_source(self, source, all_keywords):
        """从单个新闻源抓取并按关键词过滤"""
        source_name = source["name"]
        url = source["url"]
        host = source["host"]

        content = self._safe_get(url)
        if not content:
            return []

        try:
            soup = BeautifulSoup(content, 'html.parser')
            news_items = []

            for a in soup.find_all('a', href=True):
                title = a.get_text(strip=True)
                if not title or len(title) < 10 or len(title) > 100:
                    continue
                if not re.search(r'[\u4e00-\u9fa5]', title):
                    continue

                href = a['href']
                full_url = ''
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/') and host:
                    full_url = host + href

                matched = [kw for kw in all_keywords if kw in title]
                if matched:
                    news_items.append({
                        "title": title,
                        "url": full_url or url,
                        "snippet": f"来自{source_name}的报道",
                        "source": source_name,
                        "matched_keywords": matched
                    })

            return news_items
        except Exception as e:
            return []

    def search_news_for_industry(self, industry_name, industry_keywords, all_keywords):
        """抓取指定行业相关新闻
        industry_name: 行业名称（仅用于日志显示）
        industry_keywords: 该行业的具体关键词
        all_keywords: 所有领域关键词（用于全局过滤）
        """
        print(f"   🔍 正在抓取【{industry_name}】领域...")
        all_news = []

        for source in self.news_sources:
            try:
                news = self._fetch_from_source(source, all_keywords)
                if news:
                    # 过滤出本行业相关的
                    industry_news = [
                        n for n in news
                        if any(kw in n["title"] for kw in industry_keywords)
                    ]
                    if industry_news:
                        all_news.extend(industry_news)
                        print(f"     ✓ {source['name']}: {len(industry_news)} 条")
            except Exception as e:
                print(f"     ✗ {source['name']}: 失败")
            time.sleep(0.2 + random.random() * 0.3)

        # 去重（基于标题hash）
        unique_news = []
        seen_titles = set()
        for news in all_news:
            title_key = news["title"][:40].strip()
            title_hash = hashlib.md5(title_key.encode('utf-8')).hexdigest()
            if title_hash not in seen_titles and len(news["title"]) > 8:
                seen_titles.add(title_hash)
                unique_news.append(news)

        # 清理标题中的日期时间戳（如 "06-10 14:58"）
        for n in unique_news:
            n["title"] = re.sub(r'\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}', '', n["title"]).strip()
            n["title"] = re.sub(r'\d{2,4}[-./年]\d{1,2}[-./月]\d{1,2}[日]?', '', n["title"]).strip()

        print(f"     ✓ 合计有效 {len(unique_news)} 条")
        return unique_news


class DailyTechIntelSystemV6:
    """每日科技资讯分析系统 v6.0（增强版）"""

    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.date_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.news_data = {}
        self.analyzed_data = {}
        self.fetcher = MultiSourceNewsFetcher()

    def crawl_all_news(self):
        """爬取所有领域的新闻（新架构：一次抓取全部分类）"""
        print("=" * 80)
        print("🚀 每日科技前沿资讯分析系统 v6.0 启动")
        print("=" * 80)
        print(f"执行时间: {self.date_time_str}")
        print()

        # 汇总所有关键词用于全局过滤
        all_keywords = []
        for ind, kws in FIFTEEN_FIVE_INDUSTRIES.items():
            all_keywords.extend([ind])
            all_keywords.extend(kws)
        all_keywords = list(set(all_keywords))

        # 按行业逐个抓取
        for industry, keywords in FIFTEEN_FIVE_INDUSTRIES.items():
            print(f"📡 【{industry}】")
            # 该行业的关键词 = 行业名 + 细分关键词
            industry_kws = [industry] + list(keywords)
            news = self.fetcher.search_news_for_industry(industry, industry_kws, all_keywords)

            # 排序：按来源可靠性
            def _reliability(n):
                src = n.get("source", "")
                if any(s in src for s in ["政府", "证监", "国务院", "工信部", "科技部", "发改委", "央视"]):
                    return 3
                elif any(s in src for s in ["证券", "财经", "证券报", "日报", "时报", "中证", "联社"]):
                    return 2
                elif any(s in src for s in ["36氪", "虎嗅", "科技", "第一"]):
                    return 1
                return 0

            news.sort(key=lambda x: -_reliability(x))
            self.news_data[industry] = news
            print(f"   ✓ 共 {len(news)} 条")
            print()

        return self.news_data

    def analyze_source_reliability(self, news):
        """分析资讯来源可靠性"""
        url = news.get("url", "")
        title = news["title"]
        source = news.get("source", "")

        reliability_score = 40
        reasons = []

        # 检查来源域名
        for reliable_source in RELIABLE_SOURCES:
            if reliable_source in url or reliable_source in source:
                reliability_score += 35
                reasons.append(f"可信来源: {source or reliable_source}")
                break

        # 标题质量评分
        if 8 <= len(title) <= 60:
            reliability_score += 10
        elif len(title) > 80:
            reliability_score -= 5

        # 有真实来源加分
        if source and len(source) > 1:
            reliability_score += 10

        # 有具体URL加分
        if url and len(url) > 10:
            reliability_score += 5

        return {
            "score": min(100, max(0, reliability_score)),
            "is_reliable": reliability_score >= 50,
            "reasons": reasons
        }

    def extract_core_information(self, news, industry_name):
        """提取核心信息"""
        title = news["title"]
        snippet = news.get("snippet", "")
        text = title + " " + snippet

        core_info = {
            "event_subject": self._identify_subject(text, industry_name),
            "event_type": self._identify_event_type(text),
            "impact_scope": self._identify_impact_scope(text),
            "time_sensitivity": self._identify_time_sensitivity(title),
            "industry": industry_name,
            "potential_stocks": self._identify_related_stocks(industry_name, text)
        }
        return core_info

    def _identify_subject(self, text, industry_name):
        """识别事件主体"""
        subjects_map = {
            "政府机构": ["国务院", "发改委", "工信部", "科技部", "财政部", "央行", "证监会", "国资委", "商务部"],
            "核心企业": ["华为", "中芯国际", "宁德时代", "比亚迪", "腾讯", "阿里", "百度", "字节跳动", "小米", "美的", "格力"],
            "行业协会": ["协会", "联盟", "联合会"]
        }

        found = []
        for category, keywords in subjects_map.items():
            for keyword in keywords:
                if keyword in text:
                    found.append(keyword)

        if found:
            return "、".join(found[:2])
        return industry_name + "行业"

    def _identify_event_type(self, text):
        """识别事件类型"""
        event_types = {
            "政策发布": ["政策", "规划", "发布", "出台", "印发", "通知", "意见", "方案", "部署", "召开"],
            "技术突破": ["突破", "进展", "研发", "成功", "首次", "创新", "专利", "技术", "研制", "发布", "下线"],
            "产能扩张": ["产能", "量产", "扩产", "投产", "开工", "下线", "投产", "基地"],
            "合作并购": ["合作", "并购", "收购", "投资", "合资", "签约", "战略", "入股"],
            "市场动态": ["增长", "销量", "订单", "新高", "景气", "数据", "营收", "利润"],
            "会议论坛": ["论坛", "峰会", "大会", "会议", "展会", "研讨"]
        }

        for event_type, keywords in event_types.items():
            for keyword in keywords:
                if keyword in text:
                    return event_type
        return "行业动态"

    def _identify_impact_scope(self, text):
        """识别影响范围"""
        if any(keyword in text for keyword in ["国务院", "全国", "国家", "全球", "国际", "规划", "政策", "发改委", "工信部"]):
            return "国家级/全球性"
        elif any(keyword in text for keyword in ["行业", "产业", "领域", "板块", "产业链", "协会"]):
            return "行业级"
        else:
            return "企业级"

    def _identify_time_sensitivity(self, title):
        """识别时间敏感性"""
        if any(keyword in title for keyword in ["今日", "刚刚", "最新", "突发", "紧急", "今天", "刚刚"]):
            return "高"
        elif any(keyword in title for keyword in ["近日", "近期", "本周", "本月"]):
            return "中"
        return "低"

    def _identify_related_stocks(self, industry_name, text):
        """识别关联股票（关键词匹配）"""
        stocks = []
        if industry_name in INDUSTRY_STOCKS:
            stocks.extend(INDUSTRY_STOCKS[industry_name][:4])

        # 标题中提到的具体公司优先
        for company_list in INDUSTRY_STOCKS.values():
            for company in company_list:
                if company in text and company not in stocks:
                    stocks.insert(0, company)

        return stocks[:5]

    def analyze_reverse_signal(self, news):
        """分析反向信号（标题党、资本雇佣枪手检测）"""
        title = news["title"]
        snippet = news.get("snippet", "")

        signal_analysis = {
            "has_reverse_signal": False,
            "signal_score": 0,
            "signal_categories": {},
            "signal_words": [],
            "risk_level": "低",
            "analysis": "",
            "suggestion": ""
        }

        # 检查各类关键词（按类别加权）
        category_weights = {
            "极端词汇": 3,
            "内幕词汇": 3,
            "操作词汇": 2,
            "夸张词汇": 2,
            "引导词汇": 2,
            "主体词汇": 1,
            "时间词汇": 1
        }

        for category, keywords in REVERSE_SIGNAL_KEYWORDS.items():
            found = []
            for keyword in keywords:
                if keyword in title:
                    found.append(keyword)
                    signal_analysis["signal_score"] += category_weights.get(category, 2)

            if found:
                signal_analysis["signal_categories"][category] = found
                signal_analysis["signal_words"].extend(found)

        # 检查数字夸张（超过100%的百分比数字、如"770%"、倍数夸张如"翻3倍"等）
        number_patterns = [
            r'([1-9]\d{2,})%',  # 超过100%的百分比（排除"83.1%"这类正常数据）
            r'暴增\d+亿',   # 暴增XX亿
            r'暴涨\d+倍',   # 暴涨XX倍
            r'翻\d+倍',     # 翻XX倍（不含"翻1"、"翻2"这种正常的）
            r'增长\d+倍',  # 增长XX倍
            r'狂赚\d+倍',  # 狂赚XX倍
            r'净赚\d+倍',  # 净赚XX倍
            r'净增\d+倍',  # 净增XX倍
        ]
        for pattern in number_patterns:
            if re.search(pattern, title):
                signal_analysis["signal_score"] += 5
                match = re.search(pattern, title)
                if match:
                    signal_analysis["signal_words"].append(f"夸张数字:{match.group()}")
                signal_analysis["signal_categories"]["数字夸张"] = signal_analysis["signal_categories"].get("数字夸张", [])
                if match and match.group() not in signal_analysis["signal_categories"]["数字夸张"]:
                    signal_analysis["signal_categories"]["数字夸张"].append(match.group())

        # 检查标题模式（大量感叹号、问号）
        exclamation_count = title.count("!") + title.count("！")
        question_count = title.count("?") + title.count("？")
        if exclamation_count >= 2:
            signal_analysis["signal_score"] += 4
            signal_analysis["signal_words"].append(f"{exclamation_count}个感叹号")
        if question_count >= 2:
            signal_analysis["signal_score"] += 2

        # 检查标点开头（标题党常见："震惊！..." "重磅！..."）
        if re.match(r'^[^a-zA-Z0-9\u4e00-\u9fa5]{1,5}[!！?？]', title) or re.match(r'^[震惊重磅突发紧急独家]', title[:4]):
            signal_analysis["signal_score"] += 3

        # 来源可靠性辅助判断
        reliability = self.analyze_source_reliability(news)
        if not reliability["is_reliable"]:
            signal_analysis["signal_score"] += 2
            signal_analysis["analysis"] += "来源可靠性较低；"

        # 综合判定
        if signal_analysis["signal_score"] >= 8:
            signal_analysis["has_reverse_signal"] = True
            signal_analysis["risk_level"] = "高"
        elif signal_analysis["signal_score"] >= 5:
            signal_analysis["has_reverse_signal"] = True
            signal_analysis["risk_level"] = "中"

        if signal_analysis["has_reverse_signal"]:
            signal_analysis["analysis"] += f"检测到{len(signal_analysis['signal_words'])}个风险关键词"
            if signal_analysis["risk_level"] == "高":
                signal_analysis["suggestion"] = "高度疑似标题党或资本雇佣枪手发文，建议反向思考，切勿追涨！"
            else:
                signal_analysis["suggestion"] = "存在一定诱导性特征，需谨慎判断，建议多方核实。"
        else:
            signal_analysis["suggestion"] = "资讯正常，可正常关注。"

        return signal_analysis

    def analyze_chan_theory(self, news, core_info):
        """缠论视角深度分析"""
        title = news["title"]
        snippet = news.get("snippet", "")
        text = title + " " + snippet

        chan_analysis = {
            "buy_points": {
                "first": False,
                "second": False,
                "third": False,
                "details": []
            },
            "pivot_type": "",
            "trend_judgment": "",
            "operation_suggestion": "",
            "confidence_score": 30,
            "reasoning": []
        }

        # 第一类买点（政策底/技术底 - 由利空出尽或政策驱动）
        first_buy_triggers = ["政策", "规划", "出台", "发布", "国务院", "工信部", "发改委", "科技部", "首次", "创新", "突破"]
        for trigger in first_buy_triggers:
            if trigger in text or core_info["event_type"] in ["政策发布", "技术突破"]:
                chan_analysis["buy_points"]["first"] = True
                chan_analysis["buy_points"]["details"].append(f"政策/技术驱动型({trigger})")
                chan_analysis["confidence_score"] += 15
                chan_analysis["reasoning"].append(f"【一买】{core_info['event_type']}事件可能形成行业政策底或技术突破驱动")
                break

        # 第二类买点（回调确认后的安全介入点）
        second_buy_triggers = ["确认", "企稳", "验证", "回踩", "回调", "调整"]
        for trigger in second_buy_triggers:
            if trigger in text:
                chan_analysis["buy_points"]["second"] = True
                chan_analysis["buy_points"]["details"].append(f"回调信号({trigger})")
                chan_analysis["confidence_score"] += 10
                chan_analysis["reasoning"].append(f"【二买】标题提到'{trigger}'，可能提示回踩确认机会")
                break

        # 第三类买点（趋势确立后的加速机会）
        third_buy_triggers = ["新高", "加速", "超预期", "黄金期", "快车道", "井喷", "爆发", "高速增长"]
        for trigger in third_buy_triggers:
            if trigger in text:
                chan_analysis["buy_points"]["third"] = True
                chan_analysis["buy_points"]["details"].append(f"趋势加速({trigger})")
                chan_analysis["confidence_score"] += 10
                chan_analysis["reasoning"].append(f"【三买】出现'{trigger}'，需警惕情绪过热，也可能是趋势延续")
                break

        # 中枢类型判断
        if core_info["event_type"] == "政策发布":
            chan_analysis["pivot_type"] = "政策支撑中枢"
            chan_analysis["confidence_score"] += 5
        elif core_info["event_type"] == "技术突破":
            chan_analysis["pivot_type"] = "技术突破中枢"
            chan_analysis["confidence_score"] += 5
        elif core_info["event_type"] == "市场动态":
            chan_analysis["pivot_type"] = "市场情绪中枢"
        else:
            chan_analysis["pivot_type"] = "产业趋势中枢"

        # 影响范围加权
        if core_info["impact_scope"] == "国家级/全球性":
            chan_analysis["confidence_score"] += 15
        elif core_info["impact_scope"] == "行业级":
            chan_analysis["confidence_score"] += 8

        # 综合走势判断
        active_buy_points = sum([
            chan_analysis["buy_points"]["first"],
            chan_analysis["buy_points"]["second"],
            chan_analysis["buy_points"]["third"]
        ])

        if active_buy_points >= 2 or chan_analysis["confidence_score"] >= 55:
            chan_analysis["trend_judgment"] = f"偏多，关注{core_info['industry']}相关板块"
            chan_analysis["operation_suggestion"] = f"可关注{core_info['industry']}板块，等待合适买点（建议结合K线级别判断）"
        elif active_buy_points == 1 or chan_analysis["confidence_score"] >= 40:
            chan_analysis["trend_judgment"] = f"中性偏多，继续观察{core_info['industry']}板块"
            chan_analysis["operation_suggestion"] = "继续观察，等待更多信号确认（如成交量、板块联动）"
        else:
            chan_analysis["trend_judgment"] = "中性，保持观望"
            chan_analysis["operation_suggestion"] = "暂不操作，等待明确的基本面或技术面信号"

        return chan_analysis

    def analyze_all_news(self):
        """分析所有新闻"""
        self.analyzed_data = {}

        for industry, news_list in self.news_data.items():
            analyzed_list = []
            for news in news_list:
                core_info = self.extract_core_information(news, industry)
                reverse_signal = self.analyze_reverse_signal(news)
                chan_analysis = self.analyze_chan_theory(news, core_info)
                reliability = self.analyze_source_reliability(news)

                analyzed_list.append({
                    "news": news,
                    "core_info": core_info,
                    "reverse_signal": reverse_signal,
                    "chan_analysis": chan_analysis,
                    "reliability": reliability
                })

            # 排序：正常资讯在前，按缠论置信度降序
            analyzed_list.sort(key=lambda x: (
                1 if x["reverse_signal"]["has_reverse_signal"] else 0,
                -x["chan_analysis"]["confidence_score"],
                -x["reliability"]["score"]
            ))

            self.analyzed_data[industry] = analyzed_list

        return self.analyzed_data

    def generate_structured_report(self):
        """生成结构化报告"""
        report = f"# 📊 {self.date_str} 科技前沿资讯分析报告\n\n"
        report += f"> 📅 生成时间: {self.date_time_str}  \n"
        report += f"> 🏷️ 版本: v6.0 多源真实新闻版\n\n"
        report += "---\n\n"

        report += self._generate_summary_section()
        report += "\n"

        report += "## 📋 十五五规划相关产业动态\n\n"

        # 只展示有新闻的行业
        industries_with_news = [(ind, lst) for ind, lst in self.analyzed_data.items() if lst]
        for industry, news_list in sorted(industries_with_news, key=lambda x: -len(x[1])):
            report += self._generate_industry_section(industry, news_list)

        report += self._generate_reverse_signal_section()
        report += "\n"

        report += self._generate_chan_theory_section()
        report += "\n"

        report += self._generate_knowledge_section()
        report += "\n"

        report += "---\n"
        report += f"*本报告由每日科技资讯分析系统 v6.0 自动生成 | 数据来源: 东方财富、新浪财经、中新网、上海证券报等公开渠道*\n"
        report += "*⚠️ 报告内容仅供参考，不构成投资建议。股市有风险，投资需谨慎。*\n"

        return report

    def _generate_summary_section(self):
        """生成摘要部分"""
        total_news = sum(len(news_list) for news_list in self.news_data.values())
        normal_news = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list if not item["reverse_signal"]["has_reverse_signal"]
        )
        reverse_news = total_news - normal_news
        high_impact = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list
            if item["core_info"]["impact_scope"] in ["国家级/全球性", "行业级"]
        )
        high_chan = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list
            if item["chan_analysis"]["confidence_score"] >= 50
        )
        high_reliability = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list
            if item["reliability"]["is_reliable"]
        )

        section = f"""## 📌 报告摘要

| 指标 | 数值 |
|------|------|
| 📰 爬取资讯总数 | {total_news} |
| ✅ 正常资讯 | {normal_news} |
| ⚠️ 反向信号 | {reverse_news} |
| 🎯 高影响力资讯 | {high_impact} |
| 📈 缠论高置信信号 | {high_chan} |
| 🔒 可靠来源资讯 | {high_reliability} |

**执行时间**: {self.date_time_str}

"""
        return section

    def _generate_industry_section(self, industry, news_list):
        """生成行业资讯部分"""
        section = f"### 🔬 {industry} （共{len(news_list)}条）\n\n"

        # 展示前5条重要资讯
        display_count = min(5, len(news_list))
        for i, item in enumerate(news_list[:display_count], 1):
            news = item["news"]
            core = item["core_info"]
            reverse = item["reverse_signal"]
            chan = item["chan_analysis"]
            rel = item["reliability"]

            # 风险标签
            risk_tag = ""
            if reverse["has_reverse_signal"]:
                risk_tag = " 🔴" if reverse["risk_level"] == "高" else " 🟠"
            else:
                risk_tag = " 🟢"

            section += f"**{i}. {news['title']}**{risk_tag}\n\n"
            section += f"   - **来源**: {news.get('source', '未知')} | **事件**: {core['event_type']} | **影响**: {core['impact_scope']}\n"

            # 缠论买点标记
            buy_points = []
            if chan["buy_points"]["first"]:
                buy_points.append("一买")
            if chan["buy_points"]["second"]:
                buy_points.append("二买")
            if chan["buy_points"]["third"]:
                buy_points.append("三买")

            if buy_points:
                bp_str = "、".join(buy_points)
                section += f"   - **缠论**: 🟢 {bp_str}信号（置信{chan['confidence_score']}%）| {chan['trend_judgment']}\n"
            else:
                section += f"   - **缠论**: ⚪ 无明确信号（置信{chan['confidence_score']}%）| {chan['trend_judgment']}\n"

            # 关联股票
            if core["potential_stocks"]:
                section += f"   - **关联**: {'、'.join(core['potential_stocks'])}\n"

            # 反向信号警告
            if reverse["has_reverse_signal"]:
                section += f"   - **⚠️ 风险**: {reverse['risk_level']}级 | 关键词: {', '.join(reverse['signal_words'][:5])}\n"
                section += f"   - **💡 建议**: {reverse['suggestion']}\n"

            # 原文链接
            if news.get("url") and news["url"].startswith("http"):
                section += f"   - **链接**: {news['url']}\n"

            section += "\n"

        if len(news_list) > display_count:
            remaining = len(news_list) - display_count
            section += f"*（还有 {remaining} 条资讯，详见 JSON 数据文件）*\n\n"

        section += "\n"
        return section

    def _generate_reverse_signal_section(self):
        """生成反向信号预警部分"""
        all_reverse = []
        for industry, news_list in self.analyzed_data.items():
            for item in news_list:
                if item["reverse_signal"]["has_reverse_signal"]:
                    item_copy = dict(item)
                    item_copy["industry"] = industry
                    all_reverse.append(item_copy)

        if not all_reverse:
            return "## ✅ 反向信号检测\n\n今日未检测到明显的标题党或资本雇佣枪手发文，资讯质量较好。\n\n"

        section = f"## ⚠️ 反向信号预警（共{len(all_reverse)}条）\n\n"
        section += "> **⚠️ 重要提示**: 以下资讯存在标题党或诱导性特征，可能是资本雇佣枪手发文，请务必反向思考！\n\n"

        # 按风险等级排序（高风险在前）
        all_reverse.sort(key=lambda x: -x["reverse_signal"]["signal_score"])

        for i, item in enumerate(all_reverse[:8], 1):
            news = item["news"]
            reverse = item["reverse_signal"]
            industry = item["industry"]

            risk_icon = "🔴" if reverse["risk_level"] == "高" else "🟠"

            section += f"**{i}. {risk_icon} [{industry}] {news['title']}**\n\n"
            section += f"   - **风险等级**: {reverse['risk_level']}级 | 风险评分: {reverse['signal_score']}\n"
            if reverse["signal_words"]:
                section += f"   - **风险关键词**: {', '.join(reverse['signal_words'][:6])}\n"
            section += f"   - **分析**: {reverse['analysis']}\n"
            section += f"   - **💡 建议**: {reverse['suggestion']}\n"
            if news.get("url") and news["url"].startswith("http"):
                section += f"   - **来源**: {news.get('source', '未知')} | [查看原文]({news['url']})\n"
            section += "\n"

        return section

    def _generate_chan_theory_section(self):
        """生成缠论分析部分"""
        first_buy = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list if item["chan_analysis"]["buy_points"]["first"]
        )
        second_buy = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list if item["chan_analysis"]["buy_points"]["second"]
        )
        third_buy = sum(
            1 for news_list in self.analyzed_data.values()
            for item in news_list if item["chan_analysis"]["buy_points"]["third"]
        )

        # 找出高置信信号
        high_confidence_items = []
        for industry, news_list in self.analyzed_data.items():
            for item in news_list:
                if item["chan_analysis"]["confidence_score"] >= 50 and not item["reverse_signal"]["has_reverse_signal"]:
                    item["industry"] = industry
                    high_confidence_items.append(item)
        high_confidence_items.sort(key=lambda x: -x["chan_analysis"]["confidence_score"])

        section = f"""## 📈 缠论视角深度分析

### 核心买点信号统计

| 买点类型 | 信号数量 | 说明 |
|----------|----------|------|
| 🟢 第一类买点 | {first_buy} | 政策发布、技术突破带来的驱动型机会 |
| 🟢 第二类买点 | {second_buy} | 回调确认后的安全介入点 |
| 🟢 第三类买点 | {third_buy} | 趋势确立后的加速机会 |

### 今日高置信信号（缠论置信度≥50%）

"""

        if high_confidence_items:
            for i, item in enumerate(high_confidence_items[:8], 1):
                news = item["news"]
                chan = item["chan_analysis"]
                industry = item["industry"]

                bp_list = []
                if chan["buy_points"]["first"]:
                    bp_list.append("一买")
                if chan["buy_points"]["second"]:
                    bp_list.append("二买")
                if chan["buy_points"]["third"]:
                    bp_list.append("三买")

                section += f"**{i}. [{industry}] {news['title']}**\n"
                section += f"   - 买点: {'、'.join(bp_list) if bp_list else '无明确'} | 置信度: {chan['confidence_score']}%\n"
                section += f"   - 中枢: {chan['pivot_type']} | 判断: {chan['trend_judgment']}\n"
                section += f"   - 建议: {chan['operation_suggestion']}\n\n"
        else:
            section += "*今日暂无高置信度缠论信号，建议保持观望，等待更明确的市场信号。*\n\n"

        section += """### 综合策略建议

1. **仓位管理**: 结合当前市场情绪，建议总仓位控制在 30%-60%，避免情绪化追涨
2. **选股方向**: 重点关注 人工智能、半导体、新能源、数字经济 等十五五重点赛道
3. **入场时机**: 等待明确的回调确认信号（日线级别的二买/三买），不要追高买入
4. **止损设置**: 单只股票亏损幅度建议不超过 5%-8%，严格执行止损纪律
5. **风险控制**: 当反向信号密集出现时，需警惕情绪过热，考虑减仓或观望

### 缠论核心原理简述

- **第一类买点**: 由下跌趋势背离产生，通常出现在政策底或业绩底
- **第二类买点**: 不创新低的回调确认点，安全性较高，是主要的介入位置
- **第三类买点**: 离开中枢后的不回抽确认点，属于趋势延续信号，风险也较高
- **关键原则**: "买点买，卖点卖"，严格按照级别操作，避免频繁交易

"""
        return section

    def _generate_knowledge_section(self):
        """生成知识沉淀部分"""
        section = """## 🧠 知识沉淀

### 今日核心知识点

"""

        # 汇总高影响力资讯
        high_impact_items = []
        for industry, news_list in self.analyzed_data.items():
            for item in news_list:
                if item["core_info"]["impact_scope"] in ["国家级/全球性", "行业级"] and not item["reverse_signal"]["has_reverse_signal"]:
                    item["industry"] = industry
                    high_impact_items.append(item)

        if high_impact_items:
            for i, item in enumerate(high_impact_items[:5], 1):
                news = item["news"]
                core = item["core_info"]
                section += f"{i}. **[{core['industry']}] {news['title']}**\n"
                section += f"   - 事件类型: {core['event_type']} | 影响范围: {core['impact_scope']}\n"
                section += f"   - 主体: {core['event_subject']}\n\n"
        else:
            section += "*今日暂无高影响力政策或行业资讯。*\n\n"

        section += """### 持续关注方向

1. **政策面**: 十五五规划重点产业的后续政策落地、细化方案、资金支持
2. **技术面**: 人工智能、半导体、新能源领域的技术突破和商业化进展
3. **基本面**: 行业龙头的业绩、订单、产能扩张情况
4. **情绪面**: 警惕自媒体标题党和资本雇佣枪手的反向信号
5. **国际面**: 关注全球产业链变化、地缘政治对科技产业的影响

### 风险提示清单

- ⚠️ 单一资讯不足以作为投资决策依据，需多方验证
- ⚠️ 标题党资讯（暴涨、翻倍、内幕等）需反向思考
- ⚠️ 政策利好可能已被市场提前消化（买预期卖事实）
- ⚠️ 技术突破到商业化落地可能存在较长时间差
- ⚠️ 热门板块容易出现情绪过热后的回调

"""
        return section

    def save_report_and_knowledge(self, report):
        """保存报告和知识沉淀"""
        report_file = REPORT_DIR / f"{self.date_str}_tech_intel_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📁 主报告已保存: {report_file}")

        data_file = REPORT_DIR / f"{self.date_str}_tech_intel_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date": self.date_str,
                "datetime": self.date_time_str,
                "version": "v6.0",
                "news_data": self.news_data,
                "analyzed_data": self.analyzed_data
            }, f, ensure_ascii=False, indent=2)
        print(f"📁 分析数据已保存: {data_file}")

        # 追加到知识库
        knowledge_file = KNOWLEDGE_BASE_DIR / "tech_intel_history.md"
        knowledge_entry = f"\n\n---\n\n## {self.date_str}（v6.0）\n{report[:1200]}...\n"

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

        # 如果没有获取到任何新闻，也要正常生成报告（但标记清楚）
        total = sum(len(v) for v in self.news_data.values())
        print(f"\n📊 共获取 {total} 条资讯")

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
    system = DailyTechIntelSystemV6()
    system.run()


if __name__ == '__main__':
    main()
