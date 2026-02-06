# src/scheduler/dingtalk_config.py
DINGTALK_CONFIG = {
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=e08a39e5f72e5fa6966a72507bed3c6c3c7133288696bcfc585297c13f3df611",
    "secret": "SECfc699d2056a92e6a8594b836e916bd0df8af8b774ba5424a508349896ab42ee2",
    "importance_threshold": 5,  # 降低到5分测试
    "keywords": ["财经快讯"],
    "sentiment_emoji": {
        "bullish": "📈",
        "bearish": "📉",
        "neutral": "📊"
    }
}