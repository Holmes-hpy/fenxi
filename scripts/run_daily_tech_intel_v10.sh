#!/bin/bash
# 每日科技前沿资讯自动化任务 v10.0
# 执行时间: 每日上午9:30
# 功能: 执行WebSearch资讯分析、缠论分析、反向信号识别、报告生成
# 变更: 使用daily_tech_intel_webssearch.py作为主执行引擎

PROJECT_DIR="/Users/houpengyuan/Documents/trae_projects/a-stock-data"
LOG_DIR="$PROJECT_DIR/logs"
DATE=$(date +%Y-%m-%d)
HOUR=$(date +%H)

if [ "$HOUR" -lt 12 ]; then
    SESSION="上午"
else
    SESSION="下午"
fi

LOG_FILE="$LOG_DIR/daily_tech_intel_v10_${DATE}_${SESSION}.log"

echo "========================================" >> "$LOG_FILE"
echo "科技前沿资讯自动化任务 v10.0 启动【${SESSION}】" >> "$LOG_FILE"
echo "执行日期: $DATE" >> "$LOG_FILE"
echo "执行时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd "$PROJECT_DIR"

# 检查Python环境
PYTHON3=$(which python3)
if [ -z "$PYTHON3" ]; then
    echo "ERROR: python3 not found" >> "$LOG_FILE"
    exit 1
fi

# 检查依赖
python3 -c "import requests; import bs4" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..." >> "$LOG_FILE"
    pip3 install requests beautifulsoup4 2>> "$LOG_FILE"
fi

# 执行主脚本
echo "执行资讯分析（v10 WebSearch增强版）..." >> "$LOG_FILE"
python3 daily_tech_intel_webssearch.py "$SESSION" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "任务执行成功" >> "$LOG_FILE"
    echo "报告位置: $PROJECT_DIR/daily_tech_intel/${DATE}_${SESSION}_tech_intel_report.md" >> "$LOG_FILE"
else
    echo "任务执行失败，请检查日志" >> "$LOG_FILE"
fi

echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "日志已保存至: $LOG_FILE"
