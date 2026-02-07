#!/usr/bin/env python3
"""
财经新闻采集调度器 - 正确工作版
"""

import sys
import os
import time
import logging
import argparse
from datetime import datetime
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

# 导入模块
try:
    from collectors.eastmoney_collector import EastMoneyCollector
    from analyzers.basic_analyzer import BasicNewsAnalyzer
    from notifiers.dingtalk_notifier import DingTalkNotifier

    # 钉钉配置
    DINGTALK_CONFIG = {
        "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611",
        "secret": "SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2",
        "importance_threshold": 5,
        "keywords": ["财经快讯"],
        "sentiment_emoji": {"bullish": "📈", "bearish": "📉", "neutral": "📊"}
    }

    MODULES_LOADED = True
    print("  ✅ 所有模块导入成功")

except ImportError as e:
    print(f"  ❌ 模块导入失败: {e}")
    MODULES_LOADED = False

print("=" * 60)


# ========== 调度管理器类 ==========
class SchedulerManager:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.setup_logging()

        if not MODULES_LOADED:
            self.logger.error("模块加载失败")
            return

        self.logger.info("初始化组件...")

        # 初始化分析器
        try:
            self.analyzer = BasicNewsAnalyzer()
            self.logger.info("✅ 新闻分析器初始化成功")
        except Exception as e:
            self.logger.error(f"分析器初始化失败: {e}")
            self.analyzer = None

        # 初始化钉钉推送器
        try:
            self.dingtalk_notifier = DingTalkNotifier(
                webhook_url=DINGTALK_CONFIG['webhook_url'],
                secret=DINGTALK_CONFIG['secret'],
                importance_threshold=DINGTALK_CONFIG['importance_threshold']
            )
            self.logger.info("✅ 钉钉推送器初始化成功")
        except Exception as e:
            self.logger.error(f"钉钉推送器初始化失败: {e}")
            self.dingtalk_notifier = None

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

    def collect_and_store(self):
        """完整的采集、分析、推送流程"""
        try:
            start_time = time.time()
            self.logger.info("📡 开始执行采集任务...")

            # 1. 采集新闻
            collector = EastMoneyCollector()

            # 尝试不同的采集方法
            news_list = []
            if hasattr(collector, 'fetch_news'):
                news_list = collector.fetch_news()
            elif hasattr(collector, 'collect_latest_news'):
                news_list = collector.collect_latest_news()
            elif hasattr(collector, 'collect'):
                news_list = collector.collect()

            if not news_list:
                self.logger.warning("未采集到新闻数据")
                return

            self.logger.info(f"成功采集到 {len(news_list)} 条新闻")

            # 2. 处理每条新闻
            processed = 0
            pushed = 0

            # 在 collect_and_store 方法中，找到分析新闻的部分，添加调试输出
            for news_item in news_list:
                try:
                    # 分析新闻
                    if self.analyzer:
                        analysis = self.analyzer.analyze_news(news_item)
                        importance_score = analysis['importance_score']
                        sentiment = analysis['sentiment']
                        title = news_item.get('title', '')[:40]

                        # 添加调试输出
                        if importance_score >= 5:
                            self.logger.info(f"📊 高分新闻: {importance_score}/10 - {title}...")
                        else:
                            self.logger.debug(f"低分新闻: {importance_score}/10 - {title}...")
                    else:
                        importance_score = 5
                        sentiment = 'neutral'


                    news_item['importance_score'] = importance_score
                    news_item['sentiment'] = sentiment

                    # 检查是否需要推送
                    if self.dingtalk_notifier and importance_score >= 3:
                        self.logger.info(f"📨 推送新闻: {importance_score}/10 - {news_item['title'][:40]}...")

                        success = self.dingtalk_notifier.send_news_alert(
                            news_item=news_item,
                            importance_score=importance_score,
                            sentiment=sentiment,
                            sentiment_emoji=DINGTALK_CONFIG.get('sentiment_emoji')
                        )

                        if success:
                            pushed += 1

                    processed += 1

                except Exception as e:
                    self.logger.error(f"处理新闻失败: {e}")
                    continue

            # 3. 输出统计
            elapsed = time.time() - start_time
            self.logger.info("=" * 50)
            self.logger.info(f"📊 任务完成统计:")
            self.logger.info(f"   采集: {len(news_list)} 条")
            self.logger.info(f"   处理: {processed} 条")
            self.logger.info(f"   推送: {pushed} 条")
            self.logger.info(f"   耗时: {elapsed:.2f} 秒")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.error(f"采集任务执行失败: {e}")

    def start(self):
        """启动调度器"""
        self.scheduler.start()


# ========== 主函数 ==========
def main():
    parser = argparse.ArgumentParser(description='财经新闻采集调度器')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--interval', type=int, default=30, help='采集间隔（分钟）')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🚀 财经新闻智能采集系统")
    print("=" * 60 + "\n")

    # 创建调度管理器
    scheduler = SchedulerManager()

    # 测试模式
    if args.test:
        print("🔬 测试模式 - 执行一次完整流程")
        print("-" * 40)
        scheduler.collect_and_store()
        print("-" * 40)
        print("✅ 测试完成！")
        return

    # 正常模式
    print(f"⏰ 配置定时任务（每 {args.interval} 分钟）")
    scheduler.scheduler.add_job(
        func=scheduler.collect_and_store,
        trigger='interval',
        minutes=args.interval,
        id='news_collector'
    )

    print("\n✅ 系统已启动，按 Ctrl+C 退出\n")
    scheduler.start()


if __name__ == "__main__":
    main()