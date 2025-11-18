"""
数据提供器

提供统一的数据获取接口，支持多种数据源
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd


class DataProvider(ABC):
    """
    数据提供器抽象基类

    定义统一的数据获取接口，支持多种数据源实现
    """

    @abstractmethod
    def get_daily_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        获取日K线数据

        Args:
            symbol: 股票代码，如 '000001.SZ'
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame，包含以下列：
                - date: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
        """
        pass

    @abstractmethod
    def get_market_cap(
        self,
        symbols: List[str],
        date: datetime
    ) -> pd.Series:
        """
        获取市值数据

        Args:
            symbols: 股票代码列表
            date: 日期

        Returns:
            Series，index为symbol，value为总市值（元）
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
    def is_trading_day(
        self,
        date: datetime
    ) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期

        Returns:
            是否为交易日
        """
        pass


class LocalDataProvider(DataProvider):
    """
    本地数据提供器

    从本地CSV或Parquet文件加载数据
    """

    def __init__(self, data_dir: str):
        """
        初始化

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self._cache: Dict[str, pd.DataFrame] = {}

    def get_daily_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """从本地文件读取日K数据"""
        # 检查缓存
        if symbol in self._cache:
            df = self._cache[symbol]
        else:
            # 尝试加载CSV或Parquet
            file_path = f"{self.data_dir}/{symbol}.csv"
            try:
                df = pd.read_csv(file_path)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                self._cache[symbol] = df
            except FileNotFoundError:
                # 尝试Parquet格式
                try:
                    file_path = f"{self.data_dir}/{symbol}.parquet"
                    df = pd.read_parquet(file_path)
                    self._cache[symbol] = df
                except FileNotFoundError:
                    raise ValueError(f"未找到股票 {symbol} 的数据文件")

        # 筛选日期范围
        mask = (df.index >= start_date) & (df.index <= end_date)
        return df.loc[mask].copy()

    def get_market_cap(
        self,
        symbols: List[str],
        date: datetime
    ) -> pd.Series:
        """从本地文件读取市值数据"""
        file_path = f"{self.data_dir}/market_cap.csv"
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])

        # 筛选日期和股票
        df_date = df[df['date'] == date]
        df_filtered = df_date[df_date['symbol'].isin(symbols)]

        return pd.Series(
            data=df_filtered['total_market_cap'].values,
            index=df_filtered['symbol'].values
        )

    def get_stock_universe(
        self,
        date: datetime,
        market: str = "A_SHARE"
    ) -> List[str]:
        """从本地文件读取股票池"""
        file_path = f"{self.data_dir}/stock_universe.csv"
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])

        # 筛选日期和市场
        df_filtered = df[
            (df['date'] == date) &
            (df['market'] == market)
        ]

        return df_filtered['symbol'].tolist()

    def is_trading_day(
        self,
        date: datetime
    ) -> bool:
        """判断是否为交易日"""
        # 从交易日历文件中读取
        file_path = f"{self.data_dir}/trading_calendar.csv"
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])

        df_day = df[df['date'] == date]
        if df_day.empty:
            return False

        return df_day['is_trading_day'].iloc[0]


class TushareDataProvider(DataProvider):
    """
    Tushare数据提供器

    从Tushare获取数据（需要Token）
    文档：https://tushare.pro/document/2
    """

    def __init__(self, token: str):
        """
        初始化

        Args:
            token: Tushare Token

        Usage:
            provider = TushareDataProvider(token="your_token_here")
            df = provider.get_daily_bars("000001.SZ", start_date, end_date)
        """
        self.token = token
        self._api = None

        try:
            import tushare as ts
            self._api = ts.pro_api(token)
        except ImportError:
            raise ImportError("请安装tushare: pip install tushare")

    def get_daily_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """从Tushare获取日K数据"""
        if self._api is None:
            raise RuntimeError("Tushare API未初始化")

        # 转换日期格式
        start = start_date.strftime("%Y%m%d")
        end = end_date.strftime("%Y%m%d")

        # 转换股票代码格式
        ts_code = self._convert_symbol(symbol)

        # 查询数据
        df = self._api.daily(
            ts_code=ts_code,
            start_date=start,
            end_date=end
        )

        if df.empty:
            return pd.DataFrame()

        # 数据清洗
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.rename(columns={
            'trade_date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'vol': 'volume'
        })

        df = df.sort_values('date').set_index('date')
        return df[['open', 'high', 'low', 'close', 'volume']]

    def get_market_cap(
        self,
        symbols: List[str],
        date: datetime
    ) -> pd.Series:
        """从Tushare获取市值数据"""
        if self._api is None:
            raise RuntimeError("Tushare API未初始化")

        trade_date = date.strftime("%Y%m%d")

        # 转换股票代码
        ts_codes = [self._convert_symbol(s) for s in symbols]

        # 查询数据
        df = self._api.daily_basic(
            ts_code=','.join(ts_codes),
            trade_date=trade_date,
            fields='ts_code,circ_mv'  # 流通市值（万元）
        )

        if df.empty:
            return pd.Series(dtype=float)

        # 转换为标准格式
        df['symbol'] = df['ts_code'].apply(self._convert_reverse)
        df['total_market_cap'] = df['circ_mv'] * 10000  # 转换为元

        return pd.Series(
            data=df['total_market_cap'].values,
            index=df['symbol'].values
        )

    def get_stock_universe(
        self,
        date: datetime,
        market: str = "A_SHARE"
    ) -> List[str]:
        """从Tushare获取股票池"""
        if self._api is None:
            raise RuntimeError("Tushare API未初始化")

        trade_date = date.strftime("%Y%m%d")

        # 查询当日所有A股
        df = self._api.daily_basic(
            trade_date=trade_date,
            fields='ts_code'
        )

        if df.empty:
            return []

        # 转换代码格式
        symbols = df['ts_code'].apply(self._convert_reverse).tolist()

        return symbols

    def is_trading_day(
        self,
        date: datetime
    ) -> bool:
        """判断是否为交易日"""
        if self._api is None:
            raise RuntimeError("Tushare API未初始化")

        trade_date = date.strftime("%Y%m%d")

        # 查询交易日历
        df = self._api.trade_cal(
            start_date=trade_date,
            end_date=trade_date
        )

        if df.empty:
            return False

        return df['is_open'].iloc[0] == 1

    @staticmethod
    def _convert_symbol(symbol: str) -> str:
        """转换股票代码格式"""
        # "000001.SZ" -> "000001.SZ"
        # "600000.SH" -> "600000.SH"
        return symbol

    @staticmethod
    def _convert_reverse(ts_code: str) -> str:
        """反向转换"""
        # "000001.SZ" -> "000001.SZ"
        # "600000.SH" -> "600000.SH"
        return ts_code


class AkshareDataProvider(DataProvider):
    """
    Akshare数据提供器

    从Akshare获取数据（不需要Token，但稳定性较差）
    文档：https://akshare.readthedocs.io/
    """

    def __init__(self):
        """初始化"""
        try:
            import akshare as ak
            self._ak = ak
        except ImportError:
            raise ImportError("请安装akshare: pip install akshare")

    def get_daily_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """从Akshare获取日K数据"""
        # 转换股票代码格式
        # Akshare使用形如 "sz000001" 或 "sh600000"
        if symbol.endswith('.SZ'):
            ak_symbol = f"sz{symbol[:-3]}"
        elif symbol.endswith('.SH'):
            ak_symbol = f"sh{symbol[:-3]}"
        else:
            ak_symbol = symbol

        # 获取数据
        df = self._ak.stock_zh_a_hist(
            symbol=ak_symbol,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            period="daily",
            adjust="qfq"  # 前复权
        )

        if df.empty:
            return pd.DataFrame()

        # 数据清洗
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume'
        })

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        return df[['open', 'high', 'low', 'close', 'volume']]

    def get_market_cap(
        self,
        symbols: List[str],
        date: datetime
    ) -> pd.Series:
        """从Akshare获取市值数据"""
        # Akshare的市值接口不稳定，建议使用Tushare
        raise NotImplementedError("Akshare暂不支持批量获取市值，建议使用TushareDataProvider")

    def get_stock_universe(
        self,
        date: datetime,
        market: str = "A_SHARE"
    ) -> List[str]:
        """从Akshare获取股票池"""
        # 获取A股列表
        df = self._ak.stock_info_a_code_name()

        if df.empty:
            return []

        # 转换代码格式
        symbols = df['code'].apply(
            lambda x: f"{x}.SH" if x.startswith('6') else f"{x}.SZ"
        ).tolist()

        return symbols

    def is_trading_day(
        self,
        date: datetime
    ) -> bool:
        """判断是否为交易日"""
        try:
            # Akshare的交易日历接口
            df = self._ak.tool_trade_date_hist_sina()
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            return date in df['trade_date'].values
        except:
            # 如果失败，默认周一到周五为交易日
            return date.weekday() < 5
