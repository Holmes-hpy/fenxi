#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证最近的选股预测
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from stock_selection_system import StockSelectionSystem


def main():
    print("=" * 70)
    print("🔍 验证最近未验证的选股预测")
    print("=" * 70)
    print()
    
    system = StockSelectionSystem()
    
    # 加载选股历史
    history = system._load_history()
    
    # 找到最近未验证的选股
    unverified = []
    for s in reversed(history['selections']):
        if 'result' not in s:
            unverified.append(s)
            if len(unverified) >= 3:  # 最多验证最近3个
                break
    
    if not unverified:
        print("✅ 没有需要验证的选股记录")
    else:
        print(f"📋 找到 {len(unverified)} 个未验证的选股记录：")
        for s in unverified:
            print(f"  - {s['stock_name']}({s['stock_code']}) @ {s['selection_date']}")
        
        print()
        
        # 验证每个未验证的记录
        for s in unverified:
            print(f"--- 验证 {s['stock_name']}({s['stock_code']}) ---")
            try:
                result = system.verify_prediction(s['stock_code'])
                if 'error' not in result:
                    print(f"  验证结果：{'正确 ✅' if result['result'] == 'correct' else '错误 ❌'}")
                    print(f"  实际涨跌：{result['actual_change_pct']:+.2f}%")
                else:
                    print(f"  验证失败：{result['error']}")
            except Exception as e:
                print(f"  验证出错：{e}")
            print()
    
    # 显示最新的准确度统计
    print("=" * 70)
    print("📊 最新准确度统计")
    print("=" * 70)
    stats = system.get_accuracy_stats()
    print(f"总预测次数：{stats['total_predictions']}")
    print(f"正确次数：{stats['correct_predictions']}")
    print(f"错误次数：{stats['incorrect_predictions']}")
    print(f"准确率：{stats['accuracy_rate']:.2f}%")
    print()
    print("=" * 70)
    print("✅ 验证流程完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
