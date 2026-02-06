# config/dingtalk_config.py
DINGTALK_CONFIG = {
    # ✅ 您的Webhook地址
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611",

    # ✅ 您的加签密钥
    "secret": "SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2",

    # 推送配置
    "msg_type": "markdown",  # 使用Markdown格式，支持富文本
    "importance_threshold": 7,  # 重要性阈值：>=7分的新闻才推送
    "at_all": False,  # 是否@所有人
    "keywords": ["财经快讯"],  # 钉钉要求的关键词（消息中需包含）

    # 情感倾向表情映射
    "sentiment_emoji": {
        "bullish": "📈",  # 看多
        "bearish": "📉",  # 看空
        "neutral": "📊"  # 中性
    }
}