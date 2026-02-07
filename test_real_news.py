# 创建 test_real_news.py 在项目根目录
# !/usr/bin/env python3
"""
测试实际新闻采集和推送
"""

import sys
import os

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

print("🧪 测试实际新闻采集和推送")
print("=" * 60)

try:
    # 导入采集器
    from collectors.eastmoney_collector import EastMoneyCollector

    print("✅ 采集器导入成功")

    # 导入分析器
    from analyzers.basic_analyzer import BasicNewsAnalyzer

    print("✅ 分析器导入成功")

    # 导入钉钉推送器
    from notifiers.dingtalk_notifier import DingTalkNotifier

    print("✅ 钉钉推送器导入成功")

    # 创建实例
    collector = EastMoneyCollector()
    analyzer = BasicNewsAnalyzer()

    # 钉钉配置
    dingtalk_notifier = DingTalkNotifier(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611",
        secret="SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2",
        importance_threshold=5
    )

    # 1. 采集实际新闻
    print("\n1. 采集实际新闻...")
    if hasattr(collector, 'fetch_news'):
        news_list = collector.fetch_news()
    elif hasattr(collector, 'collect_latest_news'):
        news_list = collector.collect_latest_news()
    else:
        news_list = []

    if not news_list:
        print("❌ 没有采集到新闻")
        sys.exit(1)

    print(f"✅ 采集到 {len(news_list)} 条新闻")

    # 2. 分析并显示前5条新闻
    print("\n2. 分析新闻评分...")
    for i, news_item in enumerate(news_list[:5]):  # 只看前5条
        analysis = analyzer.analyze_news(news_item)
        score = analysis['importance_score']
        sentiment = analysis['sentiment']
        title = news_item.get('title', '')[:60]

        print(f"   新闻{i + 1}: {score}/10 - {title}...")
        print(f"      情感: {sentiment}, 推送: {'是' if score >= 5 else '否'}")

        # 如果分数足够高，测试推送
        if score >= 5:
            print(f"    🚨 测试推送这条新闻...")
            success = dingtalk_notifier.send_news_alert(
                news_item=news_item,
                importance_score=score,
                sentiment=sentiment,
                sentiment_emoji={"bullish": "📈", "bearish": "📉", "neutral": "📊"}
            )
            if success:
                print(f"    ✅ 推送成功！请检查钉钉群")
            else:
                print(f"    ❌ 推送失败")

    print("\n3. 查看所有新闻标题...")
    for i, news_item in enumerate(news_list):
        title = news_item.get('title', '')
        print(f"   {i + 1:2d}. {title[:80]}...")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback

    traceback.print_exc()

print("=" * 60)
print("测试完成")