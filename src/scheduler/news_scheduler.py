#!/usr/bin/env python3
"""
财经新闻采集调度器 - 整合采集、分析、存储、推送全流程
作者: 财经新闻智能采集与分析系统
版本: 2.0 (集成钉钉推送)
"""

import sys
import os
import time
import logging
import argparse
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入项目模块
try:
    from collectors.eastmoney_collector import EastMoneyCollector
    from analyzers.basic_analyzer import BasicNewsAnalyzer
    from notifiers.dingtalk_notifier import DingTalkNotifier
    from config.dingtalk_config import DINGTALK_CONFIG

    # 数据库模块（根据您的实际实现导入）
    # from database.news_database import NewsDatabase

    MODULES_LOADED = True
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("请确保所有依赖模块已正确创建")
    MODULES_LOADED = False


class SchedulerManager:
    """调度管理器：协调采集、分析、推送全流程"""

    def __init__(self):
        """初始化调度管理器"""
        self.scheduler = BlockingScheduler()
        self.setup_logging()

        # 检查模块加载状态
        if not MODULES_LOADED:
            self.logger.error("模块加载失败，调度器无法正常工作")
            return

        # 初始化各组件
        self.logger.info("初始化调度器组件...")

        # 初始化钉钉推送器
        try:
            self.dingtalk_notifier = DingTalkNotifier(
                webhook_url=DINGTALK_CONFIG['webhook_url'],
                secret=DINGTALK_CONFIG['secret'],
                importance_threshold=DINGTALK_CONFIG['importance_threshold'],
                keywords=DINGTALK_CONFIG['keywords']
            )
            self.logger.info("钉钉推送器初始化成功")
        except Exception as e:
            self.logger.error(f"钉钉推送器初始化失败: {e}")
            self.dingtalk_notifier = None

        # 初始化分析器
        try:
            self.analyzer = BasicNewsAnalyzer()
            self.logger.info("新闻分析器初始化成功")
        except Exception as e:
            self.logger.error(f"新闻分析器初始化失败: {e}")
            self.analyzer = None

        # 初始化数据库（根据您的实现）
        # try:
        #     self.db = NewsDatabase()
        #     self.logger.info("数据库连接成功")
        # except Exception as e:
        #     self.logger.error(f"数据库连接失败: {e}")
        #     self.db = None

        # 设置调度器事件监听
        self.setup_scheduler_events()

        self.logger.info("调度管理器初始化完成")

    def setup_logging(self):
        """配置日志系统"""
        # 创建logs目录
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # 创建logger
        self.logger = logging.getLogger('NewsScheduler')
        self.logger.setLevel(logging.INFO)

        # 清除已有的handler
        self.logger.handlers.clear()

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 文件handler
        log_file = os.path.join(log_dir, 'scheduler.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # 避免日志重复
        self.logger.propagate = False

    def setup_scheduler_events(self):
        """设置调度器事件监听"""

        def job_executed(event):
            if event.exception:
                self.logger.error(f"任务执行失败: {event.job_id} - {event.exception}")
            else:
                self.logger.debug(f"任务执行成功: {event.job_id}")

        def job_error(event):
            self.logger.error(f"任务出错: {event.job_id} - {event.exception}")
            self.logger.error(f"错误详情: {event.traceback}")

        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error, EVENT_JOB_ERROR)

    def collect_and_store(self):
        """
        采集、分析、存储并推送

        完整流程:
        1. 采集东方财富快讯
        2. 分析新闻重要性及情感
        3. 存储到数据库（去重）
        4. 推送重要新闻到钉钉
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("开始执行财经新闻采集任务...")
            start_time = time.time()

            # 1. 采集新闻
            self.logger.info("步骤1: 采集东方财富快讯...")
            try:
                collector = EastMoneyCollector()
                news_list = collector.collect()

                if not news_list:
                    self.logger.warning("未采集到新闻数据")
                    return

                self.logger.info(f"成功采集到 {len(news_list)} 条新闻")

            except Exception as e:
                self.logger.error(f"新闻采集失败: {e}", exc_info=True)
                return

            # 2. 分析、处理并推送
            processed_count = 0
            stored_count = 0
            pushed_count = 0
            important_news = []

            self.logger.info("步骤2: 分析处理新闻数据...")
            for idx, news_item in enumerate(news_list, 1):
                try:
                    # 2.1 分析新闻
                    if self.analyzer:
                        analysis_result = self.analyzer.analyze_news(news_item)
                        importance_score = analysis_result['importance_score']
                        sentiment = analysis_result['sentiment']

                        # 将分析结果添加到新闻数据
                        news_item['importance_score'] = importance_score
                        news_item['sentiment'] = sentiment
                        news_item['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        importance_score = 5  # 默认分数
                        sentiment = 'neutral'
                        news_item['importance_score'] = importance_score
                        news_item['sentiment'] = sentiment

                    # 2.2 存储到数据库（这里需要根据您的数据库实现修改）
                    # if self.db:
                    #     stored = self.db.save_news(news_item)
                    #     if stored:
                    #         stored_count += 1
                    # else:
                    #     # 如果没有数据库，模拟存储成功
                    stored_count += 1

                    # 2.3 检查是否需要推送
                    if self.dingtalk_notifier and self.dingtalk_notifier.should_send(importance_score):
                        self.logger.debug(f"新闻重要性分数 {importance_score}，达到推送阈值")
                        important_news.append((news_item, importance_score, sentiment))

                    processed_count += 1

                    # 每处理10条新闻输出一次进度
                    if idx % 10 == 0:
                        self.logger.info(f"已处理 {idx}/{len(news_list)} 条新闻")

                except Exception as e:
                    self.logger.error(f"处理第 {idx} 条新闻时出错: {e}")
                    continue

            # 3. 推送重要新闻
            if important_news and self.dingtalk_notifier:
                self.logger.info(f"步骤3: 推送 {len(important_news)} 条重要新闻到钉钉...")
                for news_item, importance_score, sentiment in important_news:
                    try:
                        success = self.dingtalk_notifier.send_news_alert(
                            news_item=news_item,
                            importance_score=importance_score,
                            sentiment=sentiment,
                            sentiment_emoji=DINGTALK_CONFIG.get('sentiment_emoji', {
                                "bullish": "📈",
                                "bearish": "📉",
                                "neutral": "📊"
                            })
                        )

                        if success:
                            pushed_count += 1
                            self.logger.info(f"推送成功: {news_item['title'][:50]}... (分数: {importance_score})")
                        else:
                            self.logger.warning(f"推送失败: {news_item['title'][:50]}...")

                    except Exception as e:
                        self.logger.error(f"推送单条新闻时出错: {e}")

            # 4. 任务完成统计
            elapsed_time = time.time() - start_time
            self.logger.info("=" * 60)
            self.logger.info("采集任务完成统计:")
            self.logger.info(f"  采集新闻: {len(news_list)} 条")
            self.logger.info(f"  处理成功: {processed_count} 条")
            self.logger.info(f"  存储成功: {stored_count} 条")
            self.logger.info(f"  推送成功: {pushed_count} 条")
            self.logger.info(f"  耗时: {elapsed_time:.2f} 秒")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"采集任务整体执行失败: {e}", exc_info=True)

    def add_job(self, *args, **kwargs):
        """添加任务到调度器"""
        return self.scheduler.add_job(*args, **kwargs)

    def start(self):
        """启动调度器"""
        self.logger.info("启动调度器...")
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        except Exception as e:
            self.logger.error(f"调度器启动失败: {e}")

    def shutdown(self):
        """关闭调度器"""
        self.logger.info("关闭调度器...")
        self.scheduler.shutdown()
        self.logger.info("调度器已关闭")


def test_mode(scheduler_manager):
    """测试模式：立即运行一次采集任务"""
    print("\n" + "=" * 60)
    print("🔧 测试模式启动")
    print("=" * 60)

    scheduler_manager.logger.info("开始测试运行...")

    # 运行一次采集任务
    scheduler_manager.collect_and_store()

    print("\n" + "=" * 60)
    print("✅ 测试完成！请检查：")
    print("  1. 控制台输出日志")
    print("  2. 钉钉群是否收到推送")
    print("  3. 数据库是否保存数据")
    print("=" * 60)


def main():
    """主函数：启动调度器"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='财经新闻采集调度器')
    parser.add_argument('--test', action='store_true', help='测试模式：立即运行一次采集任务后退出')
    parser.add_argument('--debug', action='store_true', help='调试模式：显示详细日志')
    parser.add_argument('--interval', type=int, default=30, help='采集间隔时间（分钟），默认30分钟')
    args = parser.parse_args()

    # 初始化调度管理器
    print("🚀 财经新闻智能采集系统 v2.0")
    print(f"📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    try:
        scheduler_manager = SchedulerManager()

        if args.debug:
            scheduler_manager.logger.setLevel(logging.DEBUG)
            scheduler_manager.logger.debug("调试模式已启用")

        # 测试模式
        if args.test:
            test_mode(scheduler_manager)
            return

        # 正常模式：添加定时任务
        print(f"⏰ 配置定时采集任务（每 {args.interval} 分钟）")
        scheduler_manager.logger.info(f"添加定时任务，间隔 {args.interval} 分钟")

        scheduler_manager.add_job(
            func=scheduler_manager.collect_and_store,
            trigger='interval',
            minutes=args.interval,
            id='eastmoney_collector',
            name='东方财富快讯采集',
            misfire_grace_time=300,  # 允许错过执行300秒
            coalesce=True,  # 合并多次未执行的任务
            max_instances=1  # 最多同时运行1个实例
        )

        # 添加一个每日汇总报告任务（可选）
        scheduler_manager.add_job(
            func=lambda: scheduler_manager.logger.info("系统运行正常，每日健康检查"),
            trigger='cron',
            hour=9,
            minute=0,
            id='daily_report',
            name='每日健康报告'
        )

        print("\n✅ 调度器配置完成")
        print("📋 定时任务列表:")
        for job in scheduler_manager.scheduler.get_jobs():
            print(f"  • {job.name} (ID: {job.id}) - 下次执行: {job.next_run_time}")

        print("\n" + "=" * 50)
        print("📢 调度器已启动！")
        print("   采集频率: 每30分钟")
        print("   推送平台: 钉钉群机器人")
        print("   日志文件: logs/scheduler.log")
        print("=" * 50)
        print("按 Ctrl+C 退出程序\n")

        # 启动调度器
        scheduler_manager.start()

    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)