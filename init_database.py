# init_database.py
import sqlite3
import os
from datetime import datetime


def init_database():
    """初始化SQLite数据库和表结构"""

    # 数据库文件路径（放在项目根目录下）
    db_path = 'finance_news.db'

    print(f"正在初始化数据库: {db_path}")

    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 新闻主表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_code VARCHAR(50) UNIQUE NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        source VARCHAR(100) DEFAULT '东方财富',
        publish_time DATETIME,
        category VARCHAR(50),
        importance INTEGER DEFAULT 5 CHECK(importance >= 1 AND importance <= 10),
        url TEXT,
        has_stock_mention BOOLEAN DEFAULT 0,
        related_stocks TEXT,  -- SQLite没有专门的JSON类型，用TEXT存储JSON字符串
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. 去重表（基于news_code去重）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_deduplication (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_code_hash VARCHAR(64) UNIQUE NOT NULL,
        news_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (news_id) REFERENCES news_articles(id) ON DELETE CASCADE
    )
    ''')

    # 3. 推送记录表（为企业微信推送做准备）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS push_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id INTEGER NOT NULL,
        push_type VARCHAR(20) DEFAULT 'wechat',
        push_status VARCHAR(20) DEFAULT 'pending',  -- pending/success/failed
        push_time TIMESTAMP,
        retry_count INTEGER DEFAULT 0,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (news_id) REFERENCES news_articles(id) ON DELETE CASCADE
    )
    ''')

    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news_articles(publish_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_created_at ON news_articles(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_push_records_status ON push_records(push_status)')

    # 提交更改
    conn.commit()

    # 检查表是否创建成功
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("✅ 数据库初始化完成！")
    print("已创建的表:")
    for table in tables:
        print(f"  - {table[0]}")

    # 统计（如果有历史数据）
    cursor.execute("SELECT COUNT(*) FROM news_articles")
    news_count = cursor.fetchone()[0]
    print(f"当前新闻数量: {news_count} 条")

    conn.close()
    print(f"\n数据库文件位置: {os.path.abspath(db_path)}")
    print("\n下一步: 运行 'python storage/news_storage.py' 测试数据存储")


if __name__ == "__main__":
    init_database()