"""
本地CSV文件加载器
专门处理包含中文表头、特定日期格式的A股数据
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

from .base_source import BaseDataSource
from ..schema.bar import BarData
from ..schema.tick import TickData
from ..schema.fundamental import FundamentalData
from ..schema.constant import Exchange, Interval


class LocalCSVLoader(BaseDataSource):
    """
    本地CSV文件加载器
    专门处理包含中文表头、特定日期格式的A股数据
    """

    def __init__(self, root_path: str):
        """
        构造函数
        
        Args:
            root_path: CSV文件的根目录 (e.g. "C:/Users/123/A股数据/个股数据/")
        """
        self.root_path = Path(root_path)
        self.logger = logging.getLogger(__name__)
        
        # 列名映射表：CSV中文列名 -> BarData属性名
        self.column_mapping = {
            '交易日期': 'date',
            '开盘价': 'open_price',
            '最高价': 'high_price', 
            '最低价': 'low_price',
            '收盘价': 'close_price',
            '成交量(手)': 'volume',
            '成交额(千元)': 'turnover',
            '今日涨停价': 'limit_up',
            '今日跌停价': 'limit_down',
            '复权因子': 'adj_factor',
            '总市值(万元)': 'total_mv',
            '市盈率': 'pe_ttm',
            '换手率(%)': 'turnover_rate',
            '昨收价': 'pre_close'
        }

    def _get_file_path(self, symbol: str) -> Path:
        """
        辅助方法：根据symbol拼接完整文件路径
        
        Args:
            symbol: "000001"
        Returns:
            Path对象 (e.g. .../000001.csv)
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        file_path = self.root_path / f"{symbol}.csv"
        if not file_path.exists():
            raise FileNotFoundError(
                f"数据文件不存在: {file_path}\n"
                f"请检查以下配置:\n"
                f"1. 股票代码 {symbol} 是否正确\n"
                f"2. CSV文件是否存在于目录 {self.root_path}\n"
                f"3. 检查 .env 配置中的 CSV_ROOT_PATH 路径是否正确\n"
                f"4. 确认文件没有被其他程序（如Excel）占用锁定"
            )
        return file_path

    def _standardize_exchange(self, exchange: str) -> str:
        """
        标准化交易所代码格式
        
        统一转换为 Backtrader/VeighNa 标准格式：
        - SZSE -> SZ (深圳证券交易所)
        - SSE -> SH (上海证券交易所)
        - 其他保持不变
        
        Args:
            exchange: 原始交易所代码
            
        Returns:
            标准化后的交易所代码
        """
        exchange_mapping = {
            'SZSE': 'SZ',    # 深圳证券交易所
            'SSE': 'SH',     # 上海证券交易所
            'BSE': 'BJ',     # 北京证券交易所
        }
        
        standardized = exchange_mapping.get(exchange, exchange)
        
        if standardized != exchange:
            self.logger.debug(f"交易所代码标准化: {exchange} -> {standardized}")
        
        return standardized

    def _parse_datetime(self, date_str) -> datetime:
        """
        辅助方法：解析日期列

        Logic:
            将"20251114" (str, int或float) 转换为datetime(2025, 11, 14)
            处理NaN值的情况
        """
        try:
            # 检查是否为NaN（float类型的NaN或pandas的NaT/NaN）
            if pd.isna(date_str):
                raise ValueError(f"日期值为NaN: {date_str}")

            # 处理int和float类型（如20251114或20251114.0）
            if isinstance(date_str, (int, float)):
                # 确保不是NaN后再转换
                date_str = str(int(date_str))  # 先转int去掉小数，再转str

            if isinstance(date_str, str) and len(date_str) == 8:
                return datetime.strptime(date_str, "%Y%m%d")
            else:
                # 尝试其他可能的日期格式
                return pd.to_datetime(date_str).to_pydatetime()
        except Exception as e:
            self.logger.error(f"日期解析失败: {date_str}, 错误: {e}")
            raise ValueError(f"无法解析日期: {date_str}")

    def _map_row_to_bar_data(self, row: pd.Series, symbol: str, exchange: Exchange) -> BarData:
        """
        将CSV行数据映射为BarData对象
        
        Args:
            row: pandas Series对象，包含一行数据
            symbol: 股票代码
            exchange: 交易所枚举
            
        Returns:
            BarData对象
        """
        # 创建extra字典用于存放非标准字段
        extra: Dict[str, Any] = {}
        
        # 标准化股票代码格式：代码.交易所
        standardized_symbol = f"{symbol}.{exchange.value}"
        
        # 提取基础OHLCV数据
        bar_data = BarData(
            gateway_name="LocalCSV",
            symbol=standardized_symbol,
            exchange=exchange,
            datetime=self._parse_datetime(row['交易日期']),
            interval=Interval.DAILY,
            open_price=float(row['开盘价']),
            high_price=float(row['最高价']),
            low_price=float(row['最低价']),
            close_price=float(row['收盘价']),
            # 成交量从"手"转换为"股"（1手=100股）
            volume=float(row['成交量(手)']) * 100,
            # 成交额从"千元"转换为"元"
            turnover=float(row['成交额(千元)']) * 1000,
            limit_up=float(row['今日涨停价']),
            limit_down=float(row['今日跌停价']),
            pre_close=float(row.get('昨收价', 0)),
            extra=extra
        )
        
        # 将其他字段存入extra字典
        if '复权因子' in row:
            extra['adj_factor'] = float(row['复权因子'])
        
        if '总市值(万元)' in row:
            extra['total_mv'] = float(row['总市值(万元)']) * 10000  # 转换为元
            
        if '市盈率' in row:
            extra['pe_ttm'] = float(row['市盈率'])
            
        if '换手率(%)' in row:
            extra['turnover_rate'] = float(row['换手率(%)'])
        
        return bar_data

    def filter_existing_symbols(self, symbol_list: List[str]) -> List[str]:
        """
        [新增方法] 快速过滤掉本地没有CSV文件的股票代码
        
        Args:
            symbol_list: 股票代码列表，如 ['000001.SZ', 'DELISTED.SH', '000002.SZ']
            
        Returns:
            过滤后的有效股票代码列表
        """
        valid_symbols = []
        missing_symbols = []
        
        for symbol in symbol_list:
            try:
                # 从 vt_symbol 中提取纯股票代码
                if '.' in symbol:
                    pure_symbol = symbol.split('.')[0]
                else:
                    pure_symbol = symbol
                
                # 构建文件路径
                file_path = self.root_path / f"{pure_symbol}.csv"
                
                if file_path.exists():
                    valid_symbols.append(symbol)
                else:
                    missing_symbols.append(symbol)
            except Exception as e:
                # 如果路径解析都报错（比如格式不对），也算缺失
                missing_symbols.append(symbol)
        
        if missing_symbols:
            self.logger.warning(f"本地缺失 {len(missing_symbols)} 只股票数据: {missing_symbols[:3]}...")
        
        return valid_symbols

    def load_bar_data(self, 
                      symbol: str, 
                      exchange: str, 
                      start_date: datetime, 
                      end_date: datetime) -> List[BarData]:
        """
        核心实现方法
        
        Steps:
            1. 调用_get_file_path获取路径
            2. 使用pandas读取文件
            3. 过滤：只保留start_date到end_date之间的行
            4. 映射：将中文列名转换为BarData的属性
            5. 单位转换：成交额(千元)->*1000, 成交量(手)->*100
            6. 返回BarData列表
        """
        try:
            # 获取文件路径
            file_path = self._get_file_path(symbol)
            
            # 读取CSV文件 - 添加文件锁定检测
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except PermissionError as e:
                raise PermissionError(
                    f"文件被占用，无法读取: {file_path}\n"
                    f"请检查以下情况:\n"
                    f"1. 文件是否被Excel、WPS等程序打开\n"
                    f"2. 文件是否被其他程序锁定\n"
                    f"3. 尝试关闭相关程序后重试"
                ) from e
            except pd.errors.EmptyDataError as e:
                raise ValueError(
                    f"CSV文件为空: {file_path}\n"
                    f"请检查:\n"
                    f"1. 文件是否包含数据\n"
                    f"2. 文件格式是否正确\n"
                    f"3. 文件是否损坏"
                ) from e
            except UnicodeDecodeError as e:
                raise ValueError(
                    f"CSV文件编码错误: {file_path}\n"
                    f"请检查:\n"
                    f"1. 文件编码是否为UTF-8\n"
                    f"2. 尝试用记事本打开并另存为UTF-8格式"
                ) from e
            
            # 检查必要的列是否存在
            required_columns = ['交易日期', '开盘价', '最高价', '最低价', '收盘价']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(
                    f"CSV文件缺少必要的列: {missing_columns}\n"
                    f"文件路径: {file_path}\n"
                    f"当前列名: {list(df.columns)}\n"
                    f"请确保CSV文件包含标准的A股数据列名"
                )

            # 过滤掉日期为NaN的行（避免解析错误）
            df_before = len(df)
            df = df.dropna(subset=['交易日期']).copy()
            df_after = len(df)
            if df_before != df_after:
                self.logger.warning(f"{symbol}: 过滤掉 {df_before - df_after} 行日期为NaN的数据")

            # 转换日期列
            df['datetime'] = df['交易日期'].apply(self._parse_datetime)
            
            # 过滤日期范围
            mask = (df['datetime'] >= start_date) & (df['datetime'] <= end_date)
            df_filtered = df[mask].copy()
            
            if df_filtered.empty:
                self.logger.warning(f"在指定日期范围内未找到数据: {symbol}, {start_date} - {end_date}")
                return []
            
            # 转换为BarData对象列表
            # 标准化交易所代码格式
            standardized_exchange = self._standardize_exchange(exchange)
            exchange_enum = Exchange(standardized_exchange)
            bar_data_list = []
            
            for _, row in df_filtered.iterrows():
                try:
                    bar_data = self._map_row_to_bar_data(row, symbol, exchange_enum)
                    bar_data_list.append(bar_data)
                except Exception as e:
                    self.logger.error(f"映射数据失败: {symbol}, 行数据: {row}, 错误: {e}")
                    continue
            
            # 按时间升序排列
            bar_data_list.sort(key=lambda x: x.datetime)
            
            self.logger.info(f"成功加载K线数据: {symbol}, 共 {len(bar_data_list)} 条记录")
            return bar_data_list
            
        except FileNotFoundError as e:
            # 重新抛出更友好的FileNotFoundError，已经在_get_file_path中格式化
            raise
        except (PermissionError, ValueError, UnicodeDecodeError) as e:
            # 重新抛出已经格式化的异常
            raise
        except Exception as e:
            # 捕获其他未预期的异常
            self.logger.error(f"加载K线数据失败: {symbol}, 错误: {e}")
            raise ValueError(
                f"加载 {symbol} 的CSV数据时发生未知错误\n"
                f"错误信息: {str(e)}\n"
                f"请检查:\n"
                f"1. 文件路径是否正确: {self.root_path / f'{symbol}.csv'}\n"
                f"2. 文件格式是否符合标准\n"
                f"3. 查看详细日志获取更多信息"
            ) from e

    def load_tick_data(self, 
                       symbol: str, 
                       exchange: str, 
                       start_date: datetime, 
                       end_date: datetime) -> List[TickData]:
        """
        加载Tick数据（本地CSV暂不支持）
        """
        raise NotImplementedError("本地CSV加载器暂不支持Tick数据")

    def load_fundamental_data(self, 
                             symbol: str, 
                             exchange: str, 
                             start_date: datetime, 
                             end_date: datetime) -> List[FundamentalData]:
        """
        加载财务数据（本地CSV暂不支持）
        """
        raise NotImplementedError("本地CSV加载器暂不支持财务数据")