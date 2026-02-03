# src/storage/news_storage.py
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class NewsStorage:
    def __init__(self, db_path: str = None):
        """
        初始化存储管理器

        Args:
            db_path: SQLite数据库文件路径，如果为None则自动定位到项目根目录的finance_news.db
        """
        if db_path is None:
            # 自动定位到项目根目录下的finance_news.db
            import os
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))  # src/storage/
            # 向上两级到项目根目录
            project_root = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
            # 构建完整路径
            db_path = os.path.join(project_root, 'finance_news.db')

        self.db_path = db_path
        print(f"📁 数据库文件路径: {self.db_path}")  # 添加调试信息
        print(f"📁 文件是否存在: {os.path.exists(self.db_path)}")  # 检查文件
        self._init_connection()

    def _init_connection(self):
        """初始化数据库连接"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # 启用外键支持
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 设置返回字典格式的游标
            self.conn.row_factory = sqlite3.Row
            logger.info(f"已连接到数据库: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def save_news_batch(self, news_list: List[Dict]) -> Dict:
        """
        批量保存新闻数据，自动去重

        Args:
            news_list: 新闻字典列表

        Returns:
            统计信息: {'total': 总数, 'saved': 保存数, 'duplicates': 重复数}
        """
        if not news_list:
            return {'total': 0, 'saved': 0, 'duplicates': 0}

        stats = {'total': len(news_list), 'saved': 0, 'duplicates': 0}

        try:
            cursor = self.conn.cursor()

            for news in news_list:
                # 1. 检查是否已存在（基于news_code去重）
                news_code = news.get('code', '')
                if not news_code:
                    # 如果没有code，使用标题+时间的哈希
                    import hashlib
                    unique_str = f"{news.get('title', '')}_{news.get('publish_time', '')}"
                    news_code = hashlib.md5(unique_str.encode()).hexdigest()[:16]
                    news['code'] = news_code

                # 检查是否已存在
                cursor.execute(
                    "SELECT id FROM news_articles WHERE news_code = ?",
                    (news_code,)
                )
                existing = cursor.fetchone()

                if existing:
                    stats['duplicates'] += 1
                    logger.debug(f"跳过重复新闻: {news.get('title', '')[:50]}...")
                    continue

                # 2. 准备插入数据
                # 处理相关股票列表（列表转JSON字符串）
                related_stocks = news.get('related_stocks', [])
                if isinstance(related_stocks, list):
                    related_stocks_json = json.dumps(related_stocks, ensure_ascii=False)
                else:
                    related_stocks_json = '[]'

                # 处理发布时间
                publish_time = news.get('publish_time', '')
                if not publish_time:
                    publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 3. 插入新闻数据
                cursor.execute('''
                INSERT INTO news_articles (
                    news_code, title, content, source, publish_time,
                    category, importance, url, has_stock_mention, related_stocks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news_code,
                    news.get('title', '')[:500],  # 限制标题长度
                    news.get('content', ''),
                    news.get('source', '东方财富'),
                    publish_time,
                    news.get('category', '其他'),
                    news.get('importance', 5),
                    news.get('url', ''),
                    1 if news.get('has_stock_mention', False) else 0,
                    related_stocks_json
                ))

                news_id = cursor.lastrowid

                # 4. 记录去重哈希
                cursor.execute(
                    "INSERT INTO news_deduplication (news_code_hash, news_id) VALUES (?, ?)",
                    (news_code, news_id)
                )

                stats['saved'] += 1
                logger.debug(f"保存新闻: {news.get('title', '')[:60]}...")

            # 提交事务
            self.conn.commit()
            logger.info(f"批量保存完成: 总数={stats['total']}, 新增={stats['saved']}, 重复={stats['duplicates']}")

            return stats

        except Exception as e:
            self.conn.rollback()
            logger.error(f"批量保存失败: {e}")
            raise

    def get_recent_news(self, limit: int = 20) -> List[Dict]:
        """
        获取最近新闻

        Args:
            limit: 返回数量限制

        Returns:
            新闻字典列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM news_articles 
                ORDER BY publish_time DESC 
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()

            # 转换为字典列表
            news_list = []
            for row in rows:
                news_dict = dict(row)
                # 解析related_stocks JSON字符串
                if news_dict.get('related_stocks'):
                    try:
                        news_dict['related_stocks'] = json.loads(news_dict['related_stocks'])
                    except:
                        news_dict['related_stocks'] = []
                news_list.append(news_dict)

            logger.debug(f"获取最近 {len(news_list)} 条新闻")
            return news_list

        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            return []

    def get_news_count(self) -> int:
        """获取新闻总数"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM news_articles")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取新闻总数失败: {e}")
            return 0

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")


# 单例模式（可选）
_global_storage = None


def get_storage() -> NewsStorage:
    """获取全局存储实例"""
    global _global_storage
    if _global_storage is None:
        _global_storage = NewsStorage()
    return _global_storage


def test_storage():
    """测试存储功能"""
    print("测试新闻存储功能...")

    # 创建测试数据
    test_news = [
        {
            'code': 'TEST001',
            'title': '测试新闻标题1',
            'content': '测试新闻内容1',
            'source': '测试来源',
            'publish_time': '2026-02-03 10:00:00',
            'category': '测试',
            'importance': 7,
            'url': 'https://example.com/test1',
            'has_stock_mention': False,
            'related_stocks': []
        },
        {
            'code': 'TEST002',
            'title': '测试新闻标题2',
            'content': '测试新闻内容2',
            'source': '测试来源',
            'publish_time': '2026-02-03 10:05:00',
            'category': '测试',
            'importance': 8,
            'url': 'https://example.com/test2',
            'has_stock_mention': True,
            'related_stocks': ['000001.SZ', '600000.SH']
        }
    ]

    storage = NewsStorage()

    # 测试保存
    print("1. 测试批量保存...")
    stats = storage.save_news_batch(test_news)
    print(f"   结果: {stats}")

    # 测试查询
    print("2. 测试查询最近新闻...")
    recent_news = storage.get_recent_news(5)
    print(f"   获取到 {len(recent_news)} 条新闻")
    for i, news in enumerate(recent_news):
        print(f"     {i + 1}. {news['title'][:40]}... ({news['publish_time']})")

    # 测试计数
    print("3. 测试新闻计数...")
    count = storage.get_news_count()
    print(f"   数据库中共有 {count} 条新闻")

    storage.close()
    print("✅ 存储测试完成！")


if __name__ == "__main__":
    test_storage()