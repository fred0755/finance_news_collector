import json
import sys
import os
from pathlib import Path
from datetime import datetime
from eastmoney_collector import EastMoneyCollector


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
    print(f"📁 数据目录: {data_dir}")

    # 切换到项目根目录
    os.chdir(project_root)
    print(f"📁 工作目录: {os.getcwd()}")

    # 采集新闻
    print("\n🔄 开始采集...")
    collector = EastMoneyCollector()
    news_list = collector.fetch_news(page_size=30)

    if not news_list:
        print("❌ 采集失败")
        sys.exit(1)

    print(f"✅ 成功采集 {len(news_list)} 条新闻")

    # 显示第一条作为示例
    if len(news_list) > 0:
        print(f"📰 示例: {news_list[0].get('title', '')[:50]}...")

    # ========== 保存文件 ==========
    print("\n💾 正在保存文件...")

    # 1. 保存 latest.json（最新30条）
    latest_path = data_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(news_list[:30], f, ensure_ascii=False, indent=2)
    print(f"  ✅ latest.json: {len(news_list[:30])} 条")

    # 2. 保存 today.json（全部）
    today_path = data_dir / "today.json"
    with open(today_path, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)
    print(f"  ✅ today.json: {len(news_list)} 条")

    # 3. 保存 last_update.txt（时间戳）
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)
    print(f"  ✅ last_update.txt: {current_time}")

    # 显示文件大小
    print("\n📊 文件大小:")
    print(f"  latest.json: {latest_path.stat().st_size} 字节")
    print(f"  today.json: {today_path.stat().st_size} 字节")
    print(f"  last_update.txt: {timestamp_path.stat().st_size} 字节")

    print("\n" + "=" * 50)
    print("✅ 采集任务完成！")
    print("=" * 50)

    sys.exit(0)


if __name__ == "__main__":
    main()