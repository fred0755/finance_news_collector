import requests
import json
import time


def try_api(url, name):
    """尝试请求一个API并打印结果"""
    print(f"\n=== 尝试: {name} ===")
    print(f"URL: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://kuaixun.eastmoney.com/'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            # 尝试解析JSON
            try:
                data = response.json()
                print(f"响应类型: {type(data)}")
                print(f"响应键名: {list(data.keys()) if isinstance(data, dict) else '非字典'}")
                # 简单打印前100个字符
                print(f"响应预览:\n{json.dumps(data, ensure_ascii=False)[:200]}...")
            except json.JSONDecodeError:
                print("响应不是有效的JSON，可能是JSONP")
                print(f"文本预览:\n{response.text[:200]}...")
        else:
            print(f"请求失败: {response.status_code}")

    except Exception as e:
        print(f"请求异常: {e}")

    return response


def main():
    """主函数：尝试多个可能的API端点"""
    # 基础URL
    base_urls = [
        "https://push2.eastmoney.com",
        "https://datacenter.eastmoney.com",
        "https://newsapi.eastmoney.com"
    ]

    # 可能的路径模式（基于我们看到的 pattern）
    paths = [
        "/api/qt/clist/get",  # 我们已经看到的股票列表接口模式
        "/api/data/v1/get",  # 常见的数据接口模式
        "/api/news/getFastNewsList",  # 最有可能的快讯接口
        "/securities/api/data/get",  # 数据中心常见路径
        "/api/news/list",  # 简单直接的新闻列表
    ]

    # 常见的查询参数（东方财富风格）
    common_params = {
        "pn": 1,  # page number
        "pz": 20,  # page size
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",  # 示例token
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23",  # 市场筛选示例
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
        "_": int(time.time() * 1000)  # 时间戳
    }

    print("开始探索东方财富快讯API...")
    print("=" * 60)

    successful_responses = []

    # 尝试不同的组合
    for base in base_urls:
        for path in paths:
            # 构建完整URL
            if "?" in path:
                url = f"{base}{path}"
            else:
                # 添加参数
                param_str = "&".join([f"{k}={v}" for k, v in common_params.items()])
                url = f"{base}{path}?{param_str}"

            response = try_api(url, f"{base}{path}")

            if response.status_code == 200:
                successful_responses.append((url, response))

    print("\n" + "=" * 60)
    print("探索完成！")

    if successful_responses:
        print(f"找到 {len(successful_responses)} 个返回200的接口:")
        for url, resp in successful_responses:
            print(f"  - {url}")

        # 检查哪个可能包含新闻
        print("\n分析最有可能的新闻接口...")
        for url, resp in successful_responses:
            if "news" in url.lower() or "fast" in url.lower():
                print(f"\n⚠️ 可能找到新闻接口: {url}")
                try:
                    data = resp.json()
                    if isinstance(data, dict) and 'data' in data:
                        print(f"  包含 'data' 字段，可能是新闻数据")
                except:
                    pass
    else:
        print("未找到返回200的接口，可能需要调整参数或检查网络")


if __name__ == "__main__":
    main()