#!/usr/bin/env python3
"""
量化策略回测执行脚本
使用真实历史数据验证策略
创建时间：2026-05-26
"""

import sys
from pathlib import Path
from datetime import datetime

# 导入回测模块
sys.path.insert(0, str(Path(__file__).parent))
from quant_backtest import (
    calculate_all_indicators,
    StrategyMaMacd,
    StrategyBollingerRsi,
    analyze_backtest_result,
    generate_backtest_report,
    get_historical_k_data
)


def backtest_ma_macd(stock_code, stock_name, initial_cash=20000.0, days=120):
    """双均线+MACD策略回测"""
    print(f"\n{'='*60}")
    print(f"策略: 双均线+MACD")
    print(f"股票: {stock_name} ({stock_code})")
    print(f"初始资金: {initial_cash}")
    print(f"回测天数: {days}")
    print("="*60)
    
    # 获取数据
    print(f"正在获取历史数据...")
    raw_data = get_historical_k_data(stock_code, 'daily', days)
    
    if len(raw_data) == 0:
        print("获取数据失败！")
        return None
    
    print(f"历史数据长度: {len(raw_data)} 个交易日")
    
    # 计算指标
    print("正在计算技术指标...")
    data = calculate_all_indicators(raw_data)
    
    # 运行回测
    print("正在执行回测...")
    strategy = StrategyMaMacd(initial_cash)
    result = strategy.run_backtest(data, stock_code)
    
    # 分析结果
    analysis = analyze_backtest_result(result, initial_cash)
    
    # 生成报告
    print("\n" + "="*60)
    print("回测结果")
    print("="*60)
    
    if analysis is not None:
        print(f"初始资金: {initial_cash:.0f}")
        print(f"最终资金: {analysis['final_value']:.2f}")
        print(f"总收益率: {analysis['total_return_pct']:.2f}%")
        print(f"最大回撤: {analysis['max_drawdown_pct']:.2f}%")
        print(f"交易次数: {analysis['trade_count']}")
    
    print("\n" + "="*60)
    print("交易记录")
    print("="*60)
    for i, trade in enumerate(result.trades):
        print(f"{i+1}. {trade['date']} {trade['type']} @ {trade['price']:.2f} x {trade['shares']}")
    
    print("\n" + "="*60)
    
    return result, analysis


def backtest_boll_rsi(stock_code, stock_name, initial_cash=20000.0, days=120):
    """布林带RSI策略回测"""
    print(f"\n{'='*60}")
    print(f"策略: 布林带RSI")
    print(f"股票: {stock_name} ({stock_code})")
    print(f"初始资金: {initial_cash}")
    print(f"回测天数: {days}")
    print("="*60)
    
    # 获取数据
    print(f"正在获取历史数据...")
    raw_data = get_historical_k_data(stock_code, 'daily', days)
    
    if len(raw_data) == 0:
        print("获取数据失败！")
        return None
    
    print(f"历史数据长度: {len(raw_data)} 个交易日")
    
    # 计算指标
    print("正在计算技术指标...")
    data = calculate_all_indicators(raw_data)
    
    # 运行回测
    print("正在执行回测...")
    strategy = StrategyBollingerRsi(initial_cash)
    result = strategy.run_backtest(data, stock_code)
    
    # 分析结果
    analysis = analyze_backtest_result(result, initial_cash)
    
    # 生成报告
    print("\n" + "="*60)
    print("回测结果")
    print("="*60)
    
    if analysis is not None:
        print(f"初始资金: {initial_cash:.0f}")
        print(f"最终资金: {analysis['final_value']:.2f}")
        print(f"总收益率: {analysis['total_return_pct']:.2f}%")
        print(f"最大回撤: {analysis['max_drawdown_pct']:.2f}%")
        print(f"交易次数: {analysis['trade_count']}")
    
    print("\n" + "="*60)
    print("交易记录")
    print("="*60)
    for i, trade in enumerate(result.trades):
        print(f"{i+1}. {trade['date']} {trade['type']} @ {trade['price']:.2f} x {trade['shares']}")
    
    print("\n" + "="*60)
    
    return result, analysis


def main():
    print("="*60)
    print("量化策略回测系统")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试股票列表
    test_stocks = [
        ('600036', '招商银行'),
        ('000001', '平安银行'),
        ('600900', '长江电力'),
        ('600584', '长电科技'),
    ]
    
    initial_cash = 20000.0
    days = 120  # 约半年数据
    
    results = {}
    
    for stock_code, stock_name in test_stocks:
        print(f"\n{'='*60}")
        print(f"开始回测 {stock_name} ({stock_code})")
        print("="*60)
        
        # 策略1: 双均线+MACD
        print(f"\n{'='*60}")
        print("【策略1】双均线+MACD")
        print("="*60)
        try:
            result1, analysis1 = backtest_ma_macd(stock_code, stock_name, initial_cash, days)
            if analysis1 is not None:
                results[(stock_code, 'ma_macd')] = analysis1
        except Exception as e:
            print(f"回测出错: {str(e)}")
        
        # 策略2: 布林带RSI
        print(f"\n{'='*60}")
        print("【策略2】布林带RSI")
        print("="*60)
        try:
            result2, analysis2 = backtest_boll_rsi(stock_code, stock_name, initial_cash, days)
            if analysis2 is not None:
                results[(stock_code, 'boll_rsi')] = analysis2
        except Exception as e:
            print(f"回测出错: {str(e)}")
    
    # 生成汇总报告
    print(f"\n{'='*60}")
    print("策略回测汇总")
    print("="*60)
    
    print(f"{'股票':10} {'策略':15} {'收益(%)':>10} {'最大回撤(%)':>15} {'交易次数':>10}")
    print("-"*60)
    
    for key, analysis in sorted(results.items()):
        stock_code, strategy_name = key
        stock_name = next((n for c, n in test_stocks if c == stock_code), stock_code)
        
        strat_display = {
            'ma_macd': '双均线+MACD',
            'boll_rsi': '布林带RSI',
        }.get(strategy_name, strategy_name)
        
        print(f"{stock_name:10} {strat_display:15} {analysis['total_return_pct']:10.2f} {analysis['max_drawdown_pct']:15.2f} {analysis['trade_count']:10}")
    
    print("-"*60)
    
    print("\n回测完成！")
    
    return results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n回测中断")
    except Exception as e:
        print(f"\n\n程序出错: {str(e)}")
        import traceback
        traceback.print_exc()
