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
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        return file_path

    def _parse_datetime(self, date_str) -> datetime:
        """
        辅助方法：解析日期列
        
        Logic:
            将"20251114" (str或int) 转换为datetime(2025, 11, 14)
        """
        try:
            if isinstance(date_str, int):
                date_str = str(date_str)
            if len(date_str) == 8:
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
        
        # 提取基础OHLCV数据
        bar_data = BarData(
            gateway_name="LocalCSV",
            symbol=symbol,
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
            
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 检查必要的列是否存在
            required_columns = ['交易日期', '开盘价', '最高价', '最低价', '收盘价']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"CSV文件缺少必要的列: {missing_columns}")
            
            # 转换日期列
            df['datetime'] = df['交易日期'].apply(self._parse_datetime)
            
            # 过滤日期范围
            mask = (df['datetime'] >= start_date) & (df['datetime'] <= end_date)
            df_filtered = df[mask].copy()
            
            if df_filtered.empty:
                self.logger.warning(f"在指定日期范围内未找到数据: {symbol}, {start_date} - {end_date}")
                return []
            
            # 转换为BarData对象列表
            exchange_enum = Exchange(exchange)
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
            
        except Exception as e:
            self.logger.error(f"加载K线数据失败: {symbol}, 错误: {e}")
            raise

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