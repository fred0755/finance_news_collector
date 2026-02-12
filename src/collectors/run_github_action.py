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

    print(f"✅ 成功采集 {len(news_list)} 条")

    # 保存文件
    with open(data_dir / "latest.json", "w", encoding="utf-8") as f:
        json.dump(news_list[:30], f, ensure_ascii=False, indent=2)

    with open(data_dir / "today.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

    with open(data_dir / "last_update.txt", "w", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print(f"✅ 数据已保存到 {data_dir}")
    print(f"📰 示例: {news_list[0].get('title', '')[:50]}...")
    sys.exit(0)


if __name__ == "__main__":
    main()