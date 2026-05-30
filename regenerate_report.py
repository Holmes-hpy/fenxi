#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成今日报告，包含最新的准确度统计
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from stock_selection_system import StockSelectionSystem


def main():
    print("=" * 70)
    print("📊 重新生成今日选股报告")
    print("=" * 70)
    print()
    
    system = StockSelectionSystem()
    
    # 获取今日的选股和分析记录
    history = system._load_history()
    analyses = system._load_analyses()
    
    # 找到今日的记录
    today_date = datetime.now().strftime('%Y-%m-%d')
    selection = None
    analysis = None
    
    for s in reversed(history['selections']):
        if s['selection_date'] == today_date:
            selection = s
            break
    
    for a in reversed(analyses['analyses']):
        if a['analysis_date'] == today_date:
            analysis = a
            break
    
    if selection and analysis:
        # 重新生成报告
        report_file = system.generate_daily_selection_report(selection, analysis)
        
        print()
        print("=" * 70)
        print("✅ 报告重新生成完成！")
        print("=" * 70)
    else:
        print("⚠️ 未找到今日的选股或分析记录")


if __name__ == '__main__':
    main()
