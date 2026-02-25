#!/usr/bin/env python
"""
财经新闻采集器 - 带历史归档版
功能：
- 每次采集50条新闻
- 更新 latest.json（最近30条）
- 更新 today.json（今日所有）
- 按日归档到 archive/YYYY-MM-DD.json
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, date
from eastmoney_collector import EastMoneyCollector

# 导入标签管理器
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from tags.tag_manager import TagManager


def merge_news_by_title(existing_news, new_news):
    """按标题去重合并新闻列表"""
    news_map = {}

    # 先添加已有的
    for item in existing_news:
        title = item.get('title', '')
        if title:
            news_map[title] = item

    # 再添加新的（会覆盖相同标题的旧新闻，保留最新的）
    for item in new_news:
        title = item.get('title', '')
        if title:
            news_map[title] = item

    # 转回列表并按时间排序
    result = list(news_map.values())
    result.sort(key=lambda x: x.get('showTime', ''), reverse=True)
    return result


def main():
    print("=" * 50)
    print("🚀 财经新闻采集器（带历史归档）")
    print("=" * 50)

    # 获取项目根目录
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    data_dir = project_root / "data"
    archive_dir = data_dir / "archive"

    # 创建目录
    data_dir.mkdir(exist_ok=True, parents=True)
    archive_dir.mkdir(exist_ok=True, parents=True)

    print(f"📁 数据目录: {data_dir}")
    print(f"📁 归档目录: {archive_dir}")

    # 初始化标签管理器
    print("\n🏷️ 初始化标签管理器...")
    tag_manager = TagManager()
    stats = tag_manager.get_stats()
    print(f"  标签库版本: {stats['version']}")
    print(f"  行业数: {stats['industries']}, 概念数: {stats['concepts']}")

    # 采集新闻
    print("\n🔄 开始采集...")
    collector = EastMoneyCollector()
    news_list = collector.fetch_news(page_size=50)

    if not news_list:
        print("❌ 采集失败")
        sys.exit(1)

    print(f"✅ 成功采集 {len(news_list)} 条原始新闻")

    # 添加标签
    print("\n🏷️ 正在添加行业和概念标签...")
    tagged_news = tag_manager.add_to_news_list(news_list)

    tagged_count = sum(
        1 for item in tagged_news if item.get('tags', {}).get('industries') or item.get('tags', {}).get('concepts'))
    print(f"✅ {tagged_count}/{len(tagged_news)} 条新闻成功打上标签")

    # ========== 1. 更新 latest.json（最近30条） ==========
    latest_path = data_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(tagged_news[:30], f, ensure_ascii=False, indent=2)
    print(f"\n✅ latest.json: {len(tagged_news[:30])} 条")

    # ========== 2. 更新 today.json（今日所有） ==========
    today_path = data_dir / "today.json"

    # 读取现有的今日数据
    existing_today = []
    if today_path.exists():
        try:
            with open(today_path, "r", encoding="utf-8") as f:
                existing_today = json.load(f)
        except:
            existing_today = []

    # 合并去重
    merged_today = merge_news_by_title(existing_today, tagged_news)

    with open(today_path, "w", encoding="utf-8") as f:
        json.dump(merged_today, f, ensure_ascii=False, indent=2)
    print(f"✅ today.json: {len(merged_today)} 条")

    # ========== 3. 按日归档到 archive/YYYY-MM-DD.json ==========
    today_str = datetime.now().strftime("%Y-%m-%d")
    archive_path = archive_dir / f"{today_str}.json"

    # 读取现有的归档文件
    existing_archive = []
    if archive_path.exists():
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                existing_archive = json.load(f)
        except:
            existing_archive = []

    # 合并去重
    merged_archive = merge_news_by_title(existing_archive, tagged_news)

    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(merged_archive, f, ensure_ascii=False, indent=2)
    print(f"✅ 归档 {today_str}.json: {len(merged_archive)} 条")

    # ========== 4. 更新时间戳 ==========
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)
    print(f"✅ last_update.txt: {current_time}")

    # 显示示例
    if len(tagged_news) > 0:
        sample = tagged_news[0]
        print(f"\n📰 示例新闻:")
        print(f"  标题: {sample.get('title', '')[:50]}...")
        tags = sample.get('tags', {})
        industries = [ind['name'] for ind in tags.get('industries', [])]
        concepts = [con['name'] for con in tags.get('concepts', [])]
        print(f"  行业: {', '.join(industries) if industries else '无'}")
        print(f"  概念: {', '.join(concepts) if concepts else '无'}")

    print("\n" + "=" * 50)
    print("✅ 采集任务完成！")
    print("=" * 50)

    sys.exit(0)


if __name__ == "__main__":
    main()