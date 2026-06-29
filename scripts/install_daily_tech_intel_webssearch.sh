#!/bin/bash
# ================================================================================
# MacOS 定时任务安装脚本（WebSearch增强版）
# ================================================================================
# 功能: 安装每日科技前沿资讯自动化任务到MacOS launchd
# 执行时间: 每个工作日 上午9:30 和 下午14:30
# 版本: WebSearch增强版
# ================================================================================

echo "========================================"
echo "🚀 科技前沿资讯自动化任务【WebSearch增强版】- 安装脚本"
echo "========================================"
echo ""

# 项目路径
PROJECT_DIR="/Users/houpengyuan/Documents/trae_projects/a-stock-data"
SCRIPT_FILE="$PROJECT_DIR/scripts/run_daily_tech_intel_webssearch.sh"

PLIST_MORNING_SOURCE="$PROJECT_DIR/config/com.user.dailytechintel.webssearch.morning.plist"
PLIST_AFTERNOON_SOURCE="$PROJECT_DIR/config/com.user.dailytechintel.webssearch.afternoon.plist"

PLIST_MORNING_TARGET="$HOME/Library/LaunchAgents/com.user.dailytechintel.webssearch.morning.plist"
PLIST_AFTERNOON_TARGET="$HOME/Library/LaunchAgents/com.user.dailytechintel.webssearch.afternoon.plist"

# 检查文件是否存在
echo "📋 检查配置文件..."
if [ ! -f "$PLIST_MORNING_SOURCE" ]; then
    echo "❌ 错误: 上午任务plist配置文件不存在"
    echo "   路径: $PLIST_MORNING_SOURCE"
    exit 1
fi
echo "   ✓ 上午任务配置文件存在"

if [ ! -f "$PLIST_AFTERNOON_SOURCE" ]; then
    echo "❌ 错误: 下午任务plist配置文件不存在"
    echo "   路径: $PLIST_AFTERNOON_SOURCE"
    exit 1
fi
echo "   ✓ 下午任务配置文件存在"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "❌ 错误: shell执行脚本不存在"
    echo "   路径: $SCRIPT_FILE"
    exit 1
fi
echo "   ✓ 执行脚本文件存在"

if [ ! -f "$PROJECT_DIR/daily_tech_intel_webssearch.py" ]; then
    echo "❌ 错误: Python分析脚本不存在"
    echo "   路径: $PROJECT_DIR/daily_tech_intel_webssearch.py"
    exit 1
fi
echo "   ✓ Python分析脚本存在"
echo ""

# 给shell脚本添加执行权限
echo "📝 设置脚本执行权限..."
chmod +x "$SCRIPT_FILE"
echo "   ✓ 完成"
echo ""

# 创建必要目录
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/daily_tech_intel"
mkdir -p "$PROJECT_DIR/knowledge"
mkdir -p "$PROJECT_DIR/knowledge_graph"

# 复制plist文件到LaunchAgents目录
echo "📦 安装定时任务配置..."
cp "$PLIST_MORNING_SOURCE" "$PLIST_MORNING_TARGET"
echo "   ✓ 上午任务配置已复制"
cp "$PLIST_AFTERNOON_SOURCE" "$PLIST_AFTERNOON_TARGET"
echo "   ✓ 下午任务配置已复制"
echo ""

# 加载定时任务（先卸载旧的，再加载新的）
echo "⚡ 加载定时任务..."
launchctl unload "$PLIST_MORNING_TARGET" 2>/dev/null
launchctl load "$PLIST_MORNING_TARGET"
echo "   ✓ 上午任务已加载"

launchctl unload "$PLIST_AFTERNOON_TARGET" 2>/dev/null
launchctl load "$PLIST_AFTERNOON_TARGET"
echo "   ✓ 下午任务已加载"
echo ""

# 验证任务是否加载成功
echo "🔍 验证任务状态..."
MORNING_LOADED=$(launchctl list | grep dailytechintel.webssearch.morning)
AFTERNOON_LOADED=$(launchctl list | grep dailytechintel.webssearch.afternoon)

if [ -n "$MORNING_LOADED" ]; then
    echo "   ✅ 上午任务 (dailytechintel.webssearch.morning) - 已加载"
else
    echo "   ❌ 上午任务 - 未加载成功"
fi

if [ -n "$AFTERNOON_LOADED" ]; then
    echo "   ✅ 下午任务 (dailytechintel.webssearch.afternoon) - 已加载"
else
    echo "   ❌ 下午任务 - 未加载成功"
fi
echo ""

echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📋 任务信息:"
echo "   【上午任务 - WebSearch增强版】"
echo "   - 任务名称: com.user.dailytechintel.webssearch.morning"
echo "   - 执行时间: 每个工作日上午 9:30"
echo ""
echo "   【下午任务 - WebSearch增强版】"
echo "   - 任务名称: com.user.dailytechintel.webssearch.afternoon"
echo "   - 执行时间: 每个工作日下午 14:30"
echo ""
echo "📁 目录结构:"
echo "   - 执行脚本: $SCRIPT_FILE"
echo "   - Python脚本: $PROJECT_DIR/daily_tech_intel_webssearch.py"
echo "   - 日志目录: $PROJECT_DIR/logs"
echo "   - 报告目录: $PROJECT_DIR/daily_tech_intel"
echo "   - 知识库: $PROJECT_DIR/knowledge"
echo "   - 知识图谱: $PROJECT_DIR/knowledge_graph"
echo ""
echo "🔧 管理命令:"
echo "   查看任务状态:"
echo "      launchctl list | grep dailytechintel.webssearch"
echo ""
echo "   手动执行上午任务:"
echo "      launchctl start com.user.dailytechintel.webssearch.morning"
echo ""
echo "   手动执行下午任务:"
echo "      launchctl start com.user.dailytechintel.webssearch.afternoon"
echo ""
echo "   停止任务:"
echo "      launchctl stop com.user.dailytechintel.webssearch.morning"
echo "      launchctl stop com.user.dailytechintel.webssearch.afternoon"
echo ""
echo "   卸载任务:"
echo "      launchctl unload $PLIST_MORNING_TARGET"
echo "      launchctl unload $PLIST_AFTERNOON_TARGET"
echo ""
echo "   查看日志:"
echo "      tail -f $PROJECT_DIR/logs/daily_tech_intel_webssearch_*.log"
echo ""
echo "💡 提示:"
echo "   - 任务将在每个工作日（周一至周五）自动执行"
echo "   - 上午9:30: 盘前资讯分析，为开盘做准备"
echo "   - 下午14:30: 午间资讯更新，跟踪下午盘面"
echo "   - 系统版本: WebSearch增强版（通过DuckDuckGo获取真实搜索结果）"
echo "========================================"
