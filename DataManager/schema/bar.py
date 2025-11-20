"""
K线数据模型定义
继承自BaseData，包含OHLCV数据及A股特有字段
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import BaseData
from .constant import Interval, Exchange


@dataclass
class BarData(BaseData):
    """
    K线数据类，回测最常用的数据单元
    包含OHLCV标准字段及A股特有的风控字段
    """
    # 周期维度
    interval: Interval = Interval.DAILY  # K线周期
    
    # OHLCV 标准字段 (float类型)
    open_price: float = 0.0      # 开盘价
    high_price: float = 0.0      # 最高价
    low_price: float = 0.0       # 最低价
    close_price: float = 0.0     # 收盘价
    volume: float = 0.0          # 成交量（股票为股数，期货为手，币为数量）
    
    # 关键扩展字段
    turnover: float = 0.0        # 成交额（金额），A股策略重要指标
    open_interest: float = 0.0   # 持仓量（期货专用，股票设为0）
    
    # A股撮合风控字段
    limit_up: float = 0.0        # 涨停价
    limit_down: float = 0.0      # 跌停价
    
    # 可选字段
    pre_close: float = 0.0       # 昨收价
    settlement: float = 0.0      # 结算价（期货用）
    
    def __post_init__(self):
        """数据类初始化后处理"""
        super().__post_init__()
        
        # 数据验证
        if self.high_price < max(self.open_price, self.close_price):
            raise ValueError("最高价不能小于开盘价和收盘价的最大值")
        
        if self.low_price > min(self.open_price, self.close_price):
            raise ValueError("最低价不能大于开盘价和收盘价的最小值")
        
        if self.volume < 0:
            raise ValueError("成交量不能为负数")
        
        if self.turnover < 0:
            raise ValueError("成交额不能为负数")

    @property
    def price_change(self) -> float:
        """价格变动 = 当前收盘价 - 昨收价"""
        return self.close_price - self.pre_close

    @property
    def price_change_pct(self) -> float:
        """价格变动百分比"""
        if self.pre_close == 0:
            return 0.0
        return (self.price_change / self.pre_close) * 100

    @property
    def amplitude(self) -> float:
        """振幅百分比"""
        if self.pre_close == 0:
            return 0.0
        return ((self.high_price - self.low_price) / self.pre_close) * 100

    @property
    def is_limit_up(self) -> bool:
        """是否涨停"""
        if self.limit_up <= 0:
            return False
        return self.close_price >= self.limit_up - 0.01  # 允许小误差

    @property
    def is_limit_down(self) -> bool:
        """是否跌停"""
        if self.limit_down <= 0:
            return False
        return self.close_price <= self.limit_down + 0.01  # 允许小误差

    @property
    def average_price(self) -> float:
        """成交均价"""
        if self.volume == 0:
            return 0.0
        return self.turnover / self.volume

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"BarData: {self.vt_symbol}, {self.interval.value}, "
            f"{self.datetime}, O:{self.open_price}, H:{self.high_price}, "
            f"L:{self.low_price}, C:{self.close_price}, V:{self.volume}"
        )