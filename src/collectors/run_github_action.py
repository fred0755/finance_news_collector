#!/usr/bin/env python
"""
财经新闻采集器 - 修复版
功能：
- 增量采集东方财富快讯
- 强制按 showTime 排序，确保新新闻在最前
- 数据完整性检查
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from eastmoney_collector import EastMoneyCollector

# 导入标签管理器
sys.path.insert(0, str(Path(__file__).parent.parent))
from tags.tag_manager import TagManager


def merge_news_by_title(existing_news, new_news):
    """
    按标题去重合并新闻列表（强制按 showTime 排序）
    确保最新的新闻永远在最前面
    """
    news_map = {}

    # 先添加已有的
    for item in existing_news:
        title = item.get('title', '')
        if title:
            news_map[title] = item

    # 再添加新的，如果标题重复，保留时间更新的那条
    for item in new_news:
        title = item.get('title', '')
        if title:
            if title in news_map:
                old_time = news_map[title].get('showTime', news_map[title].get('time', ''))
                new_time = item.get('showTime', item.get('time', ''))
                if new_time > old_time:
                    news_map[title] = item
            else:
                news_map[title] = item

    # 转回列表
    result = list(news_map.values())

    # 强制按 showTime 倒序排序（最新的在前）
    result.sort(key=lambda x: x.get('showTime', x.get('time', '')), reverse=True)

    # 打印时间范围供调试
    if result:
        newest = result[0].get('showTime', result[0].get('time', '未知'))
        oldest = result[-1].get('showTime', result[-1].get('time', '未知'))
        print(f"  📊 合并后: {len(result)} 条 (原{len(existing_news)} + 新{len(new_news)})")
        print(f"  🕐 时间范围: {oldest} → {newest}")
    else:
        print(f"  ⚠️ 合并后为空")

    return result


def merge_monthly_files(archive_dir, merged_dir, cutoff_date):
    """将超过30天的日文件合并到月文件"""
    print(f"\n🔄 检查需要合并的旧文件（{cutoff_date} 之前的）...")
    daily_files = sorted(archive_dir.glob("20??-??-??.json"))

    for daily_file in daily_files:
        file_date_str = daily_file.stem
        try:
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
        except:
            continue

        if file_date < cutoff_date:
            print(f"  📦 合并 {file_date_str} 到月文件")
            try:
                with open(daily_file, 'r', encoding='utf-8') as f:
                    daily_news = json.load(f)
            except:
                print(f"    ⚠️ 读取失败，跳过")
                continue

            month_str = file_date_str[:7]
            month_file = merged_dir / f"{month_str}.json"

            month_news = []
            if month_file.exists():
                try:
                    with open(month_file, 'r', encoding='utf-8') as f:
                        month_news = json.load(f)
                except:
                    month_news = []

            merged = merge_news_by_title(month_news, daily_news)
            with open(month_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            daily_file.unlink()
            print(f"    ✅ 已合并并删除 {file_date_str}.json")


def safe_save_json(file_path, data, description=""):
    """安全保存JSON文件，包含完整性检查"""
    if not data:
        print(f"⚠️ 警告: {description} 数据为空，跳过保存 {file_path}")
        return False

    if len(data) == 0:
        print(f"⚠️ 警告: {description} 数据为空数组，跳过保存 {file_path}")
        return False

    temp_path = file_path.with_suffix('.tmp')

    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 验证临时文件
        with open(temp_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
            if len(test_data) != len(data):
                raise ValueError("数据长度不匹配")

        temp_path.replace(file_path)
        print(f"  ✅ {description}: {len(data)} 条")
        return True

    except Exception as e:
        print(f"  ❌ 保存 {description} 失败: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False


def main():
    print("=" * 50)
    print("🚀 财经新闻采集器（修复版）")
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
    eastmoney_news = eastmoney_collector.fetch_news(max_items=50)

    if not eastmoney_news:
        print("⚠️ 东方财富采集失败")
        eastmoney_news = []
    else:
        print(f"✅ 东方财富: {len(eastmoney_news)} 条")

    # ========== 2. 合并所有新闻 ==========
    all_raw_news = eastmoney_news

    if not all_raw_news:
        print("❌ 所有数据源都采集失败")
        # 即使采集失败，也要检查现有文件是否正常
        print("\n🔍 检查现有数据文件完整性...")
        today_path = data_dir / "today.json"
        if today_path.exists():
            try:
                with open(today_path, 'r', encoding='utf-8') as f:
                    today_data = json.load(f)
                print(f"✅ today.json 当前有 {len(today_data)} 条新闻")

                if today_data and len(today_data) > 0:
                    newest = today_data[0]
                    oldest = today_data[-1]
                    print(
                        f"📰 时间范围: {oldest.get('showTime', oldest.get('time', '未知'))} → {newest.get('showTime', newest.get('time', '未知'))}")
            except Exception as e:
                print(f"❌ today.json 可能已损坏: {e}")
        sys.exit(1)

    print(f"\n📊 原始新闻总数: {len(all_raw_news)} 条")

    # 添加标签
    print("\n🏷️ 正在添加行业和概念标签...")
    tagged_news = tag_manager.add_to_news_list(all_raw_news)

    tagged_count = sum(1 for item in tagged_news
                       if item.get('tags', {}).get('industries') or item.get('tags', {}).get('concepts'))
    print(f"✅ {tagged_count}/{len(tagged_news)} 条新闻成功打上标签")

    # ========== 3. 保存文件 ==========
    print("\n💾 正在保存文件...")

    # ========== 1. 更新 latest.json（最新50条） ==========
    latest_path = data_dir / "latest.json"
    safe_save_json(latest_path, tagged_news[:50], "latest.json")

    # ========== 2. 按日归档（不再维护 today.json） ==========
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
    safe_save_json(archive_path, merged_archive, f"归档 {today_str}.json")

    # 3. 可选：删除30天前的旧文件（保持仓库大小）
    # cleanup_old_files(archive_dir, days=30)

    # 安全检查：如果合并后数据为空，但之前有数据，保留原文件
    if len(merged_today) == 0 and len(existing_today) > 0:
        print("⚠️ 警告: 合并后数据为空，但原文件有数据！保留原文件。")
    else:
        safe_save_json(today_path, merged_today, "today.json")

        # 保存后立即验证
        if today_path.exists():
            with open(today_path, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
            if verify_data:
                print(f"🔍 验证 today.json 最新新闻: {verify_data[0].get('showTime', '未知')}")
                print(f"🔍 验证 today.json 最早新闻: {verify_data[-1].get('showTime', '未知')}")

    # 3.3 按日归档
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
    safe_save_json(archive_path, merged_archive, f"归档 {today_str}.json")

    # 3.4 合并超过30天的旧文件
    cutoff_date = date.today() - timedelta(days=30)
    merge_monthly_files(archive_dir, merged_dir, cutoff_date)

    # 3.5 更新时间戳
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)
    print(f"  ✅ last_update.txt: {current_time}")

    # 显示最终统计
    print("\n" + "=" * 50)
    print("📊 最终统计:")
    if today_path.exists():
        with open(today_path, 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        print(f"  today.json 总条数: {len(final_data)}")
        if final_data:
            print(f"  最新新闻时间: {final_data[0].get('showTime', final_data[0].get('time', '未知'))}")
            print(f"  最早新闻时间: {final_data[-1].get('showTime', final_data[-1].get('time', '未知'))}")
    print(f"  本次新增: {len(tagged_news)}")
    print(f"  归档文件: {archive_path.name} ({len(merged_archive)} 条)")

    # 显示示例
    if len(tagged_news) > 0:
        sample = tagged_news[0]
        print(f"\n📰 示例新闻:")
        print(f"  标题: {sample.get('title', '')[:50]}...")
        print(f"  时间: {sample.get('showTime', sample.get('time', '未知'))}")
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