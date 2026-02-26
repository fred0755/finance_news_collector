"""
财联社快讯采集器（修复版）
"""

import requests
import json
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional


class CaiLianSheCollector:
    """财联社快讯采集器"""

    def __init__(self):
        self.base_url = "https://www.cls.cn/nodeapi/updateTelegraphList"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.cls.cn/telegraph',
            'Accept': 'application/json, text/plain, */*',
        }
        # 基础固定参数
        self.base_params = {
            'app': 'CailianpressWeb',
            'os': 'web',
            'sv': '8.4.6',
            'hasFirstVipArticle': '0',
            'subscribedColumnIds': '',
            'rn': '20',  # 每次20条
        }
        # 固定签名（从抓包中获取）
        self.fixed_sign = "284a885ad218a13788bd48d6ab80b8e2"

    def fetch_news(self, limit: int = 50) -> Optional[List[Dict]]:
        """
        获取财联社快讯（获取最新新闻）
        """
        all_news = []

        # 首次请求不传 lastTime，获取最新
        params = self.base_params.copy()
        params['sign'] = self.fixed_sign

        print(f"🔄 开始采集财联社快讯...")

        try:
            while len(all_news) < limit:
                print(f"  ⏳ 请求: lastTime={params.get('lastTime', '无')}")

                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )

                if response.status_code == 304:
                    print("  ✅ 没有新数据 (304)")
                    break

                response.raise_for_status()
                data = response.json()

                if data.get('error') != 0:
                    print(f"  ❌ API返回错误: {data}")
                    break

                # 解析新闻列表
                roll_data = data.get('data', {}).get('roll_data', [])
                if not roll_data:
                    print("  ✅ 没有更多数据")
                    break

                print(f"  ✅ 获取到 {len(roll_data)} 条")

                # 解析每条新闻
                for item in roll_data:
                    news_item = self._parse_single_news(item)
                    if news_item:
                        all_news.append(news_item)

                # 关键修复：取最后一条的 ctime 作为下一次的 lastTime
                # 这样下次请求会获取更早的历史数据
                last_item = roll_data[-1]
                params['lastTime'] = last_item.get('ctime', 0)

                # 礼貌性延迟
                time.sleep(0.5)

            print(f"✅ 本次采集共获取 {len(all_news)} 条新闻")
            return all_news

        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_single_news(self, item: Dict) -> Optional[Dict]:
        """解析单条新闻"""
        try:
            news_id = str(item.get('id', ''))
            ctime = item.get('ctime', 0)

            # 标题处理：如果没有标题，用brief的前半部分
            title = item.get('title', '').strip()
            if not title:
                brief = item.get('brief', '')
                # 提取 "[标题]" 格式的内容
                if brief.startswith('【') and '】' in brief:
                    title = brief.split('】')[0].replace('【', '') + '...'
                else:
                    title = brief[:30] + '...' if len(brief) > 30 else brief

            brief = item.get('brief', '')
            content = item.get('content', '') or brief

            # 时间处理
            time_str = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S') if ctime else ''

            # 提取相关股票
            stock_list = []
            for stock in item.get('stock_list', []):
                stock_code = stock.get('StockID', '')
                if stock_code:
                    stock_list.append(stock_code)

            # 提取题材
            subjects = []
            for subject in item.get('subjects', []):
                subject_name = subject.get('subject_name', '')
                if subject_name:
                    subjects.append(subject_name)

            # 构建标准新闻对象
            news_item = {
                'id': hashlib.md5(f"{news_id}_{ctime}".encode()).hexdigest()[:16],
                'code': news_id,
                'title': title,
                'summary': brief,
                'content': content,
                'full_content': content,
                'time': time_str,
                'publish_time': time_str,
                'source': '财联社',
                'url': item.get('shareurl', f"https://www.cls.cn/telegraph"),
                'category': self._infer_category(title + ' ' + brief),
                'importance': self._calculate_importance(item),
                'sentiment': self._judge_sentiment(title + ' ' + brief),
                'related_stocks': stock_list,
                'has_stock_mention': len(stock_list) > 0,
                'subjects': subjects,
                'comment_count': item.get('comment_num', 0),
                'share_count': item.get('share_num', 0),
                'ctime': ctime,  # 保留原始时间戳，便于调试
                'raw_data': item
            }
            return news_item

        except Exception as e:
            print(f"⚠️ 解析单条新闻失败: {e}")
            return None

    def _infer_category(self, text: str) -> str:
        """推断分类"""
        text_lower = text.lower()
        categories = {
            '宏观': ['gdp', 'cpi', 'ppi', '通胀', '货币政策', '央行', '利率'],
            '股市': ['a股', '沪指', '深指', '创业板', '科创板', '涨停', '跌停'],
            '债券': ['国债', '地方债', '债券', '收益率'],
            '期货': ['期货', '原油', '黄金', '白银', '铜', '铝'],
            '公司': ['财报', '业绩', '营收', '净利润', '分红', '回购'],
            '行业': ['行业', '板块', '概念'],
            '国际': ['美联储', '加息', '降息', '贸易战'],
            '政策': ['政策', '法规', '监管'],
            '科技': ['人工智能', 'ai', '芯片', '半导体'],
        }
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        return '其他'

    def _calculate_importance(self, item: Dict) -> int:
        """计算重要性"""
        score = 5
        reading_num = item.get('reading_num', 0)
        if reading_num > 20000:
            score += 2
        elif reading_num > 10000:
            score += 1
        if item.get('stock_list'):
            score += 1
        if item.get('subjects'):
            score += 1
        return max(1, min(10, score))

    def _judge_sentiment(self, text: str) -> str:
        """判断情感"""
        text_lower = text.lower()
        bullish = ['上涨', '看好', '突破', '利好', '增长', '复苏']
        bearish = ['下跌', '看空', '跌破', '利空', '下滑', '衰退']
        bull_count = sum(1 for w in bullish if w in text_lower)
        bear_count = sum(1 for w in bearish if w in text_lower)
        if bull_count > bear_count:
            return 'bullish'
        elif bear_count > bull_count:
            return 'bearish'
        return 'neutral'

    def test_collection(self, limit: int = 20):
        """测试采集"""
        print("=" * 60)
        print("📊 财联社快讯采集器测试")
        print("=" * 60)

        news_list = self.fetch_news(limit=limit)

        if not news_list:
            print("❌ 采集失败")
            return False

        print(f"\n✅ 成功采集 {len(news_list)} 条新闻")
        print("-" * 60)

        for i, news in enumerate(news_list[:10], 1):
            time_str = news.get('time', '')[-8:]
            title = news.get('title', '')[:40]
            subjects = news.get('subjects', [])[:2]
            subject_str = f" [{','.join(subjects)}]" if subjects else ''
            stock_str = " 📈" if news.get('has_stock_mention') else ""
            print(f"{i:2d}. {time_str} {title}{subject_str}{stock_str}...")

        if len(news_list) > 10:
            print(f"... 还有 {len(news_list) - 10} 条未显示")

        return True


if __name__ == "__main__":
    collector = CaiLianSheCollector()
    collector.test_collection()