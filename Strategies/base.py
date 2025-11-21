"""
策略基类
定义所有策略必须遵守的接口规范
"""

import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import List, Optional
from datetime import datetime

from Infrastructure.events import MarketEvent, SignalEvent
from Infrastructure.enums import EventType, Direction
from DataManager.handlers.handler import BaseDataHandler
from DataManager.schema.bar import BarData


class BaseStrategy(ABC):
    """
    策略抽象基类
    
    这是所有策略的"宪法"，定义了：
    1. 标准化输入：所有策略都以相同方式接收行情数据 (MarketEvent)
    2. 标准化输出：所有策略都通过统一接口发出信号 (SignalEvent)
    3. 数据访问权限：策略通过 DataHandler 访问历史数据，严禁访问未来数据
    """
    
    def __init__(self, data_handler: BaseDataHandler, event_queue: deque):
        """
        初始化策略
        
        Args:
            data_handler: 数据处理器，用于获取历史数据
            event_queue: 事件队列，用于发送信号事件
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 核心依赖
        self.data_handler = data_handler
        self.event_queue = event_queue
        
        # 策略状态
        self.is_initialized = False
        self.current_time: Optional[datetime] = None
        
        # 统计信息
        self.signals_generated = 0
        self.market_data_processed = 0
        
        self.logger.info(f"{self.__class__.__name__} 策略初始化完成")
    
    @abstractmethod
    def on_market_data(self, event: MarketEvent) -> None:
        """
        处理行情数据
        
        这是策略的核心方法，引擎每推过来一根K线就会调用此方法。
        所有具体的策略逻辑（如双均线、网格交易等）都在这里实现。
        
        Args:
            event: 行情事件，包含具体的K线数据
        """
        pass
    
    def send_signal(
        self, 
        symbol: str, 
        direction: Direction, 
        strength: float = 1.0
    ) -> None:
        """
        发送交易信号
        
        这是策略向系统发出交易指令的标准方式。
        内部会创建 SignalEvent 并推入事件队列。
        
        Args:
            symbol: 股票代码，格式如 "000001.SZ"
            direction: 交易方向 (Direction.LONG/Direction.SHORT)
            strength: 信号强度，0.0-1.0，默认1.0表示最强信号
        """
        try:
            # 获取当前回测时间
            current_time = self.data_handler.get_current_time()
            if current_time is None:
                self.logger.warning("无法获取当前回测时间，跳过信号发送")
                return
            
            # 创建信号事件
            signal_event = SignalEvent(
                symbol=symbol,
                datetime=current_time,
                direction=direction,
                strength=strength
            )
            
            # 推入事件队列
            self.event_queue.append(signal_event)
            self.signals_generated += 1
            
            self.logger.info(
                f"发送{direction.value}信号: {symbol} @ {current_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"强度: {strength:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"发送信号失败: {e}")
    
    def get_latest_bars(self, symbol: str, n: int = 1) -> List[BarData]:
        """
        获取最近的N根K线数据
        
        这是策略获取历史数据的标准方式，确保不会访问未来数据。
        
        Args:
            symbol: 股票代码
            n: 需要获取的K线数量
            
        Returns:
            K线数据列表，按时间从旧到新排序
        """
        try:
            bars = self.data_handler.get_latest_bars(symbol, n)
            return bars
        except Exception as e:
            self.logger.error(f"获取历史数据失败 {symbol} n={n}: {e}")
            return []
    
    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        获取最新的一根K线数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            最新的K线数据，如果没有则返回None
        """
        bars = self.get_latest_bars(symbol, 1)
        return bars[0] if bars else None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        快捷方法，获取指定股票的最新收盘价。
        
        Args:
            symbol: 股票代码
            
        Returns:
            当前价格，如果没有数据则返回None
        """
        latest_bar = self.get_latest_bar(symbol)
        if latest_bar:
            return latest_bar.close_price
        return None
    
    def calculate_sma(self, symbol: str, period: int) -> Optional[float]:
        """
        计算简单移动平均线
        
        Args:
            symbol: 股票代码
            period: 周期
            
        Returns:
            SMA值，如果数据不足则返回None
        """
        bars = self.get_latest_bars(symbol, period)
        if len(bars) < period:
            return None
        
        closes = [bar.close_price for bar in bars]
        return sum(closes) / len(closes)
    
    def calculate_ema(self, symbol: str, period: int) -> Optional[float]:
        """
        计算指数移动平均线
        
        Args:
            symbol: 股票代码
            period: 周期
            
        Returns:
            EMA值，如果数据不足则返回None
        """
        bars = self.get_latest_bars(symbol, period + 10)  # 获取更多数据用于初始化
        if len(bars) < period:
            return None
        
        closes = [bar.close_price for bar in bars]
        
        # 计算初始SMA
        sma = sum(closes[:period]) / period
        
        # 计算乘数
        multiplier = 2 / (period + 1)
        
        # 计算EMA
        ema = sma
        for close in closes[period:]:
            ema = (close * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def is_price_above_sma(self, symbol: str, period: int) -> Optional[bool]:
        """
        判断当前价格是否在SMA之上
        
        Args:
            symbol: 股票代码
            period: SMA周期
            
        Returns:
            True表示价格在SMA之上，False表示在SMA之下，None表示无法判断
        """
        current_price = self.get_current_price(symbol)
        sma = self.calculate_sma(symbol, period)
        
        if current_price is None or sma is None:
            return None
        
        return current_price > sma
    
    def get_price_change_pct(self, symbol: str) -> Optional[float]:
        """
        获取当前K线的价格变动百分比
        
        Args:
            symbol: 股票代码
            
        Returns:
            价格变动百分比，正数表示上涨，负数表示下跌
        """
        latest_bar = self.get_latest_bar(symbol)
        if latest_bar:
            return ((latest_bar.close_price - latest_bar.open_price) / latest_bar.open_price) * 100
        return None
    
    def _update_strategy_state(self, event: MarketEvent) -> None:
        """
        更新策略内部状态
        
        在每次处理行情数据时调用，用于维护策略的时间同步状态。
        
        Args:
            event: 行情事件
        """
        self.current_time = event.bar.datetime
        self.market_data_processed += 1
        
        # 如果是第一次处理数据，标记为已初始化
        if not self.is_initialized:
            self.is_initialized = True
            self.logger.info(f"{self.__class__.__name__} 策略已初始化，时间: {self.current_time}")
    
    def _process_market_data(self, event: MarketEvent) -> None:
        """
        处理行情数据的内部方法
        
        这是一个模板方法，在调用具体的 on_market_data 之前，
        先更新策略状态，然后调用策略逻辑。
        
        Args:
            event: 行情事件
        """
        # 更新策略状态
        self._update_strategy_state(event)
        
        # 调用具体的策略逻辑
        try:
            self.on_market_data(event)
        except Exception as e:
            self.logger.error(f"策略处理行情数据时发生错误: {e}")
    
    def get_strategy_info(self) -> dict:
        """
        获取策略信息
        
        Returns:
            包含策略状态和统计信息的字典
        """
        return {
            'strategy_name': self.__class__.__name__,
            'is_initialized': self.is_initialized,
            'current_time': self.current_time,
            'signals_generated': self.signals_generated,
            'market_data_processed': self.market_data_processed
        }