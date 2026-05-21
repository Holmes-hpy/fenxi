# A股数据MCP服务

全自动部署的A股数据MCP（Model Context Protocol）服务，提供实时行情、基本面、研报、资金流向等全维度数据。

## 功能特性

### 行情数据
- `get_stock_quote` - 获取股票实时行情（价格、涨跌幅、PE、PB、市值等）
- `get_historical_k_data` - 获取历史K线数据（日线、周线、月线）
- `get_market_index` - 获取大盘指数（上证、深证、创业板、科创50）

### 研报数据
- `get_research_reports` - 获取研报列表
- `get_ths_hot_stocks` - 获取同花顺热点股票（题材归因）
- `get_stock_news` - 获取个股新闻

### 信号数据
- `get_northbound_flow` - 获取北向资金流向
- `get_stock_concept_blocks` - 获取概念板块归属
- `get_stock_fund_flow` - 获取个股资金流向（分钟级）
- `get_dragon_tiger_board` - 获取龙虎榜数据
- `get_lockup_expiry` - 获取限售解禁信息
- `get_industry_rankings` - 获取行业涨跌幅排名

### 资金面数据
- `get_margin_trading` - 获取融资融券数据
- `get_block_trades` - 获取大宗交易
- `get_shareholder_count` - 获取股东户数变化
- `get_dividend_history` - 获取分红送转历史
- `get_fund_flow_120d` - 获取120日资金流向

### 新闻公告
- `get_cls_flash_news` - 获取财联社快讯
- `get_announcements` - 获取股票公告

### 基本面数据
- `get_stock_basic_info` - 获取股票基本信息
- `get_quarterly_report` - 获取季度报告数据
- `get_industry_comparison` - 多股票估值对比

## 安装依赖

```bash
pip3 install "mcp[cli]" mootdx requests pandas stockstats
```

## 使用方式

### 1. 直接运行MCP服务

```bash
python3 a_stock_data_mcp.py
```

服务将启动并监听stdio输入，可以与支持MCP的AI助手配合使用。

### 2. 在Python中使用核心功能

```python
from a_stock_data_core import get_stock_quote, get_market_index
import json

# 获取股票行情
result = get_stock_quote('600519')
print(json.dumps(result, ensure_ascii=False, indent=2))

# 获取大盘指数
result = get_market_index()
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 3. 在Claude等AI助手中使用

将MCP服务配置到AI助手的MCP服务器配置中，即可通过对话方式查询A股数据。

## 数据来源

- **mootdx** - TCP行情数据（连通达信服务器）
- **腾讯财经API** - PE/PB/市值/换手率
- **百度股市通** - K线带MA、资金流向
- **东财研报API** - 研报列表、PDF下载
- **同花顺** - 热点题材、一致预期
- **iwencai** - 语义搜索研报（需API Key）
- **东方财富数据中心** - 龙虎榜、解禁、融资融券等

## 环境要求

- Python 3.10+
- macOS/Linux/Windows
- 网络连接（访问A股数据API）

## 注意事项

1. 部分API可能需要网络稳定，偶有超时属于正常现象
2. iwencai语义搜索需要配置API Key
3. 建议使用虚拟环境隔离依赖
4. SSL证书问题：已在代码中处理macOS的SSL验证问题

## 项目结构

```
a-stock-data/
├── a_stock_data_core.py    # 核心功能模块
├── a_stock_data_mcp.py    # MCP服务入口
├── extract_code.py         # 代码提取脚本
├── .gitignore             # Git忽略规则
└── README.md              # 本文件
```

## 测试验证

已验证功能：
- ✅ Python导入正常
- ✅ MCP服务启动成功
- ✅ 22个工具全部注册
- ✅ 实时行情数据获取（以茅台为例）
- ✅ SSL证书问题已修复
- ✅ Git版本管理已初始化

## 许可证

MIT License

## 作者

基于 [simonlin1212/a-stock-data](https://github.com/simonlin1212/a-stock-data) 项目自动生成
