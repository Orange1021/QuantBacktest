"""
投资组合抽象基类
定义 Engine 如何与 Portfolio 交互的标准接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from DataManager.handlers.handler import BaseDataHandler


class BasePortfolio(ABC):
    """
    投资组合抽象基类
    
    定义了投资组合必须实现的标准接口，确保与引擎的交互规范。
    这是系统的"会计师兼风控官"基类。
    """
    
    def __init__(self, data_handler: BaseDataHandler, initial_capital: float = 100000.0):
        """
        初始化投资组合
        
        Args:
            data_handler: 数据处理器，用于查询当前价格
            initial_capital: 初始资金，默认10万
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 核心依赖
        self.data_handler = data_handler
        self.initial_capital = initial_capital
        
        # 资金管理状态 - 所有子类都必须实现这些属性
        self.current_cash: float = initial_capital  # 当前可用现金
        self.positions: dict = {}  # 持仓字典 {symbol: volume}
        self.total_equity: float = initial_capital  # 总资产 = 现金 + 持仓市值
        
        # 统计信息
        self.market_updates = 0
        self.signals_processed = 0
        self.fills_processed = 0
        
        self.logger.info(f"{self.__class__.__name__} 初始化完成，初始资金: {initial_capital:,.2f}")
    
    @abstractmethod
    def update_on_market(self, event: MarketEvent) -> None:
        """
        行情更新时调用
        
        用于更新持仓市值（盯市），计算总资产。
        这是用来画资金曲线的，不是用来交易的。
        
        Args:
            event: 行情事件
        """
        pass
    
    @abstractmethod
    def update_on_fill(self, event: FillEvent) -> None:
        """
        成交时调用
        
        实际扣款、记账，更新现金和持仓。
        这是最关键的记账逻辑，必须确保资金计算准确。
        
        Args:
            event: 成交事件
        """
        pass
    
    @abstractmethod
    def process_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """
        处理信号，返回订单
        
        收到策略的"建议"（Signal），结合当前资金，计算出"指令"（Order）。
        这里涉及到仓位管理（买多少股）和风控检查。
        
        Args:
            event: 信号事件
            
        Returns:
            订单事件，如果不符合条件则返回None
        """
        pass
    
    def get_portfolio_info(self) -> dict:
        """
        获取投资组合信息
        
        Returns:
            包含投资组合状态和统计信息的字典
        """
        return {
            'portfolio_name': self.__class__.__name__,
            'initial_capital': self.initial_capital,
            'market_updates': self.market_updates,
            'signals_processed': self.signals_processed,
            'fills_processed': self.fills_processed
        }