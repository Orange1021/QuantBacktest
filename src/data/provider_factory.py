"""

数据提供器工厂和代理



提供数据提供器的工厂模式实现和降级代理功能

支持配置驱动的数据获取和自动故障转移。





创建日期: 2025-01-18

"""



import os

import logging

from typing import Dict, List, Any, Optional, Union

from pathlib import Path

import pandas as pd



from .provider import DataProvider, LocalDataProvider, TushareDataProvider, AkshareDataProvider

from .local_csv_provider import LocalCSVDataProvider



# 配置日志

logger = logging.getLogger(__name__)





class DataProviderFactory:

    """

    数据提供器工厂



    根据配置创建和管理数据提供器。

    支持多种数据源（本地CSV、Tushare、Akshare）的灵活切换。



    Attributes:

        config: 配置字典

        providers: 已创建的数据提供器字典



    Example:

        >>> factory = DataProviderFactory(config)

        >>> provider = factory.get_primary_provider()

        >>> df = provider.get_daily_bars("000001.SZ", start_date, end_date)

    """



    def __init__(self, config: Dict[str, Any]):

        """

        初始化数据提供器工厂



        Args:

            config: 配置字典，格式参考 configs/data/source.yaml



        Raises:

            ValueError: 如果配置格式错误

            TypeError: 如果config不是字典

        """

        if not isinstance(config, dict):

            raise TypeError(f"config必须是字典，实际类型: {type(config)}")



        self.config = config

        self.providers: Dict[str, DataProvider] = {}

        self.data_dir = None  # 数据根目录（用于缓存、日志等）



        # 设置默认数据目录

        if 'local_csv' in config and 'data_dir' in config['local_csv']:

            self.data_dir = Path(config['local_csv']['data_dir'])

        else:

            # 如果没有配置，使用项目下的data目录

            self.data_dir = Path(__file__).parent.parent.parent / 'data'



        self.data_dir.mkdir(parents=True, exist_ok=True)



        logger.info("=" * 60)

        logger.info("初始化数据提供器工厂")

        logger.info("=" * 60)



        # 初始化所有配置的提供器

        self._setup_providers()



    def _setup_providers(self) -> None:

        """

        初始化所有配置的数据提供器



        根据配置创建对应的数据提供器实例。

        """

        # 本地CSV提供器

        if self._is_provider_enabled('local_csv'):

            try:

                csv_config = self.config['data']['local_csv']

                data_dir = csv_config.get('data_dir')



                if not data_dir:

                    raise ValueError("local_csv.data_dir 未配置")



                if not Path(data_dir).exists():

                    logger.warning(f"本地数据目录不存在: {data_dir}")

                    logger.warning("本地CSV数据源将被禁用，请检查配置")

                else:

                    cache_config = csv_config.get('cache', {})



                    self.providers['local_csv'] = LocalCSVDataProvider(

                        data_dir=data_dir,

                        cache_size=cache_config.get('max_size', 100),

                        validate_tscode=csv_config.get('validate_tscode', True),

                        filter_future=csv_config.get('filter_future', True),

                        file_format=csv_config.get('file_format', 'csv')

                    )



                    logger.info("✓ 本地CSV提供器已创建")

                    logger.info(f"  数据目录: {data_dir}")

                    logger.info(f"  缓存大小: {cache_config.get('max_size', 100)}")



            except Exception as e:

                logger.error(f"× 本地CSV提供器创建失败: {e}")



        # Tushare提供器

        if self._is_provider_enabled('tushare'):

            try:

                ts_config = self.config['data']['tushare']

                token = ts_config.get('token', '')



                # 支持环境变量

                if not token:

                    token = os.environ.get('TUSHARE_TOKEN', '')



                if not token:

                    logger.warning("Tushare token未配置，将尝试匿名访问")

                    logger.warning("建议设置 TUSHARE_TOKEN 环境变量或配置文件")



                self.providers['tushare'] = TushareDataProvider(token=token)



                logger.info("✓ Tushare提供器已创建")



            except Exception as e:

                logger.error(f"× Tushare提供器创建失败: {e}")



        # Akshare提供器

        if self._is_provider_enabled('akshare'):

            try:

                self.providers['akshare'] = AkshareDataProvider()

                logger.info("✓ Akshare提供器已创建")

            except Exception as e:

                logger.error(f"× Akshare提供器创建失败: {e}")



        logger.info("=" * 60)

        logger.info(f"已创建的数据源数量: {len(self.providers)}")

        logger.info("=" * 60)



        # 记录统计信息

        self._log_summary()



    def _is_provider_enabled(self, provider_name: str) -> bool:

        """

        检查数据源是否启用



        Args:

            provider_name: 数据源名称



        Returns:

            是否启用

        """

        return (

            provider_name in self.config.get('data', {}) and

            self.config['data'][provider_name].get('enabled', True)

        )



    def get_primary_provider(self) -> DataProvider:

        """

        获取主数据源



        Returns:

            主数据提供器实例



        Raises:

            ValueError: 如果主数据源未配置

            RuntimeError: 如果主数据源创建失败

        """

        primary_name = self.config.get('data', {}).get('primary_provider', '')



        if not primary_name:

            raise ValueError("未配置主数据源 primary_provider")



        if primary_name not in self.providers:

            raise RuntimeError(

                f"主数据源不可用: {primary_name}\n"

                f"可用的数据源: {list(self.providers.keys())}"

            )



        logger.info(f"使用主数据源: {primary_name}")



        return self.providers[primary_name]



    def get_provider(self, name: str) -> Optional[DataProvider]:

        """

        获取指定名称的数据源



        Args:

            name: 数据源名称



        Returns:

            数据提供器实例，如果不存在返回None

        """

        return self.providers.get(name)



    def get_fallback_chain(self) -> List[str]:

        """

        获取降级链



        Returns:

            数据源名称列表

        """

        return self.config.get('data', {}).get('fallback_chain', [])



    def create_proxy(self) -> 'DataProviderProxy':

        """

        创建数据代理（支持自动降级）



        返回一个包装器，自动处理降级逻辑。

        这是推荐的使用方式。



        Returns:

            降级代理实例



        Example:

            >>> factory = DataProviderFactory(config)

            >>> proxy = factory.create_proxy()

            >>> df = proxy.get_daily_bars("000001.SZ", start_date, end_date)

        """

        try:

            primary = self.get_primary_provider()

        except Exception as e:

            logger.error(f"无法创建代理：{e}")

            raise



        fallback_names = self.get_fallback_chain()

        fallbacks = []



        for name in fallback_names:

            if name == self.config.get('data', {}).get('primary_provider'):

                continue  # 跳过主数据源



            provider = self.get_provider(name)

            if provider:

                fallbacks.append(provider)

            else:

                logger.warning(f"降级链中的数据源不可用: {name}")



        auto_fallback = self.config.get('data', {}).get('auto_fallback', True)



        logger.info("=" * 60)

        logger.info("创建数据代理")

        logger.info(f"主数据源: {self.config.get('primary_provider')}")

        logger.info(f"降级链: {len(fallbacks)} 个备用源")

        logger.info(f"自动降级: {'启用' if auto_fallback else '禁用'}")

        logger.info("=" * 60)



        return DataProviderProxy(

            primary_provider=primary,

            fallback_providers=fallbacks,

            auto_fallback=auto_fallback

        )



    def list_providers(self) -> Dict[str, Any]:

        """

        列出所有可用的数据源



        Returns:

            数据源信息字典

        """

        return {

            name: {

                "type": provider.__class__.__name__,

                "module": provider.__class__.__module__

            }

            for name, provider in self.providers.items()

        }



    def _log_summary(self) -> None:

        """记录汇总信息"""
        if not self.providers:

            logger.error("× 没有可用的数据源！")

            logger.error("请检查配置文件和环境变量")

            return



        logger.info("可用数据源:")

        for name, provider in self.providers.items():

            logger.info(f"  - {name}: {provider.__class__.__name__}")





class DataProviderProxy(DataProvider):

    """

    数据提供器代理（降级代理）



    包装真实的数据提供器，实现降级和重试逻辑。

    这是推荐使用方式，提供高可用性保障。



    Attributes:

        primary: 主数据提供器

        fallbacks: 备用数据提供器列表（按优先级排序）

        auto_fallback: 是否启用自动降级



    Example:

        >>> proxy = DataProviderProxy(

        ...     primary_provider=LocalCSVDataProvider(...),

        ...     fallback_providers=[TushareDataProvider(...)]

        ... )

        >>>

        >>> # 自动降级：如果本地失败，自动尝试Tushare

        >>> df = proxy.get_daily_bars("000001.SZ", start_date, end_date)

    """



    def __init__(

        self,

        primary_provider: DataProvider,

        fallback_providers: List[DataProvider],

        auto_fallback: bool = True

    ):

        """

        初始化降级代理



        Args:

            primary_provider: 主数据提供器

            fallback_providers: 备用数据提供器列表（按优先级排序）

            auto_fallback: 是否启用自动降级，默认True



        Raises:

            TypeError: 如果参数类型错误

        """

        if not isinstance(primary_provider, DataProvider):

            raise TypeError("primary_provider必须是DataProvider实例")



        if not isinstance(fallback_providers, list):

            raise TypeError("fallback_providers必须是列表")



        self.primary = primary_provider

        self.fallbacks = fallback_providers

        self.auto_fallback = auto_fallback



        # 降级日志文件

        self.fallback_log_file = Path(__file__).parent.parent.parent / 'data' / 'fallback_log.txt'

        self.fallback_log_file.parent.mkdir(parents=True, exist_ok=True)



        logger.debug("初始化DataProviderProxy")

        logger.debug(f"主数据源: {primary_provider.__class__.__name__}")

        logger.debug(f"备用数据源数量: {len(fallback_providers)}")



    def _try_get_data(self, method_name: str, *args, **kwargs):

        """

        尝试从所有数据源获取数据（内部方法）



        Args:

            method_name: 方法名称（如'get_daily_bars'）

            *args: 位置参数

            **kwargs: 关键字参数



        Returns:

            数据结果



        Raises:

            RuntimeError: 所有数据源都失败

        """

        # 尝试主数据源

        try:

            method = getattr(self.primary, method_name)

            result = method(*args, **kwargs)

            logger.debug(f"主数据源成功: {self.primary.__class__.__name__}.{method_name}")

            return result



        except Exception as e:

            logger.warning(f"主数据源失败: {self.primary.__class__.__name__}.{method_name}")

            logger.warning(f"错误信息: {str(e)[:100]}")



            if not self.auto_fallback:

                raise



            # 准备降级日志信息

            symbol = args[0] if args else "unknown"

            self._log_fallback(

                symbol=symbol,

                method=method_name,

                from_provider=self.primary.__class__.__name__,

                reason=str(e)

            )



        # 尝试备用数据源

        if not self.fallbacks:

            logger.error("没有可用的备用数据源")

            raise RuntimeError("主数据源失败且无备用数据源")



        for i, fallback in enumerate(self.fallbacks, 1):

            try:

                method = getattr(fallback, method_name)

                result = method(*args, **kwargs)



                logger.info(f"成功降级到备用数据源 ({i}/{len(self.fallbacks)})")

                logger.info(f"数据源: {fallback.__class__.__name__}")



                self._log_fallback(

                    symbol=symbol,

                    method=method_name,

                    from_provider=fallback.__class__.__name__,

                    reason="SUCCESS",

                    success=True

                )



                return result



            except Exception as e2:

                logger.warning(f"备用数据源失败 ({i}/{len(self.fallbacks)})")

                logger.warning(f"数据源: {fallback.__class__.__name__}")

                logger.warning(f"错误: {str(e2)[:100]}")



                # 继续下一个备用源

                continue



        # 所有数据源都失败

        logger.error("所有数据源均失败")

        raise RuntimeError(

            f"所有数据源均失败: {self.primary.__class__.__name__}, "

            f"{[fb.__class__.__name__ for fb in self.fallbacks]}"

        )



    def get_daily_bars(

        self,

        symbol: str,

        start_date,

        end_date

    ) -> pd.DataFrame:

        """

        获取日K线数据（支持降级）



        Args:

            symbol: 股票代码

            start_date: 开始日期

            end_date: 结束日期



        Returns:

            K线数据DataFrame



        Raises:

            RuntimeError: 所有数据源都失败

        """

        return self._try_get_data('get_daily_bars', symbol, start_date, end_date)



    def get_market_cap(self, symbols: List[str], date) -> pd.Series:

        """

        获取市值数据（支持降级）



        Args:

            symbols: 股票代码列表

            date: 日期



        Returns:

            市值Series



        Raises:

            RuntimeError: 所有数据源都失败

        """

        return self._try_get_data('get_market_cap', symbols, date)



    def get_stock_universe(self, date, market: str = "A_SHARE") -> List[str]:

        """

        获取股票池（支持降级）



        Args:

            date: 日期

            market: 市场类型



        Returns:

            股票代码列表



        Raises:

            RuntimeError: 所有数据源都失败

        """

        return self._try_get_data('get_stock_universe', date, market)



    def is_trading_day(self, date) -> bool:

        """

        判断是否为交易日（支持降级）



        Args:

            date: 日期



        Returns:

            是否为交易日



        Raises:

            RuntimeError: 所有数据源都失败

        """

        return self._try_get_data('is_trading_day', date)



    def _log_fallback(

        self,

        symbol: str,

        method: str,

        from_provider: str,

        reason: str,

        success: bool = False

    ) -> None:

        """

        记录降级日志



        Args:

            symbol: 股票代码

            method: 方法名称

            from_provider: 数据源名称

            reason: 原因

            success: 是否成功

        """

        try:

            with open(self.fallback_log_file, 'a', encoding='utf-8') as f:

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                status = "SUCCESS" if success else "FAIL"

                f.write(f"[{timestamp}] [{status}] {symbol} | {method} | {from_provider} | {reason}\n")



        except Exception as e:

            logger.error(f"记录降级日志失败: {e}")



    def get_fallback_stats(self) -> Dict[str, Any]:

        """

        获取降级统计信息



        Returns:

            统计信息字典

        """

        if not self.fallback_log_file.exists():

            return {"total": 0, "success": 0, "fail": 0, "log_file": str(self.fallback_log_file)}



        try:

            with open(self.fallback_log_file, 'r', encoding='utf-8') as f:

                lines = f.readlines()



            total = len(lines)

            success = sum(1 for line in lines if 'SUCCESS' in line)

            fail = total - success



            return {

                "total": total,

                "success": success,

                "fail": fail,

                "success_rate": success / total if total > 0 else 0,

                "log_file": str(self.fallback_log_file)

            }



        except Exception as e:

            logger.error(f"读取降级日志失败: {e}")

            return {"total": 0, "success": 0, "fail": 0, "error": str(e)}

