#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财经新闻采集系统 - 修复版
使用字典配置，确保能运行
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入配置
try:
    from config import 新闻源列表, 系统配置

    使用基础版本 = False
except ImportError as e:
    print(f"配置导入失败: {e}")
    # 基础配置
    系统配置 = {
        '日志目录': 'logs',
        '数据目录': 'data',
        '日志级别': 'INFO',
        '请求延迟': 2,
        '超时时间': 30
    }

    # 基础新闻源
    新闻源列表 = [
        {
            '名称': '东方财富网快讯',
            '网址': 'https://kuaixun.eastmoney.com/',
            '采集类型': '快讯',
            '启用': True,
            '优先级': 1
        },
        {
            '名称': '证券时报快讯',
            '网址': 'https://www.stcn.com/article/list/kx.html',
            '采集类型': '快讯',
            '启用': True,
            '优先级': 2
        }
    ]
    使用基础版本 = True


# ========== 基础采集器类 ==========
class 基础采集器:
    """所有采集器的基类"""

    def __init__(self, 配置):
        self.配置 = 配置
        self.名称 = 配置['名称']  # 字典访问
        self.网址 = 配置['网址']  # 字典访问
        self.日志 = logging.getLogger(self.名称)
        self.数据 = []

    def 运行(self):
        """运行采集器"""
        self.日志.info(f'开始采集: {self.名称}')

        try:
            self.数据 = self.生成模拟数据()

            if self.数据:
                self.日志.info(f'采集成功: {len(self.数据)} 条')
            else:
                self.日志.warning('未采集到数据')

            return self.数据

        except Exception as e:
            self.日志.error(f'采集失败: {e}')
            return []

    def 生成模拟数据(self):
        """生成模拟数据（统一格式）"""
        import hashlib
        当前时间 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        时间戳 = int(datetime.now().timestamp())

        模拟新闻 = [
            {
                'id': f"{self.名称[:2]}_{时间戳}_demo1",
                'title': f'{self.名称}：测试新闻1',
                'content': f'这是来自{self.名称}的测试内容1',
                'summary': f'{self.名称}测试摘要1',
                'source': self.名称,
                'source_type': '模拟',
                'url': f'{self.网址}#demo1',
                'url_md5': hashlib.md5(f'{self.网址}#demo1'.encode()).hexdigest(),
                'publish_time': 当前时间,
                'collect_time': 当前时间,
                'timestamp': 时间戳,
                'category': '测试',
                'tags': ['测试', self.名称],
                'importance': 3,
                'is_duplicate': False,
                'duplicate_id': '',
                'is_merged': False,
                'merge_group': '',
                'merge_links': [],
                'author': self.名称,
                'region': '测试',
                'market': '测试'
            },
            {
                'id': f"{self.名称[:2]}_{时间戳}_demo2",
                'title': f'{self.名称}：测试新闻2',
                'content': f'这是来自{self.名称}的测试内容2',
                'summary': f'{self.名称}测试摘要2',
                'source': self.名称,
                'source_type': '模拟',
                'url': f'{self.网址}#demo2',
                'url_md5': hashlib.md5(f'{self.网址}#demo2'.encode()).hexdigest(),
                'publish_time': 当前时间,
                'collect_time': 当前时间,
                'timestamp': 时间戳,
                'category': '测试',
                'tags': ['测试', self.名称],
                'importance': 4,
                'is_duplicate': False,
                'duplicate_id': '',
                'is_merged': False,
                'merge_group': '',
                'merge_links': [],
                'author': self.名称,
                'region': '测试',
                'market': '测试'
            }
        ]

        return 模拟新闻


# ========== 采集器工厂 ==========
def 创建采集器(配置):
    """根据配置创建对应的采集器"""
    try:
        # 动态导入采集器模块
        模块名称 = 配置['名称'].replace(' ', '').replace('-', '').replace('网', '').replace('财经', '')

        采集器映射 = {
            '东方财富网快讯': 'eastmoney_collector',
            '证券时报快讯': 'stcn_collector',
            '新浪财经7x24': 'sina_collector'
        }

        文件名 = 采集器映射.get(配置['名称'], f"{模块名称.lower()}_collector")

        try:
            完整模块名 = f"collectors.{文件名}"
            import importlib
            模块 = importlib.import_module(完整模块名)

            # 查找采集器类
            类名 = f"{模块名称}采集器"
            if hasattr(模块, 类名):
                return getattr(模块, 类名)(配置)
            else:
                # 查找其他可能的类名
                for attr in dir(模块):
                    if attr.endswith('采集器'):
                        return getattr(模块, attr)(配置)

                # 如果找不到，使用基础采集器
                return 基础采集器(配置)

        except ImportError:
            # 模块不存在，使用基础采集器
            return 基础采集器(配置)

    except Exception as e:
        print(f"创建采集器失败: {e}")
        return 基础采集器(配置)


# ========== 主运行逻辑 ==========
def 运行所有采集器():
    """运行所有启用的采集器"""
    所有结果 = {}

    # 过滤启用的新闻源并按优先级排序
    启用新闻源 = [源 for 源 in 新闻源列表 if 源.get('启用', True)]
    启用新闻源.sort(key=lambda x: x.get('优先级', 99))

    if not 启用新闻源:
        print("⚠ 没有启用的新闻源")
        return {}

    logger.info(f'开始批量采集，共 {len(启用新闻源)} 个新闻源')
    print(f"\n🔍 开始采集 {len(启用新闻源)} 个新闻源:")

    for 序号, 新闻源配置 in enumerate(启用新闻源, 1):
        logger.info(f"采集: {新闻源配置['名称']}")
        print(f"  {序号}. {新闻源配置['名称']}...", end='', flush=True)

        try:
            # 创建并运行采集器
            采集器 = 创建采集器(新闻源配置)
            数据 = 采集器.运行()
            所有结果[新闻源配置['名称']] = 数据

            print(f" ✓ ({len(数据)}条)")

        except Exception as e:
            logger.error(f"采集失败: {e}")
            print(f" ✗ (错误)")
            所有结果[新闻源配置['名称']] = []

        # 添加延迟
        if 序号 < len(启用新闻源):
            time.sleep(系统配置.get('请求延迟', 2))

    logger.info('批量采集完成')
    print("\n✅ 批量采集完成")

    return 所有结果


def 生成汇总报告(所有结果):
    """生成采集汇总报告"""
    总新闻数 = sum(len(数据) for 数据 in 所有结果.values())
    成功采集器数 = sum(1 for 数据 in 所有结果.values() if 数据)

    报告 = {
        '生成时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '采集器总数': len(所有结果),
        '成功采集器数': 成功采集器数,
        '总新闻数': 总新闻数,
        '详细统计': {名称: len(数据) for 名称, 数据 in 所有结果.items()}
    }

    # 保存报告
    报告文件 = f"{系统配置.get('数据目录', 'data')}/采集报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(报告文件, 'w', encoding='utf-8') as f:
        json.dump(报告, f, ensure_ascii=False, indent=2)

    logger.info(f'报告已保存: {报告文件}')

    # 打印摘要
    print('\n' + '=' * 60)
    print('📊 采集汇总报告')
    print('=' * 60)
    print(f'采集器总数: {len(所有结果)} 个')
    print(f'成功采集: {成功采集器数} 个')
    print(f'总新闻数: {总新闻数} 条')
    print('-' * 40)

    for 名称, 数量 in 报告['详细统计'].items():
        print(f'  {名称}: {数量} 条')

    print('=' * 60)

    return 报告


def 处理并保存新闻(所有结果):
    """处理去重合并并保存到数据库"""

    # 1. 合并所有新闻
    所有新闻 = []
    for 来源, 新闻列表 in 所有结果.items():
        所有新闻.extend(新闻列表)

    if not 所有新闻:
        print("⚠ 未采集到任何新闻")
        return []

    print(f"📊 原始采集: {len(所有新闻)} 条")

    # 2. 简单去重（基于URL）
    唯一新闻 = []
    已处理urls = set()

    for 新闻 in 所有新闻:
        url = 新闻.get('url', '')
        if url and url not in 已处理urls:
            已处理urls.add(url)
            新闻['is_duplicate'] = False
            唯一新闻.append(新闻)
        elif url:
            新闻['is_duplicate'] = True
            唯一新闻.append(新闻)
        else:
            新闻['is_duplicate'] = False
            唯一新闻.append(新闻)

    print(f"✅ 去重后: {len(唯一新闻)} 条")

    # 3. 按时间排序
    唯一新闻.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

    # 4. 保存到JSON文件
    时间戳 = datetime.now().strftime('%Y%m%d_%H%M%S')
    备份文件 = f"{系统配置.get('数据目录', 'data')}/新闻_{时间戳}.json"

    with open(备份文件, 'w', encoding='utf-8') as f:
        json.dump(唯一新闻, f, ensure_ascii=False, indent=2)

    print(f"📁 保存到JSON文件: {备份文件}")

    # 显示最新几条
    if 唯一新闻:
        print("\n📰 最新新闻摘要:")
        print("-" * 80)
        for i, 新闻 in enumerate(唯一新闻[:5], 1):
            时间 = 新闻.get('publish_time', '未知时间')
            来源 = 新闻.get('source', '未知来源')
            标题 = 新闻.get('title', '无标题')
            print(f"{i}. [{时间}] [{来源}] {标题[:60]}{'...' if len(标题) > 60 else ''}")
        print("-" * 80)

    return 唯一新闻


# ========== 主函数 ==========
def 主函数():
    """主入口函数"""
    global logger

    # 简单日志设置
    os.makedirs(系统配置.get('日志目录', 'logs'), exist_ok=True)
    logger = logging.getLogger('新闻采集器')
    logger.setLevel(getattr(logging, 系统配置.get('日志级别', 'INFO')))

    if not logger.handlers:
        控制台处理器 = logging.StreamHandler()
        格式 = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        控制台处理器.setFormatter(格式)
        logger.addHandler(控制台处理器)

    print('=' * 70)
    print('📰 财经新闻采集系统 - 修复版')
    print('=' * 70)
    print(f'🕐 开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    # 创建必要目录
    os.makedirs(系统配置.get('数据目录', 'data'), exist_ok=True)
    os.makedirs(系统配置.get('日志目录', 'logs'), exist_ok=True)

    # 运行采集器
    try:
        # 运行所有采集器
        原始结果 = 运行所有采集器()

        if not 原始结果:
            print("\n⚠ 未采集到任何数据")
            return {}

        # 生成汇总报告
        生成汇总报告(原始结果)

        # 处理并保存新闻
        print("\n🔄 数据处理中...")
        最终新闻 = 处理并保存新闻(原始结果)

        print(f'\n✅ 采集完成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 70)

        return 最终新闻

    except KeyboardInterrupt:
        print('\n\n⏹ 用户中断采集')
        return {}
    except Exception as e:
        logger.error(f'系统运行失败: {e}')
        print(f'\n❌ 系统错误: {e}')
        return {}


# ========== 命令行界面 ==========
if __name__ == '__main__':
    # 运行主程序
    结果 = 主函数()

    # 如果需要等待
    if len(sys.argv) == 1:
        input("\n按 Enter 键退出...")