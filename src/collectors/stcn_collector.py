# collectors/stcn_collector.py - 增强版
from .base_collector import BaseCollector
class EastMoneyCollector(BaseCollector):
from bs4 import BeautifulSoup
import re
from datetime import datetime


class StcnCollector(BaseCollector):
    """证券时报快讯采集器 - 增强版"""

    def 解析新闻列表(self, html: str):
        """解析证券时报快讯页面"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            新闻列表 = []

            # 方法1：尝试常见的列表容器
            容器选择器 = [
                '.list-con', '.news-list', '.article-list',
                '.content-list', 'ul.list', 'div.list'
            ]

            新闻容器 = None
            for 选择器 in 容器选择器:
                容器 = soup.select_one(选择器)
                if 容器:
                    新闻容器 = 容器
                    self.logger.info(f"找到容器: {选择器}")
                    break

            # 如果没找到特定容器，尝试其他方法
            if not 新闻容器:
                # 查找包含多个链接的容器
                all_divs = soup.find_all('div')
                for div in all_divs:
                    links = div.find_all('a')
                    if len(links) >= 5:  # 包含至少5个链接
                        link_texts = [link.get_text(strip=True) for link in links]
                        # 检查是否包含新闻关键词
                        if any(len(text) > 15 for text in link_texts):
                            新闻容器 = div
                            self.logger.info("通过链接数量找到容器")
                            break

            if 新闻容器:
                # 解析容器内的项目
                项目 = 新闻容器.find_all(['li', 'div', 'article'])
                if not 项目:
                    项目 = 新闻容器.find_all('a')  # 如果没有项目标签，直接找链接

                for 项 in 项目[:30]:
                    news = self.解析STCN新闻项(项)
                    if news:
                        新闻列表.append(news)

            # 方法2：直接搜索所有可能的新链接
            if len(新闻列表) < 3:
                self.logger.info("直接搜索所有链接")
                all_links = soup.find_all('a', href=True)
                for link in all_links[:50]:
                    text = link.get_text(strip=True)
                    if 15 <= len(text) <= 200:
                        # 检查是否是新闻标题
                        if self.是新闻标题(text):
                            href = link['href']
                            if not href.startswith('http'):
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = 'https://www.stcn.com' + href

                            # 尝试找时间
                            time_text = ''
                            parent = link.parent
                            for _ in range(3):
                                if parent:
                                    # 查找时间
                                    time_elem = parent.find(['span', 'time', 'em'],
                                                            text=re.compile(r'\d{2}:\d{2}:\d{2}|\d{2}:\d{2}'))
                                    if time_elem:
                                        time_text = time_elem.get_text(strip=True)
                                        break
                                    parent = parent.parent

                            if not time_text:
                                time_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            新闻列表.append({
                                'title': text,
                                'url': href,
                                'publish_time': time_text,
                                'content': '',
                                'source': '证券时报'
                            })

            self.logger.info(f"解析到 {len(新闻列表)} 条新闻")

            if not 新闻列表:
                self.logger.warning("未解析到新闻，使用模拟数据")
                return self.生成模拟数据()

            # 去重
            去重后 = []
            已出现标题 = set()
            for 新闻 in 新闻列表:
                标题 = 新闻['title']
                标准化标题 = re.sub(r'\s+', ' ', 标题).strip()
                if 标准化标题 not in 已出现标题:
                    已出现标题.add(标准化标题)
                    去重后.append(新闻)

            return 去重后[:15]

        except Exception as e:
            self.logger.error(f'解析页面失败: {e}', exc_info=True)
            return self.生成模拟数据()

    def 解析STCN新闻项(self, 项):
        """解析证券时报的单个新闻项"""
        try:
            # 找标题链接
            标题链接 = 项.find('a')
            if not 标题链接:
                return None

            标题 = 标题链接.get_text(strip=True)
            if len(标题) < 10:
                return None

            # 过滤导航链接
            if any(word in 标题 for word in ['首页', '更多>>', '下一页', '上一页', '返回']):
                return None

            链接 = 标题链接.get('href', '')
            if not 链接.startswith('http'):
                if 链接.startswith('//'):
                    链接 = 'https:' + 链接
                elif 链接.startswith('/'):
                    链接 = 'https://www.stcn.com' + 链接

            # 找时间
            时间 = ''
            时间元素 = 项.find('span', class_=re.compile(r'time|date|pub'))
            if not 时间元素:
                时间元素 = 项.find('em') or 项.find('time')

            if 时间元素:
                时间 = 时间元素.get_text(strip=True)

            if not 时间:
                时间 = datetime.now().strftime('%H:%M:%S')

            # 处理时间格式
            if len(时间) < 6 and ':' in 时间:
                时间 = datetime.now().strftime('%Y-%m-%d ') + 时间

            # 找内容摘要
            内容 = ''
            内容元素 = 项.find('p', class_=re.compile(r'content|summary|text|desc'))
            if not 内容元素:
                内容元素 = 项.find('div', class_=re.compile(r'content|summary|text|desc'))

            if 内容元素:
                内容 = 内容元素.get_text(strip=True)

            return {
                'title': 标题,
                'url': 链接,
                'publish_time': 时间,
                'content': 内容,
                'source': '证券时报'
            }

        except Exception as e:
            self.logger.debug(f'解析新闻项失败: {e}')
            return None

    def 是新闻标题(self, text):
        """判断文本是否是新闻标题"""
        # 长度检查
        if len(text) < 15 or len(text) > 200:
            return False

        # 包含新闻关键词
        news_keywords = ['快讯', '最新', '股市', '证券', '财经', '银行', '央行', 'A股', '港股', '美股']
        if any(keyword in text for keyword in news_keywords):
            return True

        # 包含标点符号（新闻标题特征）
        if '：' in text or ':' in text or '——' in text or '--' in text:
            return True

        # 包含数字和百分比
        if re.search(r'\d+%|\d+\.\d+%', text):
            return True

        return False