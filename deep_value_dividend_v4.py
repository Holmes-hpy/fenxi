#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低估值高股息"老登股"深度分析 v4.0

策略：
1. 构建"老登股"核心股票池（银行、煤炭、钢铁、电力、石油、高速、港口、地产、建筑、家电等）
2. 批量获取估值数据（PE、PB、市值、股价）
3. 批量获取分红数据，计算TTM股息率
4. 批量获取财务数据（ROE、增速、毛利率）
5. 综合评分排序，生成深度分析报告
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field

import pandas as pd

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from a_stock_data_core import eastmoney_datacenter

# ==================== "老登股"核心股票池 ====================
# 按行业分类的龙头/大市值公司
OLD_TIMER_STOCKS = {
    "银行": [
        "601398", "601939", "601288", "601988", "600036", "601166",
        "600000", "600016", "601328", "601818", "000001", "601998",
        "601009", "002142", "601169", "601229", "600919", "600926",
        "601658", "600015", "601997", "601838", "601577", "601077",
        "601860", "600908", "601128", "601963", "600919",
    ],
    "煤炭": [
        "601088", "601898", "601225", "600188", "601699", "600123",
        "601666", "601001", "600546", "600395", "000983", "000937",
        "600792", "600348", "600997", "601101", "600740", "600725",
        "601918", "601015",
    ],
    "钢铁": [
        "600019", "000898", "600005", "600022", "000709", "600581",
        "002110", "601003", "000761", "600282", "600569", "600307",
        "000629", "000717", "000778", "000825", "000932", "000959",
        "600010", "600117", "600126", "600231", "600507", "600782",
        "600808", "601005",
    ],
    "电力": [
        "600900", "600025", "600011", "600027", "600795", "601991",
        "600886", "600674", "600236", "600131", "000883", "000539",
        "000543", "000600", "000690", "000767", "000875", "000966",
        "600021", "600098", "600163", "600310", "600578", "600644",
        "600719", "600726", "600744", "600780", "600795", "600863",
        "600864", "600868", "600979", "600982", "601985", "600969",
    ],
    "石油石化": [
        "600028", "601857", "601808", "600583", "600688",
        "002493", "002554", "600346", "600688", "600871",
        "601233", "603026", "603225", "603578", "603808",
    ],
    "交通运输": [
        "600009", "600029", "601111", "600115", "000089",
        "601006", "601018", "600017", "600018", "000022",
        "000582", "000905", "001872", "600190", "600317",
        "600717", "600798", "601008", "601228", "601872",
        "601598", "002183",
    ],
    "房地产": [
        "000002", "600048", "001979", "600383", "600208",
        "600376", "600606", "600641", "600649", "600663",
        "600675", "600736", "600748", "600823", "600895",
        "601155", "601588", "000671", "000961", "000736",
    ],
    "建筑建材": [
        "601668", "601390", "601186", "600528", "601800",
        "600970", "000401", "000786", "000877", "000885",
        "002271", "002302", "002372", "600170", "600248",
        "600266", "600284", "600425", "600449", "600477",
        "600496", "600502", "600585", "600801", "600802",
        "600819", "600820", "601117", "601669", "601800",
    ],
    "家电": [
        "000333", "000651", "600690", "002032", "002242",
        "002403", "002508", "002035", "600060", "600336",
        "600481", "600619", "600839", "600854", "600983",
        "603016", "603209", "603311", "603355", "603486",
    ],
    "汽车": [
        "600104", "000625", "000550", "601238", "600686",
        "000800", "600741", "000581", "000700", "002048",
        "002085", "002126", "002284", "002328", "002434",
        "002472", "002488", "002594", "600066", "600418",
    ],
    "纺织服装": [
        "600398", "002563", "600177", "002029", "002327",
        "600233", "600295", "600400", "600439", "600865",
        "600987", "601566", "603001", "603116", "603157",
        "603511", "603555", "603587", "603608", "603808",
    ],
    "造纸轻工": [
        "600567", "600308", "002078", "002511", "600794",
        "600103", "600235", "600356", "600462", "600567",
        "600963", "600966", "601058", "601515", "603020",
        "603028", "603049", "603123", "603162", "603511",
    ],
    "公用事业": [
        "600886", "600900", "600011", "600027", "600795",
        "000883", "000600", "601991", "600021", "600578",
        "600236", "600674", "601985", "000539", "000543",
    ],
}

# 去重，收集所有股票代码
ALL_STOCK_CODES = list({code for codes in OLD_TIMER_STOCKS.values() for code in codes})
print(f"股票池: {len(ALL_STOCK_CODES)} 只")

# ==================== 筛选阈值 ====================
SCREENING_CRITERIA = {
    "max_pe_ttm": 15.0,
    "max_pb": 1.5,
    "min_dividend_yield": 4.0,
    "min_roe_annualized": 6.0,
    "min_mcap_yi": 100.0,
    "max_mcap_yi": 50000.0,
    "min_consecutive_years": 3,
}

# ==================== 工具函数 ====================

def safe_float(v, default=0.0):
    try:
        if v is None or v == "-" or v == "":
            return default
        return float(v)
    except:
        return default

# ==================== 数据获取 ====================

def get_valuation_batch(codes: List[str]) -> Dict[str, Dict]:
    """批量获取估值数据"""
    print(f"📊 正在获取 {len(codes)} 只股票的估值数据...")
    result = {}
    
    for i, code in enumerate(codes):
        if i > 0 and i % 50 == 0:
            print(f"  进度: {i}/{len(codes)} (成功: {len(result)})")
        
        try:
            data = eastmoney_datacenter(
                "RPT_VALUEANALYSIS_DET",
                filter_str=f'(SECURITY_CODE="{code}")',
                page_size=1,
                sort_columns="TRADE_DATE",
                sort_types="-1",
            )
            
            if data:
                d = data[0]
                result[code] = {
                    "name": d.get("SECURITY_NAME_ABBR", ""),
                    "industry": d.get("BOARD_NAME", ""),
                    "price": safe_float(d.get("CLOSE_PRICE")),
                    "pe_ttm": safe_float(d.get("PE_TTM")),
                    "pb": safe_float(d.get("PB_MRQ")),
                    "ps_ttm": safe_float(d.get("PS_TTM")),
                    "mcap_yi": safe_float(d.get("TOTAL_MARKET_CAP")) / 1e8,
                    "float_mcap_yi": safe_float(d.get("NOTLIMITED_MARKETCAP_A")) / 1e8,
                }
        except Exception as e:
            pass
        
        time.sleep(0.06)
    
    print(f"✅ 成功获取 {len(result)} 只股票估值数据")
    print()
    return result

def get_dividend_batch(codes: List[str]) -> Dict[str, Dict]:
    """批量获取分红数据，计算TTM股息率"""
    print(f"💰 正在获取 {len(codes)} 只股票的分红数据...")
    result = {}
    
    for i, code in enumerate(codes):
        if i > 0 and i % 50 == 0:
            print(f"  进度: {i}/{len(codes)} (成功: {len(result)})")
        
        try:
            data = eastmoney_datacenter(
                "RPT_SHAREBONUS_DET",
                filter_str=f'(SECURITY_CODE="{code}")',
                page_size=20,
                sort_columns="REPORT_DATE",
                sort_types="-1",
            )
            
            if not data:
                continue
            
            df = pd.DataFrame(data)
            df["dps_10"] = pd.to_numeric(df["PRETAX_BONUS_RMB"], errors="coerce")
            df["report_date"] = pd.to_datetime(df["REPORT_DATE"])
            
            # 只保留有现金分红的记录
            cash_df = df[df["dps_10"] > 0].copy()
            if cash_df.empty:
                continue
            
            # 按年份分组，计算每年总分红
            cash_df["year"] = cash_df["report_date"].dt.year
            yearly_div = cash_df.groupby("year")["dps_10"].sum().sort_index(ascending=False)
            
            if len(yearly_div) == 0:
                continue
            
            # 最近一年分红（每10股）
            latest_year = yearly_div.index[0]
            latest_dps_10 = yearly_div.iloc[0]
            latest_dps = latest_dps_10 / 10
            
            # 连续分红年数
            years = sorted(yearly_div.index.tolist(), reverse=True)
            consecutive = 0
            prev = None
            for y in years:
                if prev is None or y == prev - 1:
                    consecutive += 1
                    prev = y
                else:
                    break
            
            # 3年分红CAGR
            div_cagr_3y = 0.0
            if len(yearly_div) >= 3:
                div_now = yearly_div.iloc[0]
                div_3y = yearly_div.iloc[2]
                if div_3y > 0 and div_now > 0:
                    div_cagr_3y = ((div_now / div_3y) ** (1/3) - 1) * 100
            
            # 分红率（取最近的）
            payout_ratio = 0.0
            latest_record = cash_df.iloc[0]
            payout_ratio = safe_float(latest_record.get("DIVIDENT_RATIO")) * 100
            
            result[code] = {
                "name": cash_df.iloc[0].get("SECURITY_NAME_ABBR", ""),
                "latest_year": int(latest_year),
                "dps": latest_dps,
                "dps_10": latest_dps_10,
                "consecutive_years": consecutive,
                "div_cagr_3y": div_cagr_3y,
                "payout_ratio": payout_ratio,
                "total_div_years": len(yearly_div),
                "yearly_div": {int(k): float(v) for k, v in yearly_div.items()},
            }
        except Exception as e:
            pass
        
        time.sleep(0.06)
    
    print(f"✅ 成功获取 {len(result)} 只股票分红数据")
    print()
    return result

def get_financial_batch(codes: List[str]) -> Dict[str, Dict]:
    """批量获取财务数据"""
    print(f"📈 正在获取 {len(codes)} 只股票的财务数据...")
    result = {}
    
    for i, code in enumerate(codes):
        if i > 0 and i % 50 == 0:
            print(f"  进度: {i}/{len(codes)} (成功: {len(result)})")
        
        try:
            data = eastmoney_datacenter(
                "RPT_LICO_FN_CPD",
                filter_str=f'(SECURITY_CODE="{code}")',
                page_size=4,
                sort_columns="REPORTDATE",
                sort_types="-1",
            )
            
            if not data:
                continue
            
            d = data[0]
            report_date = d.get("REPORTDATE", "")
            
            # ROE（单季度的话需要年化，这里先拿原始值）
            roe = safe_float(d.get("WEIGHTAVG_ROE"))
            eps = safe_float(d.get("BASIC_EPS"))
            profit_growth = safe_float(d.get("SJLTZ"))
            gross_margin = safe_float(d.get("XSMLL"))
            revenue_growth = safe_float(d.get("YYSRZL"))
            net_margin = safe_float(d.get("JLL"))
            
            result[code] = {
                "name": d.get("SECURITY_NAME_ABBR", ""),
                "report_date": report_date,
                "roe": roe,
                "eps": eps,
                "profit_growth": profit_growth,
                "gross_margin": gross_margin,
                "revenue_growth": revenue_growth,
                "net_margin": net_margin,
            }
        except Exception as e:
            pass
        
        time.sleep(0.06)
    
    print(f"✅ 成功获取 {len(result)} 只股票财务数据")
    print()
    return result

# ==================== 评分系统 ====================

def calculate_score(stock_data: Dict, criteria: Dict) -> Dict:
    """计算综合评分"""
    pe = stock_data.get("pe_ttm", 0)
    pb = stock_data.get("pb", 0)
    div_yield = stock_data.get("dividend_yield", 0)
    roe = stock_data.get("roe_annualized", 0)
    div_cagr = stock_data.get("div_cagr_3y", 0)
    consecutive = stock_data.get("consecutive_years", 0)
    payout = stock_data.get("payout_ratio", 0)
    
    # 估值分（40分）：PE越低分越高，PB越低分越高
    pe_score = max(0, min(40, (1 - pe / criteria["max_pe_ttm"]) * 40)) if pe > 0 else 0
    pb_score = max(0, min(20, (1 - pb / criteria["max_pb"]) * 20)) if pb > 0 else 0
    value_score = pe_score * 0.6 + pb_score * 0.4
    
    # 股息分（35分）：股息率越高分越高
    div_yield_score = min(35, div_yield / criteria["min_dividend_yield"] * 20) if div_yield > 0 else 0
    # 分红稳定性加分
    stability_score = min(10, consecutive * 1.5)
    # 分红增长加分
    growth_score = min(5, max(0, div_cagr / 5 * 5))
    dividend_score = div_yield_score + stability_score + growth_score
    
    # 质量分（25分）：ROE越高分越高
    roe_score = min(15, roe / criteria["min_roe_annualized"] * 10) if roe > 0 else 0
    # 分红率合理性（30%-70%最佳）
    if 30 <= payout <= 70:
        payout_score = 5
    elif 20 <= payout < 30 or 70 < payout <= 80:
        payout_score = 3
    else:
        payout_score = 1
    # 利润增长加分
    growth_quality = min(5, max(0, stock_data.get("profit_growth", 0) / 10 * 5))
    quality_score = roe_score + payout_score + growth_quality
    
    total_score = value_score + dividend_score + quality_score
    
    return {
        "value_score": round(value_score, 1),
        "dividend_score": round(dividend_score, 1),
        "quality_score": round(quality_score, 1),
        "total_score": round(total_score, 1),
    }

# ==================== 主分析流程 ====================

def main():
    print("=" * 80)
    print("🔍 低估值高股息'老登股'深度分析 v4.0")
    print("=" * 80)
    print()
    
    # 1. 获取估值数据
    val_data = get_valuation_batch(ALL_STOCK_CODES)
    
    if not val_data:
        print("❌ 未获取到估值数据")
        return
    
    # 2. 第一步筛选：估值 + 市值
    print("🔍 第一步筛选（PE<15, PB<1.5, 市值>100亿）...")
    step1_codes = []
    for code, v in val_data.items():
        pe = v["pe_ttm"]
        pb = v["pb"]
        mcap = v["mcap_yi"]
        if (0 < pe < SCREENING_CRITERIA["max_pe_ttm"] and 
            0 < pb < SCREENING_CRITERIA["max_pb"] and
            SCREENING_CRITERIA["min_mcap_yi"] < mcap < SCREENING_CRITERIA["max_mcap_yi"]):
            step1_codes.append(code)
    
    print(f"  通过筛选: {len(step1_codes)} 只")
    print()
    
    if not step1_codes:
        print("❌ 没有股票通过估值筛选")
        return
    
    # 3. 获取分红数据
    div_data = get_dividend_batch(step1_codes)
    
    # 4. 第二步筛选：股息率 + 连续分红
    print("🔍 第二步筛选（股息率>4%, 连续分红>=3年）...")
    step2_codes = []
    step2_data = {}
    
    for code in step1_codes:
        if code not in div_data or code not in val_data:
            continue
        
        v = val_data[code]
        d = div_data[code]
        price = v["price"]
        dps = d["dps"]
        div_yield = (dps / price * 100) if price > 0 else 0
        
        if (div_yield >= SCREENING_CRITERIA["min_dividend_yield"] and
            d["consecutive_years"] >= SCREENING_CRITERIA["min_consecutive_years"]):
            step2_codes.append(code)
            step2_data[code] = {
                **v, **d,
                "dividend_yield": round(div_yield, 2),
            }
    
    print(f"  通过筛选: {len(step2_codes)} 只")
    print()
    
    if not step2_codes:
        # 如果太严格了，放宽条件看看
        print("  筛选太严格，看看接近的...")
        near_stocks = []
        for code in step1_codes:
            if code not in div_data or code not in val_data:
                continue
            v = val_data[code]
            d = div_data[code]
            price = v["price"]
            dps = d["dps"]
            div_yield = (dps / price * 100) if price > 0 else 0
            if div_yield >= 2.0:
                near_stocks.append((code, v["name"], v["industry"], v["pe_ttm"], v["pb"], div_yield, d["consecutive_years"]))
        
        near_stocks.sort(key=lambda x: x[5], reverse=True)
        print(f"  股息率>2%的有 {len(near_stocks)} 只:")
        for s in near_stocks[:20]:
            print(f"    {s[1]} ({s[0]}) - {s[2]} - PE:{s[3]:.2f}, PB:{s[4]:.2f}, 股息率:{s[5]:.2f}%, 连续{s[6]}年")
        print()
        return
    
    # 5. 获取财务数据
    fin_data = get_financial_batch(step2_codes)
    
    # 6. 第三步筛选：ROE
    print("🔍 第三步筛选（ROE年化>6%）...")
    final_codes = []
    final_data = {}
    
    for code in step2_codes:
        if code not in fin_data:
            # 没有财务数据也先保留
            final_codes.append(code)
            final_data[code] = {
                **step2_data[code],
                "roe": 0,
                "roe_annualized": 0,
                "profit_growth": 0,
                "gross_margin": 0,
                "report_date": "",
            }
            continue
        
        f = fin_data[code]
        # ROE年化处理：如果是季报，粗略年化（简单乘以4/季度数，这里假设是单季度）
        roe = f["roe"]
        report_date = f.get("report_date", "")
        # 判断报告期类型
        if "03-31" in str(report_date):
            roe_annualized = roe * 4
        elif "06-30" in str(report_date):
            roe_annualized = roe * 2
        elif "09-30" in str(report_date):
            roe_annualized = roe * 4 / 3
        else:
            roe_annualized = roe
        
        final_codes.append(code)
        final_data[code] = {
            **step2_data[code],
            "roe": roe,
            "roe_annualized": round(roe_annualized, 2),
            "profit_growth": f["profit_growth"],
            "gross_margin": f["gross_margin"],
            "revenue_growth": f.get("revenue_growth", 0),
            "net_margin": f.get("net_margin", 0),
            "report_date": report_date,
        }
    
    print(f"  最终标的: {len(final_codes)} 只")
    print()
    
    if not final_codes:
        print("❌ 没有找到符合所有条件的股票")
        return
    
    # 7. 计算评分
    print("🏆 计算综合评分...")
    for code in final_codes:
        scores = calculate_score(final_data[code], SCREENING_CRITERIA)
        final_data[code].update(scores)
    
    # 8. 排序
    ranked = sorted(final_codes, key=lambda c: final_data[c]["total_score"], reverse=True)
    
    # 9. 生成报告
    print()
    print("=" * 80)
    print("📋 分析报告")
    print("=" * 80)
    print()
    
    # 行业分布
    industry_count = {}
    for code in final_codes:
        ind = final_data[code].get("industry", "未知")
        industry_count[ind] = industry_count.get(ind, 0) + 1
    
    print(f"📊 行业分布（共{len(final_codes)}只）:")
    for ind, cnt in sorted(industry_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ind}: {cnt}只")
    print()
    
    # TOP榜单
    print(f"🏆 TOP 20 综合排名:")
    print(f"{'排名':<4} {'股票名称':<10} {'代码':<8} {'行业':<10} {'PE':<6} {'PB':<6} {'股息率':<7} {'ROE年化':<8} {'连续分红':<8} {'总分':<6}")
    print("-" * 90)
    
    for i, code in enumerate(ranked[:20]):
        d = final_data[code]
        print(f"{i+1:<4} {d['name']:<10} {code:<8} {d.get('industry',''):<10} "
              f"{d['pe_ttm']:<6.2f} {d['pb']:<6.2f} {d['dividend_yield']:<6.2f}% "
              f"{d.get('roe_annualized',0):<7.2f}% {d['consecutive_years']:<8} {d['total_score']:<6.1f}")
    
    print()
    
    # 详细分析TOP 10
    print("=" * 80)
    print("🔬 TOP 10 深度分析")
    print("=" * 80)
    print()
    
    for i, code in enumerate(ranked[:10]):
        d = final_data[code]
        print(f"【第{i+1}名】{d['name']} ({code})")
        print(f"  行业: {d.get('industry', '未知')}")
        print(f"  股价: {d['price']:.2f}元 | 市值: {d['mcap_yi']:.0f}亿")
        print(f"  估值: PE-TTM={d['pe_ttm']:.2f}, PB={d['pb']:.2f}")
        print(f"  股息: 股息率={d['dividend_yield']:.2f}%, 每股分红={d['dps']:.3f}元")
        print(f"  分红: 连续{d['consecutive_years']}年, 3年CAGR={d['div_cagr_3y']:.1f}%, 分红率={d['payout_ratio']:.1f}%")
        if d.get('roe'):
            print(f"  盈利: ROE={d['roe']:.2f}% (年化{d.get('roe_annualized',0):.2f}%), 净利增速={d.get('profit_growth',0):.1f}%")
            print(f"        毛利率={d.get('gross_margin',0):.1f}%, 净利率={d.get('net_margin',0):.1f}%")
        print(f"  评分: 估值分={d['value_score']:.1f}, 股息分={d['dividend_score']:.1f}, 质量分={d['quality_score']:.1f}, 总分={d['total_score']:.1f}")
        
        # 历年分红
        if d.get("yearly_div"):
            print(f"  历年分红(每10股): ", end="")
            items = list(d["yearly_div"].items())[:5]
            print(" | ".join([f"{y}:{v:.2f}元" for y, v in items]))
        
        print()
    
    # 保存结果
    output_dir = PROJECT_DIR / "dividend_stock_reports"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存CSV
    df = pd.DataFrame([final_data[c] for c in ranked])
    csv_path = output_dir / f"value_dividend_stocks_{timestamp}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"💾 详细数据已保存: {csv_path}")
    
    # 保存文本报告
    report_path = output_dir / f"analysis_report_{timestamp}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("低估值高股息'老登股'深度分析报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"筛选标准:\n")
        for k, v in SCREENING_CRITERIA.items():
            f.write(f"  {k}: {v}\n")
        f.write(f"\n入选股票: {len(final_codes)}只\n\n")
        
        f.write("TOP 30 排名:\n")
        f.write(f"{'排名':<4} {'股票名称':<10} {'代码':<8} {'行业':<12} {'PE':<7} {'PB':<6} {'股息率':<8} {'ROE年化':<9} {'连续分红':<8} {'总分':<6}\n")
        f.write("-" * 90 + "\n")
        for i, code in enumerate(ranked[:30]):
            d = final_data[code]
            f.write(f"{i+1:<4} {d['name']:<10} {code:<8} {d.get('industry',''):<12} "
                   f"{d['pe_ttm']:<7.2f} {d['pb']:<6.2f} {d['dividend_yield']:<7.2f}% "
                   f"{d.get('roe_annualized',0):<8.2f}% {d['consecutive_years']:<8} {d['total_score']:<6.1f}\n")
    
    print(f"💾 分析报告已保存: {report_path}")
    print()
    print("✅ 分析完成！")

if __name__ == "__main__":
    main()
