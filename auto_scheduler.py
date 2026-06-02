#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化定时任务调度系统
每日上午9:30执行科技前沿资讯爬取和分析
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import time

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

def check_dependencies():
    """检查并安装必要的依赖"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        print("✓ APScheduler 已安装")
        return True
    except ImportError:
        print("⚠️  正在安装 APScheduler...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "apscheduler"])
            print("✓ APScheduler 安装成功")
            return True
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            return False

def run_daily_tech_intel():
    """执行每日科技前沿资讯分析"""
    print("\n" + "="*80)
    print(f"🚀 定时任务触发 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        from daily_tech_intel_system_v2 import DailyTechIntelSystemV2
        system = DailyTechIntelSystemV2()
        system.run()
        print("\n✅ 定时任务执行完成!")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

def start_scheduler():
    """启动定时任务调度器"""
    print("⏰ 自动化定时任务调度系统启动")
    print("="*80)
    
    if not check_dependencies():
        print("❌ 依赖检查失败，请手动安装: pip install apscheduler")
        return
    
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BackgroundScheduler()
    
    # 添加每日上午9:30的任务（周一至周五）
    scheduler.add_job(
        run_daily_tech_intel,
        trigger=CronTrigger(
            hour=9,
            minute=30,
            day_of_week='mon-fri'
        ),
        id='daily_tech_intel_930',
        name='每日科技前沿资讯分析 - 9:30',
        replace_existing=True
    )
    
    # 启动调度器
    scheduler.start()
    
    print("\n✅ 定时任务已配置:")
    print("   - 任务: 每日科技前沿资讯分析")
    print("   - 时间: 周一至周五 09:30")
    print("\n💡 提示: 此程序将持续运行，按 Ctrl+C 停止\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  正在停止调度器...")
        scheduler.shutdown()
        print("✅ 调度器已停止")

def run_now():
    """立即执行一次任务（用于测试）"""
    print("🧪 立即执行一次任务...")
    run_daily_tech_intel()

def show_help():
    """显示帮助信息"""
    print("""
科技前沿资讯自动化调度系统

用法:
    python auto_scheduler.py [命令]

命令:
    start    - 启动定时任务调度器（持续运行）
    now      - 立即执行一次任务（测试用）
    help     - 显示此帮助信息

示例:
    python auto_scheduler.py start    # 启动定时调度
    python auto_scheduler.py now      # 立即执行一次
    """)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_scheduler()
    elif command == 'now':
        run_now()
    else:
        show_help()

if __name__ == '__main__':
    main()
