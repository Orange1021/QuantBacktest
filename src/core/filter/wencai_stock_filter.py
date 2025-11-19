"""
问财股票筛选器

基于pywencai的自然语言查询能力进行股票筛选
"""

from datetime import datetime
from typing import List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


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

        # 添加结果缓存（避免重复查询同一天）
        self._result_cache: Dict[str, List[str]] = {}

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
        logger.info(f"[WENCAI_DEBUG] 查询语句: {query}")

        try:
            # 调用pywencai（添加重试和延迟）
            logger.info(f"[WENCAI_DEBUG] 开始调用pywencai.get()...")

            # 添加延迟（避免频繁调用被限流）
            import time
            time.sleep(1)  # 延迟1秒

            df = self._wencai.get(query=query, cookie=self.cookie)
            logger.info(f"[WENCAI_DEBUG] pywencai.get()返回，result type: {type(df)}")

            if df is None:
                logger.warning(f"[WENCAI_DEBUG] df is None，尝试重新调用...")
                # 如果返回None，等待2秒后重试一次
                time.sleep(2)
                df = self._wencai.get(query=query, cookie=self.cookie)
                logger.info(f"[WENCAI_DEBUG] 重试后返回，result type: {type(df)}")

            if df is None:
                logger.warning(f"[WENCAI_DEBUG] 重试后仍为None，返回空列表")
                return []

            logger.info(f"[WENCAI_DEBUG] df shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
            logger.info(f"[WENCAI_DEBUG] df empty: {df.empty if hasattr(df, 'empty') else 'N/A'}")

            # 处理返回结果
            if df.empty:
                logger.info(f"[WENCAI_DEBUG] df为空，返回[]")
                return []

            logger.info(f"[WENCAI_DEBUG] 处理返回数据，调用_parse_response()")
            stocks = self._parse_response(df)
            logger.info(f"[WENCAI_DEBUG] _parse_response()返回 {len(stocks)} 只股票")
            return stocks

        except Exception as e:
            logger.error(f"[WENCAI_DEBUG] 发生异常: {e}")
            logger.error(f"[WENCAI_DEBUG] 异常类型: {type(e)}")
            import traceback
            for line in traceback.format_exc().split('\n'):
                logger.error(line)
            raise RuntimeError(f"调用问财API失败: {str(e)}")

    def _parse_response(self, df: pd.DataFrame) -> List[str]:
        """
        解析pywencai返回的数据

        Args:
            df: pywencai返回的DataFrame

        Returns:
            股票代码列表
        """
        import logging
        logger = logging.getLogger('wencai_debug')

        logger.info(f"[WENCAI_DEBUG] _parse_response()开始，输入df行数: {len(df) if hasattr(df, '__len__') else 'N/A'}")
        logger.info(f"[WENCAI_DEBUG] df列名: {list(df.columns) if hasattr(df, 'columns') else 'N/A'}")

        stocks = []

        for _, row in df.iterrows():
            try:
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

                full_code = f"{code}.{suffix}"
                stocks.append(full_code)
                logger.debug(f"[WENCAI_DEBUG] 解析成功: {full_code}")

            except Exception as e:
                logger.warning(f"[WENCAI_DEBUG] 解析行失败: {e}, row: {row.to_dict() if hasattr(row, 'to_dict') else row}")
                continue

        logger.info(f"[WENCAI_DEBUG] _parse_response()完成，返回 {len(stocks)} 只股票")
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
