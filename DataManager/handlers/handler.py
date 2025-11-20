"""
数据处理器定义
回测引擎的"发牌员"，负责将静态数据转换为流动的事件流
"""

from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Optional, Iterator
from datetime import datetime
from collections import defaultdict
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
    
    职责：
    1. 管理数据加载器
    2. 维护"当前时间"的数据视图 (Look-ahead Bias Prevention)
    3. 响应引擎的update请求，推送下一个MarketEvent
    """

    def __init__(self, data_source: BaseDataSource):
        self.data_source = data_source
        # 存储所有加载的历史数据 {symbol: [BarData, BarData...]}
        self.symbol_data: Dict[str, List[BarData]] = {}
        # 记录当前回测游标 {symbol: current_index}
        self.current_index: Dict[str, int] = {}
        # 回测是否继续的标志
        self.continue_backtest: bool = True
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def update_bars(self) -> Generator[MarketEvent, None, None]:
        """
        核心生成器
        每次yield一个MarketEvent，代表时间往前走了一步
        """
        pass

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        获取当前时间点该股票的最新K线 (用于策略获取当前价格)
        """
        pass

    @abstractmethod
    def get_latest_bars(self, symbol: str, n: int = 1) -> List[BarData]:
        """
        获取截止到当前时间点的最近N根K线 (用于策略计算MA, KDJ等指标)
        注意：严禁获取"未来"的数据
        """
        pass


class BacktestDataHandler(BaseDataHandler):
    """
    具体实现类：用于回测的数据处理器
    """

    def __init__(self, 
                 data_source: BaseDataSource, 
                 symbol_list: List[str], 
                 start_date: datetime, 
                 end_date: datetime):
        """
        初始化回测数据处理器
        
        Args:
            data_source: 数据源实例
            symbol_list: 股票代码列表
            start_date: 回测开始日期
            end_date: 回测结束日期
        """
        super().__init__(data_source)
        
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date
        
        # 时间轴：所有交易日的排序集合
        self.timeline: List[datetime] = []
        
        # 按时间索引的数据 {datetime: {symbol: BarData}}
        self.time_indexed_data: Dict[datetime, Dict[str, BarData]] = defaultdict(dict)
        
        # 当前时间指针
        self.current_time_index: int = 0
        
        # 初始化数据
        self._load_data()
        self._build_timeline()
        self._align_data_by_time()

    def _load_data(self):
        """加载所有股票的数据"""
        self.logger.info(f"开始加载数据，股票数量: {len(self.symbol_list)}")
        
        for symbol in self.symbol_list:
            try:
                # 从symbol中提取exchange
                if '.' in symbol:
                    symbol_code, exchange = symbol.split('.')
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
                bars = self.data_source.load_bar_data(
                    symbol_code, exchange, self.start_date, self.end_date
                )
                
                if bars:
                    self.symbol_data[symbol] = bars
                    self.current_index[symbol] = 0
                    self.logger.info(f"成功加载 {symbol}: {len(bars)} 条数据")
                else:
                    self.logger.warning(f"未找到 {symbol} 的数据")
                    
            except Exception as e:
                self.logger.error(f"加载 {symbol} 数据失败: {e}")
                continue

        if not self.symbol_data:
            raise ValueError("没有成功加载任何数据")

    def _build_timeline(self):
        """构建时间轴，取所有股票交易日的并集"""
        all_dates = set()
        
        for symbol, bars in self.symbol_data.items():
            for bar in bars:
                all_dates.add(bar.datetime.date())
        
        # 转换为datetime并排序
        self.timeline = [datetime.combine(date, datetime.min.time()) 
                        for date in sorted(all_dates)]
        
        self.logger.info(f"构建时间轴完成，共 {len(self.timeline)} 个交易日")

    def _align_data_by_time(self):
        """按时间对齐数据，构建时间索引"""
        for symbol, bars in self.symbol_data.items():
            for bar in bars:
                bar_date = bar.datetime.date()
                bar_datetime = datetime.combine(bar_date, datetime.min.time())
                
                if bar_datetime in self.timeline:
                    self.time_indexed_data[bar_datetime][symbol] = bar
        
        self.logger.info("数据时间对齐完成")

    def update_bars(self) -> Generator[MarketEvent, None, None]:
        """
        核心生成器
        按时间顺序推送MarketEvent
        """
        self.logger.info("开始推送行情事件")
        
        while self.current_time_index < len(self.timeline):
            current_time = self.timeline[self.current_time_index]
            
            # 获取当前时间点的所有股票数据
            current_data = self.time_indexed_data.get(current_time, {})
            
            # 为每只股票生成MarketEvent
            for symbol, bar in current_data.items():
                # 更新当前索引
                self.current_index[symbol] = self.symbol_data[symbol].index(bar)
                
                # 生成MarketEvent
                market_event = MarketEvent(bar=bar)
                yield market_event
            
            # 移动到下一个时间点
            self.current_time_index += 1
        
        # 所有数据处理完毕
        self.continue_backtest = False
        self.logger.info("行情事件推送完成")

    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        获取当前时间点该股票的最新K线
        """
        if symbol not in self.symbol_data:
            return None
        
        current_idx = self.current_index.get(symbol, -1)
        if current_idx < 0 or current_idx >= len(self.symbol_data[symbol]):
            return None
        
        return self.symbol_data[symbol][current_idx]

    def get_latest_bars(self, symbol: str, n: int = 1) -> List[BarData]:
        """
        获取截止到当前时间点的最近N根K线
        注意：严禁返回当前时刻之后的数据（即未来函数）
        """
        if symbol not in self.symbol_data:
            return []
        
        current_idx = self.current_index.get(symbol, -1)
        if current_idx < 0:
            return []
        
        # 计算起始索引，确保不越界
        start_idx = max(0, current_idx - n + 1)
        
        # 返回从start_idx到current_idx的数据（包含当前K线）
        return self.symbol_data[symbol][start_idx:current_idx + 1]

    def get_current_time(self) -> Optional[datetime]:
        """获取当前回测时间"""
        if self.current_time_index < len(self.timeline):
            return self.timeline[self.current_time_index]
        return None

    def reset(self):
        """重置数据处理器到初始状态"""
        self.current_time_index = 0
        self.continue_backtest = True
        for symbol in self.current_index:
            self.current_index[symbol] = 0
        self.logger.info("数据处理器已重置")