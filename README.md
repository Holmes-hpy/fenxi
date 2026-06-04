# A股数据 MCP 服务

一个基于 MCP (Model Context Protocol) 的 A股数据获取和分析工具集，提供实时行情、研报、资金流向、基本面分析等功能。

## ✨ 功能特性

### 行情数据
- 实时股票行情获取
- 历史K线数据（日/周/月）
- 大盘指数实时数据

### 研报与新闻
- 个股研报列表
- 个股新闻资讯
- 财联社快讯

### 资金信号
- 北向资金实时流向
- 概念板块归属
- 龙虎榜数据
- 限售解禁信息
- 融资融券数据
- 大宗交易
- 股东户数变化
- 分红送转历史

### 基本面分析
- 股票基本信息
- 季度报告数据
- 多股票估值对比

## 🚀 快速开始

### 安装依赖

```bash
pip install requests pandas mootdx
```

### 基本使用

```python
from a_stock_data_core import (
    get_stock_quote,
    get_market_index,
    get_research_reports,
    get_northbound_flow
)

# 获取实时行情
quote = get_stock_quote("600519")
print(quote)

# 获取大盘指数
index = get_market_index()
print(index)

# 获取北向资金
northbound = get_northbound_flow()
print(northbound)
```

### MCP 服务使用

直接在支持 MCP 的环境中使用，通过自然语言提问即可：

- "贵州茅台今天的股价和PE是多少？"
- "今天北向资金流入多少？"
- "比亚迪属于什么概念板块？"

## 📁 项目结构

```
a-stock-data/
├── a_stock_data_core.py    # 核心数据获取模块
├── a_stock_data_mcp.py     # MCP服务入口
├── README.md              # 项目说明文档
├── USAGE_GUIDE.md         # 使用指南
├── STOCK_SELECTION_GUIDE.md # 选股指南
└── .gitignore             # Git忽略配置
```

## ⚙️ 配置

### 环境变量（可选）

- `IWENCAI_API_KEY`: iwencai API Key（用于语义搜索）
- `IWENCAI_BASE_URL`: iwencai API 地址

## 🔧 可用工具列表

| 工具名称 | 功能描述 |
|---------|---------|
| `get_stock_quote` | 获取股票实时行情 |
| `get_historical_k_data` | 获取历史K线数据 |
| `get_market_index` | 获取大盘指数 |
| `get_research_reports` | 获取股票研报列表 |
| `get_stock_news` | 获取个股新闻 |
| `get_northbound_flow` | 获取北向资金流向 |
| `get_stock_concept_blocks` | 获取概念板块归属 |
| `get_dragon_tiger_board` | 获取龙虎榜数据 |
| `get_lockup_expiry` | 获取限售解禁信息 |
| `get_ths_hot_stocks` | 获取热点题材股票 |
| `get_margin_trading` | 获取融资融券数据 |
| `get_block_trades` | 获取大宗交易 |
| `get_shareholder_count` | 获取股东户数变化 |
| `get_dividend_history` | 获取分红送转历史 |
| `get_stock_basic_info` | 获取股票基本信息 |
| `get_quarterly_report` | 获取季度报告数据 |
| `get_industry_comparison` | 多股票估值对比 |

## ⚠️ 重要说明

- 数据仅供参考，不构成投资建议
- A股交易时间：周一至周五 9:30-11:30, 13:00-15:00
- 部分API有调用频率限制，请合理使用
- 实时数据可能有1-5分钟延迟

## 📝 许可证

本项目仅供学习交流使用。

---

**免责声明：投资有风险，入市需谨慎！**
