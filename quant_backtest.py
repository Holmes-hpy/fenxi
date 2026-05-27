"""
量化交易回测系统
基于 a_stock_data_core.py 模块构建
创建时间：2026-05-26
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

# 导入项目模块
import sys
sys.path.insert(0, str(Path(__file__).parent))
from a_stock_data_core import get_historical_k_data


# ================ 技术指标计算 ================

def calculate_ma(data, period):
    """计算移动平均线 (Moving Average)"""
    return data['close'].rolling(window=period).mean()


def calculate_ema(data, period):
    """计算指数移动平均线 (Exponential Moving Average)"""
    return data['close'].ewm(span=period, adjust=False).mean()


def calculate_macd(data, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    diff = ema_fast - ema_slow
    dea = diff.ewm(span=signal, adjust=False).mean()
    macd_hist = diff - dea
    return diff, dea, macd_hist


def calculate_rsi(data, period=14):
    """计算RSI指标"""
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(data, period=20, std_dev=2):
    """计算布林带"""
    sma = calculate_ma(data, period)
    std = data['close'].rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return sma, upper, lower


def calculate_kdj(data, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    low_list = data['low'].rolling(n).min()
    high_list = data['high'].rolling(n).max()
    
    rsv = (data['close'] - low_list) / (high_list - low_list) * 100
    
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def calculate_all_indicators(data):
    """计算所有常用技术指标"""
    result = data.copy()
    
    result['MA5'] = calculate_ma(result, 5)
    result['MA10'] = calculate_ma(result, 10)
    result['MA20'] = calculate_ma(result, 20)
    result['MA60'] = calculate_ma(result, 60)
    
    result['EMA12'] = calculate_ema(result, 12)
    result['EMA26'] = calculate_ema(result, 26)
    
    macd_diff, macd_dea, macd_hist = calculate_macd(result)
    result['MACD_DIF'] = macd_diff
    result['MACD_DEA'] = macd_dea
    result['MACD_HIST'] = macd_hist
    
    result['RSI'] = calculate_rsi(result)
    
    boll_mid, boll_upper, boll_lower = calculate_bollinger_bands(result)
    result['BOLL_MID'] = boll_mid
    result['BOLL_UPPER'] = boll_upper
    result['BOLL_LOWER'] = boll_lower
    
    kdj_k, kdj_d, kdj_j = calculate_kdj(result)
    result['KDJ_K'] = kdj_k
    result['KDJ_D'] = kdj_d
    result['KDJ_J'] = kdj_j
    
    return result


# ================ 回测引擎 ================

class BacktestEngine:
    """量化策略回测引擎"""
    
    def __init__(self, initial_cash=20000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # {code: {'shares': int, 'cost_price': float}
        self.trades = []  # 交易记录
        self.equity_curve = []  # 资金曲线
    
    def reset(self):
        """重置回测状态"""
        self.cash = self.initial_cash
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def buy(self, code, price, date, shares=None):
        """买入股票"""
        code = str(code)
        price = float(price)
        
        if shares is None:
            # 满仓买入
            max_shares = int(self.cash / price) // 100 * 100
            shares = max_shares
        
        if shares <= 0:
            return False
        
        cost = shares * price
        
        if cost > self.cash:
            return False
        
        self.cash -= cost
        
        if code not in self.positions:
            self.positions[code] = {'shares': shares, 'cost_price': price}
        else:
            # 加仓
            old_shares = self.positions[code]['shares']
            old_cost = self.positions[code]['cost_price']
            new_shares = old_shares + shares
            new_cost = (old_shares * old_cost + shares * price) / new_shares
            self.positions[code]['shares'] = new_shares
            self.positions[code]['cost_price'] = new_cost
        
        self.trades.append({
            'date': date,
            'type': 'BUY',
            'code': code,
            'price': price,
            'shares': shares,
            'cash_after': self.cash
        })
        
        return True
    
    def sell(self, code, price, date, shares=None):
        """卖出股票"""
        code = str(code)
        price = float(price)
        
        if code not in self.positions:
            return False
        
        if shares is None:
            shares = self.positions[code]['shares']
        
        if shares > self.positions[code]['shares']:
            shares = self.positions[code]['shares']
        
        proceeds = shares * price
        self.cash += proceeds
        
        old_shares = self.positions[code]['shares']
        if old_shares == shares:
            del self.positions[code]
        else:
            self.positions[code]['shares'] = old_shares - shares
        
        self.trades.append({
            'date': date,
            'type': 'SELL',
            'code': code,
            'price': price,
            'shares': shares,
            'cash_after': self.cash
        })
        
        return True
    
    def record_equity(self, date, current_prices):
        """记录当前权益"""
        # 计算持仓市值
        position_value = 0.0
        for code, pos in self.positions.items():
            if code in current_prices:
                position_value += pos['shares'] * current_prices[code]
        
        total_equity = self.cash + position_value
        
        self.equity_curve.append({
            'date': date,
            'cash': self.cash,
            'position_value': position_value,
            'total': total_equity
        })
        
        return total_equity


# ================ 策略实现 ================

class StrategyMaMacd(BacktestEngine):
    """双均线+MACD共振策略回测"""
    
    def __init__(self, initial_cash=20000.0):
        super().__init__(initial_cash)
    
    def run_backtest(self, data, code):
        self.reset()
        
        in_position = False
        last_action = None
        
        for i in range(len(data)):
            row = data.iloc[i]
            date = data.index[i]
            current_price = row['close']
            
            if i < 60:  # 跳过前期数据
                continue
            
            # 买入信号
            if not in_position:
                buy_signal = False
                # MA5上穿MA20（金叉）
                if (data['MA5'].iloc[i-1] <= data['MA20'].iloc[i-1] and 
                    data['MA5'].iloc[i] > data['MA20'].iloc[i]):
                    # MACD在零轴上方或金叉
                    if (data['MACD_DIF'].iloc[i] > 0 or 
                        (data['MACD_DIF'].iloc[i-1] <= data['MACD_DEA'].iloc[i-1] and 
                         data['MACD_DIF'].iloc[i] > data['MACD_DEA'].iloc[i])):
                        # 价格在MA20上方
                        if row['close'] > data['MA20'].iloc[i]:
                            buy_signal = True
                
                if buy_signal:
                    self.buy(code, current_price, date)
                    in_position = True
                    last_action = 'BUY'
            
            # 卖出信号
            else:
                sell_signal = False
                
                # MA5下穿MA20（死叉）
                if (data['MA5'].iloc[i-1] >= data['MA20'].iloc[i-1] and 
                    data['MA5'].iloc[i] < data['MA20'].iloc[i]):
                    sell_signal = True
                
                # 止损8%
                if 'cost_price' in self.positions.get(str(code)):
                    cost_price = self.positions[str(code)]['cost_price']
                    if current_price < cost_price * 0.92:
                        sell_signal = True
                
                if sell_signal:
                    self.sell(code, current_price, date)
                    in_position = False
                    last_action = 'SELL'
            
            # 记录权益
            self.record_equity(date, {str(code): current_price})
        
        # 回测结束
        if in_position:
            self.sell(code, current_price, date)
        
        return self


class StrategyBollingerRsi(BacktestEngine):
    """布林带RSI震荡策略回测"""
    
    def __init__(self, initial_cash=20000.0):
        super().__init__(initial_cash)
    
    def run_backtest(self, data, code):
        self.reset()
        
        in_position = False
        
        for i in range(len(data)):
            row = data.iloc[i]
            date = data.index[i]
            current_price = row['close']
            
            if i < 20:
                continue
            
            if not in_position:
                buy_signal = False
                # 价格触及下轨，RSI超卖
                if row['close'] <= row['BOLL_LOWER']:
                    if row['RSI'] < 30:
                        # 开始反弹
                        if i > 0 and data['close'].iloc[i] > data['close'].iloc[i-1]:
                            buy_signal = True
                
                if buy_signal:
                    self.buy(code, current_price, date)
                    in_position = True
            
            else:
                sell_signal = False
                # 价格触及上轨，RSI超买
                if row['close'] >= row['BOLL_UPPER']:
                    if row['RSI'] > 70:
                        sell_signal = True
                
                # 止损7%
                if 'cost_price' in self.positions.get(str(code)):
                    cost_price = self.positions[str(code)]['cost_price']
                    if current_price < cost_price * 0.93:
                        sell_signal = True
                
                if sell_signal:
                    self.sell(code, current_price, date)
                    in_position = False
            
            self.record_equity(date, {str(code): current_price})
        
        if in_position:
            self.sell(code, current_price, date)
        
        return self


# ================ 回测结果分析 ================

def analyze_backtest_result(backtest, initial_cash):
    """分析回测结果"""
    
    if len(backtest.equity_curve) == 0:
        return None
    
    equity_data = pd.DataFrame(backtest.equity_curve)
    equity_data['total'] = pd.to_numeric(equity_data['total'])
    
    final_value = equity_data['total'].iloc[-1]
    total_return = (final_value - initial_cash) / initial_cash * 100
    
    # 计算最大回撤
    equity_series = equity_data['total']
    cumulative_max = equity_series.cummax()
    drawdown = (equity_series - cumulative_max) / cumulative_max * 100
    max_drawdown = drawdown.min()
    
    # 胜率计算（简化版）
    wins = 0
    losses = 0
    # 实际计算需要配对买卖单，这里简化
    
    return {
        'initial_cash': initial_cash,
        'final_value': final_value,
        'total_return_pct': total_return,
        'max_drawdown_pct': max_drawdown,
        'trade_count': len(backtest.trades),
        'equity_curve': equity_data.to_dict('records')
    }


# ================ 回测执行 ================

def run_strategy_backtest(stock_code, strategy_name, initial_cash=20000.0, days=120):
    """执行策略回测"""
    
    print(f"正在获取 {stock_code} 历史数据...")
    raw_data = get_historical_k_data(stock_code, period='daily', days=days)
    
    if len(raw_data) == 0:
        return None, None
    
    print(f"正在计算技术指标...")
    data_with_indicators = calculate_all_indicators(raw_data)
    
    print(f"正在执行 {strategy_name} 回测...")
    
    if strategy_name == 'ma_macd':
        strategy = StrategyMaMacd(initial_cash)
    elif strategy_name == 'boll_rsi':
        strategy = StrategyBollingerRsi(initial_cash)
    else:
        return None, None
    
    result = strategy.run_backtest(data_with_indicators, stock_code)
    
    analysis = analyze_backtest_result(result, initial_cash)
    
    return result, analysis


# ================ 生成回测报告 ================

def generate_backtest_report(backtest, analysis, stock_code, strategy_name):
    """生成回测报告"""
    
    report = []
    
    report.append("# " + "="*60)
    report.append("量化策略回测报告")
    report.append("="*60)
    report.append(f"股票代码: " + str(stock_code))
    report.append(f"策略名称: " + strategy_name)
    report.append(f"回测时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    report.append("")
    
    if analysis is not None:
        report.append("---")
        report.append("回测结果:")
        report.append(f"初始资金: " + str(round(analysis['initial_cash'])))
        report.append(f"最终资金: " + str(round(analysis['final_value'], 2)))
        report.append(f"总收益率: " + str(round(analysis['total_return_pct'], 2)) + "%")
        report.append(f"最大回撤: " + str(round(analysis['max_drawdown_pct'], 2)) + "%")
        report.append(f"交易次数: " + str(analysis['trade_count']))
    
    report.append("")
    report.append("---")
    report.append("交易记录:")
    for i, trade in enumerate(backtest.trades):
        report.append(f"{i+1}. {trade['date']} {trade['type']} {trade['code']} @ {round(trade['price'], 2)} x {trade['shares']}")
    
    report.append("")
    report.append("---")
    report.append("资金曲线:")
    for i, eq in enumerate(backtest.equity_curve[-20:]):
        report.append(f"{eq['date']} 权益: {round(eq['total'], 2)}")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("="*60)
    print("量化回测系统测试")
    print("="*60)
