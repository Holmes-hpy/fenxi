#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年6月2日收盘后数据收集脚本 - 获取今日完整行情数据
"""

import sys
sys.path.insert(0, '/Users/houpengyuan/Documents/trae_projects/a-stock-data')

from a_stock_data_core import (
    get_market_index,
    industry_comparison,
    get_northbound_flow,
    get_dragon_tiger_board,
    get_stock_quote,
    get_stock_news,
    ths_hot_reason
)
import json
from datetime import datetime

def collect_market_data():
    """收集今日市场数据"""
    print("="*70)
    print("📊 2026年6月2日收盘后数据收集")
    print("="*70)
    print(f"收集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}