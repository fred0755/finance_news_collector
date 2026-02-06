#!/usr/bin/env python3
"""
财经新闻采集调度器 - 整合采集、分析、存储、推送全流程
针对 finance_news_collector 项目结构优化
"""

import sys
import os
import time
import logging
import argparse
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# 根据您的项目结构调整Python路径
# 项目根目录：C:\Users\xiefe\PycharmProjects\finance_news_collector
# 当前文件：src/scheduler/news_scheduler.py
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入项目模块（根据您的实际结构调整）
try:
    # 导入采集器 - 根据您的项目结构
    from src.collectors.eastmoney_collector import EastMoneyCollector

    # 导入分析器 - 如果不存在，我们会创建简单版本
    try:
        from src.analyzers.basic_analyzer import BasicNewsAnalyzer

        ANALYZER_AVAILABLE = True
    except ImportError:
        ANALYZER_AVAILABLE = False
        print("⚠️  分析器模块未找到，将使用简化分析")

    # 导入钉钉推送器
    try:
        from src.notifiers.dingtalk_notifier import DingTalkNotifier

        NOTIFIER_AVAILABLE = True
    except ImportError:
        NOTIFIER_AVAILABLE = False
        print("⚠️  钉钉推送器未找到")

    # 导入钉钉配置
    # 修改导入部分，先尝试本地导入
    try:
        from dingtalk_config import DINGTALK_CONFIG

        CONFIG_AVAILABLE = True
    except ImportError:
        # 如果本地没有，尝试项目根目录
        try:
            import sys
            import os

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, 'config')
            sys.path.insert(0, config_path)
            from dingtalk_config import DINGTALK_CONFIG

            CONFIG_AVAILABLE = True
        except ImportError:
            CONFIG_AVAILABLE = False
            print("⚠️ 钉钉配置文件未找到")

    MODULES_LOADED = True
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("请确保所有依赖模块已正确创建")
    MODULES_LOADED = False


class BasicNewsAnalyzerSimple:
    """简化版分析器（如果正式分析器不存在）"""

    def __init__(self):
        self.source_weights = {'东方财富': 8}
        self.importance_keywords = {
            '加息': 10, '降息': 10, '降准': 9, 'GDP': 9, 'CPI': 8,
            '涨停': 7, '跌停': 7, '暴涨': 6, '暴跌': 6
        }
        self.bullish_keywords = ['上涨', '看好', '突破', '利好', '增长']
        self.bearish_keywords = ['下跌', '看空', '跌破', '利空', '下滑']

    def analyze_news(self, news_item):
        title = news_item.get('title', '')
        source = news_item.get('source', '东方财富')

        # 计算重要性分数
        score = self.source_weights.get(source, 5)
        for keyword, weight in self.importance_keywords.items():
            if keyword in title:
                score += weight

        # 判断情感
        bullish = sum(1 for word in self.bullish_keywords if word in title)
        bearish = sum(1 for word in self.bearish_keywords if word in title)

        if bullish > bearish:
            sentiment = 'bullish'
        elif bearish > bullish:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'

        return {
            'importance_score': min(10, max(0, score // 3)),
            'sentiment': sentiment,
            'title': title,
            'source': source
        }


class DingTalkNotifierSimple:
    """简化版钉钉推送器"""

    def __init__(self, webhook_url=None, secret=None, importance_threshold=7):
        self.webhook_url = webhook_url or "未配置"
        self.secret = secret
        self.importance_threshold = importance_threshold

    def should_send(self, importance_score):
        return importance_score >= self.importance_threshold

    def send_news_alert(self, news_item, importance_score, sentiment, **kwargs):
        print(f"📤 模拟推送钉钉消息:")
        print(f"   标题: {news_item.get('title', '')[:50]}...")
        print(f"   分数: {importance_score}/10")
        print(f"   情感: {sentiment}")
        print(f"   Webhook: {self.webhook_url[:50]}..." if self.webhook_url else "   Webhook: 未配置")
        return True


class SchedulerManager:
    """调度管理器：协调采集、分析、推送全流程"""

    def __init__(self):
        """初始化调度管理器"""
        self.scheduler = BlockingScheduler()
        self.setup_logging()

        self.logger.info("=" * 50)
        self.logger.info("初始化财经新闻采集调度器")
        self.logger.info(f"项目根目录: {project_root}")
        self.logger.info("=" * 50)

        # 初始化各组件
        self.initialize_components()

        # 设置调度器事件监听
        self.setup_scheduler_events()

        self.logger.info("✅ 调度管理器初始化完成")

    def setup_logging(self):
        """配置日志系统"""
        # 创建logs目录（根据您的项目结构）
        log_dir = os.path.join(project_root, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # 配置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # 创建logger
        self.logger = logging.getLogger('NewsScheduler')
        self.logger.setLevel(logging.INFO)

        # 清除已有的handler
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 文件handler
        log_file = os.path.join(log_dir, 'scheduler.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def initialize_components(self):
        """初始化所有组件"""
        # 1. 初始化钉钉推送器
        if NOTIFIER_AVAILABLE and CONFIG_AVAILABLE:
            try:
                self.dingtalk_notifier = DingTalkNotifier(
                    webhook_url=DINGTALK_CONFIG['webhook_url'],
                    secret=DINGTALK_CONFIG['secret'],
                    importance_threshold=DINGTALK_CONFIG.get('importance_threshold', 7)
                )
                self.logger.info("✅ 钉钉推送器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 钉钉推送器初始化失败: {e}")
                self.dingtalk_notifier = DingTalkNotifierSimple()
        else:
            self.dingtalk_notifier = DingTalkNotifierSimple()
            self.logger.warning("⚠️  使用简化版钉钉推送器")

        # 2. 初始化分析器
        if ANALYZER_AVAILABLE:
            try:
                self.analyzer = BasicNewsAnalyzer()
                self.logger.info("✅ 新闻分析器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 新闻分析器初始化失败: {e}")
                self.analyzer = BasicNewsAnalyzerSimple()
        else:
            self.analyzer = BasicNewsAnalyzerSimple()
            self.logger.warning("⚠️  使用简化版新闻分析器")

        # 3. 检查采集器
        try:
            # 测试导入采集器
            from src.collectors.eastmoney_collector import EastMoneyCollector
            self.logger.info("✅ 东方财富采集器可用")
        except Exception as e:
            self.logger.error(f"❌ 采集器不可用: {e}")

    def setup_scheduler_events(self):
        """设置调度器事件监听"""

        def job_executed(event):
            if event.exception:
                self.logger.error(f"任务执行失败: {event.job_id}")
            else:
                self.logger.debug(f"任务执行成功: {event.job_id}")

        def job_error(event):
            self.logger.error(f"任务出错: {event.job_id} - {event.exception}")

        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error, EVENT_JOB_ERROR)

    def collect_and_store(self):
        try:
            start_time = time.time()
            self.logger.info("📡 开始执行采集任务...")

            # 1. 采集新闻 - 使用正确的方法名
            try:
                collector = EastMoneyCollector()

                # 根据您的采集器代码，正确的方法是 collect_latest_news()
                if hasattr(collector, 'collect_latest_news'):
                    self.logger.info("使用采集器方法: collect_latest_news()")
                    news_list = collector.collect_latest_news()
                elif hasattr(collector, 'collect'):
                    self.logger.info("使用采集器方法: collect()")
                    news_list = collector.collect()
                else:
                    # 尝试其他常见方法名
                    method_names = ['get_news', 'fetch_news', 'run']
                    for method_name in method_names:
                        if hasattr(collector, method_name):
                            self.logger.info(f"使用采集器方法: {method_name}()")
                            method = getattr(collector, method_name)
                            news_list = method()
                            break
                    else:
                        self.logger.error("采集器没有可用的采集方法")
                        return

                if not news_list:
                    self.logger.warning("未采集到新闻数据")
                    return

                self.logger.info(f"成功采集到 {len(news_list)} 条新闻")

            except Exception as e:
                self.logger.error(f"新闻采集失败: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                return

            # 2. 处理每条新闻
            processed = 0
            pushed = 0

            for news_item in news_list:
                try:
                    # 分析新闻
                    analysis = self.analyzer.analyze_news(news_item)
                    importance_score = analysis['importance_score']
                    sentiment = analysis['sentiment']

                    # 添加到新闻项
                    news_item['importance_score'] = importance_score
                    news_item['sentiment'] = sentiment
                    news_item['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # 检查是否需要推送
                    if self.dingtalk_notifier.should_send(importance_score):
                        self.logger.info(f"📨 推送重要新闻: {importance_score}/10 - {news_item['title'][:50]}...")

                        # 发送到钉钉
                        success = self.dingtalk_notifier.send_news_alert(
                            news_item=news_item,
                            importance_score=importance_score,
                            sentiment=sentiment,
                            sentiment_emoji={'bullish': '📈', 'bearish': '📉', 'neutral': '📊'}
                        )

                        if success:
                            pushed += 1

                    processed += 1

                except Exception as e:
                    self.logger.error(f"处理新闻失败: {e}")
                    continue

            # 3. 输出统计
            elapsed = time.time() - start_time
            self.logger.info("=" * 40)
            self.logger.info(f"📊 任务完成统计:")
            self.logger.info(f"   采集: {len(news_list)} 条")
            self.logger.info(f"   处理: {processed} 条")
            self.logger.info(f"   推送: {pushed} 条")
            self.logger.info(f"   耗时: {elapsed:.2f} 秒")
            self.logger.info("=" * 40)

        except Exception as e:
            self.logger.error(f"采集任务执行失败: {e}")

    def add_job(self, func, trigger='interval', minutes=30, **kwargs):
        """添加定时任务"""
        return self.scheduler.add_job(
            func=func,
            trigger=trigger,
            minutes=minutes,
            **kwargs
        )

    def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        except Exception as e:
            self.logger.error(f"调度器运行失败: {e}")

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='财经新闻采集调度器')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--interval', type=int, default=30, help='采集间隔（分钟）')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🚀 财经新闻智能采集系统")
    print(f"📂 项目路径: {project_root}")
    print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    try:
        # 创建调度管理器
        scheduler = SchedulerManager()

        if args.debug:
            scheduler.logger.setLevel(logging.DEBUG)
            print("🔧 调试模式已启用")

        # 测试模式
        if args.test:
            print("🔬 测试模式 - 执行一次完整流程")
            print("-" * 40)
            scheduler.collect_and_store()
            print("-" * 40)
            print("✅ 测试完成！")
            return

        # 正常模式：添加定时任务
        print(f"⏰ 配置定时任务（每 {args.interval} 分钟）")
        scheduler.add_job(
            func=scheduler.collect_and_store,
            trigger='interval',
            minutes=args.interval,
            id='news_collector',
            name='财经新闻采集'
        )

        print("\n✅ 调度器已启动")
        print("📋 运行信息:")
        print(f"   采集频率: 每{args.interval}分钟")
        print(f"   日志文件: {project_root}/logs/scheduler.log")
        print(f"   钉钉推送: {'已启用' if NOTIFIER_AVAILABLE else '模拟模式'}")
        print("\n📢 系统运行中... 按 Ctrl+C 退出\n")

        # 启动调度器
        scheduler.start()

    except KeyboardInterrupt:
        print("\n👋 程序已停止")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())