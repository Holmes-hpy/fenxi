#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证历史选股预测"""

import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from a_stock_data_core import get_historical_k_data


def main():
    selection_history = json.loads(Path('stock_selection_db/selection_history.json').read_text())
    analysis_records = json.loads(Path('stock_selection_db/analysis_records.json').read_text())

    print('=== 待验证选股列表 ===')
    print()

    unverified = []
    for s in selection_history['selections']:
        if 'result' not in s:
            analysis = None
            for a in reversed(analysis_records['analyses']):
                if a['stock_code'] == s['stock_code'] and a['analysis_date'] == s['selection_date']:
                    analysis = a
                    break
            if analysis and analysis['current_price'] > 0:
                unverified.append((s, analysis))

    print(f'共 {len(unverified)} 条有价格的待验证记录')
    print()

    print('=== 开始验证（使用历史K线数据） ===')
    print()

    verified_count = 0
    correct_count = 0

    for s, analysis in unverified:
        stock_code = s['stock_code']
        selection_date = s['selection_date']

        print(f'验证 {s["stock_name"]}({stock_code}) - {selection_date}')

        try:
            k_data = get_historical_k_data(stock_code, period='daily', days=90)

            if k_data.empty:
                print('  ⚠️ 无法获取K线数据')
                continue

            if 'date' not in k_data.columns:
                k_data['date'] = k_data.index

            k_data['date'] = pd.to_datetime(k_data['date'])
            selection_dt = pd.to_datetime(selection_date)

            after_selection = k_data[k_data['date'] > selection_dt].sort_values('date')

            if len(after_selection) == 0:
                print('  ⚠️ 暂无选股日后的数据')
                continue

            next_day = after_selection.iloc[0]
            next_day_price = next_day['close']
            prev_price = analysis['current_price'] if analysis['current_price'] > 0 else analysis['indicators']['price']

            actual_change = (next_day_price - prev_price) / prev_price * 100

            predicted_direction = analysis['prediction']['direction']
            if predicted_direction in ['上涨'] and actual_change > 0:
                result = 'correct'
            elif predicted_direction in ['下跌'] and actual_change < 0:
                result = 'correct'
            elif predicted_direction in ['震荡偏涨'] and actual_change > -1:
                result = 'correct'
            elif predicted_direction in ['震荡偏跌'] and actual_change < 1:
                result = 'correct'
            elif predicted_direction == '震荡' and abs(actual_change) < 2:
                result = 'correct'
            else:
                result = 'incorrect'

            print(f'  预测: {predicted_direction}')
            print(f'  次日({next_day["date"].strftime("%Y-%m-%d")})收盘价: {next_day_price:.2f} 元')
            print(f'  实际涨跌: {actual_change:+.2f}%')
            print(f'  结果: {"✅ 正确" if result == "correct" else "❌ 错误"}')
            print()

            s['result'] = result
            s['actual_price'] = next_day_price
            s['actual_change_pct'] = actual_change
            s['verified_date'] = datetime.now().strftime('%Y-%m-%d')

            verified_count += 1
            if result == 'correct':
                correct_count += 1

        except Exception as e:
            print(f'  ❌ 验证失败: {e}')
            import traceback
            traceback.print_exc()
            print()

    if verified_count > 0:
        Path('stock_selection_db/selection_history.json').write_text(
            json.dumps(selection_history, ensure_ascii=False, indent=2)
        )
        print(f'✅ 已验证 {verified_count} 条记录，其中正确 {correct_count} 条')
    else:
        print('⚠️ 没有成功验证任何记录')


if __name__ == '__main__':
    main()
