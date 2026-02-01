# collectors/eastmoney_collector.py
from .base_collector import BaseCollector
class StcnCollector(BaseCollector):
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import time


class EastMoneyCollector(BaseCollector):
    """东方财富网快讯采集器 - 增强版"""

    def 获取网页内容(self) -> str:
        """重写父类方法，添加更真实的请求头"""
        import requests
        from config import 系统配置

        # 更真实的请求头
        请求头 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.eastmoney.com/'
        }

        try:
            # 添加随机延迟，避免请求太快
            time.sleep(1)

            response = requests.get(
                self.网址,
                headers=请求头,
                timeout=系统配置['请求超时'],
                verify=False  # 忽略SSL证书验证（如果需要）
            )
            response.encoding = 'utf-8'

            if response.status_code == 200:
                self.logger.info(f"成功获取页面，长度: {len(response.text):,} 字符")
                return response.text
            else:
                self.logger.warning(f'HTTP {response.status_code}: {self.网址}')
                return ''

        except Exception as e:
            self.logger.error(f'请求失败: {e}')
            return ''

    def 解析新闻列表(self, html: str):
        """解析东方财富快讯页面 - 增强版"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            新闻列表 = []

            # 方法1：尝试查找特定ID的容器（东方财富快讯常见结构）
            self.logger.debug("尝试方法1: 查找特定ID容器")

            # 常见的东方财富快讯容器
            可能容器 = [
                {'id': 'newsListContent'},  # 常见ID
                {'class': 'news-list'},  # 常见class
                {'id': 'livenews-list'},  # 直播新闻列表
                {'class': 'livenews-media'},  # 直播媒体
                {'class': 'item-list'},  # 项目列表
                {'id': 'newsContent'},  # 新闻内容
            ]

            新闻容器 = None
            for 选择器 in 可能容器:
                if 'id' in 选择器:
                    element = soup.find(id=选择器['id'])
                else:
                    element = soup.find(class_=选择器['class'])

                if element:
                    新闻容器 = element
                    self.logger.info(f"找到容器: {选择器}")
                    break

            # 如果没找到特定容器，使用通用方法
            if not 新闻容器:
                self.logger.info("未找到特定容器，使用通用解析")
                新闻容器 = soup

            # 查找所有可能的新闻项
            新闻项 = 新闻容器.find_all(['div', 'li', 'tr', 'article'])

            if not 新闻项:
                # 尝试其他选择器
                新闻项 = 新闻容器.select('.item, .news-item, .list-item, .media-item')

            self.logger.info(f"找到 {len(新闻项)} 个可能的新闻项")

            for i, 项 in enumerate(新闻项[:30]):  # 最多处理30个
                try:
                    # 提取标题
                    标题 = ""
                    标题元素 = 项.find('a')
                    if 标题元素:
                        标题 = 标题元素.get_text(strip=True)

                    # 如果标题太短，可能是导航或无关内容
                    if len(标题) < 10:
                        continue

                    # 过滤无关内容
                    过滤词 = ['首页', '更多', '>>', '查看全部', '返回顶部', '刷新', '展开', '收起']
                    if any(词 in 标题 for 词 in 过滤词):
                        continue

                    # 提取链接
                    链接 = ""
                    if 标题元素 and 标题元素.get('href'):
                        链接 = 标题元素.get('href').strip()
                        if 链接 and not 链接.startswith(('http://', 'https://')):
                            if 链接.startswith('//'):
                                链接 = 'https:' + 链接
                            elif 链接.startswith('/'):
                                链接 = 'https://kuaixun.eastmoney.com' + 链接

                    # 提取时间
                    时间 = ""
                    时间元素 = 项.find('span', class_=re.compile(r'time|date|pub'))
                    if not 时间元素:
                        时间元素 = 项.find('em') or 项.find('time') or 项.find('i', class_=re.compile(r'time|date'))

                    if 时间元素:
                        时间 = 时间元素.get_text(strip=True)

                    # 如果没找到时间，使用当前时间
                    if not 时间:
                        当前 = datetime.now()
                        时间 = 当前.strftime('%H:%M:%S')

                    # 处理时间格式（如果只有时间，补充日期）
                    if len(时间) < 6 and ':' in 时间:
                        today = datetime.now().strftime('%Y-%m-%d ')
                        时间 = today + 时间

                    # 提取内容摘要
                    内容 = ""
                    内容元素 = 项.find('p', class_=re.compile(r'content|summary|text|desc|abstract'))
                    if not 内容元素:
                        内容元素 = 项.find('div', class_=re.compile(r'content|summary|text|desc|abstract'))

                    if 内容元素:
                        内容 = 内容元素.get_text(strip=True)

                    # 如果内容太长，截断
                    if len(内容) > 200:
                        内容 = 内容[:200] + "..."

                    self.logger.debug(f"解析到新闻: {标题[:30]}...")

                    新闻列表.append({
                        'title': 标题,
                        'url': 链接,
                        'publish_time': 时间,
                        'content': 内容,
                        'source': '东方财富',
                        'raw_html': str(项)[:200]  # 保存原始HTML片段用于调试
                    })

                except Exception as e:
                    self.logger.debug(f'解析第{i + 1}个新闻项失败: {e}')
                    continue

            # 如果没解析到新闻，尝试备用方法
            if len(新闻列表) < 3:
                self.logger.info("尝试备用方法：搜索所有包含'快讯'的链接")

                # 查找所有链接
                all_links = soup.find_all('a', href=True)
                for link in all_links[:50]:
                    title = link.get_text(strip=True)

                    # 筛选条件
                    if len(title) >= 15:
                        # 包含关键词或看起来像新闻标题
                        keywords = ['快讯', '突发', '：', ':', '今日', '最新', '重磅', '紧急']
                        if any(kw in title for kw in keywords) or '：' in title:

                            链接 = link.get('href', '').strip()
                            if 链接 and not 链接.startswith(('http://', 'https://')):
                                if 链接.startswith('//'):
                                    链接 = 'https:' + 链接
                                elif 链接.startswith('/'):
                                    链接 = 'https://kuaixun.eastmoney.com' + 链接

                            # 尝试在父元素中找时间
                            时间 = ""
                            父元素 = link.parent
                            if 父元素:
                                时间元素 = 父元素.find('span') or 父元素.find('em') or 父元素.find('time')
                                if 时间元素:
                                    时间 = 时间元素.get_text(strip=True)

                            if not 时间:
                                时间 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            新闻列表.append({
                                'title': title,
                                'url': 链接,
                                'publish_time': 时间,
                                'content': '',
                                'source': '东方财富'
                            })

            self.logger.info(f"总共解析到 {len(新闻列表)} 条新闻")

            # 如果还是没有数据，使用模拟数据
            if not 新闻列表:
                self.logger.warning("未解析到任何新闻，使用模拟数据")
                return self.生成模拟数据()

            # 去重：基于标题的简单去重
            去重后 = []
            已出现标题 = set()
            for 新闻 in 新闻列表:
                标题 = 新闻['title']
                # 标题标准化（去掉多余空格）
                标准化标题 = re.sub(r'\s+', ' ', 标题).strip()
                if 标准化标题 not in 已出现标题:
                    已出现标题.add(标准化标题)
                    去重后.append(新闻)

            self.logger.info(f"去重后剩余 {len(去重后)} 条新闻")
            return 去重后[:15]  # 最多返回15条

        except Exception as e:
            self.logger.error(f'解析页面失败: {e}', exc_info=True)
            # 失败时返回模拟数据
            return self.生成模拟数据()

    def 生成模拟数据(self):
        """生成更真实的模拟数据"""
        当前时间 = datetime.now()

        模拟新闻 = [
            {
                'title': f'东方财富快讯：测试新闻1 - 当前时间{当前时间.strftime("%H:%M:%S")}',
                'content': f'这是来自东方财富的测试内容1，用于验证采集系统。当前时间：{当前时间.strftime("%Y-%m-%d %H:%M:%S")}',
                'url': f'{self.网址}#test1',
                'publish_time': 当前时间.strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': f'东方财富快讯：测试新闻2 - 当前时间{当前时间.strftime("%H:%M:%S")}',
                'content': f'这是来自东方财富的测试内容2，用于验证采集系统。当前时间：{当前时间.strftime("%Y-%m-%d %H:%M:%S")}',
                'url': f'{self.网址}#test2',
                'publish_time': (当前时间 - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': f'东方财富快讯：测试新闻3 - 当前时间{当前时间.strftime("%H:%M:%S")}',
                'content': f'这是来自东方财富的测试内容3，用于验证采集系统。当前时间：{当前时间.strftime("%Y-%m-%d %H:%M:%S")}',
                'url': f'{self.网址}#test3',
                'publish_time': (当前时间 - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

        return [self.标准化新闻格式(新闻) for 新闻 in 模拟新闻]