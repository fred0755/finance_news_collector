# simple_collector.py
"""
简化的新闻采集器
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json
import os


def test_rss_sources():
    """测试RSS源"""
    test_sources = [
        ("BBC中文财经", "https://www.bbc.com/zhongwen/simp/business/index.xml"),
        ("Reuters中文财经", "https://cn.reuters.com/rssFeed/CNTopGenNews/"),
        ("FT中文网", "https://www.ftchinese.com/rss/news"),
        ("新浪财经国际", "https://finance.sina.com.cn/7x24/rssdomestic.xml"),
        ("华尔街日报中文版", "https://cn.wsj.com/rss/CN.xml"),
        ("网易财经", "https://www.163.com/rss/0101.xml"),
        ("搜狐财经", "https://rss.sohu.com/rss/finance.xml"),
    ]

    print("测试RSS源...")
    working_sources = []

    for name, url in test_sources:
        print(f"\n测试 {name}: {url}")
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                feed = feedparser.parse(url)
                print(f"  条目数: {len(feed.entries)}")

                if feed.entries:
                    working_sources.append((name, url))
                    print(f"  ✓ 可用")

                    # 显示第一条新闻
                    if feed.entries:
                        entry = feed.entries[0]
                        print(f"  示例: {entry.get('title', '无标题')[:50]}...")
                else:
                    print(f"  ✗ 无内容")
            else:
                print(f"  ✗ HTTP错误")

        except Exception as e:
            print(f"  ✗ 错误: {e}")

    return working_sources


def collect_news_from_rss(rss_url: str, source_name: str, max_items: int = 10) -> List[Dict]:
    """从RSS源收集新闻"""
    news_items = []

    try:
        feed = feedparser.parse(rss_url)

        # 只获取最近2天的新闻
        cutoff_date = datetime.now() - timedelta(days=2)

        for entry in feed.entries[:max_items]:
            # 获取发布日期
            pub_date_str = entry.get('published', entry.get('updated', ''))

            # 解析日期
            try:
                import dateutil.parser
                pub_date = dateutil.parser.parse(pub_date_str)
            except:
                pub_date = datetime.now()

            # 只收集最近2天的新闻
            if pub_date >= cutoff_date:
                news_item = {
                    'source': source_name,
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'link': entry.get('link', ''),
                    'publish_date': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'keywords': extract_keywords(entry.get('title', '')),
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                news_items.append(news_item)

    except Exception as e:
        print(f"从 {source_name} 收集新闻失败: {e}")

    return news_items


def extract_keywords(text: str) -> List[str]:
    """提取关键词"""
    if not text:
        return []

    keywords = [
        'A股', '港股', '美股', '科创板', '创业板',
        '证监会', '央行', '美联储',
        'CPI', 'PPI', 'PMI', 'GDP',
        '加息', '降息', '利率',
        '人工智能', '新能源', '半导体', '芯片',
        '财报', '业绩', '盈利',
        '上涨', '下跌', '反弹'
    ]

    found_keywords = []
    for keyword in keywords:
        if keyword in text:
            found_keywords.append(keyword)

    return found_keywords


def analyze_news(news_data: List[Dict]) -> Dict:
    """分析新闻数据"""
    if not news_data:
        return {"error": "没有新闻数据"}

    # 基础统计
    total_news = len(news_data)

    # 按来源统计
    by_source = {}
    for news in news_data:
        source = news['source']
        by_source[source] = by_source.get(source, 0) + 1

    # 提取所有关键词
    all_keywords = []
    for news in news_data:
        all_keywords.extend(news.get('keywords', []))

    # 统计关键词频率
    from collections import Counter
    keyword_counter = Counter(all_keywords)
    top_keywords = dict(keyword_counter.most_common(10))

    return {
        'summary': {
            'total_news': total_news,
            'sources_count': len(by_source),
            'latest_collection': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'by_source': by_source,
        'top_keywords': top_keywords,
        'sample_news': news_data[:5]
    }


def save_results(news_data: List[Dict], analysis_result: Dict):
    """保存结果"""
    # 确保目录存在
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存原始数据
    raw_file = f"data/raw/news_{timestamp}.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    print(f"原始数据保存到: {raw_file}")

    # 保存分析结果
    analysis_file = f"data/reports/analysis_{timestamp}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    print(f"分析结果保存到: {analysis_file}")

    # 生成文本报告
    report_file = f"data/reports/report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("财经新闻分析报告\n")
        f.write(f"生成时间: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"📊 数据概览:\n")
        f.write(f"   新闻总数: {analysis_result['summary']['total_news']} 条\n")
        f.write(f"   来源媒体: {analysis_result['summary']['sources_count']} 家\n\n")

        f.write(f"📰 来源分布:\n")
        for source, count in analysis_result['by_source'].items():
            f.write(f"   {source}: {count} 条\n")
        f.write("\n")

        if analysis_result['top_keywords']:
            f.write(f"🔑 热门关键词:\n")
            for keyword, count in analysis_result['top_keywords'].items():
                f.write(f"   {keyword}: {count} 次\n")
            f.write("\n")

        f.write(f"📋 新闻摘要:\n")
        for i, news in enumerate(analysis_result['sample_news'], 1):
            f.write(f"\n{i}. [{news['source']}] {news['title']}\n")
            if news.get('summary'):
                f.write(f"   摘要: {news['summary'][:100]}...\n")
            if news.get('keywords'):
                f.write(f"   关键词: {', '.join(news['keywords'])}\n")

    print(f"文本报告保存到: {report_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("简化版财经新闻采集系统")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 测试RSS源
    print("\n1. 测试RSS源...")
    working_sources = test_rss_sources()

    if not working_sources:
        print("\n⚠️ 没有可用的RSS源")
        return

    print(f"\n✓ 找到 {len(working_sources)} 个可用的RSS源")

    # 2. 收集新闻
    print("\n2. 收集新闻...")
    all_news = []

    for name, url in working_sources:
        print(f"  从 {name} 收集新闻...")
        news_items = collect_news_from_rss(url, name)
        all_news.extend(news_items)
        print(f"    收集到 {len(news_items)} 条新闻")

    if not all_news:
        print("\n⚠️ 未收集到任何新闻")
        return

    print(f"\n✓ 共收集到 {len(all_news)} 条新闻")

    # 3. 分析新闻
    print("\n3. 分析新闻...")
    analysis_result = analyze_news(all_news)

    # 4. 保存结果
    print("\n4. 保存结果...")
    save_results(all_news, analysis_result)

    # 5. 显示摘要
    print("\n" + "=" * 60)
    print("分析结果摘要")
    print("=" * 60)

    print(f"\n📊 数据概览:")
    print(f"   新闻总数: {analysis_result['summary']['total_news']} 条")
    print(f"   来源媒体: {analysis_result['summary']['sources_count']} 家")

    print(f"\n📰 来源分布:")
    for source, count in analysis_result['by_source'].items():
        print(f"   {source}: {count} 条")

    if analysis_result['top_keywords']:
        print(f"\n🔑 热门关键词:")
        for keyword, count in list(analysis_result['top_keywords'].items())[:5]:
            print(f"   {keyword}: {count} 次")

    print(f"\n📋 新闻示例:")
    for i, news in enumerate(analysis_result['sample_news'][:3], 1):
        print(f"\n{i}. [{news['source']}] {news['title']}")
        if news.get('summary'):
            print(f"   摘要: {news['summary'][:80]}...")

    print("\n" + "=" * 60)
    print("✅ 系统运行成功！")
    print("=" * 60)


if __name__ == "__main__":
    main()