"""
东方财富快讯 (kuaixun.eastmoney.com) 采集器 - 动态页面版本
使用 requests-html 处理JavaScript渲染
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from requests_html import HTMLSession, AsyncHTMLSession

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EastMoneyCollector:
    """东方财富快讯采集器（动态页面版本）"""

    LIST_URL = 'https://kuaixun.eastmoney.com/'

    def __init__(self, use_async=False):
        """
        初始化采集器
        :param use_async: 是否使用异步模式（更快但更复杂）
        """
        self.use_async = use_async
        if use_async:
            self.session = AsyncHTMLSession()
        else:
            self.session = HTMLSession()

        # 设置请求头，模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.eastmoney.com/',
        }

    async def fetch_html_async(self, url: str = None) -> Optional[str]:
        """异步获取页面（包含JavaScript渲染）"""
        target_url = url or self.LIST_URL
        try:
            logger.info(f"异步抓取（含JS渲染）: {target_url}")
            response = await self.session.get(target_url, headers=self.headers, timeout=30)
            # 等待JavaScript执行，渲染页面
            await response.html.arender(timeout=30, sleep=2)
            return response.html.html
        except Exception as e:
            logger.error(f"异步抓取失败: {e}")
            return None

    def fetch_html_sync(self, url: str = None) -> Optional[str]:
        """同步获取页面（包含JavaScript渲染）"""
        target_url = url or self.LIST_URL
        try:
            logger.info(f"同步抓取（含JS渲染）: {target_url}")
            response = self.session.get(target_url, headers=self.headers, timeout=30)
            # 等待JavaScript执行，渲染页面
            response.html.render(timeout=30, sleep=2)
            return response.html.html
        except Exception as e:
            logger.error(f"同步抓取失败: {e}")
            return None

    def parse_list(self, html: str) -> List[Dict]:
        """解析渲染后的HTML页面"""
        if not html:
            logger.warning("HTML内容为空，无法解析")
            return []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        news_list = []

        # 使用您之前提供的精确选择器
        news_elements = soup.select('div.news_item')

        if not news_elements:
            # 尝试其他可能的选择器
            news_elements = soup.select('[class*="news"]')
            logger.warning(f"主选择器未找到，尝试备用选择器找到 {len(news_elements)} 个元素")

            # 如果还是找不到，保存HTML用于调试
            if not news_elements:
                with open('rendered_page.html', 'w', encoding='utf-8') as f:
                    f.write(html[:20000])
                logger.error("未找到新闻元素，已将渲染后页面保存到 rendered_page.html")
                return []

        logger.info(f"找到 {len(news_elements)} 个新闻条目")

        for item in news_elements[:20]:  # 限制处理前20条
            try:
                # 1. 提取标题
                title_elem = item.select_one('span.news_detail_text')
                title = title_elem.get_text(strip=True) if title_elem else ''

                # 备用标题提取
                if not title:
                    link_elem = item.select_one('a.news_detail_link')
                    if link_elem:
                        title = link_elem.get_text(strip=True).replace('[点击查看全文]', '').strip()

                if not title:
                    continue  # 跳过无标题的条目

                # 2. 提取链接
                link_elem = item.select_one('a.news_detail_link')
                url = link_elem.get('href') if link_elem else ''

                # 处理链接格式
                if url:
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif url.startswith('/'):
                        url = 'https://finance.eastmoney.com' + url

                # 3. 提取时间
                time_elem = item.select_one('div.news_time')
                publish_time = time_elem.get_text(strip=True) if time_elem else ''

                # 4. 提取相关股票
                stock_elems = item.select('span.stock_name')
                related_stocks = [stock.get_text(strip=True) for stock in stock_elems]

                # 5. 构建新闻条目
                news_item = {
                    'title': title,
                    'url': url,
                    'publish_time': publish_time,
                    'source': '东方财富快讯',
                    'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'related_stocks': related_stocks
                }

                news_list.append(news_item)
                logger.debug(f"解析: {publish_time} | {title[:50]}...")

            except Exception as e:
                logger.warning(f"解析条目时出错: {e}")
                continue

        logger.info(f"成功解析 {len(news_list)} 条新闻")
        return news_list

    async def run_async(self) -> List[Dict]:
        """异步运行采集器"""
        html = await self.fetch_html_async()
        if html:
            return self.parse_list(html)
        return []

    def run_sync(self) -> List[Dict]:
        """同步运行采集器（推荐）"""
        html = self.fetch_html_sync()
        if html:
            return self.parse_list(html)
        return []


def test_collector():
    """测试采集器"""
    print("=== 测试东方财富快讯采集器（动态页面版） ===")

    # 使用同步版本（更简单）
    collector = EastMoneyCollector(use_async=False)
    news = collector.run_sync()

    if news:
        print(f"\n✅ 成功抓取到 {len(news)} 条新闻：")
        for i, item in enumerate(news[:5], 1):
            print(f"{i}. 时间：{item['publish_time']}")
            print(f"   标题：{item['title'][:60]}...")
            print(f"   链接：{item['url'][:80]}..." if item['url'] else "   链接：无")
            if item['related_stocks']:
                print(f"   相关股票：{', '.join(item['related_stocks'])}")
            print(f"   来源：{item['source']}")
            print(f"   采集于：{item['collected_at']}")
            print("-" * 70)
    else:
        print("\n❌ 未能抓取到任何新闻。可能原因：")
        print("   1. 网络问题或超时")
        print("   2. 页面结构已大幅变更")
        print("   3. 网站反爬机制")
        print("\n建议：检查生成的 rendered_page.html 文件查看渲染后页面")


if __name__ == "__main__":
    test_collector()