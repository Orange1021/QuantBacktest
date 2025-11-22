"""
量化交易系统数据结构常量定义
用于消除"魔法字符串"，提供标准化的枚举类型
"""

from enum import Enum


class Exchange(Enum):
    """交易所枚举"""
    # A股市场 - 标准化格式 (Backtrader/VeighNa 兼容)
    SH = "SH"          # 上海证券交易所
    SZ = "SZ"          # 深圳证券交易所
    BJ = "BJ"          # 北京证券交易所
    
    # 兼容旧格式
    SSE = "SSE"        # 上海证券交易所 (旧格式)
    SZSE = "SZSE"      # 深圳证券交易所 (旧格式)
    BSE = "BSE"        # 北京证券交易所 (旧格式)
    
    # 期货市场
    CFFEX = "CFFEX"    # 中金所
    SHFE = "SHFE"      # 上期所
    DCE = "DCE"        # 大商所
    CZCE = "CZCE"      # 郑商所
    
    # 港股
    HKEX = "HKEX"      # 香港交易所
    
    # 美股
    NASDAQ = "NASDAQ"  # 纳斯达克
    NYSE = "NYSE"      # 纽约证券交易所
    
    # 加密货币
    BINANCE = "BINANCE"  # 币安
    OKEX = "OKEX"        # OKX
    
    # 其他
    LOCAL = "LOCAL"    # 本地数据源


class Interval(Enum):
    """K线周期枚举"""
    TICK = "tick"
    
    # 分钟级别
    MINUTE = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    
    # 小时级别
    HOUR = "1h"
    HOUR_4 = "4h"
    
    # 日级别
    DAILY = "d"
    WEEKLY = "w"
    MONTHLY = "M"


class Direction(Enum):
    """交易方向枚举"""
    LONG = "LONG"      # 多头/买入
    SHORT = "SHORT"    # 空头/卖出
    NET = "NET"        # 净值


class Offset(Enum):
    """开平方向枚举"""
    OPEN = "OPEN"          # 开仓
    CLOSE = "CLOSE"        # 平仓
    CLOSETODAY = "CLOSETODAY"  # 平今
    CLOSEYESTERDAY = "CLOSEYESTERDAY"  # 平昨


class Status(Enum):
    """状态枚举"""
    NOTTRADED = "NOTTRADED"    # 未交易
    ALLTRADED = "ALLTRADED"    # 全部成交
    PARTTRADED = "PARTTRADED"  # 部分成交
    CANCELLED = "CANCELLED"    # 已撤销
    REJECTED = "REJECTED"      # 已拒绝