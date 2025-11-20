"""
量化交易系统枚举定义
统一定义系统中的"状态"和"类型"，避免魔法字符串
"""

from enum import Enum


class EventType(Enum):
    """事件类型枚举"""
    MARKET = "MARKET"    # 行情来了（由 DataManager 发出）
    SIGNAL = "SIGNAL"    # 策略产生想法了（由 Strategies 发出）
    ORDER = "ORDER"      # 风控通过，准备下单了（由 Portfolio 发出）
    FILL = "FILL"        # 交易所成交了（由 Execution 发出）
    ERROR = "ERROR"      # 系统报错（可选，用于异常处理）


class Direction(Enum):
    """交易方向枚举"""
    LONG = "LONG"        # 做多/买入
    BUY = "BUY"          # 买入（与LONG同义）
    SHORT = "SHORT"      # 做空/卖出
    SELL = "SELL"        # 卖出（与SHORT同义）


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "MARKET"    # 市价单（回测最常用）
    LIMIT = "LIMIT"      # 限价单（需要指定价格）