#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务工具测试脚本 - 学习如何使用MCP服务
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_mcp import (
    get_research_reports,
    get_stock_news,
    get_industry_comparison,
    get_stock_basic_info,
    get_stock_quote,
    get_industry_rankings,
    get_ths_hot_stocks,
    get_stock_concept_blocks,
    get_cls_flash_news,
    get_announcements,
    get_quarterly_report
)

import json

def test_research_reports():
    """测试研报获取"""
    print("="*70)
    print("1. 测试 get_research_reports - 研报获取")
    print("="*70)
    try:
        # 测试获取彤程新材的研报
        result = get_research_reports("603650", 90)
        data = json.loads(result)
        if isinstance(data, list) and len(data) > 0:
            print(f"✓ 成功获取 {len(data)} 份研报")
            print("\n前3份研报摘要:")
            for i, report in enumerate(data[:3]):
                print(f"\n  研报{i+1}:")
                print(f"    标题: {report.get('title', 'N/A')[:50]}...")
                print(f"    机构: {report.get('orgSName', 'N/A')}")
                print(f"    日期: {report.get('publishDate', 'N/A')[:10]}")
                print(f"    评级: {report.get('emRatingName', 'N/A')}")
                if 'predictThisYearEps' in report:
                    print(f"    今年EPS预测: {report.get('predictThisYearEps', 'N/A')}")
                if 'predictNextYearEps' in report:
                    print(f"    明年EPS预测: {report.get('predictNextYearEps', 'N/A')}")
        else:
            print("⚠️ 未获取到研报数据")
    except Exception as e:
        print(f"❌ 获取研报失败: {e}")
    print()

def test_stock_news():
    """测试新闻获取"""
    print("="*70)
    print("2. 测试 get_stock_news - 新闻获取")
    print("="*70)
    try:
        # 测试获取彤程新材的新闻
        result = get_stock_news("603650", 30)
        data = json.loads(result)
        if isinstance(data, list) and len(data) > 0:
            print(f"✓ 成功获取 {len(data)} 条新闻")
            print("\n前5条新闻:")
            for i, news in enumerate(data[:5]):
                print(f"\n  新闻{i+1}:")
                print(f"    标题: {news.get('title', 'N/A')[:50]}...")
                print(f"    来源: {news.get('source', 'N/A')}")
                print(f"    时间: {news.get('publish_time', 'N/A')[:10]}")
        else:
            print("⚠️ 未获取到新闻数据")
    except Exception as e:
        print(f"❌ 获取新闻失败: {e}")
    print()

def test_industry_comparison():
    """测试行业对比"""
    print("="*70)
    print("3. 测试 get_industry_comparison - 行业对比")
    print("="*70)
    try:
        # 对比半导体龙头
        stocks = ["603650", "300346", "688012", "002371"]
        result = get_industry_comparison(stocks)
        data = json.loads(result)
        if isinstance(data, dict) and len(data) > 0:
            print(f"✓ 成功获取 {len(data)} 只股票数据")
            print("\n股票估值对比:")
            for code, info in data.items():
                print(f"\n  {info.get('name', 'N/A')}({code}):")
                print(f"    价格: {info.get('price', 0)}元")
                print(f"    涨跌: {info.get('change_pct', 0)}%")
                print(f"    PE(TTM): {info.get('pe_ttm', 0)}")
                print(f"    PE(静): {info.get('pe_static', 0)}")
                print(f"    PB: {info.get('pb', 0)}")
                print(f"    市值: {info.get('mcap_yi', 0)}亿元")
        else:
            print("⚠️ 未获取到行业数据")
    except Exception as e:
        print(f"❌ 获取行业数据失败: {e}")
    print()

def test_stock_basic_info():
    """测试基本面信息"""
    print("="*70)
    print("4. 测试 get_stock_basic_info - 基本面信息")
    print("="*70)
    try:
        result = get_stock_basic_info("603650")
        data = json.loads(result)
        if isinstance(data, dict) and len(data) > 0:
            print(f"✓ 成功获取基本面信息")
            print(f"\n彤程新材基本面:")
            for key, value in data.items():
                if value and value != 0:
                    print(f"  {key}: {value}")
        else:
            print("⚠️ 未获取到基本面数据")
    except Exception as e:
        print(f"❌ 获取基本面失败: {e}")
    print()

def test_industry_rankings():
    """测试行业排名"""
    print("="*70)
    print("5. 测试 get_industry_rankings - 行业排名")
    print("="*70)
    try:
        result = get_industry_rankings()
        data = json.loads(result)
        if isinstance(data, dict) and len(data) > 0:
            print(f"✓ 成功获取行业排名")
            if 'top' in data:
                print(f"\n涨幅前5行业:")
                for i, ind in enumerate(data['top'][:5]):
                    print(f"  {i+1}. {ind.get('name', 'N/A')}: {ind.get('change_pct', 0)}%")
            if 'bottom' in data:
                print(f"\n跌幅前5行业:")
                for i, ind in enumerate(data['bottom'][:5]):
                    print(f"  {i+1}. {ind.get('name', 'N/A')}: {ind.get('change_pct', 0)}%")
        else:
            print("⚠️ 未获取到行业排名")
    except Exception as e:
        print(f"❌ 获取行业排名失败: {e}")
    print()

def test_ths_hot_stocks():
    """测试热点股票"""
    print("="*70)
    print("6. 测试 get_ths_hot_stocks - 热点股票")
    print("="*70)
    try:
        result = get_ths_hot_stocks()
        data = json.loads(result)
        if isinstance(data, dict) and '名称' in str(data):
            print(f"✓ 成功获取热点股票")
            # 转换为DataFrame
            import pandas as pd
            if '名称' in data:
                df = pd.DataFrame([data])
            else:
                df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            if not df.empty and '名称' in df.columns:
                print(f"\n前10只热点股票:")
                print(df[['代码', '名称', '涨幅%', '题材归因']].head(10).to_string(index=False))
        else:
            print("⚠️ 未获取到热点股票数据")
    except Exception as e:
        print(f"❌ 获取热点股票失败: {e}")
    print()

def test_stock_concept_blocks():
    """测试概念板块"""
    print("="*70)
    print("7. 测试 get_stock_concept_blocks - 概念板块")
    print("="*70)
    try:
        # 测试彤程新材的概念板块
        result = get_stock_concept_blocks("603650")
        data = json.loads(result)
        if isinstance(data, dict) and len(data) > 0:
            print(f"✓ 成功获取概念板块")
            print(f"\n彤程新材概念板块:")
            if 'industry' in data:
                print(f"  行业: {[b['name'] for b in data['industry']]}")
            if 'concept' in data:
                print(f"  概念: {data['concept_tags']}")
            if 'region' in data:
                print(f"  地域: {[b['name'] for b in data['region']]}")
        else:
            print("⚠️ 未获取到概念板块")
    except Exception as e:
        print(f"❌ 获取概念板块失败: {e}")
    print()

def test_cls_flash_news():
    """测试财联社快讯"""
    print("="*70)
    print("8. 测试 get_cls_flash_news - 财联社快讯")
    print("="*70)
    try:
        result = get_cls_flash_news()
        data = json.loads(result)
        if isinstance(data, list) and len(data) > 0:
            print(f"✓ 成功获取 {len(data)} 条财联社快讯")
            print("\n前5条快讯:")
            for i, news in enumerate(data[:5]):
                print(f"\n  快讯{i+1}:")
                print(f"    内容: {news.get('content', news.get('title', 'N/A'))[:80]}...")
        else:
            print("⚠️ 未获取到财联社快讯")
    except Exception as e:
        print(f"❌ 获取财联社快讯失败: {e}")
    print()

def test_announcements():
    """测试公告"""
    print("="*70)
    print("9. 测试 get_announcements - 公告")
    print("="*70)
    try:
        # 测试彤程新材的公告
        result = get_announcements("603650", 30)
        data = json.loads(result)
        if isinstance(data, list) and len(data) > 0:
            print(f"✓ 成功获取 {len(data)} 条公告")
            print("\n前5条公告:")
            for i, ann in enumerate(data[:5]):
                print(f"\n  公告{i+1}:")
                print(f"    标题: {ann.get('announcementTitle', ann.get('title', 'N/A'))[:50]}...")
                print(f"    时间: {str(ann.get('announcementTime', ann.get('publish_time', 'N/A')))[:10]}")
        else:
            print("⚠️ 未获取到公告")
    except Exception as e:
        print(f"❌ 获取公告失败: {e}")
    print()

def main():
    """主函数 - 测试所有MCP工具"""
    print("="*70)
    print("🔬 MCP服务工具学习与测试")
    print("="*70)
    print()

    test_research_reports()
    test_stock_news()
    test_industry_comparison()
    test_stock_basic_info()
    test_industry_rankings()
    test_ths_hot_stocks()
    test_stock_concept_blocks()
    test_cls_flash_news()
    test_announcements()

    print("="*70)
    print("✅ MCP服务工具测试完成！")
    print("="*70)
    print()
    print("📚 已掌握的MCP服务能力：")
    print("   1. ✅ get_research_reports - 获取研报和一致预期EPS")
    print("   2. ✅ get_stock_news - 获取个股新闻")
    print("   3. ✅ get_industry_comparison - 多股票估值对比")
    print("   4. ✅ get_stock_basic_info - 获取基本面信息")
    print("   5. ✅ get_industry_rankings - 获取行业涨跌幅排名")
    print("   6. ✅ get_ths_hot_stocks - 获取热点题材股票")
    print("   7. ✅ get_stock_concept_blocks - 获取概念板块归属")
    print("   8. ✅ get_cls_flash_news - 获取财联社快讯")
    print("   9. ✅ get_announcements - 获取个股公告")
    print()
    print("💡 以后将优先使用MCP服务获取数据，只有MCP无法满足时再使用互联网检索")

if __name__ == '__main__':
    main()