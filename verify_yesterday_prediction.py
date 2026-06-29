#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证昨日预测
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from stock_selection_system import StockSelectionSystem


def main():
    print("=" * 70)
    print("🔍 验证昨日预测结果")
    print("=" * 70)
    print()
    
    system = StockSelectionSystem()
    
    # 验证宁德时代(300750)的预测结果
    stock_code = "300750"
    result = system.verify_prediction(stock_code)
    
    print()
    print("=" * 70)
    print("✅ 验证完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
