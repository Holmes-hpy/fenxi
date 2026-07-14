#!/bin/bash
# 安装每日科技资讯自动化任务 v10.0
# 使用macOS launchd实现每日9:30自动执行

PLIST_NAME="com.user.dailytechintel.v10.morning"
PLIST_SRC="/Users/houpengyuan/Documents/trae_projects/a-stock-data/config/${PLIST_NAME}.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "========================================="
echo "  每日科技资讯自动化任务 v10.0 安装程序"
echo "========================================="
echo ""

# 1. 卸载旧版本
echo "[1/4] 卸载旧版本..."
launchctl unload "$PLIST_DST" 2>/dev/null
launchctl unload "$HOME/Library/LaunchAgents/com.user.dailytechintel.webssearch.morning.plist" 2>/dev/null
echo "  旧版本已卸载"

# 2. 确保脚本有执行权限
echo "[2/4] 设置脚本执行权限..."
chmod +x /Users/houpengyuan/Documents/trae_projects/a-stock-data/scripts/run_daily_tech_intel_v10.sh
echo "  执行权限已设置"

# 3. 安装plist
echo "[3/4] 安装launchd配置..."
cp "$PLIST_SRC" "$PLIST_DST"
echo "  plist已复制到 $PLIST_DST"

# 4. 加载任务
echo "[4/4] 加载定时任务..."
launchctl load "$PLIST_DST"
echo "  定时任务已加载"

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "  定时任务名称: $PLIST_NAME"
echo "  执行时间: 每工作日(周一-周五) 上午9:30"
echo "  执行脚本: run_daily_tech_intel_v10.sh"
echo "  报告目录: /Users/houpengyuan/Documents/trae_projects/a-stock-data/daily_tech_intel/"
echo ""
echo "  验证命令:"
echo "    launchctl list | grep dailytechintel"
echo ""
echo "  手动执行:"
echo "    /Users/houpengyuan/Documents/trae_projects/a-stock-data/scripts/run_daily_tech_intel_v10.sh"
echo ""
echo "  卸载命令:"
echo "    launchctl unload $PLIST_DST"
echo ""
