"""
事件系统定义
系统各模块沟通的语言，所有交互都通过传递Event对象完成
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional

try:
    from DataManager.schema.bar import BarData
except ImportError:
    from schema.bar import BarData


class EventType(Enum):
    """事件类型枚举"""
    MARKET = "MARKET"   # 行情推送
    SIGNAL = "SIGNAL"   # 策略发出信号
    ORDER = "ORDER"     # 账户发出订单
    FILL = "FILL"       # 交易所回报成交


@dataclass
class MarketEvent:
    """
    行情事件
    当新的K线到达时触发
    """
    bar: BarData
    type: EventType = EventType.MARKET
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = self.bar.datetime


@dataclass
class SignalEvent:
    """
    信号事件
    策略计算后发出的交易意图
    """
    symbol: str
    direction: str      # "LONG" (做多) / "SHORT" (做空)
    strength: float     # 信号强度 (1.0 代表全仓意愿，0.5 代表半仓意愿)
    datetime: datetime  # 信号产生的时间
    type: EventType = EventType.SIGNAL
    timestamp: Optional[datetime] = None
    price: Optional[float] = None  # 参考价格（可选）
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = self.datetime
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"SignalEvent: {self.symbol}, {self.direction}, "
            f"strength={self.strength:.2f}, time={self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@dataclass
class OrderEvent:
    """
    订单事件
    经过风控检查后，实际发出的下单指令
    """
    symbol: str
    order_type: str     # "MARKET" (市价) / "LIMIT" (限价)
    direction: str      # "BUY" / "SELL"
    volume: int         # 具体的下单数量 (股数)
    price: float = 0.0  # 只有限价单需要填
    type: EventType = EventType.ORDER
    datetime: Optional[datetime] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.datetime is None:
            self.datetime = datetime.now()
        if self.timestamp is None:
            self.timestamp = self.datetime
    
    def __str__(self) -> str:
        """字符串表示"""
        price_str = f"@{self.price:.2f}" if self.order_type == "LIMIT" else "MARKET"
        return (
            f"OrderEvent: {self.direction} {self.volume:,} {self.symbol} "
            f"{price_str}, time={self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@dataclass
class FillEvent:
    """
    成交事件
    模拟交易所成交后的回报
    """
    symbol: str
    datetime: datetime
    direction: str      # "BUY" / "SELL"
    volume: int         # 实际成交数量
    price: float        # 实际成交价格 (含滑点)
    commission: float   # 手续费成本
    type: EventType = EventType.FILL
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = self.datetime
    
    @property
    def trade_value(self) -> float:
        """成交金额"""
        return self.volume * self.price
    
    @property
    def net_value(self) -> float:
        """净成交金额（扣除手续费）"""
        if self.direction == "BUY":
            return self.trade_value + self.commission
        else:
            return self.trade_value - self.commission
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"FillEvent: {self.direction} {self.volume:,} {self.symbol} "
            f"@{self.price:.2f}, fee={self.commission:.2f}, "
            f"time={self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )