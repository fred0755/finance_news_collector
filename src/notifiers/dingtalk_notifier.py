#!/usr/bin/env python3
"""
钉钉群机器人消息推送器 - 最终优化版（直接在消息中显示完整内容）
"""

import json
import time
import hashlib
import base64
import hmac
import requests
from urllib.parse import quote_plus
import re


class DingTalkNotifier:
    """钉钉群机器人消息推送器 - 优化版"""

    def __init__(self, webhook_url, secret=None, importance_threshold=5, keywords=None):
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

    def send_news_direct(self, news_item):
        """发送新闻 - 直接在消息中显示内容（推荐使用）"""
        try:
            # 提取新闻信息
            title = news_item.get('title', '财经快讯')
            content = news_item.get('full_content', news_item.get('content', title))
            source = news_item.get('source', '东方财富快讯')
            publish_time = news_item.get('publish_time', news_item.get('time', '未知时间'))
            importance = news_item.get('importance', 5)
            sentiment = news_item.get('sentiment', 'neutral')

            # 情感表情映射
            emoji_map = {
                "bullish": "📈",
                "bearish": "📉",
                "neutral": "📊"
            }
            emoji = emoji_map.get(sentiment, "📰")

            # 重要性星级
            stars = "⭐" * min(importance, 5)

            # 格式化内容
            formatted_content = self._format_content_for_dingtalk(content)

            # 构建Markdown消息
            markdown_text = f"""# {emoji} 财经快讯 {emoji}

## {title}

**📅 发布时间**: {publish_time}  
**📋 新闻来源**: {source}  
**🎯 重要性评分**: {importance}/10 {stars}  
**📊 市场情绪**: {sentiment} ({emoji})

---

### 📝 详细内容：

{formatted_content}

---

> 🔄 实时采集 · 自动推送  
> ⏰ 推送时间: {time.strftime('%Y-%m-%d %H:%M:%S')}  
> 📌 关键词: 财经快讯"""

            # 消息标题
            alert_title = f"快讯: {title[:30]}..." if len(title) > 30 else title

            # 发送消息
            print(f"[钉钉推送] 正在发送: {title[:50]}...")
            return self.send_markdown(
                title=alert_title,
                text=markdown_text,
                at_all=False
            )

        except Exception as e:
            print(f"[钉钉推送] 发送新闻失败: {e}")
            return False

    def _format_content_for_dingtalk(self, content):
        """为钉钉格式化内容"""
        if not content:
            return "暂无详细内容"

        # 清理内容
        content = content.strip()

        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)

        # 替换多个换行为单个
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 确保内容长度合适（钉钉Markdown支持最多2000字符）
        max_length = 1500
        if len(content) > max_length:
            content = content[:max_length] + "...\n\n【内容已截断，完整内容请查看原文】"

        return content

    def send_news_alert(self, news_item, importance_score, sentiment, sentiment_emoji=None):
        """发送新闻提醒（兼容旧版）"""
        # 使用新的直接发送方法
        return self.send_news_direct(news_item)

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
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611"
    secret = "SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2"

    # 创建推送器
    notifier = DingTalkNotifier(webhook, secret, importance_threshold=5)

    # 测试新闻
    test_news = {
        'title': '马斯克：是时候大规模重返月球了',
        'full_content': '【马斯克：是时候大规模重返月球了】马斯克发帖表示，是时候大规模重返月球了。此外，有消息称SpaceX正在奥斯汀和西雅图招聘工程师，以开发人工智能卫星和太空数据中心。这一表态引发市场对太空探索相关公司的关注。',
        'content': '马斯克发帖表示，是时候大规模重返月球了。',
        'source': '东方财富快讯',
        'publish_time': '2026-02-08 17:29:40',
        'importance': 8,
        'sentiment': 'neutral'
    }

    result = notifier.send_news_direct(test_news)
    print(f"测试结果: {result}")