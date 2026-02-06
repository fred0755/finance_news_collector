# src/notifiers/dingtalk_notifier.py
import json
import time
import hashlib
import base64
import hmac
import requests
import logging
from urllib.parse import quote_plus


class DingTalkNotifier:
    """钉钉群机器人消息推送器"""

    def __init__(self, webhook_url, secret=None, importance_threshold=7, keywords=None):
        """
        初始化钉钉推送器

        Args:
            webhook_url: 钉钉机器人Webhook地址
            secret: 加签密钥（可选）
            importance_threshold: 重要性分数阈值，>=此分数才推送
            keywords: 钉钉要求的关键词列表
        """
        self.webhook_url = webhook_url
        self.secret = secret
        self.importance_threshold = importance_threshold
        self.keywords = keywords or ["财经快讯"]
        self.logger = logging.getLogger(__name__)

    def _generate_signature(self):
        """生成钉钉要求的签名"""
        if not self.secret:
            return None, None

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')

        # 使用HMAC-SHA256算法生成签名
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = quote_plus(base64.b64encode(hmac_code))

        return timestamp, sign

    def should_send(self, importance_score):
        """判断是否应该发送（基于重要性阈值）"""
        return importance_score >= self.importance_threshold

    def send_markdown(self, title, text, at_all=False, at_mobiles=None):
        """
        发送Markdown格式消息

        Args:
            title: 消息标题
            text: Markdown格式的消息内容
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表
        """
        # 确保消息包含关键词（钉钉要求）
        if not any(keyword in text for keyword in self.keywords):
            text = f"{self.keywords[0]}\n\n{text}"

        # 构建消息体
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title[:50],  # 标题截断防止过长
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
        """
        发送新闻提醒

        Args:
            news_item: 新闻字典，包含title, source, publish_time, url等
            importance_score: 重要性分数(0-10)
            sentiment: 情感倾向(bullish/bearish/neutral)
            sentiment_emoji: 情感表情映射字典
        """
        if not self.should_send(importance_score):
            self.logger.debug(f"新闻重要性分数 {importance_score} 低于阈值 {self.importance_threshold}，跳过推送")
            return False

        # 设置情感表情
        emoji_map = sentiment_emoji or {
            "bullish": "📈",
            "bearish": "📉",
            "neutral": "📊"
        }
        emoji = emoji_map.get(sentiment, "📰")

        # 构建消息内容
        title = news_item.get('title', '')
        source = news_item.get('source', '未知来源')
        publish_time = news_item.get('publish_time', '未知时间')
        url = news_item.get('url', '')

        # 重要性星级
        stars = "⭐" * min(importance_score, 5)  # 最多5颗星

        # 构建Markdown消息
        markdown_text = f"""### {emoji} 财经快讯 {emoji}

**{title}**

---

> **来源**：{source}  
> **时间**：{publish_time}  
> **重要性**：{importance_score}/10 {stars}  
> **情感倾向**：{sentiment} ({emoji})

📌 关键词：{', '.join(self.keywords)}

[查看详情]({url})"""

        # 消息标题
        alert_title = f"财经快讯：{title[:30]}..." if len(title) > 30 else title

        # 发送消息
        return self.send_markdown(
            title=alert_title,
            text=markdown_text,
            at_all=False  # 可根据需要修改为True
        )

    def _send_request(self, message):
        """发送HTTP请求到钉钉"""
        try:
            # 生成签名（如果使用加签）
            if self.secret:
                timestamp, sign = self._generate_signature()
                if timestamp and sign:
                    url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
                else:
                    url = self.webhook_url
            else:
                url = self.webhook_url

            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                url,
                data=json.dumps(message),
                headers=headers,
                timeout=10
            )

            result = response.json()

            if result.get('errcode') == 0:
                self.logger.info(f"钉钉消息发送成功: {result.get('errmsg')}")
                return True
            else:
                self.logger.error(f"钉钉消息发送失败: {result}")
                return False

        except Exception as e:
            self.logger.error(f"钉钉消息发送异常: {e}")
            return False


# 测试函数
def test_dingtalk():
    """测试钉钉推送功能"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config.dingtalk_config import DINGTALK_CONFIG

    # 初始化推送器
    notifier = DingTalkNotifier(
        webhook_url=DINGTALK_CONFIG['webhook_url'],
        secret=DINGTALK_CONFIG['secret'],
        importance_threshold=DINGTALK_CONFIG['importance_threshold'],
        keywords=DINGTALK_CONFIG['keywords']
    )

    # 测试新闻数据
    test_news = {
        'title': '央行宣布明日降准0.5个百分点，释放长期资金约1万亿元',
        'source': '东方财富快讯',
        'publish_time': '2025-02-06 15:30:00',
        'url': 'https://kuaixun.eastmoney.com/details.html?id=123456'
    }

    # 发送测试消息
    success = notifier.send_news_alert(
        news_item=test_news,
        importance_score=9,  # 高重要性
        sentiment='bullish',  # 看多
        sentiment_emoji=DINGTALK_CONFIG['sentiment_emoji']
    )

    if success:
        print("✅ 钉钉测试消息发送成功！请检查钉钉群聊。")
    else:
        print("❌ 钉钉测试消息发送失败，请检查配置和日志。")


if __name__ == "__main__":
    test_dingtalk()