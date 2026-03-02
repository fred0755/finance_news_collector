#!/usr/bin/env python
"""
财经新闻采集器 - 双数据源版
功能：
- 从东方财富采集50条
- 从财联社采集50条
- 合并去重后保存
- 30天按日归档 + 按月合并
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from eastmoney_collector import EastMoneyCollector
from cailianshe_collector import CaiLianSheCollector

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
    # 兼容两种时间字段
    result.sort(key=lambda x: x.get('showTime', x.get('time', '')), reverse=True)
    return result


def merge_monthly_files(archive_dir, merged_dir, cutoff_date):
    """
    将超过30天的日文件合并到月文件
    cutoff_date: 保留的最近日期（此日期之前的文件需要合并）
    """
    print(f"\n🔄 检查需要合并的旧文件（{cutoff_date} 之前的）...")

    # 获取所有日文件
    daily_files = sorted(archive_dir.glob("20??-??-??.json"))

    for daily_file in daily_files:
        # 从文件名提取日期
        file_date_str = daily_file.stem
        try:
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
        except:
            continue

        # 如果文件日期早于cutoff_date，需要合并
        if file_date < cutoff_date:
            print(f"  📦 合并 {file_date_str} 到月文件")

            # 读取日文件内容
            try:
                with open(daily_file, 'r', encoding='utf-8') as f:
                    daily_news = json.load(f)
            except:
                print(f"    ⚠️ 读取失败，跳过")
                continue

            # 生成月文件名 (YYYY-MM.json)
            month_str = file_date_str[:7]  # 取 "YYYY-MM"
            month_file = merged_dir / f"{month_str}.json"

            # 读取已有的月文件
            month_news = []
            if month_file.exists():
                try:
                    with open(month_file, 'r', encoding='utf-8') as f:
                        month_news = json.load(f)
                except:
                    month_news = []

            # 合并去重
            merged = merge_news_by_title(month_news, daily_news)

            # 写回月文件
            with open(month_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            # 删除原来的日文件
            daily_file.unlink()
            print(f"    ✅ 已合并并删除 {file_date_str}.json")


def main():
    print("=" * 50)
    print("🚀 财经新闻采集器（双数据源版）")
    print("=" * 50)

    # 获取项目根目录
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    data_dir = project_root / "data"
    archive_dir = data_dir / "archive"
    merged_dir = archive_dir / "merged"

    # 创建目录
    data_dir.mkdir(exist_ok=True, parents=True)
    archive_dir.mkdir(exist_ok=True, parents=True)
    merged_dir.mkdir(exist_ok=True, parents=True)

    print(f"📁 数据目录: {data_dir}")
    print(f"📁 日归档目录: {archive_dir}")
    print(f"📁 月合并目录: {merged_dir}")

    # 初始化标签管理器
    print("\n🏷️ 初始化标签管理器...")
    tag_manager = TagManager()
    stats = tag_manager.get_stats()
    print(f"  标签库版本: {stats['version']}")
    print(f"  行业数: {stats['industries']}, 概念数: {stats['concepts']}")

    # ========== 1. 采集东方财富 ==========
    print("\n" + "=" * 40)
    print("📈 开始采集东方财富快讯...")
    print("=" * 40)

    eastmoney_collector = EastMoneyCollector()
    eastmoney_news = eastmoney_collector.fetch_news(page_size=50)

    if not eastmoney_news:
        print("⚠️ 东方财富采集失败")
        eastmoney_news = []
    else:
        print(f"✅ 东方财富: {len(eastmoney_news)} 条")

    # ========== 2. 采集财联社（暂时注释掉） ==========
    # print("\n" + "=" * 40)
    # print("📡 开始采集财联社快讯...")
    # print("=" * 40)
    #
    # cailianshe_collector = CaiLianSheCollector()
    # cailianshe_news = cailianshe_collector.fetch_news(limit=50)
    #
    # if not cailianshe_news:
    #     print("⚠️ 财联社采集失败")
    #     cailianshe_news = []
    # else:
    #     print(f"✅ 财联社: {len(cailianshe_news)} 条")

    # ========== 3. 合并所有新闻 ==========
    # all_raw_news = eastmoney_news + cailianshe_news
    all_raw_news = eastmoney_news  # 暂时只用东方财富

    if not all_raw_news:
        print("❌ 所有数据源都采集失败")
        sys.exit(1)

    print(f"\n📊 原始新闻总数: {len(all_raw_news)} 条")

    # 添加标签
    print("\n🏷️ 正在添加行业和概念标签...")
    tagged_news = tag_manager.add_to_news_list(all_raw_news)

    tagged_count = sum(1 for item in tagged_news
                       if item.get('tags', {}).get('industries') or item.get('tags', {}).get('concepts'))
    print(f"✅ {tagged_count}/{len(tagged_news)} 条新闻成功打上标签")

    # ========== 4. 保存文件 ==========
    print("\n💾 正在保存文件...")

    # 4.1 latest.json（最近50条）
    latest_path = data_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(tagged_news[:50], f, ensure_ascii=False, indent=2)
    print(f"  ✅ latest.json: {len(tagged_news[:50])} 条")

    # 4.2 today.json（今日所有）
    today_path = data_dir / "today.json"
    existing_today = []
    if today_path.exists():
        try:
            with open(today_path, "r", encoding="utf-8") as f:
                existing_today = json.load(f)
        except:
            existing_today = []

    merged_today = merge_news_by_title(existing_today, tagged_news)
    with open(today_path, "w", encoding="utf-8") as f:
        json.dump(merged_today, f, ensure_ascii=False, indent=2)
    print(f"  ✅ today.json: {len(merged_today)} 条")

    # 4.3 按日归档
    today_str = datetime.now().strftime("%Y-%m-%d")
    archive_path = archive_dir / f"{today_str}.json"

    existing_archive = []
    if archive_path.exists():
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                existing_archive = json.load(f)
        except:
            existing_archive = []

    merged_archive = merge_news_by_title(existing_archive, tagged_news)
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(merged_archive, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 归档 {today_str}.json: {len(merged_archive)} 条")

    # 4.4 合并超过30天的旧文件
    cutoff_date = date.today() - timedelta(days=30)
    merge_monthly_files(archive_dir, merged_dir, cutoff_date)

    # 4.5 更新时间戳
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)
    print(f"  ✅ last_update.txt: {current_time}")

    # 显示示例
    if len(tagged_news) > 0:
        sample = tagged_news[0]
        print(f"\n📰 示例新闻:")
        print(f"  标题: {sample.get('title', '')[:50]}...")
        print(f"  来源: {sample.get('source', '未知')}")
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