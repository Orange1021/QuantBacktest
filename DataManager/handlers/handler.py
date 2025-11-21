"""
数据处理器定义
回测引擎的"发牌员"，负责将静态数据转换为流动的事件流
"""

from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Optional
from datetime import datetime
import logging

try:
    from DataManager.schema.bar import BarData
    from DataManager.sources.base_source import BaseDataSource
    from Infrastructure.events import MarketEvent
except ImportError:
    from schema.bar import BarData
    from sources.base_source import BaseDataSource
    from Infrastructure.events import MarketEvent


class BaseDataHandler(ABC):
    """
    数据处理器抽象基类
    
    职责：定义数据处理器对外的标准接口，确保策略层调用数据的方式统一
    """

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        获取指定股票在"当前回测时间点"的最新一根 K 线
        用途：策略判断当前价格（如 bar.close_price）时使用
        """
        pass

    @abstractmethod
    def get_latest_bars(self, symbol: str, n: int = 1) -> List[BarData]:
        """
        获取指定股票截止到"当前回测时间点"的最近 N 根 K 线
        用途：策略计算技术指标（如计算 MA5 需要最近 5 根 Bar）
        """
        pass

    @abstractmethod
    def update_bars(self) -> Generator:
        """
        驱动系统时间流动的生成器
        行为：每次调用 next()，时间前进一步，并返回一个新的 MarketEvent
        """
        pass


class BacktestDataHandler(BaseDataHandler):
    """
    专用于历史回测，处理多只股票的时间对齐，维护"最新数据视图"以防止未来函数
    """

    def __init__(self, 
                 loader: BaseDataSource, 
                 symbol_list: List[str], 
                 start_date: datetime, 
                 end_date: datetime):
        """
        初始化回测数据处理器
        
        Args:
            loader: 数据加载器实例（如 LocalCSVLoader）
            symbol_list: 需要回测的股票代码列表
            start_date: 回测起止时间
            end_date: 回测结束时间
        """
        self.loader = loader
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date
        
        # 全量数据缓存：在初始化时一次性把所有 CSV 数据读入这里
        self._data_cache: Dict[str, List[BarData]] = {}
        
        # 统一时间轴：所有股票时间戳的并集，并按升序排列（用于解决停牌导致的时间错位）
        self._timeline: List[datetime] = []
        
        # 当前视图缓存：随着时间推进，把 _data_cache 里的数据一根根搬运到这里
        # 策略只能查这个缓存
        self._latest_data: Dict[str, List[BarData]] = {}
        
        # 当前时间指针
        self.current_time_index = 0
        
        # 初始化数据
        self._load_all_data()

    def _load_all_data(self):
        """
        私有方法：加载所有数据
        1. 遍历 symbol_list，调用 loader.load_bar_data()
        2. 将加载结果存入 _data_cache
        3. 同时收集所有 BarData 的时间戳，去重、排序，生成 _timeline
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"开始加载数据，股票数量: {len(self.symbol_list)}")
        
        all_timestamps = set()
        
        for symbol in self.symbol_list:
            try:
                # 从symbol中提取exchange
                if '.' in symbol:
                    symbol_code, exchange = symbol.split('.')
                    # 转换交易所代码格式
                    if exchange in ['SH', 'SSE']:
                        exchange = 'SSE'
                    elif exchange in ['SZ', 'SZSE']:
                        exchange = 'SZSE'
                    elif exchange in ['BJ', 'BSE']:
                        exchange = 'BSE'
                    else:
                        exchange = 'SZSE'  # 默认
                else:
                    symbol_code = symbol
                    # 默认交易所逻辑
                    if symbol_code.startswith('00') or symbol_code.startswith('30'):
                        exchange = 'SZSE'
                    elif symbol_code.startswith('60') or symbol_code.startswith('68'):
                        exchange = 'SSE'
                    else:
                        exchange = 'SZSE'  # 默认
                
                # 加载数据
                bars = self.loader.load_bar_data(
                    symbol_code, exchange, self.start_date, self.end_date
                )
                
                if bars:
                    self._data_cache[symbol] = bars
                    self._latest_data[symbol] = []  # 初始化当前视图缓存
                    
                    # 收集时间戳
                    for bar in bars:
                        # 只保留日期部分，忽略时间部分（日线数据）
                        bar_date = datetime.combine(bar.datetime.date(), datetime.min.time())
                        all_timestamps.add(bar_date)
                    
                    self.logger.info(f"成功加载 {symbol}: {len(bars)} 条数据")
                else:
                    self.logger.warning(f"未找到 {symbol} 的数据")
                    self._latest_data[symbol] = []  # 仍然初始化空列表
                    
            except Exception as e:
                self.logger.error(f"加载 {symbol} 数据失败: {e}")
                self._latest_data[symbol] = []  # 出错时仍然初始化空列表
                continue

        # 生成统一时间轴
        self._timeline = sorted(list(all_timestamps))
        
        if not self._data_cache:
            raise ValueError("没有成功加载任何数据")
        
        self.logger.info(f"数据加载完成，时间轴包含 {len(self._timeline)} 个交易日")

    def update_bars(self) -> Generator:
        """
        核心逻辑：生成器
        使用 yield 实现生成器
        外层循环：遍历 _timeline 中的每一个 timestamp
        内层循环：检查每个 symbol 在 _data_cache 中是否存在该 timestamp 的数据
            如果有：
                1. 将该 BarData 追加到 _latest_data[symbol] 列表末尾
                2. yield MarketEvent(bar) (向外抛出事件)
            如果没有（停牌）：跳过，不产生事件
        """
        self.logger.info("开始推送行情事件")
        
        for i, timestamp in enumerate(self._timeline):
            # 更新当前时间指针
            self.current_time_index = i + 1
            
            # 内层循环：检查每个股票在该时间点是否有数据
            for symbol in self.symbol_list:
                if symbol not in self._data_cache:
                    continue  # 跳过没有数据的股票
                
                # 在该股票的数据中查找当前时间点的数据
                target_bar = None
                for bar in self._data_cache[symbol]:
                    bar_date = datetime.combine(bar.datetime.date(), datetime.min.time())
                    if bar_date == timestamp:
                        target_bar = bar
                        break
                
                if target_bar:
                    # 将该 BarData 追加到 _latest_data[symbol] 列表末尾
                    self._latest_data[symbol].append(target_bar)
                    
                    # 向外抛出事件
                    market_event = MarketEvent(bar=target_bar)
                    yield market_event
                # 如果没有数据（停牌），跳过，不产生事件
        
        self.logger.info("行情事件推送完成")

    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        读取 self._latest_data[symbol] 的最后一个元素
        如果列表为空，返回 None
        """
        if symbol not in self._latest_data:
            return None
        
        if not self._latest_data[symbol]:  # 列表为空
            return None
        
        return self._latest_data[symbol][-1]

    def get_latest_bars(self, symbol: str, n: int = 1) -> List[BarData]:
        """
        读取 self._latest_data[symbol] 的最后 n 个元素
        返回列表切片
        """
        if symbol not in self._latest_data:
            return []
        
        if not self._latest_data[symbol]:  # 列表为空
            return []
        
        # 返回最后n个元素
        return self._latest_data[symbol][-n:]
    
    def get_current_time(self) -> Optional[datetime]:
        """
        获取当前回测时间
        
        Returns:
            当前回测时间点，如果还没有开始处理则返回None
        """
        if self.current_time_index > 0 and self.current_time_index <= len(self._timeline):
            return self._timeline[self.current_time_index - 1]
        return None