import requests
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class EastMoneyCollector:
    """东方财富快讯采集器（增量采集版）"""

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
                return int(time.time() * 1000000)  # 默认当前时间
        return int(time.time() * 1000000)

    def _save_last_news_id(self, news_id: int):
        """保存最后一次采集的新闻ID"""
        project_root = Path(__file__).parent.parent.parent
        last_id_file = project_root / "data" / "eastmoney_last_id.txt"

        with open(last_id_file, 'w') as f:
            f.write(str(news_id))

    def fetch_news(self, max_items: int = 100) -> Optional[List[Dict]]:
        """
        增量采集新闻
        从 last_news_id 开始，往前采集，直到采集到上次的最后一条
        """
        all_news = []
        current_sort_end = self.last_news_id
        min_sort_end = self.last_news_id
        max_pages = 10  # 最多采集10页，防止死循环

        print(f"🔄 开始增量采集，起始时间戳: {self.last_news_id}")

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
                for item in news_data:
                    news_item = self._parse_single_news(item)
                    if news_item:
                        page_news.append(news_item)

                        # ===== 修复点：确保类型一致 =====
                        item_sort = item.get('realSort', 0)
                        try:
                            # 转换为整数，如果是字符串就转一下
                            if isinstance(item_sort, str):
                                item_sort = int(item_sort)
                            if item_sort and item_sort < min_sort_end:
                                min_sort_end = item_sort
                        except (ValueError, TypeError):
                            print(f"  ⚠️ 无法转换时间戳: {item_sort}")
                            continue
                        # ===== 修复结束 =====

                print(f"  ✅ 本页获取 {len(page_news)} 条")
                all_news.extend(page_news)

                # 如果已经采集到上次的最后一条，停止
                if min_sort_end <= self.last_news_id:
                    print(f"  ✅ 已采集到上次的最后一条，停止")
                    break

                # 准备下一页
                current_sort_end = min_sort_end
                time.sleep(0.5)  # 礼貌性延迟

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
        """解析单条新闻 - 优化版（支持标题新闻）"""
        try:
            unique_str = f"{item.get('title', '')}_{item.get('showTime', '')}_{item.get('code', '')}"
            news_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]

            title_raw = item.get('title', '').strip()
            summary = item.get('summary', '').strip()
            code = item.get('code', '')
            show_time = item.get('showTime', '')
            sort_time = item.get('realSort', 0)  # 用于排序的时间戳

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
                'sort_time': sort_time,  # 保留用于排序
                'raw_data': item
            }

            # 时间字段
            if show_time:
                news_item['time'] = show_time
                news_item['publish_time'] = show_time
            else:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                news_item['time'] = current_time
                news_item['publish_time'] = current_time

            # 来源
            source = item.get('mediaName', item.get('source', ''))
            news_item['source'] = source.strip() if source else '东方财富快讯'

            # URL
            news_item['url'] = f"https://kuaixun.eastmoney.com/news/{code}.html" if code else "https://kuaixun.eastmoney.com/"

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
        """根据内容推断新闻分类"""
        text_lower = text.lower()
        category_keywords = {
            '宏观': ['gdp', 'cpi', 'ppi', '通胀', '通缩', '货币政策', '财政政策', '央行', '利率', '存款准备金'],
            '股市': ['a股', '沪指', '深指', '创业板', '科创板', '涨停', '跌停', '大盘', '指数', '股票', '股价'],
            '债券': ['国债', '地方债', '城投债', '企业债', '可转债', '债券', '收益率'],
            '期货': ['期货', '原油', '黄金', '白银', '铜', '铝', '螺纹钢', '铁矿石'],
            '外汇': ['美元', '人民币', '欧元', '英镑', '日元', '汇率', '外汇'],
            '商品': ['原油', '黄金', '白银', '铜', '大宗商品', '现货'],
            '理财': ['银行理财', '信托', '保险', '基金', '资管', '理财产品'],
            '房地产': ['房价', '房地产', '楼市', '房企', '土地', '拍卖'],
            '公司': ['财报', '业绩', '营收', '净利润', '分红', '回购', 'st', 'ipo'],
            '行业': ['行业', '板块', '概念', '产业链', '产能', '产量'],
            '国际': ['美联储', '欧央行', '加息', '降息', '通胀', '贸易战'],
            '政策': ['政策', '法规', '条例', '监管', '检查', '整治'],
            '科技': ['人工智能', 'ai', '大数据', '云计算', '区块链', '芯片', '半导体'],
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        return '其他'

    def _calculate_importance(self, item) -> int:
        """计算新闻重要性分数（1-10分）"""
        score = 5
        title = item.get('title', '')
        stock_list = item.get('stockList', [])
        comment_count = item.get('pinglun_Num', 0)

        urgent_keywords = ['紧急', '突发', '重磅', '重大', '预警', '警报', '危机', '崩盘', '暴跌', '暴涨']
        for keyword in urgent_keywords:
            if keyword in title:
                score += 2
                break

        if len(stock_list) > 0:
            score += min(len(stock_list) * 0.5, 3)

        if comment_count > 10:
            score += 1
        if comment_count > 50:
            score += 1

        return max(1, min(10, int(score)))

    def _judge_sentiment(self, text: str) -> str:
        """判断情感倾向"""
        text_lower = text.lower()
        bullish_keywords = ['上涨', '看好', '突破', '利好', '增长', '复苏', '扩张', '买入', '推荐', '超预期']
        bearish_keywords = ['下跌', '看空', '跌破', '利空', '下滑', '衰退', '收缩', '卖出', '预警', '不及预期']

        bullish_count = sum(1 for word in bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in bearish_keywords if word in text_lower)

        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'

    def test_collection(self):
        """测试采集功能"""
        print("=" * 60)
        print("东方财富快讯采集器测试（增量版）")
        print("=" * 60)

        news_list = self.fetch_news(max_items=20)

        if news_list:
            print(f"✅ 成功采集到 {len(news_list)} 条新闻!")
            print("-" * 50)

            for i, news in enumerate(news_list[:10], 1):
                time_str = news.get('time', 'N/A')
                title = news.get('title', '无标题')[:40]
                source = news.get('source', 'N/A')
                has_detail = ' 📄' if news.get('full_content') != news.get('title') else ''
                print(f"{i:2d}. [{time_str}] {title}{has_detail}... ({source})")

            if len(news_list) > 10:
                print(f"... 还有 {len(news_list) - 10} 条未显示")
            return True
        else:
            print("❌ 采集失败")
            return False


if __name__ == "__main__":
    collector = EastMoneyCollector()
    collector.test_collection()