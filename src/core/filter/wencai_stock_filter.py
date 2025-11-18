"""
问财股票筛选器

基于pywencai的自然语言查询能力进行股票筛选
"""

from datetime import datetime
from typing import List, Optional
import pandas as pd


class WencaiStockFilter:
    """
    问财股票筛选器

    使用pywencai的自然语言查询功能筛选股票
    优势：查询条件灵活，支持复杂条件组合

    注意事项：
    - 需要有效的Cookie（定期更新）
    - 依赖问财网站稳定性
    - 只能查询当前日期的数据，不支持历史数据
    """

    def __init__(self, cookie: str):
        """
        初始化

        Args:
            cookie: 问财Cookie字符串（从浏览器获取）

        Usage:
            filter = WencaiStockFilter(cookie="your_cookie_here")
            stocks = filter.get_eligible_stocks(date=datetime(2023, 1, 1))
        """
        self.cookie = cookie
        self._wencai = None

        try:
            import pywencai
            self._wencai = pywencai
        except ImportError:
            raise ImportError("请安装pywencai: pip install pywencai")

    def get_eligible_stocks(
        self,
        date: datetime,
        decline_days_threshold: int = 8,
        market_cap_threshold: Optional[float] = None
    ) -> List[str]:
        """
        获取符合条件的股票

        默认策略：连续下跌N天的股票（排除ST、退市、新股）

        Args:
            date: 查询日期
            decline_days_threshold: 连续下跌天数阈值（默认8天）
            market_cap_threshold: 最小市值（元），可选

        Returns:
            股票代码列表，格式 ['000001.SZ', '600000.SH', ...]

        Example:
            >>> filter = WencaiStockFilter(cookie="...")
            >>> stocks = filter.get_eligible_stocks(
            ...     date=datetime(2023, 1, 10),
            ...     decline_days_threshold=8
            ... )
            >>> print(stocks)
            ['000001.SZ', '600000.SH', '000002.SZ']
        """
        # 格式化日期（中文格式）
        formatted_date = f"{date.year}年{date.month}月{date.day}日"

        # 构建查询语句
        query_parts = [
            f"{formatted_date}连续下跌天数>={decline_days_threshold}",
            "非st",  # 排除ST股票
            "非退市",  # 排除退市股票
            "非新股",  # 排除新股
        ]

        # 添加市值条件
        if market_cap_threshold:
            # 问财通常使用亿元为单位
            min_cap_yi = market_cap_threshold / 1e8  # 转换为亿元
            query_parts.append(f"总市值>{min_cap_yi}亿")

        # 添加排序（按流通市值从大到小）
        query_parts.append("流通市值降序")

        # 组合查询语句
        query = ";".join(query_parts)

        try:
            # 调用pywencai
            df = self._wencai.get(query=query, cookie=self.cookie)

            # 处理返回结果
            if df is None or df.empty:
                return []

            # 转换数据格式
            return self._parse_response(df)

        except Exception as e:
            raise RuntimeError(f"调用问财API失败: {str(e)}")

    def _parse_response(self, df: pd.DataFrame) -> List[str]:
        """
        解析pywencai返回的数据

        Args:
            df: pywencai返回的DataFrame

        Returns:
            股票代码列表
        """
        stocks = []

        for _, row in df.iterrows():
            code = str(row['code'])

            # 根据代码前缀判断市场
            # 6开头 -> 上证（.SH）
            # 0或3开头 -> 深证（.SZ）
            if code.startswith('6'):
                suffix = 'SH'
            elif code.startswith(('0', '3')):
                suffix = 'SZ'
            else:
                # 其他代码，默认SZ
                suffix = 'SZ'

            stocks.append(f"{code}.{suffix}")

        return stocks

    def test_connection(self) -> bool:
        """
        测试问财连接是否正常

        Returns:
            是否连接成功
        """
        try:
            # 使用简单的查询测试
            test_query = "非st"
            df = self._wencai.get(query=test_query, cookie=self.cookie)
            return df is not None and not df.empty
        except:
            return False
