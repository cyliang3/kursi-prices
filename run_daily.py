#!/usr/bin/env python3
# Kursi Trades - 每日价格抓取脚本
# ==========================================
# 
# 使用方法:
#   1. 直接运行: python run_daily.py
#   2. 设置定时任务（见下方说明）
#
# 定时任务设置:
#   
#   Mac/Linux (crontab):
#   ---------------------
#   打开终端，输入: crontab -e
#   添加一行（每天早上9点运行）:
#   0 9 * * * cd /Users/liangcaiyi/Kursi\ Trades/price_scraper && /usr/bin/python3 run_daily.py >> logs/cron.log 2>&1
#
#   Windows (任务计划程序):
#   -----------------------
#   1. 打开"任务计划程序"
#   2. 创建基本任务
#   3. 设置触发器: 每天 09:00
#   4. 操作: 启动程序
#      程序: python
#      参数: run_daily.py
#      起始于: C:\path\to\price_scraper
#

import os
import sys
from datetime import datetime

# 确保可以导入同目录的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from price_scraper import PriceScraper


def setup_logging():
    """设置日志目录"""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def main():
    """主函数"""
    setup_logging()
    
    print("\n" + "=" * 60)
    print(f"🕐 Kursi Trades 价格抓取系统")
    print(f"📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    try:
        scraper = PriceScraper()
        result = scraper.run()
        
        if "error" not in result:
            print("\n✅ 今日价格抓取完成!")
            return 0
        else:
            print(f"\n❌ 抓取失败: {result.get('error')}")
            return 1
            
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
