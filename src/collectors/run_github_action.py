import json
import sys
import os
from pathlib import Path
from datetime import datetime
from eastmoney_collector import EastMoneyCollector


def main():
    print("=" * 50)
    print("🚀 东方财富快讯采集器 - GitHub Actions 版")
    print("=" * 50)

    # 获取项目根目录
    current_file = Path(__file__).resolve()
    print(f"📁 脚本位置: {current_file}")

    # 向上找项目根目录 (src/collectors -> src -> 项目根目录)
    project_root = current_file.parent.parent.parent
    print(f"📁 项目根目录: {project_root}")

    # 创建数据目录
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    print(f"📁 数据目录: {data_dir}")

    # 切换工作目录到项目根目录（避免路径问题）
    os.chdir(project_root)
    print(f"📁 当前工作目录: {os.getcwd()}")

    # 采集新闻
    print("\n🔄 开始采集东方财富快讯...")
    collector = EastMoneyCollector()
    news_list = collector.fetch_news(page_size=30)

    if not news_list:
        print("❌ 采集失败：未获取到新闻数据")
        sys.exit(1)

    print(f"✅ 成功采集 {len(news_list)} 条新闻")

    # 验证数据结构
    if len(news_list) > 0:
        sample = news_list[0]
        print(f"\n📰 示例新闻:")
        print(f"   标题: {sample.get('title', 'N/A')}")
        print(f"   时间: {sample.get('time', 'N/A')}")
        print(f"   来源: {sample.get('source', 'N/A')}")
        print(f"   重要性: {sample.get('importance', 'N/A')}")

    # 保存 latest.json
    latest_path = data_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(news_list[:30], f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {latest_path} ({len(news_list[:30])} 条)")

    # 保存 today.json
    today_path = data_dir / "today.json"
    with open(today_path, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {today_path} ({len(news_list)} 条)")

    # 保存时间戳
    timestamp_path = data_dir / "last_update.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(timestamp_path, "w", encoding="utf-8") as f:
        f.write(current_time)
    print(f"✅ 已保存: {timestamp_path} ({current_time})")

    # 检查文件大小
    for file_path in [latest_path, today_path, timestamp_path]:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"📊 {file_path.name}: {size} 字节")

    print("\n" + "=" * 50)
    print("🎉 采集任务完成！")
    print("=" * 50)

    sys.exit(0)


if __name__ == "__main__":
    main()