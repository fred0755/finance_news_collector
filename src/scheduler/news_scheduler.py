#!/usr/bin/env python3
"""
财经新闻采集调度器 - 精简版（只采集+存JSON，无钉钉）
"""

import sys
import os
import time
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler

# ========== 模块导入 ==========
current_dir = os.path.dirname(os.path.abspath(__file__))  # src/scheduler
src_dir = os.path.dirname(current_dir)  # src
project_root = os.path.dirname(src_dir)  # 项目根目录

print("=" * 60)
print("🚀 财经新闻采集调度器启动")
print(f"📁 项目根目录: {project_root}")

# 添加src目录到Python路径
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("\n🔄 正在导入模块...")

# 只导入采集器
try:
    from collectors.eastmoney_collector import EastMoneyCollector
    MODULES_LOADED = True
    print("  ✅ 采集器导入成功")
except ImportError as e:
    print(f"  ❌ 采集器导入失败: {e}")
    MODULES_LOADED = False

print("=" * 60)


# ========== 调度管理器类 ==========
class SchedulerManager:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.setup_logging()

        if not MODULES_LOADED:
            self.logger.error("模块加载失败，退出")
            sys.exit(1)

        self.logger.info("✅ 调度管理器初始化完成")

    def setup_logging(self):
        """配置日志系统"""
        log_dir = os.path.join(project_root, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        self.logger = logging.getLogger('NewsScheduler')
        self.logger.setLevel(logging.INFO)

        if self.logger.handlers:
            self.logger.handlers.clear()

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件输出
        log_file = os.path.join(log_dir, 'scheduler.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def collect_and_save_json(self):
        """采集新闻并保存为JSON文件"""
        try:
            start_time = time.time()
            self.logger.info("📡 开始执行采集任务...")

            # 1. 采集新闻
            collector = EastMoneyCollector()
            news_list = collector.fetch_news(page_size=30)

            if not news_list:
                self.logger.warning("未采集到新闻数据")
                return

            self.logger.info(f"✅ 成功采集到 {len(news_list)} 条新闻")

            # 2. 保存JSON文件
            data_dir = Path(project_root) / "data"
            data_dir.mkdir(exist_ok=True, parents=True)

            # 保存 latest.json（最新30条）
            latest_path = data_dir / "latest.json"
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(news_list[:30], f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 已保存: {latest_path}")

            # 保存 today.json（全部）
            today_path = data_dir / "today.json"
            with open(today_path, "w", encoding="utf-8") as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 已保存: {today_path}")

            # 保存时间戳
            timestamp_path = data_dir / "last_update.txt"
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(timestamp_path, "w", encoding="utf-8") as f:
                f.write(current_time)
            self.logger.info(f"✅ 已保存: {timestamp_path} ({current_time})")

            # 3. 输出统计
            elapsed = time.time() - start_time
            self.logger.info("=" * 50)
            self.logger.info(f"📊 任务完成统计:")
            self.logger.info(f"   采集: {len(news_list)} 条")
            self.logger.info(f"   文件大小: {latest_path.stat().st_size} 字节")
            self.logger.info(f"   耗时: {elapsed:.2f} 秒")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.error(f"❌ 采集任务执行失败: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """启动调度器"""
        self.scheduler.start()


# ========== 主函数 ==========
def main():
    parser = argparse.ArgumentParser(description='财经新闻采集调度器（JSON版）')
    parser.add_argument('--test', action='store_true', help='测试模式（执行一次后退出）')
    parser.add_argument('--interval', type=int, default=30, help='采集间隔（分钟）')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🚀 财经新闻智能采集系统 - JSON版")
    print("=" * 60 + "\n")

    # 创建调度管理器
    scheduler = SchedulerManager()

    # 测试模式
    if args.test:
        print("🔬 测试模式 - 执行一次")
        print("-" * 40)
        scheduler.collect_and_save_json()
        print("-" * 40)
        print("✅ 测试完成！")
        return

    # 正常模式
    print(f"⏰ 配置定时任务（每 {args.interval} 分钟）")
    scheduler.scheduler.add_job(
        func=scheduler.collect_and_save_json,
        trigger='interval',
        minutes=args.interval,
        id='news_collector'
    )

    print("\n✅ 系统已启动，按 Ctrl+C 退出\n")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n👋 调度器已停止")


if __name__ == "__main__":
    main()