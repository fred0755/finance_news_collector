import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import hashlib


class EastMoneyCollector:
    """东方财富快讯采集器（优化版 - 直接在消息中显示内容）"""

    def __init__(self):
        # 真实API地址
        self.base_url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://kuaixun.eastmoney.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        # API参数
        self.base_params = {
            'client': 'web',
            'biz': 'web_724',
            'fastColumn': '102',  # 快讯栏目ID
            'pageSize': 20,
            'sortEnd': int(time.time() * 1000000),
            'req_trace': int(time.time() * 1000),
            '_': int(time.time() * 1000),
            'callback': f'jQuery_{int(time.time() * 1000)}'
        }

    def fetch_news(self, page_size: int = 20) -> Optional[List[Dict]]:
        """
        获取东方财富快讯新闻（优化版）

        Args:
            page_size: 每页数量

        Returns:
            结构化的新闻列表，包含完整内容
        """
        try:
            # 更新参数
            params = self.base_params.copy()
            params['pageSize'] = page_size
            params['sortEnd'] = int(time.time() * 1000000)
            params['_'] = int(time.time() * 1000)
            params['callback'] = f'jQuery_{int(time.time() * 1000)}'

            print(f"正在抓取快讯，每页 {page_size} 条...")

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )

            response.raise_for_status()

            # 处理JSONP响应
            raw_text = response.text
            json_start = raw_text.find('(')
            json_end = raw_text.rfind(')')

            if json_start != -1 and json_end != -1:
                json_str = raw_text[json_start + 1:json_end]
                data = json.loads(json_str)

                # 解析新闻数据
                news_list = self._parse_news_data(data)
                return news_list
            else:
                print(f"响应不是有效的JSONP格式")
                return None

        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"原始响应: {raw_text[:500]}...")
            return None
        except Exception as e:
            print(f"未知错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_news_data(self, data: Dict) -> List[Dict]:
        """
        解析API返回的新闻数据
        """
        news_items = []

        # 根据API结构查找新闻数据
        if isinstance(data, dict) and data.get('code') == "1":
            # 从fastNewsList获取数据
            news_data = data.get('data', {}).get('fastNewsList', [])

            if isinstance(news_data, list):
                print(f"开始解析 {len(news_data)} 条新闻...")

                for i, item in enumerate(news_data):
                    try:
                        # 解析单条新闻
                        news_item = self._parse_single_news(item)
                        if news_item and news_item.get('title'):
                            news_items.append(news_item)

                            # 只显示前3条作为示例
                            if i < 3:
                                print(f"  示例{i + 1}: {news_item['title'][:50]}...")

                    except Exception as e:
                        print(f"解析第{i + 1}条新闻失败: {e}")
                        continue

        return news_items

    def _parse_single_news(self, item) -> Dict:
        """解析单条新闻 - 优化版（包含完整内容）"""
        try:
            # 为新闻生成唯一ID
            unique_str = f"{item.get('title', '')}_{item.get('showTime', '')}_{item.get('code', '')}"
            news_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]

            # 提取关键信息
            title = item.get('title', '').strip()
            summary = item.get('summary', '').strip()
            code = item.get('code', '')
            show_time = item.get('showTime', '')

            # 使用摘要作为内容，如果没有摘要则使用标题
            content = summary if summary else title

            # 基础新闻结构
            news_item = {
                'id': news_id,
                'code': code,
                'title': title,
                'summary': summary,
                'content': content,  # 简短内容
                'full_content': content,  # 完整内容（摘要）
                'raw_data': item  # 保存原始数据
            }

            # 时间字段
            if show_time:
                news_item['time'] = show_time
                news_item['publish_time'] = show_time
            else:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                news_item['time'] = current_time
                news_item['publish_time'] = current_time

            # 来源处理
            source = item.get('mediaName', item.get('source', ''))
            if not source:
                source = '东方财富快讯'
            news_item['source'] = source.strip()

            # URL（虽然可能无法在钉钉中访问，但仍保留）
            news_item[
                'url'] = f"https://kuaixun.eastmoney.com/news/{code}.html" if code else "https://kuaixun.eastmoney.com/"

            # 分类
            news_item['category'] = self._infer_category(item)

            # 重要性评分
            news_item['importance'] = self._calculate_importance(item)

            # 情感分析
            news_item['sentiment'] = self._judge_sentiment(title + summary)

            # 股票关联
            stock_list = item.get('stockList', [])
            if stock_list and isinstance(stock_list, list):
                news_item['related_stocks'] = stock_list
                news_item['has_stock_mention'] = True
            else:
                news_item['related_stocks'] = []
                news_item['has_stock_mention'] = False

            # 互动数据
            news_item['comment_count'] = item.get('pinglun_Num', 0)
            news_item['share_count'] = item.get('share', 0)

            # 清理和验证
            self._clean_news_item(news_item)

            return news_item

        except Exception as e:
            print(f"解析单条新闻异常: {e}")
            import traceback
            traceback.print_exc()
            # 返回最小可用的新闻对象
            return {
                'id': hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
                'title': str(item.get('title', '解析失败'))[:200],
                'content': str(item)[:500],
                'full_content': str(item)[:500],
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': '解析异常',
                'url': '',
                'category': '其他',
                'importance': 5,
                'sentiment': 'neutral'
            }

    def _infer_category(self, item) -> str:
        """根据内容推断新闻分类"""
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()

        # 关键词匹配分类
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

        # 检查每个分类
        text_to_check = f"{title} {summary}"
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    return category

        return '其他'

    def _calculate_importance(self, item) -> int:
        """计算新闻重要性分数（1-10分）"""
        score = 5  # 基础分

        title = item.get('title', '')
        summary = item.get('summary', '')

        # 紧急关键词加分
        urgent_keywords = ['紧急', '突发', '重磅', '重大', '预警', '警报', '危机', '崩盘', '暴跌', '暴涨']
        for keyword in urgent_keywords:
            if keyword in title:
                score += 2
                break

        # 涉及股票数量加分
        stock_list = item.get('stockList', [])
        if len(stock_list) > 0:
            score += min(len(stock_list) * 0.5, 3)

        # 评论数加分
        comment_count = item.get('pinglun_Num', 0)
        if comment_count > 10:
            score += 1
        if comment_count > 50:
            score += 1

        # 确保分数在1-10之间
        return max(1, min(10, int(score)))

    def _judge_sentiment(self, text) -> str:
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

    def _clean_news_item(self, news_item):
        """清理和标准化新闻数据"""
        # 确保标题和内容不为空
        if not news_item.get('title'):
            news_item['title'] = '无标题新闻'

        if not news_item.get('content'):
            news_item['content'] = news_item['title']

        if not news_item.get('full_content'):
            news_item['full_content'] = news_item['content']

        # 截断过长的字段
        max_title_len = 200
        max_content_len = 5000

        if len(news_item['title']) > max_title_len:
            news_item['title'] = news_item['title'][:max_title_len] + '...'

        if len(news_item['content']) > max_content_len:
            news_item['content'] = news_item['content'][:max_content_len] + '...'

        if len(news_item['full_content']) > max_content_len:
            news_item['full_content'] = news_item['full_content'][:max_content_len] + '...'

    def test_collection(self):
        """测试采集功能"""
        print("=" * 60)
        print("东方财富快讯采集器测试")
        print("=" * 60)

        print(f"\n尝试抓取 10 条新闻...")
        news_list = self.fetch_news(page_size=10)

        if news_list:
            print(f"✅ 成功采集到 {len(news_list)} 条新闻!")
            print("-" * 50)

            # 显示所有新闻标题
            for i, news in enumerate(news_list[:5], 1):
                time_str = news.get('time', 'N/A')
                title = news.get('title', '无标题')[:60]
                source = news.get('source', 'N/A')
                print(f"{i:2d}. [{time_str}] {title}... (来源: {source})")

            if len(news_list) > 5:
                print(f"... 还有 {len(news_list) - 5} 条未显示")

            # 验证数据质量
            self._validate_data(news_list)
            return True
        else:
            print("❌ 采集失败")
            return False

    def _validate_data(self, news_list):
        """验证数据质量"""
        print("\n数据质量检查:")
        print("-" * 30)

        total = len(news_list)
        if total == 0:
            print("❌ 没有采集到任何新闻")
            return

        # 统计字段完整性
        fields = ['title', 'content', 'full_content', 'time', 'source']
        stats = {}

        for field in fields:
            count = sum(1 for news in news_list if news.get(field))
            stats[field] = count

        print(f"新闻总数: {total}")
        for field, count in stats.items():
            percentage = (count / total) * 100
            status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
            print(f"{status} {field}: {count}/{total} ({percentage:.1f}%)")

        # 检查内容长度
        avg_content_len = sum(len(news.get('content', '')) for news in news_list) / total
        print(f"平均内容长度: {avg_content_len:.1f} 字符")


# 主函数 - 直接运行测试
if __name__ == "__main__":
    print("东方财富快讯采集器 v3.0")
    print("优化版 - 直接在消息中显示内容")
    print()

    collector = EastMoneyCollector()
    success = collector.test_collection()

    print("\n" + "=" * 60)
    if success:
        print("✅ 采集器测试成功！")
        print("\n🎉 系统特点:")
        print("1. ✅ 直接显示新闻内容，无需点击链接")
        print("2. ✅ 包含重要性评分和情感分析")
        print("3. ✅ 数据完整，适合钉钉推送")
    else:
        print("❌ 采集器测试失败")