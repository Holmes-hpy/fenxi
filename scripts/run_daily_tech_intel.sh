#!/bin/bash
# ================================================================================
# 每日科技前沿资讯自动化任务 - Shell执行脚本
# ================================================================================
# 执行时间: 每日上午9:30
# 功能: 爬取科技资讯、分析、生成报告、知识沉淀
# ================================================================================

# 设置项目路径
PROJECT_DIR="/Users/houpengyuan/Documents/trae_projects/a-stock-data"
LOG_DIR="$PROJECT_DIR/logs"
REPORT_DIR="$PROJECT_DIR/daily_tech_intel"

# 创建必要目录
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# 获取当前日期
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/daily_tech_intel_$DATE.log"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "🚀 科技前沿资讯自动化任务启动" >> "$LOG_FILE"
echo "📅 执行日期: $DATE" >> "$LOG_FILE"
echo "⏰ 执行时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 切换到项目目录
cd "$PROJECT_DIR"

# 执行Python分析脚本（使用内置示例数据）
echo "📡 执行资讯分析..." >> "$LOG_FILE"
python3 daily_tech_intel_executor.py --date "$DATE" >> "$LOG_FILE" 2>&1

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "✅ 任务执行成功" >> "$LOG_FILE"
    echo "📁 报告位置: $REPORT_DIR/$DATE_tech_intel_report.md" >> "$LOG_FILE"
else
    echo "❌ 任务执行失败，请检查日志" >> "$LOG_FILE"
fi

echo "========================================" >> "$LOG_FILE"
echo "任务完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 输出日志路径
echo "日志已保存至: $LOG_FILE"