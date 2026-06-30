#!/bin/bash
# ================================================================================
# 科技资讯自动化任务 - 简易安装脚本（适用于权限受限环境）
# ================================================================================
# 功能: 使用cron定时任务实现每日下午14:30执行科技资讯爬取
# ================================================================================

PROJECT_DIR="/Users/houpengyuan/Documents/trae_projects/a-stock-data"
SCRIPT_FILE="$PROJECT_DIR/scripts/run_daily_tech_intel.sh"

echo "========================================"
echo "🚀 科技资讯自动化任务安装（cron方式）"
echo "========================================"
echo ""

# 给脚本执行权限
chmod +x "$SCRIPT_FILE"
chmod +x "$PROJECT_DIR/daily_tech_intel_system_v7.py"

# 创建必要目录
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/daily_tech_intel"
mkdir -p "$PROJECT_DIR/knowledge"
mkdir -p "$PROJECT_DIR/knowledge_graph"

echo "✓ 已创建必要目录"
echo ""

# 检查是否已存在cron任务
EXISTING_CRON=$(crontab -l 2>/dev/null | grep "daily_tech_intel")

if [ -n "$EXISTING_CRON" ]; then
    echo "⚠️ 发现已存在的cron任务:"
    echo "$EXISTING_CRON"
    echo ""
    echo "正在更新cron任务..."
    # 删除旧任务
    crontab -l 2>/dev/null | grep -v "daily_tech_intel" | crontab -
fi

# 添加新的cron任务（工作日下午14:30执行）
# 格式: 分 时 日 月 周 命令
# 30 14 * * 1-5 表示周一到周五下午14:30执行
(crontab -l 2>/dev/null; echo "30 14 * * 1-5 $SCRIPT_FILE") | crontab -

echo "✓ 已添加cron定时任务"
echo ""

# 验证cron任务
echo "🔍 验证cron任务:"
crontab -l | grep "daily_tech_intel"
echo ""

echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📋 任务信息:"
echo "   - 执行时间: 每个工作日下午 14:30"
echo "   - 执行脚本: $SCRIPT_FILE"
echo "   - Python脚本: $PROJECT_DIR/daily_tech_intel_system_v7.py"
echo ""
echo "📁 输出目录:"
echo "   - 日志: $PROJECT_DIR/logs"
echo "   - 报告: $PROJECT_DIR/daily_tech_intel"
echo "   - 知识库: $PROJECT_DIR/knowledge"
echo "   - 知识图谱: $PROJECT_DIR/knowledge_graph"
echo ""
echo "🔧 管理命令:"
echo "   查看任务:"
echo "      crontab -l"
echo ""
echo "   手动执行:"
echo "      cd $PROJECT_DIR && python3 daily_tech_intel_system_v7.py 下午"
echo ""
echo "   查看日志:"
echo "      tail -f $PROJECT_DIR/logs/daily_tech_intel_*.log"
echo ""
echo "   编辑任务:"
echo "      crontab -e"
echo ""
echo "   删除任务:"
echo "      crontab -l | grep -v 'daily_tech_intel' | crontab -"
echo ""
echo "💡 提示:"
echo "   - 任务将在每个工作日（周一至周五）下午14:30自动执行"
echo "   - 系统版本: v7.0（十五五规划重点产业跟踪 + 缠论分析 + 反向信号识别）"
echo ""