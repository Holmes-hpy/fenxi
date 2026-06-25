#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日科技前沿资讯分析系统 v7.0（增强版）
- 每日上午9:30、下午14:30 定时执行
- 使用多个真实财经/科技频道首页抓取，通过十五五产业关键词过滤
- 结合缠论进行深度知识沉淀
- 智能识别反向信号（自媒体标题党、资本雇佣枪手发文）
- 结构化知识图谱保存（JSON Graph 格式）
- 严格禁止生成虚假模拟数据，只保留真实获取的资讯
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
from collections import defaultdict, Counter

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
GRAPH_DIR = PROJECT_DIR / "knowledge_graph"
GRAPH_DIR.mkdir(exist_ok=True)


# ============================================================
# 1. 十五五规划重点关注产业
# ============================================================
FIFTEEN_FIVE_INDUSTRIES = {
    "人工智能": ["人工智能", "AI", "大模型", "生成式AI", "深度学习", "人形机器人", "机器视觉", "多模态", "智能体", "AGI", "机器学习", "神经网络"],
    "半导体": ["半导体", "芯片", "集成电路", "先进制程", "国产替代", "中芯国际", "光刻", "先进封装", "存储", "晶圆", "EDA", "GPU", "CPU", "DRAM", "NAND"],
    "新能源": ["新能源", "光伏", "风电", "储能", "新能源汽车", "锂电池", "宁德时代", "比亚迪", "氢能", "燃料电池", "储能电池", "碳酸锂", "固态电池"],
    "数字经济": ["数字经济", "数据中心", "算力", "云计算", "大数据", "东数西算", "工业互联网", "数据要素", "数字中国", "信创"],
    "十五五规划": ["十五五规划", "高质量发展", "现代化产业体系", "政策", "规划", "新质生产力", "国务院", "发改委", "工信部", "科技部"],
    "新材料": ["新材料", "稀土", "碳纤维", "第三代半导体", "碳化硅", "氮化镓", "石墨烯", "超导"],
    "生物医药": ["生物医药", "创新药", "基因编辑", "医疗器械", "CXO", "生物科技", "mRNA", "ADC", "GLP-1", "减肥药"],
    "航天军工": ["航天", "商业航天", "卫星互联网", "军工", "无人机", "低空经济", "卫星", "北斗"],
    "智能网联汽车": ["自动驾驶", "车联网", "智能驾驶", "L3", "L4", "激光雷达", "毫米波雷达", "域控制器"],
    "量子科技": ["量子计算", "量子通信", "量子科技", "量子比特"]
}


# ============================================================
# 2. 可靠资讯来源（按可信程度分级）
# ============================================================
RELIABLE_SOURCES = [
    # A级：政府官媒（最高信任）
    "gov.cn", "miit.gov.cn", "most.gov.cn", "ndrc.gov.cn", "csrc.gov.cn",
    "www.gov.cn", "news.cn", "xinhuanet.com", "people.com.cn", "cctv.com",
    # B级：权威财经媒体
    "stcn.com", "cs.com.cn", "zqrb.cn", "chinadaily.com.cn",
    "caixin.com", "yicai.com", "cls.cn",
    # C级：主流媒体
    "eastmoney.com", "sina.com.cn", "163.com", "sohu.com",
    # D级：专业科技媒体
    "36kr.com", "huxiu.com", "ithome.com", "leiphone.com"
]


# ============================================================
# 3. 新闻抓取源（首页/频道页 URL）
# ============================================================
NEWS_SOURCES = [
    {"name": "证券时报", "url": "https://www.stcn.com/", "host": "https://www.stcn.com", "trust_level": "B"},
    {"name": "中国证券报", "url": "https://www.cs.com.cn/", "host": "https://www.cs.com.cn", "trust_level": "B"},
    {"name": "证券日报", "url": "https://www.zqrb.cn/", "host": "https://www.zqrb.cn", "trust_level": "B"},
    {"name": "财联社", "url": "https://www.cls.cn/", "host": "https://www.cls.cn", "trust_level": "B"},
    {"name": "第一财经", "url": "https://www.yicai.com/", "host": "https://www.yicai.com", "trust_level": "B"},
    {"name": "新浪财经", "url": "https://finance.sina.com.cn/", "host": "https://finance.sina.com.cn", "trust_level": "C"},
    {"name": "网易财经", "url": "https://money.163.com/", "host": "https://money.163.com", "trust_level": "C"},
    {"name": "东方财富网", "url": "https://www.eastmoney.com/", "host": "https://www.eastmoney.com", "trust_level": "C"},
    {"name": "央视新闻", "url": "https://news.cctv.com/", "host": "https://news.cctv.com", "trust_level": "A"},
    {"name": "新华网", "url": "http://www.xinhuanet.com/", "host": "http://www.xinhuanet.com", "trust_level": "A"},
    {"name": "人民网", "url": "http://www.people.com.cn/", "host": "http://www.people.com.cn", "trust_level": "A"},
    {"name": "36氪", "url": "https://36kr.com/", "host": "https://36kr.com", "trust_level": "D"},
    {"name": "虎嗅网", "url": "https://www.huxiu.com/", "host": "https://huxiu.com", "trust_level": "D"},
]


# ============================================================
# 4. 反向信号关键词（标题党/枪手特征识别）
# ============================================================
REVERSE_SIGNAL_KEYWORDS = {
    "极端词汇": ["暴涨", "暴跌", "必涨", "必跌", "翻倍", "妖股", "疯涨", "崩盘", "血洗", "涨停潮", "跌停潮",
                "炸了", "疯了", "暴增", "暴富", "狂涨", "狂跌", "井喷", "飙升", "爆发", "炸裂", "逆天",
                "彻底疯了", "彻底爆发", "历史首次", "全球第一", "全球首发", "行业第一", "彻底改变", "颠覆"],
    "内幕词汇": ["内幕", "独家", "重磅", "惊天", "震惊", "秘密", "内部消息", "绝密", "泄密", "爆料", "实锤",
                "曝光", "揭秘", "藏不住了", "瞒不住了", "不可告人", "不敢说"],
    "主体词汇": ["主力", "游资", "机构", "大佬", "牛散", "庄家", "操盘手", "国家队", "外资", "神秘资金", "聪明钱"],
    "时间词汇": ["即将", "马上", "立刻", "今日", "最新", "突发", "紧急", "刚刚", "就在刚才", "就在今天", "周末",
                "就在刚刚", "今晚", "今夜"],
    "引导词汇": ["手把手", "带你", "教你", "跟着", "躺赢", "赚钱", "发财", "致富", "必看", "收藏", "速看", "快看",
                "牛股", "龙头股", "十倍股", "翻倍股", "布局", "重点关注", "强烈推荐", "赶紧上车", "不要错过",
                "最后的机会", "千载难逢"],
    "操作词汇": ["抄底", "逃顶", "上车", "下车", "接力", "打板", "追涨", "杀跌", "核按钮", "满仓", "重仓", "梭哈",
                "All in", "砸锅卖铁", "卖房炒股"],
    "夸张词汇": ["震惊", "慌了", "哭了", "笑了", "懵了", "爽了", "赚翻了", "太可怕", "吓尿", "惊呆", "炸锅", "沸腾",
                "疯狂", "失控", "彻底失控", "泪目", "燃爆", "炸裂"],
    "权威滥用": ["央视", "新华社", "人民日报", "中央定调", "高层发话", "刚刚召开", "重磅会议"]
}


# ============================================================
# 5. 股票关联映射
# ============================================================
INDUSTRY_STOCKS = {
    "人工智能": ["寒武纪", "科大讯飞", "海天瑞声", "云从科技", "拓尔思", "工业富联", "浪潮信息", "三六零", "昆仑万维"],
    "半导体": ["中芯国际", "北方华创", "韦尔股份", "紫光国微", "卓胜微", "兆易创新", "长电科技", "华虹公司", "寒武纪"],
    "新能源": ["宁德时代", "比亚迪", "隆基绿能", "通威股份", "阳光电源", "天齐锂业", "赣锋锂业", "亿纬锂能"],
    "数字经济": ["宝信软件", "用友网络", "金山办公", "中科曙光", "浪潮信息", "紫光股份", "星环科技"],
    "新材料": ["北方稀土", "中国宝安", "光威复材", "中简科技", "天奈科技", "中钨高新"],
    "生物医药": ["恒瑞医药", "药明康德", "迈瑞医疗", "爱尔眼科", "智飞生物", "百济神州", "荣昌生物"],
    "航天军工": ["中航沈飞", "航天电器", "中国卫星", "中直股份", "高德红外", "航天彩虹"],
    "智能网联汽车": ["德赛西威", "华阳集团", "均胜电子", "英伟达概念", "小鹏汽车", "理想汽车"],
    "量子科技": ["国盾量子", "本源量子", "中科曙光"]
}


# ============================================================
# 【模块1】多源新闻抓取器
# ============================================================
class MultiSourceNewsFetcher:
    """多源新闻抓取器 - 直接抓取财经/科技频道首页，通过十五五产业关键词过滤"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def _safe_get(self, url, timeout=20):
        """安全获取网页内容"""
        try:
            response = self.session.get(url, verify=False, timeout=timeout)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text
        except Exception:
            pass
        return None

    def _fetch_from_source(self, source, all_keywords):
        """从单个新闻源首页抓取并按关键词过滤"""
        source_name = source["name"]
        url = source["url"]
        host = source["host"]
        trust_level = source.get("trust_level", "C")

        content = self._safe_get(url)
        if not content:
            return []

        try:
            soup = BeautifulSoup(content, 'html.parser')
            news_items = []

            for a in soup.find_all('a', href=True):
                title = a.get_text(strip=True)
                if not title or len(title) < 8 or len(title) > 120:
                    continue
                if not re.search(r'[\u4e00-\u9fa5]', title):
                    continue
                # 过滤纯数字/纯符号标题
                if re.match(r'^[\d\s\-\.:：,，。！？!?""]+$', title):
                    continue

                href = a['href']
                full_url = ''
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/') and host:
                    full_url = host + href

                matched = [kw for kw in all_keywords if kw and kw in title]
                if matched and len(matched) >= 1:
                    news_items.append({
                        "title": title,
                        "url": full_url or url,
                        "snippet": f"来自{source_name}的报道",
                        "source": source_name,
                        "trust_level": trust_level,
                        "matched_keywords": matched
                    })

            return news_items
        except Exception:
            return []

    def search_news_for_industry(self, industry_name, industry_keywords, all_keywords):
        """抓取指定行业相关新闻"""
        print(f"   🔍 正在抓取【{industry_name}】领域...")
        all_news = []

        for source in NEWS_SOURCES:
            try:
                news = self._fetch_from_source(source, all_keywords)
                if news:
                    industry_news = [
                        n for n in news
                        if any(kw in n["title"] for kw in industry_keywords)
                    ]
                    if industry_news:
                        all_news.extend(industry_news)
                        print(f"     ✓ {source['name']}: {len(industry_news)} 条")
            except Exception:
                print(f"     ✗ {source['name']}: 失败")
            time.sleep(0.15 + random.random() * 0.25)

        # 去重（基于标题hash）
        unique_news = []
        seen_titles = set()
        for news in all_news:
            title_key = news["title"][:50].strip()
            title_hash = hashlib.md5(title_key.encode('utf-8')).hexdigest()
            if title_hash not in seen_titles and len(news["title"]) > 8:
                seen_titles.add(title_hash)
                unique_news.append(news)

        # 清理标题中的日期时间戳
        for n in unique_news:
            n["title"] = re.sub(r'\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}', '', n["title"]).strip()
            n["title"] = re.sub(r'\d{2,4}[-./年]\d{1,2}[-./月]\d{1,2}[日]?', '', n["title"]).strip()
            n["title"] = re.sub(r'\s+', ' ', n["title"]).strip()

        print(f"     ✓ 合计有效 {len(unique_news)} 条")
        return unique_news


# ============================================================
# 【模块2】反向信号分析器（标题党/枪手识别）
# ============================================================
class ReverseSignalAnalyzer:
    """反向信号分析器 - 智能识别标题党和资本雇佣枪手发文"""

    def __init__(self):
        self.keywords = REVERSE_SIGNAL_KEYWORDS
        # 关键词权重（不同类别权重不同）
        self.category_weights = {
            "极端词汇": 3,
            "内幕词汇": 3,
            "操作词汇": 3,
            "引导词汇": 2,
            "夸张词汇": 2,
            "主体词汇": 1,
            "时间词汇": 1,
            "权威滥用": 2
        }

    def analyze(self, title, snippet, source, url):
        """分析单条资讯的反向信号"""
        text = (title + " " + snippet).strip()

        signal = {
            "has_reverse_signal": False,
            "signal_score": 0,
            "signal_categories": {},
            "signal_words": [],
            "risk_level": "低",
            "title_party_pattern": [],
            "gunman_pattern": [],
            "analysis": "",
            "suggestion": ""
        }

        # 1. 关键词匹配
        for category, kws in self.keywords.items():
            found = []
            for kw in kws:
                if kw in title:
                    found.append(kw)
                    signal["signal_score"] += self.category_weights.get(category, 2)
            if found:
                signal["signal_categories"][category] = found
                signal["signal_words"].extend(found)

        # 2. 数字夸张检测（超过100%的百分比、夸张倍数）
        exaggeration_patterns = [
            (r'([1-9]\d{2,})%', '夸张百分比'),
            (r'暴增\s*\d+\s*亿', '暴增XX亿'),
            (r'暴涨\s*\d+\s*倍', '暴涨XX倍'),
            (r'翻\s*\d+\s*倍', '翻XX倍'),
            (r'增长\s*\d+\s*倍', '增长XX倍'),
            (r'狂赚\s*\d+\s*倍', '狂赚XX倍'),
        ]
        for pattern, label in exaggeration_patterns:
            match = re.search(pattern, title)
            if match:
                signal["signal_score"] += 5
                signal["signal_words"].append(f"{label}:{match.group()}")
                signal["signal_categories"]["数字夸张"] = signal["signal_categories"].get("数字夸张", [])
                if match.group() not in signal["signal_categories"]["数字夸张"]:
                    signal["signal_categories"]["数字夸张"].append(match.group())

        # 3. 标点符号检测（大量感叹号/问号）
        excl = title.count("!") + title.count("！")
        ques = title.count("?") + title.count("？")
        if excl >= 2:
            signal["signal_score"] += 4
            signal["signal_words"].append(f"{excl}个感叹号")
            signal["title_party_pattern"].append("多感叹号")
        if ques >= 2:
            signal["signal_score"] += 2
            signal["title_party_pattern"].append("多问号")

        # 4. 标题开头模式检测（典型标题党开头）
        title_patterns = [
            (r'^[震惊重磅突发紧急独家揭秘]', '强情绪开头'),
            (r'^刚刚', '时间压迫开头'),
            (r'!.*!', '感叹号堆砌'),
            (r'^\s*[！!]', '感叹号开头'),
            (r'[暴涨暴跌必涨必跌翻倍涨停].*[暴涨暴跌必涨必跌翻倍涨停]', '极端词汇重复'),
        ]
        for pattern, label in title_patterns:
            if re.search(pattern, title):
                signal["signal_score"] += 3
                signal["title_party_pattern"].append(label)
                break

        # 5. 标题党模式2：非标题性描述（"手把手教你XX"、"XX一定要看"）
        titleparty_2 = [
            (r'手把手', '引导式操作'),
            (r'教你|带你|跟着', '主观引导'),
            (r'一定要看|不得不看|不得不提', '强制引导'),
            (r'最后的机会|千载难逢', '稀缺诱导'),
        ]
        for pattern, label in titleparty_2:
            if re.search(pattern, title):
                signal["gunman_pattern"].append(label)
                signal["signal_score"] += 2

        # 6. 来源域名可靠性判断
        is_reliable_source = False
        for rs in RELIABLE_SOURCES:
            if rs in url or rs in source:
                is_reliable_source = True
                break
        if not is_reliable_source:
            signal["signal_score"] += 3
            signal["analysis"] += "来源域名不在可信白名单；"

        # 7. 标题长度异常（过短或过长）
        if len(title) < 6 or len(title) > 80:
            signal["signal_score"] += 2

        # 8. 英文大写情绪词（Bull run、Moon等）
        emotional_english = [r'\bMOON\b', r'\bBULL\b', r'\b🚀', r'\bTO THE MOON\b']
        for pattern in emotional_english:
            if re.search(pattern, title, re.IGNORECASE):
                signal["signal_score"] += 3
                signal["gunman_pattern"].append("英文情绪词")

        # 9. 综合风险判定
        if signal["signal_score"] >= 10:
            signal["has_reverse_signal"] = True
            signal["risk_level"] = "高"
        elif signal["signal_score"] >= 6:
            signal["has_reverse_signal"] = True
            signal["risk_level"] = "中"
        elif signal["signal_score"] >= 3:
            signal["risk_level"] = "低"

        # 10. 生成分析与建议
        if signal["has_reverse_signal"]:
            signal["analysis"] += f"检测到{len(signal['signal_words'])}个风险关键词；"
            if signal["title_party_pattern"]:
                signal["analysis"] += f"标题党模式: {', '.join(signal['title_party_pattern'])}；"
            if signal["gunman_pattern"]:
                signal["analysis"] += f"枪手特征: {', '.join(signal['gunman_pattern'])}；"
            if signal["risk_level"] == "高":
                signal["suggestion"] = "高度疑似标题党或资本雇佣枪手发文，建议反向思考，切勿追涨！需结合正规媒体多方核实。"
            else:
                signal["suggestion"] = "存在一定诱导性特征，需谨慎判断，建议多方核实后再决策。"
        else:
            signal["suggestion"] = "资讯质量正常，可正常关注，仍需结合多源信息判断。"

        return signal


# ============================================================
# 【模块3】资讯可靠性分析器
# ============================================================
class ReliabilityAnalyzer:
    """资讯来源可靠性分析"""

    def analyze(self, news):
        url = news.get("url", "")
        title = news["title"]
        source = news.get("source", "")
        trust_level = news.get("trust_level", "C")

        score = 40
        reasons = []

        # 来源域名检查
        for reliable in RELIABLE_SOURCES:
            if reliable in url or reliable in source:
                score += 35
                reasons.append(f"可信来源({source})")
                break

        # 信任级别加分
        if trust_level == "A":
            score += 20
            reasons.append("官方媒体")
        elif trust_level == "B":
            score += 10
            reasons.append("权威财经")
        elif trust_level == "C":
            score += 5
            reasons.append("主流媒体")

        # 标题长度合理性
        if 8 <= len(title) <= 60:
            score += 10
        elif len(title) > 80:
            score -= 5

        # URL 完整性
        if url and url.startswith("http") and len(url) > 10:
            score += 5

        score = min(100, max(0, score))
        return {
            "score": score,
            "is_reliable": score >= 50,
            "reasons": reasons
        }


# ============================================================
# 【模块4】核心信息提取器（事件主体/类型/影响范围）
# ============================================================
class CoreInfoExtractor:
    """核心信息提取 - 将新闻转化为结构化知识"""

    EVENT_TYPES = {
        "政策发布": ["政策", "规划", "发布", "出台", "印发", "通知", "意见", "方案", "部署", "召开", "会议"],
        "技术突破": ["突破", "进展", "研发", "成功", "首次", "创新", "专利", "技术", "研制", "下线", "量产"],
        "产能扩张": ["产能", "量产", "扩产", "投产", "开工", "下线", "基地", "项目", "投资"],
        "合作并购": ["合作", "并购", "收购", "投资", "合资", "签约", "战略", "入股", "收购"],
        "市场动态": ["增长", "销量", "订单", "新高", "景气", "数据", "营收", "利润", "出货量"],
        "会议论坛": ["论坛", "峰会", "大会", "会议", "展会", "研讨", "召开"],
        "人事变动": ["人事", "任命", "离职", "换届", "调整"]
    }

    SUBJECT_MAP = {
        "政府机构": ["国务院", "发改委", "工信部", "科技部", "财政部", "央行", "证监会", "国资委", "商务部", "中央", "中共中央"],
        "核心企业": ["华为", "中芯国际", "宁德时代", "比亚迪", "腾讯", "阿里", "百度", "字节跳动", "小米", "美的", "格力",
                    "寒武纪", "科大讯飞", "工业富联", "浪潮信息"],
        "行业协会": ["协会", "联盟", "联合会", "商会"],
        "国际组织": ["联合国", "WTO", "WHO", "IMF", "世界银行"]
    }

    def extract(self, news, industry_name):
        title = news["title"]
        snippet = news.get("snippet", "")
        text = title + " " + snippet

        core = {
            "event_subject": self._identify_subject(text),
            "event_type": self._identify_event_type(text),
            "impact_scope": self._identify_impact_scope(text),
            "time_sensitivity": self._identify_time_sensitivity(title),
            "industry": industry_name,
            "potential_stocks": self._identify_stocks(industry_name, text),
            "key_keywords": news.get("matched_keywords", [])
        }
        return core

    def _identify_subject(self, text):
        found = []
        for category, kws in self.SUBJECT_MAP.items():
            for kw in kws:
                if kw in text:
                    found.append(kw)
        if found:
            return "、".join(found[:3])
        return "行业相关主体"

    def _identify_event_type(self, text):
        for etype, kws in self.EVENT_TYPES.items():
            for kw in kws:
                if kw in text:
                    return etype
        return "行业动态"

    def _identify_impact_scope(self, text):
        gov_keywords = ["国务院", "全国", "国家", "全球", "国际", "规划", "政策", "发改委", "工信部", "科技部", "中央", "中共中央"]
        if any(kw in text for kw in gov_keywords):
            return "国家级/全球性"
        elif any(kw in text for kw in ["行业", "产业", "领域", "板块", "产业链", "协会"]):
            return "行业级"
        else:
            return "企业级"

    def _identify_time_sensitivity(self, title):
        high_words = ["今日", "刚刚", "最新", "突发", "紧急", "今天", "刚刚", "今夜"]
        mid_words = ["近日", "近期", "本周", "本月", "今年"]
        if any(w in title for w in high_words):
            return "高"
        elif any(w in title for w in mid_words):
            return "中"
        return "低"

    def _identify_stocks(self, industry_name, text):
        stocks = []
        if industry_name in INDUSTRY_STOCKS:
            stocks.extend(INDUSTRY_STOCKS[industry_name][:5])
        for company_list in INDUSTRY_STOCKS.values():
            for company in company_list:
                if company in text and company not in stocks:
                    stocks.insert(0, company)
        return stocks[:6]


# ============================================================
# 【模块5】缠论分析器
# ============================================================
class ChanTheoryAnalyzer:
    """缠论视角深度分析 - 判断买卖点、中枢类型、趋势判断"""

    def analyze(self, title, snippet, core_info):
        text = title + " " + snippet
        analysis = {
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

        # 第一类买点（政策驱动/技术突破）
        first_triggers = ["政策", "规划", "出台", "发布", "国务院", "工信部", "发改委", "科技部", "首次", "创新", "突破", "国产替代"]
        for trigger in first_triggers:
            if trigger in text or core_info["event_type"] in ["政策发布", "技术突破"]:
                analysis["buy_points"]["first"] = True
                analysis["buy_points"]["details"].append(f"政策/技术驱动({trigger})")
                analysis["confidence_score"] += 15
                analysis["reasoning"].append(f"【一买】{core_info['event_type']}事件可能形成行业政策底或技术突破驱动")
                break

        # 第二类买点（回调确认）
        second_triggers = ["确认", "企稳", "验证", "回踩", "回调", "调整", "筑底"]
        for trigger in second_triggers:
            if trigger in text:
                analysis["buy_points"]["second"] = True
                analysis["buy_points"]["details"].append(f"回调信号({trigger})")
                analysis["confidence_score"] += 10
                analysis["reasoning"].append(f"【二买】标题提到'{trigger}'，可能提示回踩确认机会")
                break

        # 第三类买点（趋势加速）
        third_triggers = ["新高", "加速", "超预期", "黄金期", "快车道", "井喷", "爆发", "高速增长", "供不应求"]
        for trigger in third_triggers:
            if trigger in text:
                analysis["buy_points"]["third"] = True
                analysis["buy_points"]["details"].append(f"趋势加速({trigger})")
                analysis["confidence_score"] += 10
                analysis["reasoning"].append(f"【三买】出现'{trigger}'，需警惕情绪过热，也可能是趋势延续")
                break

        # 中枢类型判断
        event_type = core_info["event_type"]
        if event_type == "政策发布":
            analysis["pivot_type"] = "政策支撑中枢"
            analysis["confidence_score"] += 8
        elif event_type == "技术突破":
            analysis["pivot_type"] = "技术突破中枢"
            analysis["confidence_score"] += 8
        elif event_type == "市场动态":
            analysis["pivot_type"] = "市场情绪中枢"
            analysis["confidence_score"] += 3
        elif event_type == "产能扩张":
            analysis["pivot_type"] = "基本面扩张中枢"
            analysis["confidence_score"] += 5
        else:
            analysis["pivot_type"] = "产业趋势中枢"

        # 影响范围加权
        scope = core_info["impact_scope"]
        if scope == "国家级/全球性":
            analysis["confidence_score"] += 15
        elif scope == "行业级":
            analysis["confidence_score"] += 8

        # 时间敏感性
        ts = core_info["time_sensitivity"]
        if ts == "高":
            analysis["confidence_score"] += 5

        # 综合走势判断
        active_bp = sum([analysis["buy_points"]["first"], analysis["buy_points"]["second"], analysis["buy_points"]["third"]])

        if active_bp >= 2 or analysis["confidence_score"] >= 55:
            analysis["trend_judgment"] = f"偏多，关注{core_info['industry']}相关板块"
            analysis["operation_suggestion"] = f"可关注{core_info['industry']}板块，等待合适买点（建议结合K线级别判断）"
        elif active_bp == 1 or analysis["confidence_score"] >= 40:
            analysis["trend_judgment"] = f"中性偏多，继续观察{core_info['industry']}板块"
            analysis["operation_suggestion"] = "继续观察，等待更多信号确认（如成交量、板块联动）"
        else:
            analysis["trend_judgment"] = "中性，保持观望"
            analysis["operation_suggestion"] = "暂不操作，等待明确的基本面或技术面信号"

        return analysis


# ============================================================
# 【模块6】知识图谱构建器（结构化知识沉淀）
# ============================================================
class KnowledgeGraphBuilder:
    """构建十五五产业知识图谱（节点=产业/企业/事件，边=关联关系）"""

    def __init__(self):
        self.nodes = []
        self.edges = []
        self._node_ids = {}
        self._next_id = 1

    def _get_or_create_node(self, name, ntype, industry=None, extra=None):
        key = f"{ntype}:{name}"
        if key in self._node_ids:
            return self._node_ids[key]
        nid = f"N{self._next_id:04d}"
        self._next_id += 1
        node = {
            "id": nid,
            "name": name,
            "type": ntype,
            "industry": industry,
            "extra": extra or {}
        }
        self.nodes.append(node)
        self._node_ids[key] = nid
        return nid

    def _add_edge(self, from_id, to_id, relation, weight=1.0, extra=None):
        edge = {
            "from": from_id,
            "to": to_id,
            "relation": relation,
            "weight": weight,
            "extra": extra or {}
        }
        self.edges.append(edge)

    def add_news_item(self, industry, news, core_info, chan_analysis, reverse_signal):
        """添加一条新闻到知识图谱"""
        title = news["title"]
        source = news.get("source", "未知")
        event_type = core_info["event_type"]
        subject = core_info["event_subject"]
        impact = core_info["impact_scope"]
        stocks = core_info.get("potential_stocks", [])
        confidence = chan_analysis.get("confidence_score", 30)

        # 节点1: 产业
        industry_id = self._get_or_create_node(industry, "industry", industry,
                                               {"category": "十五五重点产业"})

        # 节点2: 事件主体
        if subject and subject != "行业相关主体":
            subject_id = self._get_or_create_node(subject, "subject", industry,
                                                  {"source": source})
            self._add_edge(industry_id, subject_id, "涉及主体", 1.0)

        # 节点3: 新闻事件节点（以标题hash为唯一标识，避免重复）
        title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
        event_id = self._get_or_create_node(f"{title}({title_hash})", "news_event", industry,
                                            {
                                                "title": title,
                                                "url": news.get("url", ""),
                                                "source": source,
                                                "event_type": event_type,
                                                "impact_scope": impact,
                                                "time_sensitivity": core_info.get("time_sensitivity", ""),
                                                "chan_confidence": confidence,
                                                "has_reverse_signal": reverse_signal.get("has_reverse_signal", False),
                                                "risk_level": reverse_signal.get("risk_level", "低")
                                            })
        self._add_edge(industry_id, event_id, "出现事件", 1.0)

        # 节点4: 关联股票
        for stock in stocks:
            stock_id = self._get_or_create_node(stock, "stock", industry,
                                                {"source": source})
            self._add_edge(event_id, stock_id, "关联股票",
                           0.8 if not reverse_signal.get("has_reverse_signal", False) else 0.3)

        # 节点5: 事件类型（政策发布、技术突破等）
        if event_type:
            etype_id = self._get_or_create_node(event_type, "event_type", industry)
            self._add_edge(event_id, etype_id, "属于事件类型", 1.0)

        # 节点6: 影响范围
        if impact:
            impact_id = self._get_or_create_node(impact, "impact_level")
            self._add_edge(event_id, impact_id, "影响等级",
                           1.5 if impact == "国家级/全球性" else 1.0)

    def export_graph(self, date_str):
        """导出知识图谱为 JSON 文件"""
        return {
            "metadata": {
                "date": date_str,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "v7.0",
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges)
            },
            "nodes": self.nodes,
            "edges": self.edges,
            "node_type_stats": dict(Counter(n["type"] for n in self.nodes)),
            "industry_stats": dict(Counter(n["industry"] for n in self.nodes if n["industry"]))
        }


# ============================================================
# 【主 orchestrator】每日科技资讯系统 v7
# ============================================================
class DailyTechIntelSystemV7:
    """每日科技前沿资讯分析系统 v7.0 - orchestrator"""

    def __init__(self, session_label="下午"):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.time_str = datetime.now().strftime("%H:%M:%S")
        self.date_time_str = f"{self.date_str} {self.time_str}"
        self.session_label = session_label  # 上午 / 下午
        self.news_data = {}
        self.analyzed_data = {}

        self.fetcher = MultiSourceNewsFetcher()
        self.reverse_analyzer = ReverseSignalAnalyzer()
        self.reliability_analyzer = ReliabilityAnalyzer()
        self.core_extractor = CoreInfoExtractor()
        self.chan_analyzer = ChanTheoryAnalyzer()
        self.graph_builder = KnowledgeGraphBuilder()

    # --------------------- 流程 1: 爬取 ---------------------
    def crawl_all_news(self):
        print("=" * 80)
        print(f"🚀 每日科技前沿资讯分析系统 v7.0 启动【{self.session_label}】")
        print("=" * 80)
        print(f"执行时间: {self.date_time_str}")
        print()

        all_keywords = []
        for ind, kws in FIFTEEN_FIVE_INDUSTRIES.items():
            all_keywords.append(ind)
            all_keywords.extend(kws)
        all_keywords = list(set(all_keywords))

        for industry, kws in FIFTEEN_FIVE_INDUSTRIES.items():
            print(f"📡 【{industry}】")
            industry_kws = [industry] + list(kws)
            news = self.fetcher.search_news_for_industry(industry, industry_kws, all_keywords)

            # 按来源可靠性排序
            def _reliability(n):
                src = n.get("source", "")
                if any(s in src for s in ["政府", "证监", "国务院", "工信部", "科技部", "发改委", "央视", "新华", "人民"]):
                    return 3
                elif any(s in src for s in ["证券", "财经", "证券报", "时报", "中证", "联社", "日报"]):
                    return 2
                elif any(s in src for s in ["36氪", "虎嗅", "第一"]):
                    return 1
                return 0

            news.sort(key=lambda x: -_reliability(x))
            self.news_data[industry] = news
            print(f"   ✓ 共 {len(news)} 条")
            print()

        return self.news_data

    # --------------------- 流程 2: 分析 ---------------------
    def analyze_all_news(self):
        print("🔍 正在分析每条资讯...")
        self.analyzed_data = {}

        for industry, news_list in self.news_data.items():
            analyzed_list = []
            for news in news_list:
                title = news["title"]
                snippet = news.get("snippet", "")
                source = news.get("source", "")
                url = news.get("url", "")

                core_info = self.core_extractor.extract(news, industry)
                reverse_signal = self.reverse_analyzer.analyze(title, snippet, source, url)
                reliability = self.reliability_analyzer.analyze(news)
                chan = self.chan_analyzer.analyze(title, snippet, core_info)

                analyzed_list.append({
                    "news": news,
                    "core_info": core_info,
                    "reverse_signal": reverse_signal,
                    "reliability": reliability,
                    "chan_analysis": chan
                })

                # 添加到知识图谱
                self.graph_builder.add_news_item(industry, news, core_info, chan, reverse_signal)

            # 排序：正常资讯在前，按缠论置信度降序
            analyzed_list.sort(key=lambda x: (
                1 if x["reverse_signal"]["has_reverse_signal"] else 0,
                -x["chan_analysis"]["confidence_score"],
                -x["reliability"]["score"]
            ))
            self.analyzed_data[industry] = analyzed_list

        total = sum(len(v) for v in self.analyzed_data.values())
        print(f"   ✓ 已分析 {total} 条资讯")
        return self.analyzed_data

    # --------------------- 流程 3: 生成报告 ---------------------
    def generate_report(self):
        print("📝 正在生成分析报告...")

        report = f"# 📊 {self.date_str}【{self.session_label}】科技前沿资讯分析报告\n\n"
        report += f"> 📅 生成时间: {self.date_time_str}  \n"
        report += f"> 🏷️ 版本: v7.0（增强版 | 十五五规划重点产业跟踪）\n"
        report += f"> 🔁 每日两次更新：上午9:30 & 下午14:30\n\n"
        report += "---\n\n"

        report += self._section_summary()
        report += self._section_industries()
        report += self._section_reverse_signal()
        report += self._section_chan()
        report += self._section_knowledge()

        report += "---\n"
        report += f"*本报告由每日科技资讯分析系统 v7.0 自动生成 | 数据来源: 证券时报、中国证券报、财联社、第一财经、新华网、央视新闻等公开渠道*\n"
        report += "*⚠️ 报告内容仅供参考，不构成投资建议。股市有风险，投资需谨慎。*\n"

        return report

    def _section_summary(self):
        total_news = sum(len(v) for v in self.news_data.values())
        normal = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if not item["reverse_signal"]["has_reverse_signal"]
        )
        reverse = total_news - normal
        high_impact = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if item["core_info"]["impact_scope"] in ["国家级/全球性", "行业级"]
        )
        high_chan = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if item["chan_analysis"]["confidence_score"] >= 50
        )
        high_rel = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if item["reliability"]["is_reliable"]
        )

        return f"""## 📌 报告摘要

| 指标 | 数值 |
|------|------|
| 📰 爬取资讯总数 | {total_news} |
| ✅ 正常资讯 | {normal} |
| ⚠️ 反向信号（疑似标题党/枪手） | {reverse} |
| 🎯 高影响力资讯 | {high_impact} |
| 📈 缠论高置信信号(≥50%) | {high_chan} |
| 🔒 可靠来源资讯 | {high_rel} |

**执行时间**: {self.date_time_str}
**本次会话**: {self.session_label}（14:30 午间盘面更新 + 下午资讯整合）

"""

    def _section_industries(self):
        section = "## 📋 十五五规划相关产业动态\n\n"
        industries_with_news = [(ind, lst) for ind, lst in self.analyzed_data.items() if lst]

        if not industries_with_news:
            section += "> ⚠️ 本次爬取未获取到相关资讯，请稍候再试。\n\n"
            return section

        industries_with_news.sort(key=lambda x: -len(x[1]))

        for industry, news_list in industries_with_news:
            section += f"### 🔬 {industry}（共{len(news_list)}条）\n\n"
            display_count = min(6, len(news_list))
            for i, item in enumerate(news_list[:display_count], 1):
                news = item["news"]
                core = item["core_info"]
                reverse = item["reverse_signal"]
                chan = item["chan_analysis"]
                rel = item["reliability"]

                if reverse["has_reverse_signal"]:
                    risk_tag = " 🔴" if reverse["risk_level"] == "高" else " 🟠"
                else:
                    risk_tag = " 🟢"

                section += f"**{i}. {news['title']}**{risk_tag}\n\n"
                section += f"   - **来源**: {news.get('source', '未知')}（可靠度: {rel['score']}%）| **事件**: {core['event_type']} | **影响**: {core['impact_scope']}\n"

                buy_points = []
                if chan["buy_points"]["first"]:
                    buy_points.append("一买")
                if chan["buy_points"]["second"]:
                    buy_points.append("二买")
                if chan["buy_points"]["third"]:
                    buy_points.append("三买")

                if buy_points:
                    bp_str = "、".join(buy_points)
                    section += f"   - **缠论**: 🟢 {bp_str}信号（置信{chan['confidence_score']}%）| 中枢: {chan['pivot_type']} | {chan['trend_judgment']}\n"
                else:
                    section += f"   - **缠论**: ⚪ 无明确信号（置信{chan['confidence_score']}%）| {chan['trend_judgment']}\n"

                if core["potential_stocks"]:
                    section += f"   - **关联股票**: {'、'.join(core['potential_stocks'])}\n"

                if reverse["has_reverse_signal"]:
                    section += f"   - **⚠️ 风险**: {reverse['risk_level']}级 | 关键词: {', '.join(reverse['signal_words'][:5])}\n"
                    section += f"   - **💡 建议**: {reverse['suggestion']}\n"

                if news.get("url") and news["url"].startswith("http"):
                    section += f"   - **原文链接**: {news['url']}\n"

                section += "\n"

            if len(news_list) > display_count:
                remaining = len(news_list) - display_count
                section += f"*（还有 {remaining} 条资讯，详见 JSON 数据文件）*\n\n"

            section += "\n"
        return section

    def _section_reverse_signal(self):
        all_reverse = []
        for industry, news_list in self.analyzed_data.items():
            for item in news_list:
                if item["reverse_signal"]["has_reverse_signal"]:
                    item_copy = dict(item)
                    item_copy["industry"] = industry
                    all_reverse.append(item_copy)

        if not all_reverse:
            return "## ✅ 反向信号检测\n\n本次未检测到明显的标题党或资本雇佣枪手发文，资讯质量较好。\n\n"

        section = f"## ⚠️ 反向信号预警（共{len(all_reverse)}条）\n\n"
        section += "> **⚠️ 重要提示**: 以下资讯存在标题党或诱导性特征，疑似资本雇佣枪手发文，请务必反向思考！\n\n"

        all_reverse.sort(key=lambda x: -x["reverse_signal"]["signal_score"])
        for i, item in enumerate(all_reverse[:10], 1):
            news = item["news"]
            reverse = item["reverse_signal"]
            industry = item["industry"]

            risk_icon = "🔴" if reverse["risk_level"] == "高" else "🟠"

            section += f"**{i}. {risk_icon} [{industry}] {news['title']}**\n\n"
            section += f"   - **风险评分**: {reverse['signal_score']}分 | **风险等级**: {reverse['risk_level']}级\n"
            if reverse["signal_words"]:
                section += f"   - **风险关键词**: {', '.join(reverse['signal_words'][:6])}\n"
            if reverse["title_party_pattern"]:
                section += f"   - **标题党模式**: {', '.join(reverse['title_party_pattern'])}\n"
            if reverse["gunman_pattern"]:
                section += f"   - **枪手特征模式**: {', '.join(reverse['gunman_pattern'])}\n"
            if reverse["analysis"]:
                section += f"   - **综合分析**: {reverse['analysis']}\n"
            section += f"   - **💡 操作建议**: {reverse['suggestion']}\n"
            if news.get("url") and news["url"].startswith("http"):
                section += f"   - **来源**: {news.get('source', '未知')} | 查看原文: {news['url']}\n"
            section += "\n"

        # 总结：标题党/枪手识别原理
        section += "### 🔬 反向信号识别原理\n\n"
        section += "本系统通过以下维度综合判断是否为标题党或资本雇佣枪手发文：\n\n"
        section += "1. **情绪词检测**: 极端词汇（暴涨、暴跌、逆天等）、内幕词汇（独家、重磅、揭秘等）、操作词汇（抄底、上车、梭哈等）\n"
        section += "2. **夸张数字检测**: 出现\"暴涨XX倍\"、\"暴增XX亿\"等诱导性数字\n"
        section += "3. **标点模式识别**: 多感叹号、感叹号开头、多问号等\n"
        section += "4. **开头模式识别**: \"震惊！\"、\"刚刚\"、\"重磅！\"等典型标题党开头\n"
        section += "5. **引导语句识别**: \"手把手教你\"、\"一定要看\"、\"最后的机会\"等\n"
        section += "6. **来源可靠性**: 域名是否在官方媒体/权威财经白名单\n"
        section += "7. **综合评分**: 总分≥10判定为高风险（疑似枪手），≥6为中风险（标题党）\n\n"
        return section

    def _section_chan(self):
        first_buy = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if item["chan_analysis"]["buy_points"]["first"]
        )
        second_buy = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if item["chan_analysis"]["buy_points"]["second"]
        )
        third_buy = sum(
            1 for lst in self.analyzed_data.values()
            for item in lst if item["chan_analysis"]["buy_points"]["third"]
        )

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
| 🟢 第一类买点 | {first_buy} | 政策发布、技术突破带来的驱动型机会（行业政策底） |
| 🟢 第二类买点 | {second_buy} | 回调确认后的安全介入点（不创新低的回踩确认） |
| 🟢 第三类买点 | {third_buy} | 趋势确立后的加速机会（离开中枢不回抽，需警惕情绪过热） |

### 今日高置信信号（缠论置信度≥50%）

"""

        if high_confidence_items:
            for i, item in enumerate(high_confidence_items[:10], 1):
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
                section += f"   - 中枢类型: {chan['pivot_type']} | 走势判断: {chan['trend_judgment']}\n"
                section += f"   - 操作建议: {chan['operation_suggestion']}\n\n"
        else:
            section += "*本次暂无高置信度缠论信号，建议保持观望，等待更明确的市场信号。*\n\n"

        section += """### 综合策略建议

1. **仓位管理**: 结合当前市场情绪，建议总仓位控制在 30%-60%，避免情绪化追涨
2. **选股方向**: 重点关注 人工智能、半导体、新能源、数字经济 等十五五重点赛道
3. **入场时机**: 等待明确的回调确认信号（日线级别的二买/三买），不要追高买入
4. **止损设置**: 单只股票亏损幅度建议不超过 5%-8%，严格执行止损纪律
5. **风险控制**: 当反向信号密集出现时，需警惕情绪过热，考虑减仓或观望
6. **【14:30 特别提示】**: 下午时段需特别警惕自媒体炒作，关注正规媒体下午更新的权威资讯

### 缠论核心原理简述

- **第一类买点**: 由下跌趋势背离产生，通常出现在政策底或业绩底（"政策底-市场底-业绩底"三部曲）
- **第二类买点**: 不创新低的回调确认点，安全性较高，是主要的介入位置
- **第三类买点**: 离开中枢后的不回抽确认点，属于趋势延续信号，风险也较高
- **关键原则**: "买点买，卖点卖"，严格按照级别操作，避免频繁交易
- **核心逻辑**: 走势终完美 —— 任何级别的走势类型终将完成，完成后必然转化为其他类型

"""
        return section

    def _section_knowledge(self):
        section = """## 🧠 知识沉淀与持续跟踪

### 今日核心知识点（高影响力资讯）

"""

        high_impact_items = []
        for industry, news_list in self.analyzed_data.items():
            for item in news_list:
                if item["core_info"]["impact_scope"] in ["国家级/全球性", "行业级"] and not item["reverse_signal"]["has_reverse_signal"]:
                    item["industry"] = industry
                    high_impact_items.append(item)

        if high_impact_items:
            for i, item in enumerate(high_impact_items[:6], 1):
                news = item["news"]
                core = item["core_info"]
                section += f"{i}. **[{core['industry']}] {news['title']}**\n"
                section += f"   - 事件类型: {core['event_type']} | 影响范围: {core['impact_scope']} | 时间敏感度: {core['time_sensitivity']}\n"
                section += f"   - 主体: {core['event_subject']}\n"
                if core["potential_stocks"]:
                    section += f"   - 关联股票: {'、'.join(core['potential_stocks'])}\n"
                section += "\n"
        else:
            section += "*本次暂无高影响力政策或行业资讯。*\n\n"

        # 产业热度统计
        section += "### 📊 本次产业热度排行\n\n"
        heat_data = [(ind, len(lst)) for ind, lst in self.analyzed_data.items() if lst]
        heat_data.sort(key=lambda x: -x[1])
        for rank, (ind, count) in enumerate(heat_data[:10], 1):
            bar = "█" * min(count, 20)
            section += f"{rank}. {ind:<10} {bar} {count}条\n"
        section += "\n"

        section += """### 🔭 持续关注方向

1. **政策面**: 十五五规划重点产业的后续政策落地、细化方案、资金支持
2. **技术面**: 人工智能、半导体、新能源领域的技术突破和商业化进展
3. **基本面**: 行业龙头的业绩、订单、产能扩张情况
4. **情绪面**: 警惕自媒体标题党和资本雇佣枪手的反向信号
5. **国际面**: 关注全球产业链变化、地缘政治对科技产业的影响

### ⚠️ 风险提示清单

- ⚠️ 单一资讯不足以作为投资决策依据，需多方验证
- ⚠️ 标题党资讯（暴涨、翻倍、内幕等）需反向思考（利好出尽是利空）
- ⚠️ 政策利好可能已被市场提前消化（买预期卖事实）
- ⚠️ 技术突破到商业化落地可能存在较长时间差（注意产业链兑现节奏）
- ⚠️ 热门板块容易出现情绪过热后的回调（情绪高位风险）
- ⚠️ 【特别警示】下午14:30-15:00是A股T+1交易机制下的尾盘博弈时段，需特别警惕自媒体和资金联手营造的虚假繁荣

### 📜 缠论操作口诀

1. 买点买，卖点卖，纪律第一
2. 看大做小，长短线结合
3. 级别递归，走势分解
4. 中枢震荡做短差，趋势持有
5. 严格止损，控制仓位

"""
        return section

    # --------------------- 流程 4: 保存结果 ---------------------
    def save_results(self, report):
        print("💾 正在保存结果...")

        # 1. Markdown 报告
        report_file = REPORT_DIR / f"{self.date_str}_{self.session_label}_tech_intel_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📁 分析报告: {report_file}")

        # 2. JSON 原始数据
        data_file = REPORT_DIR / f"{self.date_str}_{self.session_label}_tech_intel_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date": self.date_str,
                "datetime": self.date_time_str,
                "session": self.session_label,
                "version": "v7.0",
                "news_data": self.news_data,
                "analyzed_data": self.analyzed_data
            }, f, ensure_ascii=False, indent=2)
        print(f"📁 分析数据: {data_file}")

        # 3. 知识图谱 JSON
        graph_data = self.graph_builder.export_graph(self.date_str)
        graph_file = GRAPH_DIR / f"{self.date_str}_{self.session_label}_knowledge_graph.json"
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        print(f"📁 知识图谱: {graph_file}（{graph_data['metadata']['total_nodes']} 节点, {graph_data['metadata']['total_edges']} 边）")

        # 4. 追加到历史知识库
        knowledge_file = KNOWLEDGE_BASE_DIR / "tech_intel_history.md"
        knowledge_entry = f"\n\n---\n\n## {self.date_str}【{self.session_label}】（v7.0）\n{report[:1500]}...\n"
        if knowledge_file.exists():
            with open(knowledge_file, 'a', encoding='utf-8') as f:
                f.write(knowledge_entry)
        else:
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                f.write("# 科技资讯知识沉淀库\n" + knowledge_entry)
        print(f"📚 知识库追加: {knowledge_file}")

        return report_file, data_file, graph_file

    # --------------------- 主入口 ---------------------
    def run(self):
        print("📡 开始爬取资讯...")
        self.crawl_all_news()

        total = sum(len(v) for v in self.news_data.values())
        print(f"\n📊 共获取 {total} 条资讯")

        if total == 0:
            print("\n⚠️ 未获取到任何资讯，将生成空报告。")
        else:
            print("\n🔍 开始分析资讯...")
            self.analyze_all_news()

        print("\n📝 生成分析报告...")
        report = self.generate_report()

        print("\n💾 保存结果...")
        self.save_results(report)

        print("\n" + "=" * 80)
        print("✅ 分析完成！")
        print("=" * 80)

        return report


# ============================================================
# 命令行入口
# ============================================================
def main():
    # 判断当前时段（上午/下午）
    now = datetime.now()
    hour = now.hour
    session = "上午" if hour < 12 else "下午"

    # 支持命令行参数指定 session
    if len(sys.argv) >= 2:
        if "morning" in sys.argv[1] or "上午" in sys.argv[1]:
            session = "上午"
        elif "afternoon" in sys.argv[1] or "下午" in sys.argv[1]:
            session = "下午"

    system = DailyTechIntelSystemV7(session_label=session)
    system.run()


if __name__ == '__main__':
    main()
