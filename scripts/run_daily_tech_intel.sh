#!/bin/bash
# ================================================================================
# 每日科技前沿资讯自动化任务 - Shell执行脚本（v7.0增强版）
# ================================================================================
# 执行时间: 每日上午9:30 和 下午14:30
# 功能: 爬取科技资讯、分析、生成报告、知识沉淀、反向信号识别
# 版本: v7.0
# ================================================================================

# 设置项目路径
PROJECT_DIR="/Users/houpengyuan/Documents/trae_projects/a-stock-data"
LOG_DIR="$PROJECT_DIR/logs"
REPORT_DIR="$PROJECT_DIR/daily_tech_intel"
KNOWLEDGE_DIR="$PROJECT_DIR/knowledge"
GRAPH_DIR="$PROJECT_DIR/knowledge_graph"

# 创建必要目录
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"
mkdir -p "$KNOWLEDGE_DIR"
mkdir -p "$GRAPH_DIR"

# 获取当前日期和小时
DATE=$(date +%Y-%m-%d)
HOUR=$(date +%H)

# 判断是上午还是下午
if [ "$HOUR" -lt 12 ]; then
    SESSION="上午"
else
    SESSION="下午"
fi

LOG_FILE="$LOG_DIR/daily_tech_intel_${DATE}_${SESSION}.log"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "🚀 科技前沿资讯自动化任务 v7.0 启动【${SESSION}】" >> "$LOG_FILE"
echo "📅 执行日期: $DATE" >> "$LOG_FILE"
echo "⏰ 执行时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 切换到项目目录
cd "$PROJECT_DIR"

# 执行Python分析脚本（RSS独立爬虫版）
echo "📡 执行资讯分析（RSS Crawler v4.0）..." >> "$LOG_FILE"
python3 daily_tech_intel_rss_crawler.py >> "$LOG_FILE" 2>&1

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "✅ 任务执行成功" >> "$LOG_FILE"
    echo "📁 报告位置: $REPORT_DIR/${DATE}_${SESSION}_tech_intel_report.md" >> "$LOG_FILE"
    echo "📊 数据位置: $REPORT_DIR/${DATE}_${SESSION}_tech_intel_data.json" >> "$LOG_FILE"
    echo "🧠 知识图谱: $GRAPH_DIR/${DATE}_${SESSION}_knowledge_graph.json" >> "$LOG_FILE"
else
    echo "❌ 任务执行失败，请检查日志" >> "$LOG_FILE"
fi

echo "========================================" >> "$LOG_FILE"
echo "任务完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 输出日志路径
echo "日志已保存至: $LOG_FILE"
