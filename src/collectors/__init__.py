# collectors/__init__.py
from .base_collector import BaseCollector
from .eastmoney_collector import EastMoneyCollector
from .stcn_collector import StcnCollector

__all__ = ['BaseCollector', 'EastMoneyCollector', 'StcnCollector', 'SinaCollector']

# 尝试导入其他采集器
try:
    from .sina_collector import SinaCollector
except ImportError:
    # 如果文件不存在，创建一个简单的替代类
    class SinaCollector(BaseCollector):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.source_name = "新浪财经"

        def fetch_news_list(self):
            return []