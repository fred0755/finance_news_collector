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
        """解析单条新闻 - 优化版（根据实际数据结构）"""
        try:
            # 为新闻生成唯一ID（使用标题+时间的哈希）
            unique_str = f"{item.get('title', '')}_{item.get('showTime', '')}_{item.get('code', '')}"
            news_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]

            # 基础新闻结构
            news_item = {
                'id': news_id,
                'code': item.get('code', ''),  # 新闻唯一代码
                'raw_data': item  # 保存原始数据
            }

            # 1. 标题和内容（直接从API字段映射）
            news_item['title'] = item.get('title', '').strip()
            news_item['content'] = item.get('summary', '').strip()

            # 如果内容为空，使用标题作为内容
            if not news_item['content']:
                news_item['content'] = news_item['title']

            # 2. 时间字段（关键修复）
            # 优先使用showTime，如果没有则使用当前时间
            show_time = item.get('showTime', '')
            if show_time:
                # showTime已经是格式化字符串，直接使用
                news_item['time'] = show_time
                news_item['publish_time'] = show_time

                # 同时保存时间戳格式（便于排序和计算）
                try:
                    # 尝试将字符串时间转为时间戳
                    dt_obj = datetime.strptime(show_time, '%Y-%m-%d %H:%M:%S')
                    news_item['timestamp'] = int(dt_obj.timestamp())
                except:
                    news_item['timestamp'] = int(time.time())
            else:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                news_item['time'] = current_time
                news_item['publish_time'] = current_time
                news_item['timestamp'] = int(time.time())

            # 3. 来源处理（东方财富快讯可能没有明确的外部来源）
            # 先尝试从可能的字段获取，否则使用默认值
            source = item.get('mediaName', item.get('source', ''))
            if not source:
                # 根据内容判断可能的来源
                summary = item.get('summary', '')
                if '综合运输春运工作专班数据' in summary:
                    source = '交通运输部'
                elif '央行' in summary or '货币政策' in summary:
                    source = '中国人民银行'
                elif '证监会' in summary or '上交所' in summary or '深交所' in summary:
                    source = '证监会/交易所'
                else:
                    source = '东方财富快讯'  # 默认来源

            news_item['source'] = source.strip()

            # 4. 其他字段
            news_item['url'] = f"https://kuaixun.eastmoney.com/news/{news_item['code']}.html"
            news_item['category'] = self._infer_category(item)
            news_item['importance'] = self._calculate_importance(item)

            # 5. 股票/概念关联（如果有的话）
            stock_list = item.get('stockList', [])
            if stock_list and isinstance(stock_list, list):
                news_item['related_stocks'] = stock_list
                news_item['has_stock_mention'] = True
            else:
                news_item['related_stocks'] = []
                news_item['has_stock_mention'] = False

            # 6. 互动数据
            news_item['comment_count'] = item.get('pinglun_Num', 0)
            news_item['share_count'] = item.get('share', 0)

            # 7. 清理和验证
            self._clean_news_item(news_item)

            return news_item

        except Exception as e:
            print(f"解析单条新闻异常: {e}")
            import traceback
            traceback.print_exc()
            # 返回最小可用的新闻对象
            return {
                'id': hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
                'title': str(item.get('title', '解析失败'))[:200],
                'content': str(item)[:500],
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': '解析异常',
                'url': '',
                'category': '其他',
                'importance': 1
            }

    def _infer_category(self, item) -> str:
        """根据内容推断新闻分类"""
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()

        # 关键词匹配分类
        category_keywords = {
            '宏观': ['gdp', 'cpi', 'ppi', '通胀', '通缩', '货币政策', '财政政策', '央行', '利率', '存款准备金', 'mlf',
                     'slf', '逆回购', '经济数据', 'pmi', '工业增加值', '固定资产投资', '消费品零售总额', '失业率',
                     '外汇储备', '贸易顺差', '贸易逆差', '进出口'],
            '股市': ['a股', '沪指', '深指', '创业板', '科创板', '北证', '涨停', '跌停', '大盘', '指数', '股票', '股价',
                     '市值', '市盈率', '市净率', '换手率', '成交量', '成交额', '主力资金', '北向资金', '南向资金',
                     '融资融券', '两融'],
            '债券': ['国债', '地方债', '城投债', '企业债', '可转债', '债券', '收益率', '利率债', '信用债', '债市',
                     '到期收益率', '久期', '凸性', '信用利差', '评级'],
            '期货': ['期货', '原油', '黄金', '白银', '铜', '铝', '锌', '铅', '镍', '锡', '螺纹钢', '铁矿石', '焦煤',
                     '焦炭', '动力煤', '天然橡胶', '棉花', '白糖', '豆粕', '豆油', '棕榈油', '玉米', '鸡蛋', '生猪',
                     '苹果'],
            '外汇': ['美元', '人民币', '欧元', '英镑', '日元', '澳元', '加元', '瑞郎', '汇率', '外汇', '中间价', '在岸',
                     '离岸', 'cfets', '一篮子货币'],
            '商品': ['原油', '黄金', '白银', '铜', '铝', '锌', '铅', '镍', '锡', '螺纹钢', '铁矿石', '焦煤', '焦炭',
                     '动力煤', '天然橡胶', '棉花', '白糖', '豆粕', '豆油', '棕榈油', '玉米', '鸡蛋', '生猪', '苹果',
                     '大宗商品', '现货', '商品'],
            '理财': ['银行理财', '信托', '保险', '基金', '资管', '理财产品', '收益率', '净值', '申购', '赎回', '开放期',
                     '封闭期'],
            '房地产': ['房价', '房地产', '楼市', '房企', '土地', '拍卖', '成交', '销售', '投资', '开发', '住宅', '商业',
                       '办公', '租赁', '租金', '空置率', '去化周期'],
            '公司': ['财报', '业绩', '营收', '净利润', '毛利率', '净利率', 'roe', 'roa', '负债率', '现金流', '分红',
                     '送转', '回购', '增持', '减持', '质押', '冻结', '诉讼', '仲裁', '处罚', 'st', '*st', '退市',
                     '上市', 'ipo', '再融资', '定增', '配股', '可转债', '发债'],
            '行业': ['行业', '板块', '概念', '主题', '产业链', '供应链', '上下游', '产能', '产量', '销量', '库存',
                     '价格', '成本', '利润', '竞争', '垄断', '集中度', '市场份额', '龙头', '中小企业'],
            '国际': ['美联储', '欧央行', '日央行', '英央行', '澳洲联储', '加拿大央行', '瑞士央行', '加息', '降息', 'qe',
                     'qt', '缩表', '通胀目标', '就业数据', '贸易数据', '经济数据', '地缘政治', '战争', '冲突', '制裁',
                     '关税', '贸易战', '科技战', '金融战'],
            '政策': ['政策', '法规', '条例', '办法', '通知', '公告', '意见', '规划', '计划', '方案', '措施', '指导意见',
                     '实施细则', '监管', '检查', '整治', '整顿', '清理', '规范', '标准', '准入', '许可', '备案', '审批',
                     '核准', '登记', '注册'],
            '科技': ['人工智能', 'ai', '大数据', '云计算', '区块链', '数字货币', '元宇宙', '物联网', '5g', '6g', '芯片',
                     '半导体', '集成电路', '光刻机', '操作系统', '数据库', '中间件', '应用软件', '网络安全', '信息安全',
                     '数据安全', '隐私保护', '算法', '模型', '算力', '数据'],
        }

        # 检查每个分类
        text_to_check = f"{title} {summary}"
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    return category

        return '其他'

    def _calculate_importance(self, item) -> int:
        """计算新闻重要性分数（1-10分）"""
        score = 5  # 基础分

        title = item.get('title', '')
        summary = item.get('summary', '')

        # 紧急关键词加分
        urgent_keywords = ['紧急', '突发', '重磅', '重大', '预警', '警报', '危机', '崩盘', '暴跌', '暴涨', '破位',
                           '突破', '历史', '首次', '纪录', '新高', '新低']
        for keyword in urgent_keywords:
            if keyword in title:
                score += 2
                break

        # 涉及股票数量加分
        stock_list = item.get('stockList', [])
        if len(stock_list) > 0:
            score += min(len(stock_list) * 0.5, 3)  # 最多加3分

        # 评论数加分
        comment_count = item.get('pinglun_Num', 0)
        if comment_count > 10:
            score += 1
        if comment_count > 50:
            score += 1

        # 确保分数在1-10之间
        return max(1, min(10, int(score)))

    def _clean_news_item(self, news_item):
        """清理和标准化新闻数据"""
        # 确保标题和内容不为空
        if not news_item.get('title'):
            news_item['title'] = '无标题新闻'

        if not news_item.get('content'):
            news_item['content'] = news_item['title']

        # 截断过长的字段
        max_title_len = 200
        max_content_len = 5000

        if len(news_item['title']) > max_title_len:
            news_item['title'] = news_item['title'][:max_title_len] + '...'

        if len(news_item['content']) > max_content_len:
            news_item['content'] = news_item['content'][:max_content_len] + '...'

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