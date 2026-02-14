#!/usr/bin/env python
"""
标签管理器本地测试脚本
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent
project_root = src_dir.parent
sys.path.insert(0, str(src_dir))

from tags.tag_manager import TagManager


def load_sample_news():
    """加载示例新闻用于测试"""
    sample_path = project_root / "data" / "latest.json"
    if not sample_path.exists():
        print(f"❌ 找不到示例新闻: {sample_path}")
        return None

    with open(sample_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_single_news(tag_manager, news_item):
    """测试单条新闻"""
    print("\n" + "=" * 60)
    print(f"📰 测试新闻: {news_item.get('title', '无标题')}")
    print("=" * 60)

    # 添加标签
    tagged = tag_manager.add_to_news(news_item)

    # 显示匹配结果
    tags = tagged.get('tags', {})

    print(f"\n✅ 匹配到的行业:")
    for ind in tags.get('industries', []):
        print(f"  - {ind['level1']} > {ind['level2']} > {ind['name']} (匹配词: {ind['matched_keyword']})")

    print(f"\n✅ 匹配到的概念:")
    for con in tags.get('concepts', []):
        print(f"  - {con['name']} (匹配词: {con['matched_keyword']})")

    return tagged


def test_batch(tag_manager, news_list, limit=10):
    """批量测试"""
    print("\n" + "=" * 60)
    print(f"📊 批量测试前 {limit} 条新闻")
    print("=" * 60)

    stats = {
        'total': 0,
        'with_industry': 0,
        'with_concept': 0,
        'industry_count': 0,
        'concept_count': 0
    }

    for i, item in enumerate(news_list[:limit]):
        tagged = tag_manager.add_to_news(item)
        tags = tagged.get('tags', {})

        stats['total'] += 1
        if tags.get('industries'):
            stats['with_industry'] += 1
            stats['industry_count'] += len(tags['industries'])
        if tags.get('concepts'):
            stats['with_concept'] += 1
            stats['concept_count'] += len(tags['concepts'])

        # 显示简略信息
        title = item.get('title', '')[:30] + "..."
        ind_count = len(tags.get('industries', []))
        con_count = len(tags.get('concepts', []))
        print(f"{i + 1:2d}. {title:35} 🏭 {ind_count} 📌 {con_count}")

    # 显示统计
    print("\n📊 统计信息:")
    print(f"  总新闻数: {stats['total']}")
    print(f"  有行业标签: {stats['with_industry']} ({stats['with_industry'] / stats['total'] * 100:.1f}%)")
    print(f"  有概念标签: {stats['with_concept']} ({stats['with_concept'] / stats['total'] * 100:.1f}%)")
    print(f"  平均行业数: {stats['industry_count'] / stats['total']:.2f}")
    print(f"  平均概念数: {stats['concept_count'] / stats['total']:.2f}")


def main():
    print("=" * 60)
    print("🚀 标签管理器本地测试")
    print("=" * 60)

    # 初始化标签管理器
    tag_manager = TagManager()

    # 显示标签库统计
    stats = tag_manager.get_stats()
    print(f"\n📚 标签库信息:")
    print(f"  版本: {stats['version']}")
    print(f"  最后更新: {stats['last_update']}")
    print(f"  行业数: {stats['industries']}")
    print(f"  概念数: {stats['concepts']}")
    print(f"  行业关键词: {stats['industry_keywords']}")
    print(f"  概念关键词: {stats['concept_keywords']}")

    # 加载示例新闻
    news_list = load_sample_news()
    if not news_list:
        return

    print(f"\n📰 加载了 {len(news_list)} 条新闻")

    # 测试单条新闻
    if len(news_list) > 0:
        test_single_news(tag_manager, news_list[0])

    # 批量测试
    test_batch(tag_manager, news_list, limit=10)

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()