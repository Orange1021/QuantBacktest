"""
选股器抽象基类
统一"输入(日期)"与"输出(股票列表)"的标准，屏蔽底层查询逻辑的差异
"""

from abc import ABC, abstractmethod
from typing import List
from datetime import datetime


class BaseStockSelector(ABC):
    """
    [抽象基类] 选股器接口
    职责：统一"输入(日期)"与"输出(股票列表)"的标准，屏蔽底层查询逻辑的差异。
    """

    @abstractmethod
    def select_stocks(self, date: datetime, **kwargs) -> List[str]:
        """
        [抽象方法] 执行选股
        
        Args:
            date (datetime): 必须参数，查询的基准日期。
            **kwargs: 动态参数，用于传递具体的筛选条件。
                      - Wencai 实现类读取: kwargs['query'] (例如: "{date}涨幅大于5%")
                      - Tushare 实现类读取: kwargs['min_pe'], kwargs['industry'] (未来扩展)
        
        Returns:
            List[str]: 标准化的股票代码列表。
                       必须统一格式为: "000001.SZ", "600000.SH", "830000.BJ"。
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        [抽象方法] 连接健康检查
        Returns:
            bool: 如果API连接/Cookie有效返回 True，否则 False。
        """
        pass