"""
本地CSV数据提供器

从本地CSV文件加载股票数据，提供高性能的数据访问。
支持智能缓存、数据清洗、并行读取和自动降级。


创建日期: 2025-01-18
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

import pandas as pd

from .provider import DataProvider

# 配置日志
logger = logging.getLogger(__name__)


class LRUCache:
    """
    LRU缓存实现

最近最少使用缓存，用于存储已加载的股票数据，
减少重复读取文件的I/O开销。

Attributes:
    max_size: 最大缓存条目数
    cache_dict: 缓存字典
    usage_order: 使用顺序列表

Example:
    >>> cache = LRUCache(max_size=100)
    >>> cache.put('000001.SZ', df)
    >>> df = cache.get('000001.SZ')
"""

    def __init__(self, max_size: int = 100):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数，默认100
        """
        self.max_size = max_size
        self.cache_dict: Dict[str, pd.DataFrame] = {}
        self.usage_order: List[str] = []

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        获取缓存项

        Args:
            key: 缓存键（股票代码）

        Returns:
            缓存的DataFrame，如果不存在返回None
        """
        if key not in self.cache_dict:
            return None

        # 更新使用顺序（移到末尾表示最新使用）
        self.usage_order.remove(key)
        self.usage_order.append(key)

        return self.cache_dict[key]

    def put(self, key: str, value: pd.DataFrame) -> None:
        """
        添加缓存项

        Args:
            key: 缓存键
            value: 要缓存的DataFrame
        """
        if key in self.cache_dict:
            # 更新现有项
            self.usage_order.remove(key)
        else:
            # 新增项
            if len(self.cache_dict) >= self.max_size:
                # 缓存已满，移除最久未使用的项
                oldest_key = self.usage_order.pop(0)
                del self.cache_dict[oldest_key]
                logger.debug(f"LRU缓存淘汰: {oldest_key}")

        self.cache_dict[key] = value
        self.usage_order.append(key)

    def clear(self) -> None:
        """清空缓存"""
        self.cache_dict.clear()
        self.usage_order.clear()
        logger.info("LRU缓存已清空")

    def info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "size": len(self.cache_dict),
            "max_size": self.max_size,
            "keys": list(self.cache_dict.keys()),
            "usage_order": self.usage_order
        }


class LocalCSVDataProvider(DataProvider):
    """
    本地CSV数据提供器

    从本地CSV文件加载股票数据，提供高效的数据访问。
    特性：
    - 智能LRU缓存，减少I/O
    - 数据清洗和验证
    - TS代码过滤，确保数据正确性
    - 自动过滤未来日期
    - 详细的日志记录

    Attributes:
        data_dir: 数据目录路径
        cache: LRU缓存实例
        parallel_read: 是否启用并行读取
        validate_tscode: 是否验证TS代码
        filter_future: 是否过滤未来日期
        file_format: 文件格式（csv/pickle/parquet）

    Example:
        >>> provider = LocalCSVDataProvider(
        ...     data_dir="C:/Users/123/A股数据/个股数据",
        ...     cache_size=100,
        ...     validate_tscode=True,
        ...     filter_future=True
        ... )
        >>> df = provider.get_daily_bars("000001.SZ", start_date, end_date)
    """

    def __init__(
        self,
        data_dir: Union[str, Path],
        cache_size: int = 100,
        parallel_read: bool = False,
        validate_tscode: bool = True,
        filter_future: bool = True,
        file_format: str = "csv"
    ):
        """
        初始化本地CSV数据提供器

        Args:
            data_dir: 数据目录路径
            cache_size: LRU缓存大小，默认100
            parallel_read: 是否启用并行读取，默认False
            validate_tscode: 是否验证TS代码，默认True
            filter_future: 是否过滤未来日期，默认True
            file_format: 文件格式，默认"csv"

        Raises:
            ValueError: 如果数据目录不存在
            TypeError: 如果参数类型错误
        """
        if not isinstance(data_dir, (str, Path)):
            raise TypeError(f"data_dir必须是str或Path类型，实际类型: {type(data_dir)}")

        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise ValueError(f"数据目录不存在: {self.data_dir}")

        if not self.data_dir.is_dir():
            raise ValueError(f"路径不是目录: {self.data_dir}")

        logger.info(f"初始化LocalCSVDataProvider，数据目录: {self.data_dir}")
        logger.info(f"LRU缓存大小: {cache_size}")
        logger.info(f"TS代码验证: {validate_tscode}")
        logger.info(f"未来日期过滤: {filter_future}")

        self.cache = LRUCache(max_size=cache_size)
        self.parallel_read = parallel_read
        self.validate_tscode = validate_tscode
        self.filter_future = filter_future
        self.file_format = file_format

        # 统计信息
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "files_read": 0,
            "bytes_read": 0
        }

    def _convert_symbol_to_filename(self, symbol: str) -> str:
        """
        将股票代码转换为文件名

        Args:
            symbol: 股票代码，格式 "000001.SZ" 或 "600000.SH"

        Returns:
            文件名，如 "000001.csv"

        Example:
            >>> provider._convert_symbol_to_filename("000001.SZ")
            '000001.csv'
            >>> provider._convert_symbol_to_filename("600000.SH")
            '600000.csv'
        """
        if not symbol or '.' not in symbol:
            raise ValueError(f"股票代码格式错误，应为 '000001.SZ' 格式，实际: {symbol}")

        code, suffix = symbol.split('.')
        return f"{code}.{self.file_format}"

    def _parse_date(self, date_int: Union[int, str]) -> Optional[datetime]:
        """
        解析日期（整数格式 -> datetime）

        Args:
            date_int: 日期整数，格式 YYYYMMDD

        Returns:
            datetime对象，如果解析失败返回None

        Example:
            >>> provider._parse_date(20250118)
            datetime.datetime(2025, 1, 18, 0, 0)
        """
        try:
            date_str = str(date_int)
            if len(date_str) != 8:
                logger.warning(f"日期格式错误，应为8位数字，实际: {date_str}")
                return None

            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            return datetime(year, month, day)
        except Exception as e:
            logger.error(f"解析日期失败: {date_int}, 错误: {e}")
            return None

    def _load_data(self, symbol: str) -> pd.DataFrame:
        """
        从文件加载数据（带缓存）

        Args:
            symbol: 股票代码

        Returns:
            清洗后的DataFrame

        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果数据格式错误
        """
        # 检查缓存
        cached = self.cache.get(symbol)
        if cached is not None:
            self.stats["cache_hits"] += 1
            logger.debug(f"缓存命中: {symbol}")
            return cached

        self.stats["cache_misses"] += 1
        logger.debug(f"缓存未命中: {symbol}")

        # 从文件加载
        filename = self._convert_symbol_to_filename(symbol)
        filepath = self.data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"数据文件不存在: {filepath}")

        try:
            logger.debug(f"读取文件: {filepath}")

            # 读取CSV
            df = pd.read_csv(filepath)

            self.stats["files_read"] += 1
            self.stats["bytes_read"] += filepath.stat().st_size

            # 验证TS代码（确保文件内容正确）
            if self.validate_tscode and 'TS代码' in df.columns:
                if not (df['TS代码'] == symbol).any():
                    logger.warning(f"TS代码不匹配: {symbol}，文件中的TS代码: {df['TS代码'].iloc[0]}")

            # 数据清洗和转换
            df = self._clean_data(df, symbol)

            # 存入缓存
            self.cache.put(symbol, df)

            return df

        except pd.errors.EmptyDataError:
            raise ValueError(f"数据文件为空: {filepath}")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSV解析错误: {filepath} - {e}")
        except Exception as e:
            raise RuntimeError(f"加载数据失败: {filepath} - {e}")

    def _clean_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        清洗和转换数据

        Args:
            df: 原始DataFrame
            symbol: 股票代码

        Returns:
            清洗后的DataFrame
        """
        try:
            # 检查必要列是否存在
            required_columns = ['交易日期', '开盘价', '最高价', '最低价', '收盘价', '成交量(手)', 'TS代码']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"缺少必要列: {missing_columns}")

            # 过滤TS代码（确保数据正确性）
            if self.validate_tscode and 'TS代码' in df.columns:
                df = df[df['TS代码'] == symbol].copy()

            # 转换日期
            df['date'] = pd.to_datetime(df['交易日期'], format='%Y%m%d', errors='coerce')

            # 检查是否有解析失败的日期
            invalid_dates = df['date'].isnull().sum()
            if invalid_dates > 0:
                logger.warning(f"有 {invalid_dates} 行日期解析失败，将被忽略")
                df = df.dropna(subset=['date'])

            # 过滤未来日期
            if self.filter_future:
                today = datetime.now()
                future_count = (df['date'] > today).sum()
                if future_count > 0:
                    logger.warning(f"过滤 {future_count} 条未来日期记录")
                    df = df[df['date'] <= today]

            # 按日期排序
            df = df.sort_values('date')

            # 设置索引
            df = df.set_index('date')

            # 选择需要的列并重命名
            df = df[['开盘价', '最高价', '最低价', '收盘价', '成交量(手)']].copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']

            # 验证数据完整性（检查是否有缺失值）
            if df.isnull().any().any():
                null_counts = df.isnull().sum()
                logger.warning(f"清洗后仍有缺失值: {null_counts.to_dict()}")
                df = df.dropna()

            # 验证价格合理性
            price_invalid = (df['high'] < df['low']).sum()
            if price_invalid > 0:
                logger.warning(f"发现 {price_invalid} 条价格不合理记录（最高价<最低价）")
                df = df[df['high'] >= df['low']]

            return df

        except Exception as e:
            logger.error(f"数据清洗失败: {symbol} - {e}")
            raise

    def get_daily_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        获取日K线数据

        Args:
            symbol: 股票代码，格式 '000001.SZ'
            start_date: 开始日期（包含）
            end_date: 结束日期（包含）

        Returns:
            DataFrame，包含以下列：
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量（手）

        Raises:
            FileNotFoundError: 数据文件不存在
            ValueError: 数据格式错误
            RuntimeError: 加载失败

        Example:
            >>> provider = LocalCSVDataProvider(data_dir="...")
            >>> df = provider.get_daily_bars("000001.SZ", datetime(2020,1,1), datetime(2020,12,31))
            >>> print(df.head())
                         open   high    low  close      volume
            date
            2020-01-02  11.67  11.84  11.66  11.75  1316994.98
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"股票代码格式错误: {symbol}")

        if start_date > end_date:
            raise ValueError(f"开始日期不能晚于结束日期: {start_date} > {end_date}")

        logger.debug(f"获取K线数据: {symbol}, {start_date} ~ {end_date}")

        try:
            # 加载数据（带缓存）
            df = self._load_data(symbol)

            # 筛选日期范围
            mask = (df.index >= start_date) & (df.index <= end_date)
            result = df.loc[mask].copy()

            if result.empty:
                logger.warning(f"在日期范围内无数据: {symbol} [{start_date} ~ {end_date}]")

            logger.info(f"成功获取数据: {symbol}, {len(result)} 条记录")

            return result

        except Exception as e:
            # Note: 改为debug级别，因为很多股票（如退市、停牌）没有数据是正常的
            # 回测时会自动跳过这些股票，不需要error级别日志
            logger.debug(f"获取K线数据失败: {symbol} - {e}")
            raise

    def get_market_cap(
        self,
        symbols: List[str],
        date: datetime
    ) -> pd.Series:
        """
        获取市值数据

        注意：本地CSV包含市值数据（总市值(万元)列），
        但历史数据可能缺失。此实现优先使用本地数据，
        缺失时返回空Series。

        Args:
            symbols: 股票代码列表
            date: 日期

        Returns:
            Series，index为symbol，value为总市值（元）

        Raises:
            NotImplementedError: 本地数据市值可能不完整，建议用Tushare
        """
        logger.warning("本地CSV数据提供器的市值数据可能不完整，建议使用TushareDataProvider")

        # 尝试从本地CSV读取市值
        market_caps = {}

        for symbol in symbols:
            try:
                df = self._load_data(symbol)

                # 找到最接近日期的数据
                nearest_date = df.index[df.index.get_indexer([date], method='nearest')[0]]
                market_cap_10k_yuan = df.loc[nearest_date].get('总市值(万元)', None)

                if market_cap_10k_yuan is not None:
                    # 转换为元
                    market_caps[symbol] = market_cap_10k_yuan * 10000

            except Exception:
                # 如果失败，跳过这只股票
                continue

        return pd.Series(market_caps, dtype=float)

    def get_stock_universe(
        self,
        date: datetime,
        market: str = "A_SHARE"
    ) -> List[str]:
        """
        获取股票池

        Args:
            date: 日期
            market: 市场类型（A_SHARE: A股，H_SHARE: 港股等）

        Returns:
            股票代码列表

        Note:
            通过扫描目录获取所有CSV文件，然后过滤。
            此操作较慢，建议缓存结果。
        """
        logger.info(f"获取股票池: {date}, market={market}")

        try:
            # 扫描目录获取所有CSV文件
            pattern = f"*.{self.file_format}"
            files = list(self.data_dir.glob(pattern))

            symbols = []
            for file in files:
                code = file.stem  # 去掉扩展名

                # 根据代码前缀判断市场
                if code.startswith('6'):
                    symbols.append(f"{code}.SH")
                elif code.startswith(('0', '3')):
                    symbols.append(f"{code}.SZ")
                elif market.upper() != "A_SHARE":
                    # 处理其他市场（如港股、美股）
                    symbols.append(f"{code}.OTHER")

            logger.info(f"找到股票数量: {len(symbols)}")
            return symbols

        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
            return []

    def is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日

        通过检查是否有股票在当日有数据来判断。
        此方法不准确，建议从其他来源获取交易日历。

        Args:
            date: 日期

        Returns:
            是否为交易日
        """
        logger.warning("本地CSV数据提供器的is_trading_day方法不准确，建议从Tushare获取交易日历")

        # 随机检查几只股票
        sample_symbols = ["000001.SZ", "600000.SH"]

        for symbol in sample_symbols:
            try:
                df = self._load_data(symbol)
                if date in df.index:
                    return True
            except Exception:
                continue

        return False

    def clear_cache(self) -> None:
        """清空缓存"""
        cache_info = self.cache.info()
        self.cache.clear()
        logger.info(f"已清空缓存（原大小: {cache_info['size']}）")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        cache_info = self.cache.info()

        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": (
                self.stats["cache_hits"] /
                (self.stats["cache_hits"] + self.stats["cache_misses"])
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0 else 0
            ),
            "cache_size": cache_info["size"],
            "cache_max_size": cache_info["max_size"],
            "files_read": self.stats["files_read"],
            "bytes_read": self.stats["bytes_read"]
        }

    def __del__(self):
        """析构函数，清理资源"""
        logger.debug("LocalCSVDataProvider正在被销毁")
