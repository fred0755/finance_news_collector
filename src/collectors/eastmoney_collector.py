import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import hashlib


class EastMoneyCollector:
    """东方财富快讯采集器（使用真实API）"""

    def __init__(self):
        # 您找到的真实API地址
        self.base_url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://kuaixun.eastmoney.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        # 根据您截图中的参数构建
        self.base_params = {
            'client': 'web',
            'biz': 'web_724',
            'fastColumn': '102',  # 快讯栏目ID
            'pageSize': 20,  # 每页条数
            'sortEnd': int(time.time() * 1000000),  # 微秒时间戳
            'req_trace': int(time.time() * 1000),  # 毫秒时间戳
            '_': int(time.time() * 1000),
            'callback': f'jQuery_{int(time.time() * 1000)}'
        }

    def fetch_news(self, page_size: int = 20) -> Optional[List[Dict]]:
        """
        获取东方财富快讯新闻

        Args:
            page_size: 每页数量

        Returns:
            结构化的新闻列表
        """
        try:
            # 更新参数
            params = self.base_params.copy()
            params['pageSize'] = page_size
            params['sortEnd'] = int(time.time() * 1000000)
            params['_'] = int(time.time() * 1000)
            params['callback'] = f'jQuery_{int(time.time() * 1000)}'

            print(f"正在抓取快讯，每页 {page_size} 条...")
            print(f"API URL: {self.base_url}")

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )

            response.raise_for_status()
            print(f"HTTP状态码: {response.status_code}")

            # 处理JSONP响应
            raw_text = response.text
            print(f"原始响应长度: {len(raw_text)} 字符")

            # 提取JSON部分（JSONP格式：callback({...})）
            json_start = raw_text.find('(')
            json_end = raw_text.rfind(')')

            if json_start != -1 and json_end != -1:
                json_str = raw_text[json_start + 1:json_end]
                data = json.loads(json_str)
                print(f"成功解析JSON数据")

                # 解析新闻数据
                news_list = self._parse_news_data(data)
                return news_list
            else:
                print(f"响应不是有效的JSONP格式")
                print(f"响应预览: {raw_text[:200]}...")
                return None

        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"原始响应: {raw_text[:500]}...")
            return None
        except Exception as e:
            print(f"未知错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_news_data(self, data: Dict) -> List[Dict]:
        """
        解析API返回的新闻数据

        根据东方财富API的实际数据结构进行解析
        """
        news_items = []

        print(f"API返回数据键名: {list(data.keys())}")

        # 根据常见的API结构查找新闻数据
        # 可能的数据结构：data字段、result字段或直接是数组
        if isinstance(data, dict):
            # 尝试不同的数据位置
            data_locations = ['data', 'result', 'list', 'news']

            news_data = None
            for location in data_locations:
                if location in data:
                    news_data = data[location]
                    print(f"找到新闻数据在 '{location}' 字段")
                    break

            # 如果没找到特定字段，尝试data本身
            if news_data is None:
                news_data = data
        elif isinstance(data, list):
            news_data = data
            print(f"API直接返回列表，长度: {len(news_data)}")
        else:
            print(f"未知的数据类型: {type(data)}")
            return news_items

        # 处理新闻数据
        if isinstance(news_data, list):
            print(f"开始解析 {len(news_data)} 条新闻...")

            for i, item in enumerate(news_data):
                try:
                    # 解析单条新闻
                    news_item = self._parse_single_news(item)
                    if news_item and news_item.get('title'):
                        news_items.append(news_item)

                        # 只显示前3条作为示例
                        if i < 3:
                            print(f"  示例{i + 1}: {news_item['title'][:50]}...")

                except Exception as e:
                    print(f"解析第{i + 1}条新闻失败: {e}")
                    continue

        elif isinstance(news_data, dict):
            # 如果是字典，可能包含分页信息
            print(f"新闻数据是字典，键名: {list(news_data.keys())}")

            # 尝试在字典中查找列表
            for key, value in news_data.items():
                if isinstance(value, list):
                    print(f"在 '{key}' 中找到列表数据，长度: {len(value)}")
                    news_items.extend([self._parse_single_news(item) for item in value[:10]])
                    break
        else:
            print(f"无法处理的新闻数据类型: {type(news_data)}")

        return news_items

    def _parse_single_news(self, item) -> Dict:
        """解析单条新闻"""
        try:
            # 为新闻生成唯一ID
            news_id = hashlib.md5(str(item).encode()).hexdigest()[:16]

            # 根据常见的字段名提取信息
            news_item = {
                'id': news_id,
                'raw_data': item  # 保存原始数据用于调试
            }

            # 尝试提取标准字段（根据东方财富的实际字段名）
            field_mapping = {
                'title': ['title', 'Title', 'tit', 'newstitle'],
                'content': ['content', 'Content', 'body', 'newscontent', 'digest'],
                'time': ['time', 'Time', 'publish_time', 'showtime', 'ctime', 'timestamp'],
                'source': ['source', 'Source', 'media', 'author'],
                'url': ['url', 'Url', 'link', 'newsurl'],
                'category': ['category', 'Category', 'type', 'column'],
                'importance': ['importance', 'level', 'rank', 'hot']
            }

            # 自动匹配字段
            if isinstance(item, dict):
                for field_name, possible_keys in field_mapping.items():
                    for key in possible_keys:
                        if key in item and item[key] is not None:
                            news_item[field_name] = str(item[key])
                            break
                    if field_name not in news_item:
                        news_item[field_name] = ''

            # 确保必要字段
            news_item.setdefault('title', '')
            news_item.setdefault('content', '')
            news_item.setdefault('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            news_item.setdefault('source', '东方财富')
            news_item.setdefault('url', '')
            news_item.setdefault('category', '')
            news_item.setdefault('importance', 0)

            # 清理数据
            news_item['title'] = news_item['title'].strip()
            news_item['content'] = news_item['content'].strip()

            # 生成摘要（如果没有内容则用标题）
            if not news_item['content'] and news_item['title']:
                news_item['content'] = news_item['title']

            return news_item

        except Exception as e:
            print(f"解析单条新闻异常: {e}")
            return {'title': '解析失败', 'content': str(item)[:100]}

    def test_collection(self):
        """测试采集功能"""
        print("=" * 60)
        print("东方财富快讯采集器测试（使用真实API）")
        print("=" * 60)

        # 尝试抓取不同数量的新闻进行测试
        for page_size in [5, 10, 20]:
            print(f"\n尝试抓取 {page_size} 条新闻...")
            news_list = self.fetch_news(page_size=page_size)

            if news_list:
                print(f"✅ 成功采集到 {len(news_list)} 条新闻!")
                print("-" * 50)

                # 显示所有新闻标题
                for i, news in enumerate(news_list[:10], 1):
                    time_str = news.get('time', 'N/A')
                    title = news.get('title', '无标题')[:60]
                    source = news.get('source', 'N/A')
                    print(f"{i:2d}. [{time_str}] {title}... (来源: {source})")

                if len(news_list) > 10:
                    print(f"... 还有 {len(news_list) - 10} 条未显示")

                # 保存详细数据用于分析
                self._save_debug_data(news_list)

                # 验证数据质量
                self._validate_data(news_list)
                return True
            else:
                print(f"❌ 采集 {page_size} 条失败，尝试调整参数...")

        print("\n所有尝试均失败，请检查网络或API参数")
        return False

    def _save_debug_data(self, news_list):
        """保存调试数据"""
        if news_list:
            # 保存第一条新闻的完整数据
            debug_data = {
                'total_count': len(news_list),
                'sample_news': news_list[0] if news_list else {},
                'all_titles': [news.get('title', '') for news in news_list]
            }

            with open('debug_eastmoney_news.json', 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)

            print(f"\n调试数据已保存到: debug_eastmoney_news.json")

            # 也保存原始响应用于分析
            if news_list and 'raw_data' in news_list[0]:
                with open('debug_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(news_list[0]['raw_data'], f, ensure_ascii=False, indent=2)
                print(f"原始响应数据已保存到: debug_raw_response.json")

    def _validate_data(self, news_list):
        """验证数据质量"""
        print("\n数据质量检查:")
        print("-" * 30)

        total = len(news_list)
        if total == 0:
            print("❌ 没有采集到任何新闻")
            return

        # 统计字段完整性
        fields = ['title', 'content', 'time', 'source']
        stats = {}

        for field in fields:
            count = sum(1 for news in news_list if news.get(field))
            stats[field] = count

        print(f"新闻总数: {total}")
        for field, count in stats.items():
            percentage = (count / total) * 100
            status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
            print(f"{status} {field}: {count}/{total} ({percentage:.1f}%)")

        # 检查标题长度
        avg_title_len = sum(len(news.get('title', '')) for news in news_list) / total
        print(f"平均标题长度: {avg_title_len:.1f} 字符")

        if avg_title_len < 5:
            print("⚠️ 警告: 平均标题长度过短，可能数据解析有误")


# 主函数 - 直接运行测试
if __name__ == "__main__":
    print("东方财富快讯采集器 v2.0")
    print("基于真实API: https://np-weblist.eastmoney.com/comm/web/getFastNewsList")
    print()

    collector = EastMoneyCollector()
    success = collector.test_collection()

    print("\n" + "=" * 60)
    if success:
        print("✅ 采集器测试成功！")
        print("\n🎉 恭喜！您已成功完成：")
        print("1. ✅ 找到东方财富真实快讯API")
        print("2. ✅ 实现可工作的采集器")
        print("3. ✅ 获取结构化新闻数据")

        print("\n📋 下一步计划（M1.1 完成后的后续步骤）:")
        print("1. 集成调度器（APScheduler）实现定时采集")
        print("2. 设计数据库表结构并实现存储")
        print("3. 添加基础去重功能（URL哈希）")
        print("4. 创建简单的命令行管理界面")
    else:
        print("❌ 采集器测试失败")
        print("\n🔧 调试建议:")
        print("1. 检查网络连接")
        print("2. 检查API参数是否过期")
        print("3. 查看生成的调试文件分析数据结构")
        print("4. 尝试在浏览器中直接访问API链接测试")