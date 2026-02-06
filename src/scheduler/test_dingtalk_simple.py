# src/scheduler/test_dingtalk_simple.py
import sys
import os

# 添加项目路径
sys.path.append('..')

# 导入钉钉推送器
from notifiers.dingtalk_notifier import DingTalkNotifier

# 测试配置
config = {
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611",
    "secret": "SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2",
    "importance_threshold": 5,
}

print("测试钉钉推送器...")

# 创建推送器
notifier = DingTalkNotifier(
    webhook_url=config['webhook_url'],
    secret=config['secret'],
    importance_threshold=config['importance_threshold']
)

# 测试新闻
test_news = {
    'title': '【测试】央行宣布降准，释放资金1万亿元',
    'source': '测试系统',
    'publish_time': '2026-02-06 18:45:00',
    'url': 'https://kuaixun.eastmoney.com'
}

print("发送测试消息...")
success = notifier.send_news_alert(
    news_item=test_news,
    importance_score=9,
    sentiment='bullish',
    sentiment_emoji={'bullish': '📈', 'bearish': '📉', 'neutral': '📊'}
)

if success:
    print("✅ 钉钉消息发送成功！请检查钉钉群")
else:
    print("❌ 钉钉消息发送失败")