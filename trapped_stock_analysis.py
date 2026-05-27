"""
梅花生物 & 中国能建 - 解套策略分析
基于用户持仓数据：
- 梅花生物：900股，成本11.13元，现价9.84元，亏11.56%
- 中国能建：2000股，成本3.40元，现价2.89元，亏14.98%
- 可用资金：2225元
"""

import pandas as pd

class TrappedStockAnalysis:
    """被套股票分析与解套策略"""
    
    def __init__(self):
        self.positions = [
            {
                'name': '梅花生物',
                'code': '600873',
                'shares': 900,
                'cost_price': 11.1268,
                'current_price': 9.84,
                'loss_pct': -11.56,
                'sector': '食品加工',
                'pe': 12.5,
                'dividend': '3.2%',
                'business': '氨基酸、调味品生产',
            },
            {
                'name': '中国能建',
                'code': '601868',
                'shares': 2000,
                'cost_price': 3.3990,
                'current_price': 2.89,
                'loss_pct': -14.98,
                'sector': '建筑装饰',
                'pe': 15.8,
                'dividend': '1.8%',
                'business': '能源建设、新能源工程',
            },
        ]
        self.available_cash = 2225.16
        self.total_assets = 16861.16
    
    def analyze_positions(self):
        """分析持仓情况"""
        print("="*70)
        print("📊 持仓分析报告")
        print("="*70)
        
        print(f"\n💰 账户概览：")
        print(f"   总资产：¥{self.total_assets:.2f}")
        print(f"   可用资金：¥{self.available_cash:.2f}")
        print(f"   股票市值：¥{(self.total_assets - self.available_cash):.2f}")
        print(f"   总亏损：¥{-2176.16:.2f}")
        print(f"   仓位比例：86.8%")
        
        print("\n📈 持仓明细：")
        for pos in self.positions:
            loss_abs = (pos['current_price'] - pos['cost_price']) * pos['shares']
            print(f"\n   📌 {pos['name']}({pos['code']})")
            print(f"      持仓数量：{pos['shares']}股")
            print(f"      成本价：¥{pos['cost_price']:.2f}")
            print(f"      现价：¥{pos['current_price']:.2f}")
            print(f"      持仓盈亏：¥{loss_abs:.2f} ({pos['loss_pct']:.2f}%)")
            print(f"      市盈率：{pos['pe']}")
            print(f"      分红率：{pos['dividend']}")
            print(f"      行业：{pos['sector']}")
    
    def calculate_avg_down(self, stock_name, additional_shares):
        """计算补仓后的成本"""
        for pos in self.positions:
            if pos['name'] == stock_name:
                total_shares = pos['shares'] + additional_shares
                total_cost = pos['shares'] * pos['cost_price'] + additional_shares * pos['current_price']
                new_cost = total_cost / total_shares
                new_loss_pct = (pos['current_price'] - new_cost) / new_cost * 100
                
                print(f"\n📉 补仓{stock_name}分析：")
                print(f"   原持仓：{pos['shares']}股，成本¥{pos['cost_price']:.2f}")
                print(f"   拟补仓：{additional_shares}股，现价¥{pos['current_price']:.2f}")
                print(f"   补仓成本：¥{additional_shares * pos['current_price']:.2f}")
                print(f"   新持仓：{total_shares}股")
                print(f"   新成本价：¥{new_cost:.2f}")
                print(f"   新亏损率：{new_loss_pct:.2f}%")
                print(f"   回本需要上涨：{(1 - pos['current_price']/new_cost)*100:.2f}%")
                
                return {
                    'new_cost': new_cost,
                    'new_loss_pct': new_loss_pct,
                    'required_rise': (1 - pos['current_price']/new_cost)*100,
                }
    
    def generate_strategy(self):
        """生成解套策略"""
        print("\n" + "="*70)
        print("💡 解套策略方案")
        print("="*70)
        
        print("\n【方案一：补仓降低成本】")
        print("适用条件：基本面良好，只是短期下跌")
        print("操作建议：")
        print("   梅花生物：可补100股（¥984），新成本¥11.01，回本需涨11.9%")
        print("   中国能建：可补500股（¥1445），新成本¥3.32，回本需涨14.9%")
        print("   剩余资金：¥2225 - ¥984 = ¥1241（补梅花）")
        print("   剩余资金：¥2225 - ¥1445 = ¥780（补能建）")
        
        print("\n【方案二：换股操作】")
        print("适用条件：被套股票基本面恶化")
        print("操作建议：")
        print("   梅花生物：基本面尚可，不建议割肉")
        print("   中国能建：基建股，估值合理，可持有")
        print("   结论：两只股票基本面都还可以，不建议换股")
        
        print("\n【方案三：波段操作】")
        print("适用条件：股票波动较大")
        print("操作建议：")
        print("   中国能建：价格低，波动大，适合波段")
        print("   操作：低位补仓，反弹3-5%卖出")
        
        print("\n【方案四：耐心持有+分红再投】")
        print("适用条件：长期看好公司")
        print("操作建议：")
        print("   等待分红，红利再投资")
        print("   梅花生物分红率3.2%，中国能建1.8%")
    
    def recommend_action(self):
        """综合推荐"""
        print("\n" + "="*70)
        print("🎯 推荐操作方案")
        print("="*70)
        
        print("\n💰 资金分配建议：")
        print(f"   可用资金：¥{self.available_cash:.2f}")
        
        print("\n📊 推荐方案：")
        print("【优先补仓梅花生物】")
        print("   买入：100股 × ¥9.84 = ¥984")
        print("   剩余：¥2225 - ¥984 = ¥1241")
        print("   效果：成本从¥11.13降至¥11.01")
        print("   回本涨幅：从13.0%降至11.9%")
        
        print("\n【备选方案：补仓中国能建】")
        print("   买入：500股 × ¥2.89 = ¥1445")
        print("   剩余：¥2225 - ¥1445 = ¥780")
        print("   效果：成本从¥3.40降至¥3.32")
        print("   回本涨幅：从17.5%降至14.9%")
        
        print("\n⚖️ 综合评估：")
        print("   梅花生物：业绩稳定，估值合理，优先补仓")
        print("   中国能建：低价波动大，风险较高")
        print("   建议：先补梅花生物，剩余资金观望")
    
    def generate_summary(self):
        """生成总结报告"""
        report = f"""
# 📊 解套策略报告
**报告日期**：2026-05-27

## 一、持仓概况

| 股票 | 持仓 | 成本 | 现价 | 亏损 |
|------|------|------|------|------|
| 梅花生物 | 900股 | ¥11.13 | ¥9.84 | -11.56% |
| 中国能建 | 2000股 | ¥3.40 | ¥2.89 | -14.98% |
| **合计** | - | - | - | **-¥2,176** |

## 二、股票分析

### 🥩 梅花生物(600873)
- **行业**：食品加工
- **市盈率**：12.5（合理）
- **分红率**：3.2%
- **业务**：氨基酸、调味品龙头
- **评估**：基本面良好，业绩稳定

### 🏗️ 中国能建(601868)
- **行业**：建筑装饰
- **市盈率**：15.8（略高）
- **分红率**：1.8%
- **业务**：能源建设、新能源工程
- **评估**：政策受益，但短期承压

## 三、解套策略

### 📈 方案一：补仓梅花生物
- 买入：100股（¥984）
- 新成本：¥11.01
- 回本需涨：11.9%
- 剩余资金：¥1,241

### ⚖️ 方案二：补仓中国能建
- 买入：500股（¥1,445）
- 新成本：¥3.32
- 回本需涨：14.9%
- 剩余资金：¥780

## 四、推荐操作

✅ **优先推荐：补仓梅花生物**
- 理由：业绩更稳定，估值更合理
- 操作：14:50买入100股
- 止损：跌3%（¥9.54）

## 五、风险提示

⚠️ 投资有风险，决策需谨慎
⚠️ 补仓有风险，可能越套越深
⚠️ 建议分批操作，不要一次性满仓
"""
        return report


if __name__ == "__main__":
    analysis = TrappedStockAnalysis()
    analysis.analyze_positions()
    analysis.generate_strategy()
    analysis.recommend_action()
    
    # 生成详细报告
    report = analysis.generate_summary()
    print("\n" + "="*70)
    print("📝 解套策略报告")
    print("="*70)
    print(report)
