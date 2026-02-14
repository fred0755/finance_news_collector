#!/usr/bin/env python
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from eastmoney_collector import EastMoneyCollector

# 新增：导入标签管理器
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from tags.tag_manager import TagManager


def main():
    print("=" * 50)
    print("🚀 东方财富快讯采集器")
    print("=" * 50)

    # 获取项目根目录
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    data_dir = project_root / "data"

    # 创建数据目录
    data_dir.mkdir(exist_ok=True, parents=True)

    # 切换到项目根目录
    os.chdir(project_root)
    print(f"📁 工作目录: {os.getcwd()}")

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

    # 统计有标签的新闻
    tagged_count = sum(
        1 for item in tagged_news if item.get('tags', {}).get('industries') or item.get('tags', {}).get('concepts'))
    print(f"✅ {tagged_count}/{len(tagged_news)} 条新闻成功打上标签")

    # 保存文件
    print("\n💾 正在保存文件...")

    # 1. 保存 latest.json（最新30条，带标签）
    latest_path = data_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(tagged_news[:30], f, ensure_ascii=False, indent=2)
    print(f"  ✅ latest.json: {len(tagged_news[:30])} 条")

    # 2. 保存 today.json（全部，带标签）
    today_path = data_dir / "today.json"
    with open(today_path, "w", encoding="utf-8") as f:
        json.dump(tagged_news, f, ensure_ascii=False, indent=2)
    print(f"  ✅ today.json: {len(tagged_news)} 条")

    # 3. 保存时间戳
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)
    print(f"  ✅ last_update.txt: {current_time}")

    # 显示第一条作为示例
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