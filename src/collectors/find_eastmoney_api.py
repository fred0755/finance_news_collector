"""
查找东方财富快讯的API接口
"""
import requests
import json
import re
from datetime import datetime


def find_eastmoney_apis():
    """查找可能的API接口"""
    print("=== 开始查找东方财富快讯API接口 ===\n")

    # 首先获取主页面，查找可能的API线索
    main_url = 'https://kuaixun.eastmoney.com/'

    try:
        print(f"1. 获取主页面: {main_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(main_url, headers=headers, timeout=10)

        if response.status_code == 200:
            html = response.text

            # 方法1：在HTML中搜索可能的API路径
            print("2. 在HTML中搜索API路径...")
            api_patterns = [
                r'api[^"\']*\.(?:json|js|ajax)',
                r'list[^"\']*\.(?:json|js|ajax)',
                r'news[^"\']*\.(?:json|js|ajax)',
                r'data[^"\']*\.(?:json|js|ajax)',
                r'getNewsList|getList|newsList',
            ]

            found_apis = set()
            for pattern in api_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if len(match) < 50:  # 避免匹配到太长的乱码
                        found_apis.add(match)

            if found_apis:
                print(f"   找到 {len(found_apis)} 个可能的API线索:")
                for api in sorted(found_apis)[:10]:  # 只显示前10个
                    print(f"   - {api}")
            else:
                print("   未在HTML中找到明显的API线索")

            # 方法2：直接测试一些已知的财经网站API模式
            print("\n3. 测试常见API模式...")

            # 东方财富常见的API模式
            test_patterns = [
                # 模式1: 带时间戳的API
                f'https://newsapi.eastmoney.com/kuaixun/v1/getlist?size=20&_={int(datetime.now().timestamp() * 1000)}',
                'https://kuaixun.eastmoney.com/apiapp/newslist',
                'https://api.eastmoney.com/kuaixun/list',
                'https://data.eastmoney.com/kuaixun/newslist',

                # 模式2: 带参数的API
                'https://newsapi.eastmoney.com/kuaixun/v1/getlist?size=50',
                'https://kuaixun.eastmoney.com/api/news/list?page=1',

                # 模式3: JSONP格式（常见于财经网站）
                'https://datainterface.eastmoney.com/EM_DataCenter/JS.aspx?type=KX',
                'https://datacenter.eastmoney.com/securities/api/data/get?type=RPT_KX_NEWS',
            ]

            successful_apis = []
            for api_url in test_patterns:
                try:
                    print(f"   测试: {api_url[:60]}...")
                    resp = requests.get(api_url, headers=headers, timeout=8)

                    if resp.status_code == 200:
                        content_type = resp.headers.get('Content-Type', '')
                        content = resp.text[:500]  # 只取前500字符

                        # 判断是否是有效数据
                        is_json = 'json' in content_type or content.strip().startswith(('{', '[', '('))
                        has_news_data = any(keyword in content.lower() for keyword in ['title', 'news', '时间', '内容'])

                        if is_json or has_news_data:
                            print(f"   ✅ 发现可用接口!")
                            print(f"      状态码: {resp.status_code}")
                            print(f"      类型: {content_type}")
                            print(f"      预览: {content[:200]}...")
                            print()
                            successful_apis.append({
                                'url': api_url,
                                'type': content_type,
                                'preview': content[:200]
                            })
                    else:
                        print(f"   ❌ 状态码: {resp.status_code}")

                except Exception as e:
                    print(f"   ⚠️  请求失败: {str(e)[:50]}")

            # 显示结果汇总
            if successful_apis:
                print(f"\n🎉 共找到 {len(successful_apis)} 个可用API接口:")
                for i, api in enumerate(successful_apis, 1):
                    print(f"{i}. {api['url']}")
                    print(f"   预览: {api['preview']}")
                    print()

                # 保存结果到文件
                with open('found_apis.json', 'w', encoding='utf-8') as f:
                    json.dump(successful_apis, f, ensure_ascii=False, indent=2)
                print("   结果已保存到: found_apis.json")

                return successful_apis
            else:
                print("\n❌ 未找到可用的API接口")
                print("\n备用方案：")
                print("1. 使用浏览器开发者工具分析网络请求（F12 → 网络选项卡）")
                print("2. 查找实际加载新闻的XHR请求")
                print("3. 手动打开 https://kuaixun.eastmoney.com/ 按F12查看")

        else:
            print(f"主页面请求失败: {response.status_code}")

    except Exception as e:
        print(f"查找过程中出错: {e}")
        import traceback
        traceback.print_exc()

    return []


def analyze_browser_network():
    """指导如何用浏览器开发者工具分析API"""
    print("\n" + "=" * 60)
    print("手动分析API的步骤:")
    print("1. 打开Chrome/Edge浏览器")
    print("2. 访问: https://kuaixun.eastmoney.com/")
    print("3. 按 F12 打开开发者工具")
    print("4. 切换到 '网络' (Network) 选项卡")
    print("5. 刷新页面 (F5)")
    print("6. 在筛选器中输入 'api' 或 'news'")
    print("7. 查看返回JSON数据的请求")
    print("8. 右键点击该请求 → 复制 → 复制为cURL")
    print("9. 将复制的URL发给我分析")
    print("=" * 60)


if __name__ == "__main__":
    apis = find_eastmoney_apis()
    if not apis:
        analyze_browser_network()