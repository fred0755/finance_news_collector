"""
深入探索东方财富数据中心API
"""
import requests
import json
import time


def explore_api():
    print("=== 探索东方财富数据中心API参数 ===\n")

    base_url = "https://datacenter.eastmoney.com/securities/api/data/get"

    # 测试不同的参数组合
    test_cases = [
        # 基础参数测试
        {"type": "RPT_KX_NEWS", "sty": "APP_KX_NEWS"},
        {"type": "RPT_KX_NEWS", "sty": "APP_KX_NEWS", "ps": 20, "p": 1},
        {"type": "RPT_KX_NEWS", "sty": "APP_KX_NEWS", "ps": 50, "p": 1, "sr": -1, "st": "showtime"},
        {"type": "RPT_KX_NEWS", "sty": "APP_KX_NEWS", "ps": 10, "p": 1, "filter": "(type=\"7x24\")"},

        # 尝试其他可能的type
        {"type": "RPT_KUAIXUN_NEWS"},
        {"type": "RPT_NEWS_KUAIXUN"},
        {"type": "KX_NEWS"},

        # 带时间范围的查询
        {"type": "RPT_KX_NEWS", "sty": "APP_KX_NEWS", "ps": 20, "p": 1,
         "filter": f"(showtime>='2026-02-01')"},
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://kuaixun.eastmoney.com/',
        'Origin': 'https://kuaixun.eastmoney.com'
    }

    successful_responses = []

    for i, params in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"  参数: {params}")

        try:
            response = requests.get(
                base_url,
                params=params,
                headers=headers,
                timeout=10
            )

            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()

                    # 分析响应结构
                    print(f"  success: {data.get('success')}")
                    print(f"  code: {data.get('code')}")
                    print(f"  message: {data.get('message', '')[:50]}...")

                    if data.get('success') and data.get('result'):
                        result = data['result']
                        print(f"  ✅ 找到数据!")
                        print(
                            f"    数据条数: {len(result.get('data', [])) if isinstance(result.get('data'), list) else 'N/A'}")
                        print(f"    总条数: {result.get('total', 'N/A')}")

                        # 保存成功的结果
                        successful_responses.append({
                            'params': params,
                            'data_preview': str(data)[:300]
                        })

                        # 如果有数据，显示样本
                        if 'data' in result and isinstance(result['data'], list) and result['data']:
                            sample = result['data'][0]
                            print(f"    数据样本: {str(sample)[:200]}...")

                    elif data.get('message'):
                        print(f"  ⚠️  消息: {data.get('message')}")

                except json.JSONDecodeError:
                    print(f"  ❌ 响应不是JSON格式")
                    print(f"    响应预览: {response.text[:200]}...")
            else:
                print(f"  ❌ HTTP错误")

            print("-" * 60)
            time.sleep(1)  # 避免请求过快

        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            print("-" * 60)

    # 总结结果
    if successful_responses:
        print(f"\n🎉 共找到 {len(successful_responses)} 个有效参数组合:")
        for i, resp in enumerate(successful_responses, 1):
            print(f"{i}. 参数: {resp['params']}")
            print(f"   预览: {resp['data_preview'][:150]}...")
            print()

        # 保存详细结果
        with open('api_success.json', 'w', encoding='utf-8') as f:
            json.dump(successful_responses, f, ensure_ascii=False, indent=2)
        print("详细结果已保存到: api_success.json")
    else:
        print("\n❌ 未找到返回有效数据的参数组合")
        print("\n备用方案：通过浏览器分析网络请求")
        print("1. 打开 https://kuaixun.eastmoney.com/")
        print("2. 按F12 → 网络选项卡")
        print("3. 查找包含 'data/get' 或 'RPT_' 的请求")
        print("4. 复制完整的URL（包含所有参数）")


def manual_analysis_guide():
    """手动分析指南"""
    print("\n" + "=" * 70)
    print("手动分析步骤（最可靠的方法）：")
    print("1. 打开Chrome/Edge，访问 https://kuaixun.eastmoney.com/")
    print("2. 按 F12 打开开发者工具")
    print("3. 切换到 '网络' (Network) 选项卡")
    print("4. 按 F5 刷新页面")
    print("5. 在筛选器输入: datacenter")
    print("6. 找到类似这样的请求:")
    print("   https://datacenter.eastmoney.com/securities/api/data/get?...")
    print("7. 点击该请求，查看 '负载' (Payload) 或 '参数' (Params)")
    print("8. 复制完整的URL（包含所有参数）发给我")
    print("=" * 70)


if __name__ == "__main__":
    explore_api()
    manual_analysis_guide()