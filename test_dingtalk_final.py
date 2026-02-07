#!/usr/bin/env python3
"""
钉钉推送器独立测试 - 纯代码版
"""

import sys
import os

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

print("🧪 钉钉推送器独立测试")
print("=" * 50)

try:
    # 直接导入钉钉推送器
    print("1. 导入钉钉推送器...")
    from notifiers.dingtalk_notifier import DingTalkNotifier

    print("   ✅ 导入成功")

    # 钉钉配置
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611"
    secret = "SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2"

    print("2. 创建钉钉推送器实例...")
    notifier = DingTalkNotifier(
        webhook_url=webhook_url,
        secret=secret,
        importance_threshold=5
    )
    print("   ✅ 实例创建成功")

    # 检查方法
    print("3. 检查可用方法...")
    print(f"   - has send_news_alert: {hasattr(notifier, 'send_news_alert')}")
    print(f"   - has should_send: {hasattr(notifier, 'should_send')}")
    print(f"   - has send_markdown: {hasattr(notifier, 'send_markdown')}")

    # 测试 should_send 方法
    print("4. 测试 should_send 方法...")
    print(f"   分数6，阈值5，应该推送: {notifier.should_send(6)}")
    print(f"   分数4，阈值5，不应该推送: {notifier.should_send(4)}")

    # 测试新闻数据
    print("5. 准备测试新闻数据...")
    test_news = {
        'title': '【测试】央行宣布降准0.5个百分点，释放长期资金约1万亿元',
        'source': '东方财富快讯',
        'publish_time': '2026-02-07 17:30:00',
        'url': 'https://kuaixun.eastmoney.com/details.html?id=test123'
    }

    print("6. 发送测试消息到钉钉...")
    print("   如果配置正确，钉钉群会收到消息")

    success = notifier.send_news_alert(
        news_item=test_news,
        importance_score=9,
        sentiment='bullish',
        sentiment_emoji={'bullish': '📈', 'bearish': '📉', 'neutral': '📊'}
    )

    if success:
        print("   ✅ 钉钉消息发送成功！请检查钉钉群")
    else:
        print("   ⚠️  钉钉消息发送失败或模拟发送")

except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"   当前Python路径: {sys.path}")

except Exception as e:
    print(f"❌ 测试过程中出错: {e}")
    import traceback

    traceback.print_exc()

print("=" * 50)
print("测试完成")