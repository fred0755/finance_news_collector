import json
import sys
from pathlib import Path
from eastmoney_collector import EastMoneyCollector


def main():
    print("开始采集东方财富快讯...")

    # 创建数据目录
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # 采集新闻
    collector = EastMoneyCollector()
    news_list = collector.fetch_news(page_size=30)

    if not news_list or len(news_list) == 0:
        print("❌ 采集失败")
        sys.exit(1)

    print(f"✅ 成功采集 {len(news_list)} 条新闻")

    # 保存 latest.json
    with open(data_dir / "latest.json", "w", encoding="utf-8") as f:
        json.dump(news_list[:30], f, ensure_ascii=False, indent=2)

    # 保存 today.json
    with open(data_dir / "today.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

    # 保存时间戳
    from datetime import datetime
    with open(data_dir / "last_update.txt", "w", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print("✅ JSON文件生成成功")
    print(f"📁 数据目录: {data_dir}")

    # 打印第一条作为验证
    if news_list:
        print(f"📰 示例: {news_list[0].get('title', '')[:50]}...")

    sys.exit(0)


if __name__ == "__main__":
    main()