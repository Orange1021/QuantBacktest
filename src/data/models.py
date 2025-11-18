"""
数据模型定义

包含K线数据、持仓数据、交易信号等核心数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"  # 买入
    SELL = "sell"  # 卖出
    HOLD = "hold"  # 持仓（无操作）


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"  # 待提交
    SUBMITTED = "submitted"  # 已提交
    PART_FILLED = "part_filled"  # 部分成交
    FILLED = "filled"  # 全部成交
    CANCELLED = "cancelled"  # 已撤销
    REJECTED = "rejected"  # 被拒绝


@dataclass
class BarData:
    """
    K线数据

    Attributes:
        symbol: 股票代码，如 '000001.SZ'
        datetime: K线时间
        open: 开盘价
        high: 最高价
        low: 最低价
        close: 收盘价
        volume: 成交量（手）
        open_interest: 持仓量（期货使用）
    """
    symbol: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    open_interest: float = 0.0

    def __post_init__(self):
        """数据验证"""
        if self.high < self.low:
            raise ValueError(f"最高价不能低于最低价: {self}")
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"开盘价超出范围: {self}")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"收盘价超出范围: {self}")


@dataclass
class MarketData:
    """
    市场数据（用于选股）

    Attributes:
        symbol: 股票代码
        date: 日期
        total_market_cap: 总市值（元）
        float_market_cap: 流通市值（元）
        pe_ratio: 市盈率
        pb_ratio: 市净率
    """
    symbol: str
    date: datetime
    total_market_cap: float  # 总市值（元）
    float_market_cap: float  # 流通市值（元）
    pe_ratio: Optional[float] = None  # 市盈率
    pb_ratio: Optional[float] = None  # 市净率


@dataclass
class PositionData:
    """
    持仓数据

    Attributes:
        symbol: 股票代码
        quantity: 持仓数量（股）
        avg_price: 持仓均价
        current_price: 当前价格
        market_value: 持仓市值
        entry_date: 首次建仓日期
        layer_count: 加仓层数（从0开始）
        has_risen: 是否上涨过（关键字段）
        initial_position_size: 初始仓位大小（用于计算加仓比例）
    """
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    entry_date: datetime
    layer_count: int = 0
    has_risen: bool = False
    initial_position_size: float = 0.0

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.quantity * self.current_price

    @property
    def cost_value(self) -> float:
        """持仓成本"""
        return self.quantity * self.avg_price

    @property
    def pnl(self) -> float:
        """盈亏金额"""
        return self.market_value - self.cost_value

    @property
    def pnl_percent(self) -> float:
        """盈亏百分比"""
        if self.cost_value == 0:
            return 0.0
        return self.pnl / self.cost_value

    def update_price(self, price: float) -> None:
        """更新当前价格"""
        self.current_price = price

    def check_if_risen(self) -> None:
        """
        检查是否上涨过
        逻辑：当前价格 > 持仓均价
        """
        if self.current_price > self.avg_price:
            self.has_risen = True


@dataclass
class Signal:
    """
    交易信号

    Attributes:
        symbol: 股票代码
        signal_type: 信号类型（买入/卖出）
        price: 价格
        quantity: 数量
        timestamp: 信号生成时间
        metadata: 附加信息（如加仓层数等）
    """
    symbol: str
    signal_type: SignalType
    price: float
    quantity: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """数据验证"""
        if self.price <= 0:
            raise ValueError(f"价格必须为正数: {self.price}")
        if self.quantity <= 0:
            raise ValueError(f"数量必须为正数: {self.quantity}")


@dataclass
class Order:
    """
    订单详情

    Attributes:
        order_id: 订单ID
        symbol: 股票代码
        order_type: 订单类型
        price: 价格
        quantity: 数量
        filled_quantity: 已成交数量
        status: 订单状态
        create_time: 创建时间
        update_time: 更新时间
    """
    order_id: str
    symbol: str
    order_type: OrderType
    price: float
    quantity: int
    filled_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    def __post_init__(self):
        if self.create_time is None:
            self.create_time = datetime.now()
        if self.update_time is None:
            self.update_time = self.create_time

    @property
    def remaining_quantity(self) -> int:
        """剩余数量"""
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        """是否全部成交"""
        return self.filled_quantity >= self.quantity

    @property
    def is_active(self) -> bool:
        """是否活跃状态"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PART_FILLED]
