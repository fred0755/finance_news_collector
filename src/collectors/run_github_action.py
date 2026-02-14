import json
import sys
import os
from pathlib import Path
from datetime import datetime, date
from eastmoney_collector import EastMoneyCollector


def main():
    print("=" * 50)
    print("🚀 东方财富快讯采集器")
    print("=" * 50)

    # 获取项目根目录
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    data_dir = project_root / "data"
    archive_dir = data_dir / "archive"

    # 创建数据目录
    data_dir.mkdir(exist_ok=True, parents=True)
    archive_dir.mkdir(exist_ok=True, parents=True)

    print(f"📁 数据目录: {data_dir}")
    print(f"📁 归档目录: {archive_dir}")

    # 采集新闻
    print("\n🔄 开始采集...")
    collector = EastMoneyCollector()
    news_list = collector.fetch_news(page_size=50)  # 每次采集50条

    if not news_list:
        print("❌ 采集失败")
        sys.exit(1)

    print(f"✅ 成功采集 {len(news_list)} 条新闻")

    # ========== 保存今日数据 ==========
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. 保存 latest.json（最新50条，保持兼容）
    latest_path = data_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(news_list[:50], f, ensure_ascii=False, indent=2)
    print(f"  ✅ latest.json: {len(news_list[:50])} 条")

    # 2. 更新今日汇总文件（追加新数据，去重）
    today_path = data_dir / f"today.json"

    # 读取已有的今日数据
    existing_news = []
    if today_path.exists():
        try:
            with open(today_path, "r", encoding="utf-8") as f:
                existing_news = json.load(f)
        except:
            existing_news = []

    # 合并并去重（基于标题）
    all_today_news = existing_news + news_list
    unique_today = {}
    for item in all_today_news:
        title = item.get('title', '')
        if title and title not in unique_today:
            unique_today[title] = item

    today_news = list(unique_today.values())
    # 按时间排序（假设有时间字段）
    today_news.sort(key=lambda x: x.get('showTime', ''), reverse=True)

    with open(today_path, "w", encoding="utf-8") as f:
        json.dump(today_news, f, ensure_ascii=False, indent=2)
    print(f"  ✅ today.json: {len(today_news)} 条")

    # 3. 保存到按日归档
    archive_path = archive_dir / f"{today_str}.json"

    # 读取已有的归档文件（如果存在）
    if archive_path.exists():
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                archive_news = json.load(f)
        except:
            archive_news = []
    else:
        archive_news = []

    # 合并去重
    all_archive = archive_news + news_list
    unique_archive = {}
    for item in all_archive:
        title = item.get('title', '')
        if title and title not in unique_archive:
            unique_archive[title] = item

    final_archive = list(unique_archive.values())
    final_archive.sort(key=lambda x: x.get('showTime', ''), reverse=True)

    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(final_archive, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 归档 {today_str}.json: {len(final_archive)} 条")

    # 4. 保存时间戳
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)

    print("\n📊 文件大小:")
    print(f"  latest.json: {latest_path.stat().st_size if latest_path.exists() else 0} 字节")
    print(f"  today.json: {today_path.stat().st_size if today_path.exists() else 0} 字节")
    print(f"  {today_str}.json: {archive_path.stat().st_size if archive_path.exists() else 0} 字节")

    print("\n" + "=" * 50)
    print("✅ 采集任务完成！")
    print("=" * 50)

    sys.exit(0)


if __name__ == "__main__":
    main()