#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动每日验证任务 - 2026-07-01
使用已知的价格数据手动执行验证

晶瑞电材(300655) 2026-07-01 真实收盘价: 20.71元
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serenity_daily_stock_picker import DailyStockPicker


def run_manual_verification():
    """
    手动执行每日验证（使用已知价格）
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 70)
    print("  📋 手动每日验证任务")
    print(f"  日期: {today}")
    print("  ⚠️  使用已知真实价格数据")
    print("=" * 70)
    print()
    
    # 已知的真实价格数据（从单独测试获取）
    KNOWN_PRICES = {
        "300655": 20.71,  # 晶瑞电材 2026-07-01 收盘价
    }
    
    # 1. 初始化系统
    print("【步骤1】初始化验证系统")
    print("-" * 50)
    picker = DailyStockPicker(data_dir="serenity_stock_data")
    
    # 检查策略状态
    strategy = picker.strategy_mgr.get_strategy("S001")
    if strategy:
        print(f"  策略: {strategy.strategy_name}")
        print(f"  止盈线: {strategy.risk_control.take_profit_pct:+.0f}%")
        print(f"  止损线: {strategy.risk_control.stop_loss_pct:+.0f}%")
        print(f"  最大持仓: {strategy.risk_control.max_hold_days}天")
    print()
    
    # 2. 当前验证状态
    print("【步骤2】当前验证状态")
    print("-" * 50)
    verifying = picker.selection_mgr.get_verifying_selections()
    print(f"  验证中: {len(verifying)}只")
    
    for sel in verifying:
        print(f"    📊 {sel.stock_name}({sel.stock_code})")
        print(f"       成本价: {sel.buy_price:.2f}元")
        print(f"       持仓天数: {sel.hold_days}天")
        print(f"       当前收益: {sel.current_return_pct:+.2f}%")
    print()
    
    # 3. 使用已知价格执行验证
    print("【步骤3】使用已知真实价格执行验证")
    print("-" * 50)
    
    price_data = {}
    for sel in verifying:
        code = sel.stock_code
        if code in KNOWN_PRICES:
            price = KNOWN_PRICES[code]
            price_data[code] = price
            
            # 计算真实收益
            real_return_pct = (price / sel.buy_price - 1) * 100
            
            print(f"\n  📊 {sel.stock_name}({sel.stock_code})")
            print(f"     💰 今日收盘价: {price:.2f}元")
            print(f"     📈 今日收益率: {real_return_pct:+.2f}%")
            print(f"     📊 成本价: {sel.buy_price:.2f}元")
            print(f"     🕐 持仓天数: {sel.hold_days}天")
            
            # 检查风控条件
            strategy = picker.strategy_mgr.get_strategy(sel.strategy_id)
            if strategy:
                stop_loss = strategy.risk_control.stop_loss_pct
                take_profit = strategy.risk_control.take_profit_pct
                max_days = strategy.risk_control.max_hold_days
                
                print(f"\n     🎯 风控条件检查:")
                print(f"        止盈线: {take_profit:+.0f}%")
                print(f"        止损线: {stop_loss:+.0f}%")
                print(f"        最大持仓: {max_days}天")
                
                # 检查是否触发
                if real_return_pct >= take_profit:
                    print(f"     ✅ 触发止盈！{real_return_pct:+.2f}% >= {take_profit:+.0f}%")
                elif real_return_pct <= stop_loss:
                    print(f"     ❌ 触发止损！{real_return_pct:+.2f}% <= {stop_loss:+.0f}%")
                elif sel.hold_days >= max_days:
                    print(f"     ⏰ 触发到期！持仓{sel.hold_days}天 >= {max_days}天")
                else:
                    print(f"     🟢 未触发条件，继续持有")
                    print(f"        距止盈还需: {take_profit - real_return_pct:+.2f}%")
                    print(f"        距止损还有: {real_return_pct - stop_loss:+.2f}%缓冲")
                    print(f"        剩余持仓天数: {max_days - sel.hold_days}天")
    print()
    
    # 4. 执行系统验证
    print("【步骤4】执行系统验证流程")
    print("-" * 50)
    
    if price_data:
        result = picker.daily_verification(price_data, today=today)
        
        print(f"  验证数量: {result['verified_count']}只")
        print(f"  止盈: {result['new_wins']}只")
        print(f"  止损: {result['new_losses']}只")
        print(f"  到期: {result['new_expired']}只")
        
        if result['details']:
            print()
            print("  📋 详细结果:")
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
        report_file = review_dir / f"daily_review_{today}_manual.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n  ✅ 报告已保存: {report_file}")
        
        # 7. 保存验证结果
        print()
        print("【步骤7】保存验证结果")
        print("-" * 50)
        
        # 获取验证后的最新状态
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
            "data_source": "手动输入（API不稳定）",
            "verifying_after": [
                {
                    "code": s.stock_code,
                    "name": s.stock_name,
                    "buy_price": s.buy_price,
                    "current_price": price_data.get(s.stock_code, 0),
                    "hold_days": s.hold_days,
                    "return_pct": round(s.current_return_pct, 2),
                    "status": s.status.value,
                    "max_return": round(s.max_return_pct, 2),
                    "min_return": round(s.min_return_pct, 2),
                }
                for s in verifying_after
            ],
        }
        
        result_file = Path("serenity_stock_data") / f"verification_result_{today}_manual.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 验证结果已保存: {result_file}")
        
        # 8. 显示验证后状态
        print()
        print("【步骤8】验证后状态")
        print("-" * 50)
        
        if verifying_after:
            print(f"  验证中: {len(verifying_after)}只")
            for s in verifying_after:
                icon = "🟢" if s.current_return_pct >= 0 else "🔴"
                print(f"    {icon} {s.stock_name}({s.stock_code})")
                print(f"       持仓{ s.hold_days}天 | 收益{s.current_return_pct:+.2f}%")
                print(f"       最高+{s.max_return_pct:.2f}% / 最低{s.min_return_pct:.2f}%")
        else:
            print("  所有股票已完成验证")
    else:
        print("  ❌ 没有价格数据")
    
    print()
    print("=" * 70)
    print("  ✅ 手动每日验证任务执行完成！")
    print("=" * 70)
    
    return price_data


if __name__ == '__main__':
    run_manual_verification()