import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TagManager:
    """标签管理器：加载标签库，为新闻匹配行业和概念"""

    def __init__(self, tags_path: str = None):
        """初始化标签管理器"""
        if tags_path is None:
            # 默认路径：项目根目录/data/tags.json
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            tags_path = project_root / "data" / "tags.json"

        self.tags_path = tags_path
        self.tags = self.load_tags()
        self.build_indexes()

    def load_tags(self) -> Dict:
        """加载标签库JSON文件"""
        if not os.path.exists(self.tags_path):
            print(f"⚠️ 标签文件不存在: {self.tags_path}")
            return {"industries": {}, "concepts": []}

        try:
            with open(self.tags_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载标签文件失败: {e}")
            return {"industries": {}, "concepts": []}

    def build_indexes(self):
        """构建快速查找索引"""
        self.industry_keywords = {}
        self.concept_keywords = {}

        # 构建行业关键词索引
        for level1 in self.tags.get('industries', {}).get('level1', []):
            for level2 in level1.get('level2', []):
                for level3 in level2.get('level3', []):
                    for keyword in level3.get('keywords', []):
                        self.industry_keywords[keyword] = {
                            'id': level3['id'],
                            'name': level3['name'],
                            'level1': level1['name'],
                            'level2': level2['name']
                        }

        # 构建概念关键词索引
        for concept in self.tags.get('concepts', []):
            for keyword in concept.get('keywords', []):
                self.concept_keywords[keyword] = {
                    'id': concept['id'],
                    'name': concept['name']
                }

        print(
            f"✅ 标签索引构建完成: {len(self.industry_keywords)}个行业关键词, {len(self.concept_keywords)}个概念关键词")

    def match_news(self, title: str, summary: str = "") -> Dict:
        """为新闻匹配行业和概念"""
        # 合并标题和摘要
        text = title + " " + (summary or "")
        text_lower = text.lower()

        matched_industries = []
        matched_concepts = []

        # 匹配行业（三级）
        for keyword, info in self.industry_keywords.items():
            if keyword in text:
                matched_industries.append({
                    'id': info['id'],
                    'name': info['name'],
                    'level1': info['level1'],
                    'level2': info['level2'],
                    'matched_keyword': keyword
                })

        # 匹配概念
        for keyword, info in self.concept_keywords.items():
            if keyword in text:
                matched_concepts.append({
                    'id': info['id'],
                    'name': info['name'],
                    'matched_keyword': keyword
                })

        # 去重（基于ID）
        unique_industries = {item['id']: item for item in matched_industries}.values()
        unique_concepts = {item['id']: item for item in matched_concepts}.values()

        return {
            'industries': list(unique_industries),
            'concepts': list(unique_concepts),
            'industry_ids': [item['id'] for item in unique_industries],
            'concept_ids': [item['id'] for item in unique_concepts]
        }

    def add_to_news(self, news_item: Dict) -> Dict:
        """为单条新闻添加标签"""
        title = news_item.get('title', '')
        summary = news_item.get('summary', '')

        tags = self.match_news(title, summary)

        # 添加标签到新闻对象
        news_item['tags'] = {
            'industries': tags['industries'],
            'concepts': tags['concepts'],
            'industry_ids': tags['industry_ids'],
            'concept_ids': tags['concept_ids']
        }

        return news_item

    def add_to_news_list(self, news_list: List[Dict]) -> List[Dict]:
        """为新闻列表批量添加标签"""
        tagged_news = []
        for item in news_list:
            tagged_news.append(self.add_to_news(item))
        return tagged_news

    def get_stats(self) -> Dict:
        """获取标签库统计信息"""
        return {
            'version': self.tags.get('version', 'unknown'),
            'last_update': self.tags.get('last_update', 'unknown'),
            'industry_keywords': len(self.industry_keywords),
            'concept_keywords': len(self.concept_keywords),
            'industries': len(set(info['id'] for info in self.industry_keywords.values())),
            'concepts': len(self.tags.get('concepts', []))
        }