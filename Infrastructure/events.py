"""
事件系统定义
系统各模块沟通的语言，所有交互都通过传递Event对象完成
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .enums import EventType, Direction, OrderType

try:
    from DataManager.schema.bar import BarData
except ImportError:
    from schema.bar import BarData


@dataclass
class MarketEvent:
    """
    行情事件
    承载一根 K 线或一个 Tick，驱动系统向前推进一步
    当新的K线到达时触发
    """
    bar: BarData  # 这是我们在 DataManager 定义好的结构，包含 Open/High/Low/Close
    type: EventType = EventType.MARKET  # 事件类型


@dataclass
class SignalEvent:
    """
    信号事件
    策略层发出的"建议"
    注意：这里不包含具体的买卖股数，只包含意图
    """
    symbol: str                    # 股票代码，如 "000001.SZ"
    datetime: datetime             # 信号产生的时间
    direction: Direction           # 买还是卖
    strength: float                # 信号强度，1.0 表示强烈买入，0.5 观望
    type: EventType = EventType.SIGNAL  # 事件类型
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"SignalEvent: {self.symbol}, {self.direction.value}, "
            f"strength={self.strength:.2f}, time={self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@dataclass
class OrderEvent:
    """
    订单事件
    Portfolio 经过资金计算和风控检查后，发出的"确切指令"
    """
    symbol: str                    # 股票代码
    datetime: datetime             # 订单时间
    order_type: OrderType          # 市价还是限价
    direction: Direction           # 交易方向
    volume: int                    # 关键：具体的股数，例如 1000 股，不能是金额
    limit_price: float = 0.0       # 如果是限价单，必填；市价单为 0
    type: EventType = EventType.ORDER  # 事件类型
    
    def __str__(self) -> str:
        """字符串表示"""
        price_str = f"@{self.limit_price:.2f}" if self.order_type == OrderType.LIMIT else "MARKET"
        return (
            f"OrderEvent: {self.direction.value} {self.volume:,} {self.symbol} "
            f"{price_str}, time={self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@dataclass
class FillEvent:
    """
    成交事件
    模拟交易所（Execution）撮合成功后返回的凭证
    Portfolio 收到这个才能扣钱
    """
    symbol: str                    # 股票代码
    datetime: datetime             # 实际成交时间，可能滞后于订单时间
    direction: Direction           # 交易方向
    volume: int                    # 实际成交数量，可能因为滑点或资金不足只成交了一半
    price: float                   # 实际成交价，包含滑点影响
    commission: float              # 产生的手续费金额
    type: EventType = EventType.FILL  # 事件类型
    
    @property
    def trade_value(self) -> float:
        """成交金额"""
        return self.volume * self.price
    
    @property
    def net_value(self) -> float:
        """净成交金额（扣除手续费）"""
        if self.direction == Direction.LONG:
            # 买入：成本 = 成交金额 + 手续费
            return self.trade_value + self.commission
        else:
            # 卖出：收入 = 成交金额 - 手续费
            return self.trade_value - self.commission
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"FillEvent: {self.direction.value} {self.volume:,} {self.symbol} "
            f"@{self.price:.2f}, fee={self.commission:.2f}, "
            f"time={self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )