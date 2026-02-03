# src/scheduler/news_scheduler.py 文件开头部分

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import logging
import sys
import os

# ============ 1. 路径配置 ============
# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 2. 导入模块 ============
from collectors.eastmoney_collector import EastMoneyCollector
from storage.news_storage import get_storage  # 确保这行存在

# ============ 3. 日志配置（必须在函数外部！）============
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)  # 这行定义了logger变量！
# ========================================================

# ============ 4. 采集任务函数 ============
def collect_eastmoney_news():
    """定时采集任务"""
    try:
        logger.info("=" * 50)  # 这里开始使用logger
        logger.info("开始执行东方财富快讯采集任务...")
        # ... 函数其余部分保持不变

        collector = EastMoneyCollector()
        # 每次采集20条最新快讯
        news_list = collector.fetch_news(page_size=20)

        if news_list:
            logger.info(f"✅ 采集成功！共获取 {len(news_list)} 条新闻")

            # 记录采集到的新闻（前3条作为示例）
            for i, news in enumerate(news_list[:3]):
                logger.info(f"  示例{i + 1}: [{news.get('time', 'N/A')}] {news.get('title', '无标题')[:60]}...")

            # ============ 新增：保存到数据库 ============
            try:
                storage = get_storage()
                stats = storage.save_news_batch(news_list)
                logger.info(f"💾 数据存储完成: 新增 {stats['saved']} 条, 跳过 {stats['duplicates']} 条重复数据")
                logger.info(f"📊 数据库总计: {storage.get_news_count()} 条新闻")
            except Exception as storage_error:
                logger.error(f"❌ 数据存储失败: {storage_error}")
            # ==========================================

        else:
            logger.warning("⚠️ 采集失败或无新数据")

        logger.info("采集任务完成")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ 采集任务执行失败: {e}", exc_info=True)


def main():
    """主调度函数"""
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)

    logger.info("财经新闻采集调度器启动中...")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建调度器
    scheduler = BlockingScheduler()

    # 添加采集任务
    # 每30分钟执行一次（生产环境配置）
    scheduler.add_job(
        collect_eastmoney_news,
        'interval',
        minutes=30,
        id='eastmoney_collection',
        name='东方财富快讯采集',
        max_instances=1,
        next_run_time=datetime.now(),  # 立即执行一次
        misfire_grace_time=60  # 允许60秒的容错时间
    )

    # 可选：添加每日统计任务
    scheduler.add_job(
        lambda: logger.info("系统运行正常，等待下一次采集..."),
        'interval',
        hours=1,
        id='heartbeat',
        name='心跳检测'
    )

    logger.info("调度器配置完成:")
    logger.info("  - 东方财富快讯采集: 每30分钟一次")
    logger.info("  - 系统心跳检测: 每小时一次")
    logger.info("\n🚀 调度器已启动！按 Ctrl+C 退出程序")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止调度器...")
    except Exception as e:
        logger.error(f"调度器运行异常: {e}", exc_info=True)
    finally:
        logger.info("财经新闻采集调度器已停止")
        logger.info(f"停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()