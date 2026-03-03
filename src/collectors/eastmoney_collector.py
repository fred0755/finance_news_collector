import requests
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class EastMoneyCollector:
    """东方财富快讯采集器（修复增量方向版）"""

    def __init__(self):
        self.base_url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"

        # 用于记录最后一次采集到的最小 news_id（时间戳）
        self.last_news_id = self._load_last_news_id()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://kuaixun.eastmoney.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        self.base_params = {
            'client': 'web',
            'biz': 'web_724',
            'fastColumn': '102',
            'pageSize': 50,
        }

    def _load_last_news_id(self) -> int:
        """加载最后一次采集的新闻ID（时间戳）"""
        project_root = Path(__file__).parent.parent.parent
        last_id_file = project_root / "data" / "eastmoney_last_id.txt"

        if last_id_file.exists():
            try:
                with open(last_id_file, 'r') as f:
                    return int(f.read().strip())
            except:
                # 如果文件损坏，返回一个很早的时间戳，确保能采集到所有新闻
                return 0
        return int(time.time() * 1000000)  # 默认当前时间

    def _save_last_news_id(self, news_id: int):
        """保存最后一次采集的新闻ID"""
        project_root = Path(__file__).parent.parent.parent
        last_id_file = project_root / "data" / "eastmoney_last_id.txt"

        with open(last_id_file, 'w') as f:
            f.write(str(news_id))

    def fetch_news(self, max_items: int = 50) -> Optional[List[Dict]]:
        """
        增量采集新闻 - 修复版
        从当前时间开始，往前采集，直到遇到已采集过的新闻
        """
        all_news = []

        # ===== 修复：从当前时间开始采集，而不是从 last_news_id =====
        current_sort_end = int(time.time() * 1000000)  # 当前时间戳
        min_sort_end = current_sort_end
        max_pages = 10

        print(f"🔄 开始增量采集，当前时间戳: {current_sort_end}, 上次最后ID: {self.last_news_id}")

        for page in range(max_pages):
            try:
                params = self.base_params.copy()
                params['sortEnd'] = current_sort_end
                params['req_trace'] = int(time.time() * 1000)
                params['_'] = int(time.time() * 1000)
                params['callback'] = f'jQuery_{int(time.time() * 1000)}'

                print(f"  ⏳ 请求第 {page + 1} 页，sortEnd={current_sort_end}")

                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )

                raw_text = response.text
                json_start = raw_text.find('(')
                json_end = raw_text.rfind(')')

                if json_start == -1 or json_end == -1:
                    print("  ⚠️ 响应不是JSONP格式")
                    break

                json_str = raw_text[json_start + 1:json_end]
                data = json.loads(json_str)

                if data.get('code') != "1":
                    print(f"  ⚠️ API返回错误: {data}")
                    break

                news_data = data.get('data', {}).get('fastNewsList', [])
                if not news_data:
                    print("  ✅ 没有更多数据")
                    break

                # 解析新闻
                page_news = []
                page_min_sort = current_sort_end

                for item in news_data:
                    news_item = self._parse_single_news(item)
                    if news_item:
                        page_news.append(news_item)

                        # 更新本页最小时间戳
                        item_sort = item.get('realSort', 0)
                        try:
                            if isinstance(item_sort, str):
                                item_sort = int(item_sort)
                            if item_sort and item_sort < page_min_sort:
                                page_min_sort = item_sort
                        except:
                            pass

                print(f"  ✅ 本页获取 {len(page_news)} 条，本页最小时间戳: {page_min_sort}")

                # 如果这一页的新闻都小于上次的最后ID，说明已经采集过
                if page_min_sort <= self.last_news_id:
                    # 只保留比上次最后ID大的新闻
                    new_in_page = [n for n in page_news if n.get('sort_time', 0) > self.last_news_id]
                    print(f"  🔍 本页新增 {len(new_in_page)} 条（过滤掉已采集的）")
                    all_news.extend(new_in_page)
                    break
                else:
                    all_news.extend(page_news)
                    current_sort_end = page_min_sort
                    min_sort_end = min(min_sort_end, page_min_sort)

                time.sleep(0.5)

            except Exception as e:
                print(f"  ❌ 采集失败: {e}")
                break

        # 更新 last_news_id 为本次采集到的最小时间戳
        if all_news and min_sort_end < self.last_news_id:
            self.last_news_id = min_sort_end
            self._save_last_news_id(min_sort_end)
            print(f"✅ 更新最后ID为: {min_sort_end}")

        print(f"✅ 本次共采集 {len(all_news)} 条新新闻")

        # 按时间倒序排列（最新的在前）
        all_news.sort(key=lambda x: x.get('sort_time', 0), reverse=True)
        return all_news[:max_items]

    def _parse_single_news(self, item) -> Optional[Dict]:
        """解析单条新闻"""
        try:
            unique_str = f"{item.get('title', '')}_{item.get('showTime', '')}_{item.get('code', '')}"
            news_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]

            title_raw = item.get('title', '').strip()
            summary = item.get('summary', '').strip()
            code = item.get('code', '')
            show_time = item.get('showTime', '')
            sort_time = item.get('realSort', 0)

            # 处理标题新闻
            if summary.startswith('【') and '】' in summary:
                bracket_title = summary.split('】')[0].replace('【', '')
                title = bracket_title
                content = summary
                full_content = summary
            else:
                title = title_raw
                content = summary if summary else title
                full_content = content

            news_item = {
                'id': news_id,
                'code': code,
                'title': title,
                'summary': summary,
                'content': content,
                'full_content': full_content,
                'sort_time': sort_time,
                'showTime': show_time,  # 保留用于排序
                'time': show_time,
                'publish_time': show_time,
                'raw_data': item
            }

            # 来源
            source = item.get('mediaName', item.get('source', ''))
            news_item['source'] = source.strip() if source else '东方财富快讯'

            # URL
            news_item[
                'url'] = f"https://kuaixun.eastmoney.com/news/{code}.html" if code else "https://kuaixun.eastmoney.com/"

            # 其他字段
            news_item['category'] = self._infer_category(title + ' ' + summary)
            news_item['importance'] = self._calculate_importance(item)
            news_item['sentiment'] = self._judge_sentiment(title + ' ' + summary)

            # 股票关联
            stock_list = item.get('stockList', [])
            news_item['related_stocks'] = stock_list if isinstance(stock_list, list) else []
            news_item['has_stock_mention'] = len(news_item['related_stocks']) > 0

            news_item['comment_count'] = item.get('pinglun_Num', 0)
            news_item['share_count'] = item.get('share', 0)

            return news_item

        except Exception as e:
            print(f"解析单条新闻异常: {e}")
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

    def _calculate_importance(self, item) -> int:
        """计算重要性"""
        score = 5
        reading_num = item.get('reading_num', 0)
        if reading_num > 20000:
            score += 2
        elif reading_num > 10000:
            score += 1
        if item.get('stockList'):
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

    def test_collection(self):
        """测试采集"""
        print("=" * 60)
        print("东方财富快讯采集器测试（修复版）")
        print("=" * 60)
        news_list = self.fetch_news(max_items=20)
        if news_list:
            print(f"✅ 成功采集 {len(news_list)} 条")
            for i, n in enumerate(news_list[:5]):
                print(f"  {i + 1}. {n.get('time')} {n.get('title')[:30]}...")
            return True
        print("❌ 采集失败")
        return False


if __name__ == "__main__":
    collector = EastMoneyCollector()
    collector.test_collection()