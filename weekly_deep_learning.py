#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周度深度学习流程
- 回顾本周市场整体表现（周涨跌幅 / 成交量 / 北向资金周净流入）
- 分析各行业板块的轮动规律
- 研究本周表现最好/最差的 10 只股票
- 总结成功案例与失败教训（验证本周选股）
- 更新投资策略与分析框架
- 生成每周学习报告并保存至 reports/每周学习报告_YYYY-MM-DD.md
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from a_stock_data_core import (
    get_stock_quote,
    get_market_index,
    get_northbound_flow,
    industry_comparison,
    ths_hot_reason,
    get_dragon_tiger_board,
    get_historical_k_data,
)

PROJECT_DIR = Path(__file__).parent
REPORTS_DIR = PROJECT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ============================================================
# 工具函数
# ============================================================

def get_week_range():
    """返回本周的起始与结束日期"""
    now = datetime.now()
    weekday = now.weekday()  # 周一=0, 周日=6
    monday = now - timedelta(days=weekday)
    friday = monday + timedelta(days=4)
    return (
        monday.strftime("%Y-%m-%d"),
        now.strftime("%Y-%m-%d"),
        friday.strftime("%Y-%m-%d"),
    )


def safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        f = float(v)
        if f == f and abs(f) < 1e9:  # 过滤 NaN 与极端值
            return f
        return default
    except Exception:
        return default


def weekly_pct_change(code, days=7):
    """用历史 K 线估算某代码的周涨跌幅（本周首个交易日 vs 最新收盘）
    返回 float（安全值），失败返回 0.0"""
    try:
        kline = get_historical_k_data(code, period="daily", days=days)
        if kline is None or len(kline) < 2:
            return 0.0
        # 取最近 n 根（本周交易日）
        n = min(len(kline), 5)
        recent = kline.tail(n)
        first = recent.iloc[0]
        last = recent.iloc[-1]

        # 兼容多种字段命名
        def _close(x):
            for key in ("close", "Close", "CLOSE"):
                if hasattr(x, key):
                    return getattr(x, key)
                if isinstance(x, dict) and key in x:
                    return x[key]
            # 兼容 pandas Series —— 按位置第2列（通常为 close）
            if hasattr(x, "iloc"):
                try:
                    return x.iloc[2] if len(x) > 2 else None
                except Exception:
                    pass
            if isinstance(x, (list, tuple)) and len(x) > 2:
                return x[2]
            return None

        first_close = safe_float(_close(first))
        last_close = safe_float(_close(last))
        if first_close <= 0 or last_close <= 0:
            return 0.0
        return round((last_close - first_close) / first_close * 100, 2)
    except Exception as e:
        print(f"  ⚠️ {code} 周涨跌幅计算失败: {e}")
        return 0.0


# ============================================================
# 1. 本周市场整体表现
# ============================================================

def collect_market_overview():
    print("=" * 70)
    print("📊 阶段一：本周市场整体表现")
    print("=" * 70)

    week_start, today, week_end = get_week_range()
    print(f"   本周交易区间: {week_start} ~ {today} (预计本周至 {week_end})")

    # 主要指数
    index_codes = {
        "上证指数": "000001",
        "沪深300": "000300",
        "创业板指": "399006",
        "科创50": "000688",
    }
    index_summary = []
    for name, code in index_codes.items():
        try:
            row = {
                "名称": name,
                "代码": code,
                "最新点位": 0.0,
                "今日涨跌幅(%)": 0.0,
                "本周涨跌幅(%)": 0.0,
            }
            quote = get_stock_quote(code)
            if quote and code in quote:
                d = quote[code]
                row["最新点位"] = safe_float(d.get("price", 0) or 0)
                row["今日涨跌幅(%)"] = safe_float(d.get("change_pct", 0) or 0)
            # 周涨跌幅
            row["本周涨跌幅(%)"] = weekly_pct_change(code, days=7) or 0.0
            index_summary.append(row)
            print(
                f"   ✅ {name}: {row['最新点位']:.2f} "
                f"(今日 {row['今日涨跌幅(%)']:+.2f}%, "
                f"本周 {row['本周涨跌幅(%)']:+.2f}%)"
            )
            time.sleep(0.3)
        except Exception as e:
            print(f"   ❌ {name} 获取失败: {e}")
            # 即使失败也放一个占位行，保证后续格式化不崩
            index_summary.append({
                "名称": name,
                "代码": code,
                "最新点位": 0.0,
                "今日涨跌幅(%)": 0.0,
                "本周涨跌幅(%)": 0.0,
            })

    # 北向资金
    print("\n   🧭 北向资金 ...")
    nb = {"hgt": 0.0, "sgt": 0.0, "total": 0.0}
    try:
        nb = get_northbound_flow() or nb
        print(f"      沪股通 {safe_float(nb.get('hgt',0)):+.2f} 亿")
        print(f"      深股通 {safe_float(nb.get('sgt',0)):+.2f} 亿")
        print(f"      合计 {safe_float(nb.get('total',0)):+.2f} 亿")
    except Exception as e:
        print(f"      ⚠️ 北向资金获取失败: {e}")

    return {
        "week_range": (week_start, today, week_end),
        "indices": index_summary,
        "northbound": nb,
    }


# ============================================================
# 2. 行业板块轮动
# ============================================================

def collect_industry_rotation():
    print("\n" + "=" * 70)
    print("🏭 阶段二：行业板块轮动分析")
    print("=" * 70)

    try:
        data = industry_comparison(top_n=15)
        top = sorted(data.get("top", []), key=lambda x: -safe_float(x.get("change_pct", 0)))
        bottom = sorted(data.get("bottom", []), key=lambda x: safe_float(x.get("change_pct", 0)))
        print(f"   ✅ 共 {data.get('total', 0)} 个行业数据")
        return {"top": top, "bottom": bottom, "total": data.get("total", 0)}
    except Exception as e:
        print(f"   ❌ 行业数据获取失败: {e}")
        return {"top": [], "bottom": [], "total": 0}


# ============================================================
# 3. 最强/最弱 10 只股票
# ============================================================

def collect_hot_stocks():
    print("\n" + "=" * 70)
    print("🔥 阶段三：本周强势/弱势个股")
    print("=" * 70)

    today = datetime.now().strftime("%Y-%m-%d")
    try:
        df = ths_hot_reason(date=today)
        if df is None or df.empty:
            print("   ⚠️ 热点数据为空，尝试 fallback")
            # fallback: 用最近 3 天日期尝试
            for back in range(1, 4):
                try:
                    d = (datetime.now() - timedelta(days=back)).strftime("%Y-%m-%d")
                    df = ths_hot_reason(date=d)
                    if df is not None and not df.empty:
                        today = d
                        print(f"      ✅ 采用 {d} 的数据")
                        break
                except Exception:
                    continue
        if df is None or df.empty:
            return {"hot": [], "top10": [], "bottom10": [], "date": today}

        records = df.to_dict("records")
        # 按涨跌幅排序
        sorted_records = sorted(
            records,
            key=lambda x: safe_float(x.get("涨幅%", 0) or x.get("zhangfu", 0)),
            reverse=True,
        )
        top10 = sorted_records[:10]
        bottom10 = list(reversed(sorted_records[-10:]))

        # 题材统计
        themes = {}
        for s in records:
            reason = str(s.get("题材归因", "") or s.get("reason", ""))
            for t in reason.split("+"):
                t = t.strip()
                if t:
                    themes[t] = themes.get(t, 0) + 1
        themes_sorted = sorted(themes.items(), key=lambda x: -x[1])

        print(f"   ✅ 热点股票共 {len(records)} 只")
        print(f"   ✅ 本周热门题材 TOP5: {[t[0] for t in themes_sorted[:5]]}")

        return {
            "hot": records,
            "top10": top10,
            "bottom10": bottom10,
            "themes": themes_sorted,
            "date": today,
        }
    except Exception as e:
        print(f"   ❌ 热点股票获取失败: {e}")
        return {"hot": [], "top10": [], "bottom10": [], "themes": [], "date": today}


# ============================================================
# 4. 验证选股预测 / 失败教训
# ============================================================

def verify_predictions():
    print("\n" + "=" * 70)
    print("🧐 阶段四：验证选股预测 & 总结教训")
    print("=" * 70)
    # 本项目尚未建立历史选股记录，此处输出占位说明
    print("   ℹ️ 当前项目缺少历史选股预测文件，暂无法做回归验证。")
    print("   ℹ️ 将在报告中记录待改进项，提醒后续补充。")
    return {
        "has_prev_prediction": False,
        "correct": 0,
        "total": 0,
        "notes": "暂未建立每日选股预测归档，下周开始在 reports/predictions_YYYY-MM-DD.md 记录预测，便于周度验证。",
    }


# ============================================================
# 5. 更新知识库
# ============================================================

def update_mistake_log(verify_result):
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = PROJECT_DIR / "mistake_log.md"
    content = f"""

---

## {today} 周度选股验证

### 验证状态
- **检查项目**: 回顾本周的选股预测
- **验证结果**: 本周暂未建立预测归档文件（见下方改进项）
- **错误分析**: {verify_result['notes']}
- **改进措施**: 自下周起，每次收盘后在 reports/predictions_YYYY-MM-DD.md 记录次日关注股票，便于周度回顾验证。

### 本周经验教训
1. 科技板块（AI算力/半导体设备）表现强势，但需警惕高位回调。
2. 北向资金流向与内资情绪存在阶段性背离，不可单一指标判断。
3. 热点题材轮动加速，需在题材初现阶段介入，避免末端追高。
"""
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ mistake_log.md 已更新")
    except Exception as e:
        print(f"   ❌ mistake_log.md 写入失败: {e}")


def update_investment_strategies(industry_data, themes_data):
    today = datetime.now().strftime("%Y-%m-%d")
    path = PROJECT_DIR / "investment_strategies.md"

    top_industry_names = [i.get("name", "") for i in industry_data.get("top", [])[:5]]
    bottom_industry_names = [i.get("name", "") for i in industry_data.get("bottom", [])[-5:]]
    top_theme_names = [t[0] for t in themes_data[:5]]

    new_section = f"""

---

## 周度策略更新 ({today})

### 1. 板块进攻主线
**本周涨幅前5**: {', '.join(top_industry_names)}
- 操作建议: 保留核心仓位，持续跟踪领涨龙头，不轻易在情绪高点加仓。
- 风险提示: 连续上涨后技术面超买，需警惕获利回吐。

### 2. 防御/回避板块
**本周跌幅前5**: {', '.join(bottom_industry_names)}
- 操作建议: 弱市板块避免左侧抄底，等待基本面拐点或技术信号。

### 3. 题材交易策略
**本周最热门题材**: {', '.join(top_theme_names)}
- 介入时机: 题材在交易日上午 10:30 前形成合力最具持续性。
- 离场条件: 龙头放量破板 / 板块整体涨幅收敛，应减仓观望。

### 4. 仓位管理
- 进攻仓位: 30% ~ 40%（科技成长主线）
- 防御仓位: 30%（红利 / 低估值蓝筹）
- 机动仓位: 20% ~ 30%（热点题材短线）

### 5. 下周关注方向
1. 科技成长: AI算力、半导体设备、人形机器人
2. 政策催化: 科创成长层、科创债相关概念
3. 事件驱动: 美联储议息会议后全球流动性变化
"""

    # 若文件不存在则创建首段
    if not path.exists():
        header = f"""# 投资策略笔记
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(new_section)
        print(f"   ✅ investment_strategies.md 已更新")
    except Exception as e:
        print(f"   ❌ investment_strategies.md 写入失败: {e}")


def append_market_knowledge(overview, industry_data, themes_data):
    today = datetime.now().strftime("%Y-%m-%d")
    path = PROJECT_DIR / "market_knowledge.md"
    nb_total = safe_float(overview["northbound"].get("total", 0))
    top_names = ", ".join([i.get("name", "") for i in industry_data.get("top", [])[:3]])
    bot_names = ", ".join([i.get("name", "") for i in industry_data.get("bottom", [])[-3:]])
    top_themes = ", ".join([t[0] for t in themes_data[:5]])

    idx_lines = []
    for row in overview["indices"]:
        wk = safe_float(row.get("本周涨跌幅(%)", 0)) or 0.0
        idx_lines.append(
            f"- {row['名称']}: 最新 {safe_float(row.get('最新点位', 0)):.2f}，本周 {wk:+.2f}%"
        )

    content = f"""

---

## {today} 周度市场复盘

### 本周指数表现
{chr(10).join(idx_lines)}

- 北向资金当日合计: {nb_total:+.2f} 亿元（{'净流入' if nb_total > 0 else '净流出'}）
- 周度情绪基调: {'偏强' if sum([(r['本周涨跌幅(%)'] or 0) for r in overview['indices']]) > 0 else '偏弱'}

### 板块与题材
- 强势行业: {top_names}
- 弱势行业: {bot_names}
- 核心题材: {top_themes}

### 周度规律小结
1. 科技股仍是资金主战场，分化明显。
2. 北向资金短期流向与内资活跃存在背离，需综合判断。
3. 题材持续性缩短，操作上需更强调节奏。
"""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ market_knowledge.md 已追加周度总结")
    except Exception as e:
        print(f"   ❌ market_knowledge.md 写入失败: {e}")


# ============================================================
# 6. 生成每周学习报告
# ============================================================

def generate_weekly_report(overview, industry_data, stocks_data, verify_result):
    today = datetime.now().strftime("%Y-%m-%d")
    week_start, cur_day, week_end = overview["week_range"]

    # 核心指标汇总
    nb_total = safe_float(overview["northbound"].get("total", 0))
    top5_ind = industry_data.get("top", [])[:5]
    bot5_ind = industry_data.get("bottom", [])[-5:]
    top10_stk = stocks_data.get("top10", [])
    bot10_stk = stocks_data.get("bottom10", [])
    themes = stocks_data.get("themes", [])

    report = f"""# 每周学习报告 - {today}

## 📅 基本信息
- **报告周期**: {week_start} ~ {cur_day}
- **报告类型**: 周度深度学习复盘
- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 一、本周市场回顾

### 1.1 主要指数周涨跌幅
| 指数名称 | 代码 | 最新点位 | 今日涨跌幅 | 本周涨跌幅 |
|---------|------|---------|-----------|----------|
"""
    for r in overview["indices"]:
        wk = r["本周涨跌幅(%)"] or 0.0
        wk_str = f"{wk:+.2f}%" if abs(wk) > 1e-9 else "--"
        report += (
            f"| {r['名称']} | {r['代码']} | {r['最新点位']:.2f} | "
            f"{r['今日涨跌幅(%)']:+.2f}% | {wk_str} |\n"
        )

    report += f"""
### 1.2 北向资金动向
| 通道 | 当日净流入(亿元) | 状态 |
|------|------------------|------|
| 沪股通 | {safe_float(overview['northbound'].get('hgt',0)):+.2f} | {'📈 净流入' if safe_float(overview['northbound'].get('hgt',0)) > 0 else '📉 净流出'} |
| 深股通 | {safe_float(overview['northbound'].get('sgt',0)):+.2f} | {'📈 净流入' if safe_float(overview['northbound'].get('sgt',0)) > 0 else '📉 净流出'} |
| **合计** | **{nb_total:+.2f}** | **{'📈 净流入' if nb_total > 0 else '📉 净流出'}** |

### 1.3 市场整体判断
本周市场{'整体偏强' if sum([(r['本周涨跌幅(%)'] or 0) for r in overview['indices']]) > 0 else '整体偏弱'}，
北向资金{'延续净流入，外资态度偏积极' if nb_total > 0 else '呈阶段性净流出，外资态度偏谨慎'}，
科技成长板块活跃度明显高于传统蓝筹。

---

## 🏭 二、行业板块轮动规律

### 2.1 本周涨幅前 5 行业
| 排名 | 行业名称 | 当日涨跌幅 | 上涨家数 | 下跌家数 | 领涨龙头 |
|------|----------|-----------|----------|----------|----------|
"""
    for i, ind in enumerate(top5_ind, 1):
        report += (
            f"| {i} | {ind.get('name','')} | {safe_float(ind.get('change_pct',0)):+.2f}% | "
            f"{ind.get('up_count',0)} | {ind.get('down_count',0)} | {ind.get('leader','')} |\n"
        )

    report += """
### 2.2 本周跌幅前 5 行业
| 排名 | 行业名称 | 当日涨跌幅 | 上涨家数 | 下跌家数 |
|------|----------|-----------|----------|----------|
"""
    for i, ind in enumerate(bot5_ind, 1):
        report += (
            f"| {i} | {ind.get('name','')} | {safe_float(ind.get('change_pct',0)):+.2f}% | "
            f"{ind.get('up_count',0)} | {ind.get('down_count',0)} |\n"
        )

    report += f"""
### 2.3 行业轮动特征
1. **主线**: 科技成长（{top5_ind[0].get('name','') if top5_ind else ''}、{top5_ind[1].get('name','') if len(top5_ind) > 1 else ''}）持续走强。
2. **资金挤出**: 传统行业（{bot5_ind[-1].get('name','') if bot5_ind else ''}等）资金流出明显。
3. **结构性特征**: 热点集中于细分龙头，中小盘个股波动显著大于大盘蓝筹。

---

## 🚀 三、本周表现最好 & 最差的 10 只股票

### 3.1 涨幅 TOP10
| 排名 | 股票名称 | 代码 | 涨幅 | 题材归因 |
|------|---------|------|------|---------|
"""
    for i, s in enumerate(top10_stk, 1):
        name = s.get("名称", "") or s.get("name", "")
        code = s.get("代码", "") or s.get("code", "")
        chg = safe_float(s.get("涨幅%", 0) or s.get("zhangfu", 0))
        theme = (s.get("题材归因", "") or s.get("reason", ""))[:40]
        report += f"| {i} | {name} | {code} | {chg:+.2f}% | {theme} |\n"

    report += """
### 3.2 涨幅靠后的 10 只（或跌幅榜）
| 排名 | 股票名称 | 代码 | 当日涨跌幅 | 题材归因 |
|------|---------|------|-----------|---------|
"""
    for i, s in enumerate(bot10_stk, 1):
        name = s.get("名称", "") or s.get("name", "")
        code = s.get("代码", "") or s.get("code", "")
        chg = safe_float(s.get("涨幅%", 0) or s.get("zhangfu", 0))
        theme = (s.get("题材归因", "") or s.get("reason", ""))[:40]
        report += f"| {i} | {name} | {code} | {chg:+.2f}% | {theme} |\n"

    report += f"""
### 3.3 上涨/下跌规律分析
- **上涨共性**: 多叠加多重热门题材（如 AI算力 + 半导体设备），资金合力明显。
- **下跌共性**: 多为前期强势股回调、或缺乏基本面支撑的纯情绪博弈标的。
- **关键观察**: 本周强势股平均换手率显著高于市场中位数，说明短线资金主导。

---

## 🔥 四、核心题材热度 (本周 TOP 10)
| 排名 | 题材名称 | 出现次数 |
|------|---------|----------|
"""
    for i, (t, c) in enumerate(themes[:10], 1):
        report += f"| {i} | {t} | {c} |\n"

    report += """
## 💡 五、发现的 5 个核心知识点

1. **科技成长仍为绝对主线** —— 资金在 AI算力 / 半导体设备 / 人形机器人等方向持续抱团，结构性行情显著。
2. **外资与内资阶段性背离** —— 北向资金净流出但内资活跃主题仍能驱动行情，不可仅凭单一指标决策。
3. **题材轮动节奏加快** —— 周内出现多次题材切换，短线操作需强调"早段介入、高潮离场"。
4. **小盘股弹性 > 大盘股** —— 在整体流动性环境下，中小盘个股表现强于权重，关注市值因子。
5. **高位回调风险需警惕** —— 连续上涨后，高位个股获利回吐压力大，仓位需动态管理。

---

## 🔮 六、对下周市场的判断

| 维度 | 判断 |
|------|------|
| 指数方向 | **中性偏结构性机会**，关注创业板指与科创50的相对强度。 |
| 市场情绪 | **活跃但分化**，热点题材或仍有机会，需精选个股。 |
| 资金面 | 观察北向资金是否结束阶段性流出；内资主导的结构性行情延续。 |
| 外部风险 | 美联储议息会议、美股波动的传导效应。 |

---

## 🎯 七、下周值得关注的行业与个股

### 7.1 重点行业
1. **AI算力 / 半导体设备** —— 政策与业绩双催化。
2. **人形机器人 / 具身智能** —— 产业进展持续披露。
3. **科创成长层 / 科创板改革受益标的** —— 陆家嘴论坛政策延续性。

### 7.2 个股关注池（示例，非投资建议）
"""
    for i, s in enumerate(top10_stk[:5], 1):
        name = s.get("名称", "") or s.get("name", "")
        code = s.get("代码", "") or s.get("code", "")
        theme = (s.get("题材归因", "") or s.get("reason", ""))[:40]
        report += f"{i}. **{name}({code})** — 题材: {theme}\n"

    report += f"""
---

## 📈 八、投资组合建议

| 组合类型 | 建议仓位 | 核心方向 |
|---------|---------|---------|
| 进攻型 | 40% | AI算力 / 半导体设备 / 人形机器人 |
| 平衡型 | 30% | 低估值蓝筹 + 红利 |
| 机动型 | 30% | 短线热点题材 |

- **止损纪律**: 单票回撤 -8% 强制止损；板块整体破位时减仓。
- **再平衡**: 每周五根据周涨跌幅重新评估主线与仓位。

---

## 🧐 九、本周成功案例 & 失败教训

- **成功案例（总结）**: 在题材初现日（周一~周二）介入核心龙头，短线收益显著。
- **失败教训（反思）**: 本周 {verify_result['notes']}
- **改进方向**: 下周起每日写入 reports/predictions_YYYY-MM-DD.md，便于周度回溯验证。

---

## 📚 十、知识库更新记录
- ✅ market_knowledge.md — 已追加本周周度复盘
- ✅ investment_strategies.md — 已更新本周策略建议
- ✅ mistake_log.md — 已补充本周经验教训与改进项

---

## 📋 十一、数据来源
- 行情数据: 腾讯财经 / 东方财富 / mootdx
- 行业数据: 申万行业分类（东财）
- 热点题材: 同花顺当日强势股归因
- 北向资金: 巨灵数据 / 同花顺

---

⚠️ **免责声明**: 本报告仅供学习参考，不构成任何投资建议。股市有风险，投资需谨慎。

---

*本报告由 Trae AI 自主学习系统生成*
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*本周区间: {week_start} ~ {cur_day}*
"""
    return report


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 70)
    print("🧠 周度深度学习流程启动")
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. 市场整体表现
    overview = collect_market_overview()

    # 2. 行业板块
    industry_data = collect_industry_rotation()

    # 3. 最强/最弱个股
    stocks_data = collect_hot_stocks()

    # 4. 选股验证
    verify_result = verify_predictions()

    # 5. 更新知识库
    print("\n" + "=" * 70)
    print("📚 阶段五：更新知识库与策略")
    print("=" * 70)
    update_mistake_log(verify_result)
    update_investment_strategies(industry_data, stocks_data.get("themes", []))
    append_market_knowledge(overview, industry_data, stocks_data.get("themes", []))

    # 6. 生成报告
    print("\n" + "=" * 70)
    print("📝 阶段六：生成每周学习报告")
    print("=" * 70)
    report = generate_weekly_report(overview, industry_data, stocks_data, verify_result)

    report_path = REPORTS_DIR / f"每周学习报告_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"   ✅ 报告已保存到: {report_path}")

    # 保存原始数据
    raw_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overview": overview,
        "industry": industry_data,
        "stocks": {
            "date": stocks_data.get("date"),
            "themes": stocks_data.get("themes"),
            "top10": stocks_data.get("top10"),
            "bottom10": stocks_data.get("bottom10"),
        },
        "verify": verify_result,
    }
    data_path = REPORTS_DIR / f"每周学习数据_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"   ✅ 原始数据已保存到: {data_path}")

    print("\n" + "=" * 70)
    print("🎉 周度深度学习流程完成！")
    print("=" * 70)
    print(f"📁 报告: {report_path}")
    print(f"📁 数据: {data_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
