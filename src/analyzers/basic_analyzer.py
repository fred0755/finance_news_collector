# src/analyzers/basic_analyzer.py
import re
import logging


class BasicNewsAnalyzer:
    def __init__(self):
        # 1. 初始化规则：定义重要新闻的来源权重
        self.source_weights = {
            '东方财富': 8,
            '财联社': 9,
            '证券时报': 9,
            '上海证券报': 9,
            '中国证券报': 9,
        }
        # 2. 初始化关键词词典：用于重要性评分和情感判断
        self.importance_keywords = {
            '加息': 10, '降息': 10, '降准': 9,
            'GDP': 9, 'CPI': 8, 'PPI': 8,
            '贸易摩擦': 9, '关税': 8,
            '证监会': 9, '交易所': 8,
            '涨停': 7, '跌停': 7, '暴涨': 6, '暴跌': 6,
            '合作': 5, '签约': 5, '投产': 6,
            '财报': 7, '业绩预告': 7,
        }
        self.bullish_keywords = ['上涨', '看好', '突破', '利好', '增长', '复苏', '扩张', '买入', '推荐', '超预期']
        self.bearish_keywords = ['下跌', '看空', '跌破', '利空', '下滑', '衰退', '收缩', '卖出', '预警', '不及预期']
        self.logger = logging.getLogger(__name__)

    def analyze_news(self, news_item):
        """分析单条新闻，返回重要性评分和多空倾向"""
        title = news_item.get('title', '')
        source = news_item.get('source', '未知')

        # 核心分析步骤
        importance_score = self._calculate_importance(title, source)
        sentiment = self._judge_sentiment(title)

        return {
            'importance_score': importance_score,  # 0-10分
            'sentiment': sentiment,  # 'bullish'/'neutral'/'bearish'
            'title': title,
            'source': source
        }

    def _calculate_importance(self, title, source):
        """基于来源和关键词计算重要性评分"""
        score = 0
        # 规则1: 来源权重
        score += self.source_weights.get(source, 5)
        # 规则2: 标题关键词匹配
        for keyword, weight in self.importance_keywords.items():
            if keyword in title:
                score += weight
        # 规则3: 紧急标识
        if any(mark in title for mark in ['【突发】', '[紧急]', '快讯：']):
            score += 3
        # 将得分限制在0-10之间
        return min(10, max(0, score // 3))

    def _judge_sentiment(self, title):
        """判断新闻标题的多空倾向"""
        bullish_count = sum(1 for word in self.bullish_keywords if word in title)
        bearish_count = sum(1 for word in self.bearish_keywords if word in title)

        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'


# 简易测试函数
def test_analyzer():
    analyzer = BasicNewsAnalyzer()
    test_news = [
        {'title': '央行宣布明日降准0.5个百分点', 'source': '东方财富'},
        {'title': '某公司股价今日涨停', 'source': '未知'},
        {'title': '贸易摩擦加剧，出口数据下滑', 'source': '财联社'},
    ]
    for news in test_news:
        result = analyzer.analyze_news(news)
        print(f"标题: {result['title']}")
        print(f"  重要性: {result['importance_score']}/10, 情感: {result['sentiment']}")
        print("-" * 40)


if __name__ == "__main__":
    test_analyzer()