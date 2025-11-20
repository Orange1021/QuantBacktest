"""
数据源抽象基类
定义所有数据源必须遵守的契约接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Generator
from datetime import datetime

from ..schema.bar import BarData
from ..schema.tick import TickData
from ..schema.fundamental import FundamentalData


class BaseDataSource(ABC):
    """
    数据源抽象基类
    所有数据源实现必须继承此类并实现相应方法
    """
    
    @abstractmethod
    def load_bar_data(self, 
                      symbol: str, 
                      exchange: str, 
                      start_date: datetime, 
                      end_date: datetime) -> List[BarData]:
        """
        加载指定时间段的历史K线数据
        
        Args:
            symbol: 股票代码 (e.g. "000001")
            exchange: 交易所代码 (e.g. "SZSE")
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            List[BarData]: 必须返回标准的 BarData 对象列表，按时间升序排列
        """
        pass

    @abstractmethod
    def load_tick_data(self, 
                       symbol: str, 
                       exchange: str, 
                       start_date: datetime, 
                       end_date: datetime) -> List[TickData]:
        """
        加载指定时间段的历史Tick数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所代码
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            List[TickData]: Tick数据对象列表，按时间升序排列
        """
        pass

    @abstractmethod
    def load_fundamental_data(self, 
                             symbol: str, 
                             exchange: str, 
                             start_date: datetime, 
                             end_date: datetime) -> List[FundamentalData]:
        """
        加载指定时间段的历史财务数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所代码
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            List[FundamentalData]: 财务数据对象列表，按时间升序排列
        """
        pass

    def stream_bar_data(self, 
                       symbol: str, 
                       exchange: str, 
                       start_date: datetime, 
                       end_date: datetime) -> Generator[BarData, None, None]:
        """
        流式加载K线数据（生成器模式）
        默认实现基于load_bar_data，子类可以重写以优化内存使用
        
        Args:
            symbol: 股票代码
            exchange: 交易所代码
            start_date: 开始时间
            end_date: 结束时间
            
        Yields:
            BarData: 逐条生成K线数据
        """
        bar_data_list = self.load_bar_data(symbol, exchange, start_date, end_date)
        for bar in bar_data_list:
            yield bar