"""
困境解套策略 - 1500元资金配置方案
针对被套牢且资金有限的情况
"""

import pandas as pd

class SmallCapitalStrategy:
    """小额资金解套与投资策略"""
    
    def __init__(self, available_cash=1500):
        self.available_cash = available_cash
        self.max_price = available_cash / 100  # 100股所需的最大股价
    
    def analyze_current_situation(self, trapped_stocks=None):
        """分析当前困境"""
        analysis = {
            'available_cash': self.available_cash,
            'max_stock_price': round(self.max_price, 2),
            'stocks_per_trade': 100,
            'strategy_options': [],
        }
        
        print(f"📊 你的当前状况：")
        print(f"   可动用资金：¥{self.available_cash}")
        print(f"   可买股票最高价格：¥{self.max_price:.2f}（100股）")
        print(f"   可用策略：补仓解套 / 换股操作 / 等待时机")
        
        return analysis
    
    def recommend_low_price_stocks(self):
        """推荐低价优质股票（<15元）"""
        low_price_stocks = [
            {
                'name': '平安银行',
                'code': '000001',
                'price': 11.36,
                'sector': '银行',
                'pe': 8.5,
                'dividend': '4.5%',
                'rating': '稳健型',
                'analysis': '银行股，业绩稳定，分红率高，适合防守',
                'risk': '低',
            },
            {
                'name': 'TCL科技',
                'code': '000100',
                'price': 4.85,
                'sector': '电子',
                'pe': 15.2,
                'dividend': '2.1%',
                'rating': '潜力型',
                'analysis': '面板龙头，行业周期反转预期',
                'risk': '中',
            },
            {
                'name': '京东方A',
                'code': '000725',
                'price': 3.98,
                'sector': '电子',
                'pe': 22.5,
                'dividend': '1.5%',
                'rating': '周期型',
                'analysis': '面板龙头，估值较低',
                'risk': '中',
            },
            {
                'name': '包钢股份',
                'code': '600010',
                'price': 1.85,
                'sector': '钢铁',
                'pe': 18.0,
                'dividend': '1.2%',
                'rating': '投机型',
                'analysis': '低价股，波动大，风险高',
                'risk': '高',
            },
            {
                'name': '中国中铁',
                'code': '601390',
                'price': 7.25,
                'sector': '基建',
                'pe': 9.8,
                'dividend': '3.2%',
                'rating': '稳健型',
                'analysis': '基建央企，业绩稳定',
                'risk': '低',
            },
            {
                'name': '光大银行',
                'code': '601818',
                'price': 3.15,
                'sector': '银行',
                'pe': 6.8,
                'dividend': '5.2%',
                'rating': '稳健型',
                'analysis': '银行股，估值低，分红稳定',
                'risk': '低',
            },
        ]
        
        return low_price_stocks
    
    def generate_solution(self, trapped_stocks=None):
        """生成解套方案"""
        print("\n" + "="*60)
        print("💡 解套策略方案")
        print("="*60)
        
        print("\n【方案一：补仓降低成本】")
        print("适用条件：被套股票基本面良好，只是短期下跌")
        print("操作：")
        print("   1. 计算补仓后成本")
        print("   2. 分批补仓，不要一次性满仓")
        print("   3. 设定反弹目标价，达到后减仓")
        
        print("\n【方案二：换股操作】")
        print("适用条件：被套股票基本面恶化，或有更好选择")
        print("操作：")
        print("   1. 果断割肉，换入优质低价股")
        print("   2. 选择基本面好、估值低的股票")
        print("   3. 控制风险，不要追高")
        
        print("\n【方案三：耐心等待】")
        print("适用条件：市场整体下跌，个股基本面无问题")
        print("操作：")
        print("   1. 保留现金，等待市场企稳")
        print("   2. 观察成交量变化")
        print("   3. 市场转暖后再操作")
        
        print("\n【方案四：波段操作降低成本】")
        print("适用条件：股票波动较大")
        print("操作：")
        print("   1. 在低位补仓，高位卖出")
        print("   2. 反复操作降低成本")
        print("   3. 严格执行，避免失误")
    
    def recommend_action(self, trapped_stocks=None):
        """综合推荐"""
        stocks = self.recommend_low_price_stocks()
        
        print("\n" + "="*60)
        print("🎯 推荐股票（15元以下）")
        print("="*60)
        
        for i, stock in enumerate(stocks, 1):
            cost = stock['price'] * 100
            remaining = self.available_cash - cost
            
            print(f"\n{i}. {stock['name']}({stock['code']})")
            print(f"   价格：¥{stock['price']:.2f}")
            print(f"   买入成本：¥{cost:.2f}（100股）")
            print(f"   剩余资金：¥{remaining:.2f}")
            print(f"   行业：{stock['sector']}")
            print(f"   市盈率：{stock['pe']}")
            print(f"   分红率：{stock['dividend']}")
            print(f"   评级：{stock['rating']}")
            print(f"   风险：{stock['risk']}")
            print(f"   分析：{stock['analysis']}")
        
        return stocks


if __name__ == "__main__":
    strategy = SmallCapitalStrategy(available_cash=1500)
    strategy.analyze_current_situation()
    strategy.generate_solution()
    strategy.recommend_action()
