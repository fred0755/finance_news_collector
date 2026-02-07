#!/usr/bin/env python3
"""
钉钉群机器人消息推送器 - 修复版（解决emoji变量问题）
"""

import json
import time
import hashlib
import base64
import hmac
import requests
from urllib.parse import quote_plus


class DingTalkNotifier:
    """钉钉群机器人消息推送器"""

    def __init__(self, webhook_url, secret=None, importance_threshold=7, keywords=None):
        self.webhook_url = webhook_url
        self.secret = secret
        self.importance_threshold = importance_threshold
        self.keywords = keywords or ["财经快讯"]

    def _generate_signature(self, timestamp):
        """生成钉钉要求的签名"""
        if not self.secret:
            return None, None

        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')

        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = quote_plus(base64.b64encode(hmac_code))

        return timestamp, sign

    def should_send(self, importance_score):
        """判断是否应该发送"""
        return True  # 修改为始终发送，推送所有新闻

    def send_markdown(self, title, text, at_all=False, at_mobiles=None):
        """发送Markdown格式消息"""
        # 确保消息包含关键词（钉钉要求）
        if not any(keyword in text for keyword in self.keywords):
            text = f"{self.keywords[0]}\n\n{text}"

        # 构建消息体
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title[:50],
                "text": text
            }
        }

        # 添加@功能
        if at_all or at_mobiles:
            message["at"] = {}
            if at_all:
                message["at"]["isAtAll"] = True
            if at_mobiles:
                message["at"]["atMobiles"] = at_mobiles

        return self._send_request(message)

    def send_news_alert(self, news_item, importance_score, sentiment, sentiment_emoji=None):
        """发送新闻提醒"""
        # 设置情感表情
        emoji_map = sentiment_emoji or {
            "bullish": "📈",
            "bearish": "📉",
            "neutral": "📊"
        }
        emoji = emoji_map.get(sentiment, "📰")  # 关键：定义emoji变量

        # 构建消息内容
        title = news_item.get('title', '')
        source = news_item.get('source', '东方财富快讯')
        publish_time = news_item.get('publish_time', news_item.get('time', '未知时间'))
        url = news_item.get('url', '#')

        # 重要性星级
        stars = "⭐" * min(importance_score, 5)

        # 构建Markdown消息
        markdown_text = f"""### {emoji} 财经快讯 {emoji}

**{title}**

---

> **来源**: {source}  
> **时间**: {publish_time}  
> **重要性**: {importance_score}/10 {stars}  
> **情感倾向**: {sentiment} ({emoji})

📌 关键词: {', '.join(self.keywords)}

[查看详情]({url})"""

        # 消息标题
        alert_title = f"财经快讯: {title[:30]}..." if len(title) > 30 else title

        # 发送消息
        print(f"[钉钉推送] 正在发送: {title[:50]}...")
        return self.send_markdown(
            title=alert_title,
            text=markdown_text,
            at_all=False
        )

    def _send_request(self, message):
        """发送HTTP请求到钉钉"""
        try:
            # 生成签名
            if self.secret:
                timestamp = str(round(time.time() * 1000))
                timestamp, sign = self._generate_signature(timestamp)
                if timestamp and sign:
                    url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
                else:
                    url = self.webhook_url
            else:
                url = self.webhook_url

            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(message), headers=headers, timeout=10)

            result = response.json()

            if result.get('errcode') == 0:
                print(f"[钉钉推送] ✅ 消息发送成功")
                return True
            else:
                print(f"[钉钉推送] ❌ 消息发送失败: {result}")
                return False

        except Exception as e:
            print(f"[钉钉推送] ❌ 发送异常: {e}")
            return False


# 测试函数
if __name__ == "__main__":
    print("钉钉推送器模块测试")

    # 测试配置
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=test"
    secret = "SECtest"

    # 创建推送器
    notifier = DingTalkNotifier(webhook, secret, importance_threshold=5)

    # 测试新闻
    test_news = {
        'title': '测试新闻标题',
        'source': '测试',
        'publish_time': '2026-02-07 17:55:00',
        'url': 'https://test.com'
    }

    result = notifier.send_news_alert(test_news, 8, 'neutral')
    print(f"测试结果: {result}")