#!/bin/bash
# ================================================================================
# MacOS 定时任务安装脚本
# ================================================================================
# 功能: 安装每日科技前沿资讯自动化任务到MacOS launchd
# 执行时间: 每日上午9:30
# ================================================================================

echo "========================================"
echo "🚀 科技前沿资讯自动化任务 - 安装脚本"
echo "========================================"
echo ""

# 项目路径
PROJECT_DIR="/Users/houpengyuan/Documents/trae_projects/a-stock-data"
PLIST_SOURCE="$PROJECT_DIR/config/com.user.dailytechintel.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.user.dailytechintel.plist"
SCRIPT_FILE="$PROJECT_DIR/scripts/run_daily_tech_intel.sh"

# 检查文件是否存在
if [ ! -f "$PLIST_SOURCE" ]; then
    echo "❌ 错误: plist配置文件不存在"
    echo "   路径: $PLIST_SOURCE"
    exit 1
fi

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "❌ 错误: shell执行脚本不存在"
    echo "   路径: $SCRIPT_FILE"
    exit 1
fi

# 给shell脚本添加执行权限
echo "📝 设置脚本执行权限..."
chmod +x "$SCRIPT_FILE"

# 创建LaunchAgents目录（如果不存在）
mkdir -p "$HOME/Library/LaunchAgents"

# 复制plist文件到LaunchAgents目录
echo "📦 安装定时任务配置..."
cp "$PLIST_SOURCE" "$PLIST_TARGET"

# 加载定时任务
echo "⚡ 加载定时任务..."
launchctl unload "$PLIST_TARGET" 2>/dev/null  # 先卸载（如果已存在）
launchctl load "$PLIST_TARGET"

# 验证任务是否加载成功
echo ""
echo "🔍 验证任务状态..."
launchctl list | grep dailytechintel

echo ""
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📋 任务信息:"
echo "   - 任务名称: com.user.dailytechintel"
echo "   - 执行时间: 每日上午 9:30"
echo "   - 执行脚本: $SCRIPT_FILE"
echo "   - 日志目录: $PROJECT_DIR/logs"
echo "   - 报告目录: $PROJECT_DIR/daily_tech_intel"
echo ""
echo "🔧 管理命令:"
echo "   - 查看任务状态: launchctl list | grep dailytechintel"
echo "   - 手动执行任务: launchctl start com.user.dailytechintel"
echo "   - 停止任务: launchctl stop com.user.dailytechintel"
echo "   - 卸载任务: launchctl unload $PLIST_TARGET"
echo "   - 查看日志: tail -f $PROJECT_DIR/logs/daily_tech_intel_*.log"
echo ""
echo "💡 提示: 任务将在每个工作日上午9:30自动执行"
echo "========================================"