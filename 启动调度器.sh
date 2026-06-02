#!/bin/bash
# 科技前沿资讯自动化调度系统 - 一键启动脚本

echo "========================================"
echo "🚀 科技前沿资讯自动化调度系统"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 工作目录: $SCRIPT_DIR"
echo ""
echo "请选择操作:"
echo "1) 立即执行一次任务（测试）"
echo "2) 启动定时调度器（每日9:30自动执行）"
echo "3) 查看帮助"
echo "4) 退出"
echo ""

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🧪 立即执行一次任务..."
        python3 auto_scheduler.py now
        ;;
    2)
        echo ""
        echo "⏰ 启动定时调度器..."
        echo "💡 提示: 调度器将持续运行，按 Ctrl+C 可停止"
        echo ""
        python3 auto_scheduler.py start
        ;;
    3)
        echo ""
        python3 auto_scheduler.py help
        ;;
    4)
        echo ""
        echo "👋 再见!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ 无效选项!"
        exit 1
        ;;
esac

