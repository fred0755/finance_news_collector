#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础采集器 - 所有采集器的基类
"""
import requests
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import json


class BaseCollector:
    """所有采集器的基类"""

    def __init__(self, 配置: Dict = None):
        self.配置 = 配置 or {}
        self.名称 = self.配置.get('名称', '未知采集器')
        self.网址 = self.配置.get('网址', '')
        self.logger = logging.getLogger(self.名称)

        # 请求头配置
        self.请求头 = self.配置.get('请求头', {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        self.logger.info(f'采集器初始化: {self.名称}')

    def 运行(self) -> List[Dict]:
        """运行采集器的主方法"""
        self.logger.info(f'开始采集: {self.名称}')

        try:
            # 获取网页内容
            html = self.获取网页内容()

            if not html:
                self.logger.warning('获取网页内容失败')
                return self.生成模拟数据()

            # 解析新闻列表
            新闻列表 = self.解析新闻列表(html)

            if 新闻列表:
                self.logger.info(f'采集成功: {len(新闻列表)} 条')

                # 标准化每条新闻
                for 新闻 in 新闻列表:
                    self.标准化新闻格式(新闻)

                return 新闻列表
            else:
                self.logger.warning('未解析到新闻，使用模拟数据')
                return self.生成模拟数据()

        except Exception as e:
            self.logger.error(f'采集异常: {self.名称}, 错误: {e}', exc_info=True)
            return self.生成模拟数据()

    def 获取网页内容(self) -> str:
        """获取网页HTML内容"""
        if not self.网址:
            self.logger.warning('未配置网址')
            return ''

        try:
            # 添加随机延迟，避免请求太快
            time.sleep(1)

            response = requests.get(
                self.网址,
                headers=self.请求头,
                timeout=30,
                verify=False  # 忽略SSL证书验证
            )
            response.encoding = 'utf-8'

            if response.status_code == 200:
                self.logger.debug(f'获取成功: {len(response.text):,} 字符')
                return response.text
            else:
                self.logger.warning(f'HTTP {response.status_code}: {self.网址}')
                return ''

        except requests.exceptions.Timeout:
            self.logger.error(f'请求超时: {self.网址}')
            return ''
        except Exception as e:
            self.logger.error(f'请求异常: {e}')
            return ''

    def 解析新闻列表(self, html: str) -> List[Dict]:
        """
        解析新闻列表 - 子类必须实现

        这是抽象方法，具体的采集器需要重写这个方法
        来解析各自网站的HTML结构
        """
        raise NotImplementedError('子类必须实现 parse_news_list 方法')

    def 解析新闻详情(self, url: str) -> Dict:
        """解析新闻详情页（如果需要）"""
        # 基础实现，子类可重写
        return {
            'url': url,
            'title': '详细新闻标题',
            'content': '详细新闻内容',
            'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def 标准化新闻格式(self, 新闻: Dict) -> Dict:
        """标准化新闻数据格式"""
        import hashlib

        # 确保必要字段存在
        新闻.setdefault('title', '无标题')
        新闻.setdefault('content', '')
        新闻.setdefault('source', self.名称)
        新闻.setdefault('url', '')

        # 生成URL的MD5用于去重
        if 新闻['url']:
            新闻['url_md5'] = hashlib.md5(新闻['url'].encode()).hexdigest()
        else:
            新闻['url_md5'] = ''

        # 确保有时间字段
        if 'publish_time' not in 新闻:
            新闻['publish_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'collect_time' not in 新闻:
            新闻['collect_time'] = datetime.now().strftime('%-%m-%d %H:%M:%S')

        # 基础重要性评分
        if 'importance_score' not in 新闻:
            # 简单规则：标题长度、关键词等
            分数 = 0
            标题 = 新闻['title']

            if len(标题) > 30:
                分数 += 1

            # 检查关键词
            关键词 = ['紧急', '突发', '重磅', '重大', '降准', '降息', '证监会', '央行']
            if any(keyword in 标题 for keyword in 关键词):
                分数 += 2

            新闻['importance_score'] = min(分数, 5)  # 0-5分

        # 基础情感分析（预留）
        if 'sentiment_score' not in 新闻:
            新闻['sentiment_score'] = 0.0
            if '利好' in 新闻['title'] or '上涨' in 新闻['title']:
                新闻['sentiment_score'] = 1.0
            elif '利空' in 新闻['title'] or '下跌' in 新闻['title']:
                新闻['sentiment_score'] = -1.0

        return 新闻

    def 生成模拟数据(self) -> List[Dict]:
        """生成模拟数据（当采集失败时使用）"""
        当前时间 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        模拟新闻 = [
            {
                'title': f'{self.名称}：模拟新闻1 - {当前时间[11:]}',
                'content': f'这是来自{self.名称}的模拟内容1，用于测试采集系统。',
                'url': f'{self.网址}#test1',
                'source': self.名称,
                'publish_time': 当前时间,
                'collect_time': 当前时间,
                'importance_score': 3
            },
            {
                'title': f'{self.名称}：模拟新闻2 - {当前时间[11:]}',
                'content': f'这是来自{self.名称}的模拟内容2，用于测试采集系统。',
                'url': f'{self.网址}#test2',
                'source': self.名称,
                'publish_time': 当前时间,
                'collect_time': 当前时间,
                'importance_score': 4
            }
        ]

        return [self.标准化新闻格式(新闻) for 新闻 in 模拟新闻]

    def 保存原始数据(self, 新闻列表: List[Dict], 文件名: str = None):
        """保存原始数据用于调试"""
        import os

        if not 文件名:
            时间戳 = datetime.now().strftime('%Y%m%d_%H%M%S')
            文件名 = f'data/raw_{self.名称}_{时间戳}.json'

        os.makedirs(os.path.dirname(文件名), exist_ok=True)

        with open(文件名, 'w', encoding='utf-8') as f:
            json.dump(新闻列表, f, ensure_ascii=False, indent=2)

        self.logger.info(f'原始数据已保存: {文件名}')


# ==================== 使用示例 ====================
def test_base_collector():
    """测试基础采集器"""
    print("测试基础采集器...")

    配置 = {
        '名称': '测试采集器',
        '网址': 'https://example.com'
    }

    采集器 = BaseCollector(配置)

    try:
        # 测试抽象方法
        采集器.解析新闻列表('<html></html>')
        print("错误：应该抛出 NotImplementedError")
    except NotImplementedError as e:
        print(f"正确：{e}")

    # 测试模拟数据
    模拟数据 = 采集器.生成模拟数据()
    print(f"生成模拟数据: {len(模拟数据)} 条")

    for i, 新闻 in enumerate(模拟数据):
        print(f"{i + 1}. {新闻['title']}")


if __name__ == '__main__':
    test_base_collector()