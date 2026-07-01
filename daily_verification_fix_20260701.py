#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日验证任务修正版 - 2026-07-01
修正原因：实时行情API间歇性失败，使用了错误的备选价格数据
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a_stock_data_core import get_stock_quote
from serenity_daily_stock_picker import DailyStockPicker


def get_real_price_with_retry(code: str, max_retries: int = 10) -> float:
    """
    获取真实价格（带重试机制）
    """
    import time
    
    for i in range(max_retries):
        try:
            result = get_stock_quote(code)
            if result and code in result:
                price = float(result[code].get("price", 0))
                if price > 0:
                    print(f"✅ 第{i+1}次尝试成功获取真实价格: {price:.2f}元")
                    return price
            elif result and isinstance(result, dict):
                # 处理返回格式不同的情况
                for key, value in result.items():
                    if isinstance(value, dict) and "price" in value:
                        price = float(value.get("price", 0))
                        if price > 0:
                            print(f"✅ 第{i+1}次尝试成功获取真实价格: {price:.2f}元")
                            return price
            
            print(f"⚠️ 第{i+1}次尝试返回空数据")
            if i < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"❌ 第{i+1}次尝试失败: {e}")
            if i < max_retries - 1:
                time.sleep(2)
    
    return 0.0


def run_corrected_verification():
    """
    执行修正后的每日验证任务
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 70)
    print("  🔧 每日验证任务修正版")
    print(f"  日期: {today}")
    print("=" * 70)
    print()
    
    # 1. 初始化系统
    print("【步骤1】初始化验证系统")
    print("-" * 50)
    picker = DailyStockPicker(data_dir="serenity_stock_data")
    print()
    
    # 2. 获取验证中股票
    verifying = picker.selection_mgr.get_verifying_selections()
    print(f"【步骤2】当前验证状态")
    print("-" * 50)
    print(f"  验证中: {len(verifying)}只")
    
    for sel in verifying:
        print(f"    📊 {sel.stock_name}({sel.stock_code})")
        print(f"       成本价: {sel.buy_price:.2f}元")
        print(f"       持仓天数: {sel.hold_days}天")
        print(f"       当前收益: {sel.current_return_pct:+.2f}%")
    print()
    
    # 3. 获取真实收盘价
    print("【步骤3】获取今日真实收盘价")
    print("-" * 50)
    
    price_data = {}
    for sel in verifying:
        code = sel.stock_code
        print(f"\n正在获取 {sel.stock_name}({code}) 的真实价格...")
        
        real_price = get_real_price_with_retry(code, max_retries=10)
        
        if real_price > 0:
            price_data[code] = real_price
            
            # 计算真实收益
            real_return_pct = (real_price / sel.buy_price - 1) * 100
            
            print(f"  💰 真实收盘价: {real_price:.2f}元")
            print(f"  📈 真实收益率: {real_return_pct:+.2f}%")
            
            # 检查止盈止损条件
            # 从策略管理器获取风控参数
            strategy = picker.strategy_mgr.get_strategy(sel.strategy_id)
            if strategy:
                stop_loss_pct = strategy.risk_control.stop_loss_pct
                take_profit_pct = strategy.risk_control.take_profit_pct
                max_hold_days = strategy.risk_control.max_hold_days
            else:
                # 默认风控参数
                stop_loss_pct = -10.0
                take_profit_pct = 20.0
                max_hold_days = 20
            
            print(f"  🎯 风控条件:")
            print(f"     止盈线: {take_profit_pct:+.0f}%")
            print(f"     止损线: {stop_loss_pct:+.0f}%")
            print(f"     最大持仓: {max_hold_days}天")
            
            # 检查是否触发条件
            triggered = []
            if real_return_pct >= take_profit_pct:
                triggered.append("止盈")
                print(f"  ✅ 触发止盈条件！收益{real_return_pct:+.2f}% >= {take_profit_pct:+.0f}%")
            
            if real_return_pct <= stop_loss_pct:
                triggered.append("止损")
                print(f"  ❌ 触发止损条件！收益{real_return_pct:+.2f}% <= {stop_loss_pct:+.0f}%")
            
            if sel.hold_days >= max_hold_days:
                triggered.append("到期")
                print(f"  ⏰ 触发到期条件！持仓{sel.hold_days}天 >= {max_hold_days}天")
            
            if not triggered:
                print(f"  🟢 未触发任何条件，继续持有")
        else:
            print(f"  ❌ 无法获取真实价格")
    
    print()
    
    # 4. 执行验证
    print("【步骤4】执行每日验证")
    print("-" * 50)
    
    if price_data:
        result = picker.daily_verification(price_data, today=today)
        
        print(f"  验证数量: {result['verified_count']}只")
        print(f"  止盈: {result['new_wins']}只")
        print(f"  止损: {result['new_losses']}只")
        print(f"  到期: {result['new_expired']}只")
        
        if result['details']:
            print()
            print("  详细结果:")
            for detail in result['details']:
                print(f"    {detail}")
        
        # 5. 策略淘汰评估
        print()
        print("【步骤5】策略淘汰评估")
        print("-" * 50)
        
        if result['abandonments']:
            print(f"  ⚠️  触发淘汰的策略: {len(result['abandonments'])}个")
            for ab in result['abandonments']:
                print(f"    ❌ [{ab['strategy_id']}] {ab['strategy_name']}")
                print(f"       原因: {ab['reason']}")
        else:
            print("  ✅ 无策略触发淘汰条件")
        
        # 6. 生成复盘报告
        print()
        print("【步骤6】生成每日复盘报告")
        print("-" * 50)
        
        report = picker.generate_daily_review(today=today)
        print(report)
        
        # 保存报告
        review_dir = Path("serenity_stock_data") / "daily_reviews"
        review_dir.mkdir(exist_ok=True)
        report_file = review_dir / f"daily_review_{today}_corrected.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n  ✅ 修正后的报告已保存: {report_file}")
        
        # 7. 保存验证结果
        print()
        print("【步骤7】保存修正后的验证结果")
        print("-" * 50)
        
        # 获取验证后的状态
        verifying_after = picker.selection_mgr.get_verifying_selections()
        
        result_summary = {
            "date": today,
            "verified_count": result["verified_count"],
            "new_wins": result["new_wins"],
            "new_losses": result["new_losses"],
            "new_expired": result["new_expired"],
            "abandonments_count": len(result["abandonments"]),
            "details": result["details"],
            "price_data": price_data,
            "real_price_used": True,  # 标记使用了真实价格
            "verifying_after": [
                {
                    "code": s.stock_code,
                    "name": s.stock_name,
                    "buy_price": s.buy_price,
                    "current_price": price_data.get(s.stock_code, 0),
                    "hold_days": s.hold_days,
                    "return_pct": round(s.current_return_pct, 2),
                    "status": s.status.value,
                }
                for s in verifying_after
            ],
        }
        
        result_file = Path("serenity_stock_data") / f"verification_result_{today}_corrected.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 修正后的验证结果已保存: {result_file}")
    else:
        print("  ❌ 没有获取到任何价格数据")
    
    print()
    print("=" * 70)
    print("  ✅ 每日验证任务（修正版）执行完成！")
    print("=" * 70)
    
    return price_data


if __name__ == '__main__':
    run_corrected_verification()