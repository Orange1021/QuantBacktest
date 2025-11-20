"""
Tick数据模型定义
继承自BaseData，包含五档盘口数据及实时行情信息
"""

from dataclasses import dataclass
from typing import Optional

from .base import BaseData
from .constant import Exchange


@dataclass
class TickData(BaseData):
    """
    Tick数据类，高频回测的基础数据单元
    包含最新价、五档盘口深度等实时行情信息
    """
    # 基本信息
    name: str = ""              # 中文名称，方便日志打印
    
    # 最新成交信息
    last_price: float = 0.0     # 最新成交价
    last_volume: float = 0.0    # 最新成交量
    
    # 卖盘五档 (Ask)
    ask_price_1: float = 0.0    # 卖一价
    ask_price_2: float = 0.0    # 卖二价
    ask_price_3: float = 0.0    # 卖三价
    ask_price_4: float = 0.0    # 卖四价
    ask_price_5: float = 0.0    # 卖五价
    
    ask_volume_1: float = 0.0   # 卖一量
    ask_volume_2: float = 0.0   # 卖二量
    ask_volume_3: float = 0.0   # 卖三量
    ask_volume_4: float = 0.0   # 卖四量
    ask_volume_5: float = 0.0   # 卖五量
    
    # 买盘五档 (Bid)
    bid_price_1: float = 0.0    # 买一价
    bid_price_2: float = 0.0    # 买二价
    bid_price_3: float = 0.0    # 买三价
    bid_price_4: float = 0.0    # 买四价
    bid_price_5: float = 0.0    # 买五价
    
    bid_volume_1: float = 0.0   # 买一量
    bid_volume_2: float = 0.0   # 买二量
    bid_volume_3: float = 0.0   # 买三量
    bid_volume_4: float = 0.0   # 买四量
    bid_volume_5: float = 0.0   # 买五量
    
    # 其他字段
    limit_up: float = 0.0       # 涨停价
    limit_down: float = 0.0     # 跌停价
    open_interest: float = 0.0  # 持仓量（期货专用）
    pre_close: float = 0.0      # 昨收价
    
    # 统计数据
    turnover: float = 0.0       # 累计成交额
    volume: float = 0.0         # 累计成交量
    avg_price: float = 0.0      # 当日均价

    def __post_init__(self):
        """数据类初始化后处理"""
        super().__post_init__()
        
        # 盘口数据验证
        for i in range(1, 6):
            ask_price = getattr(self, f"ask_price_{i}")
            ask_volume = getattr(self, f"ask_volume_{i}")
            bid_price = getattr(self, f"bid_price_{i}")
            bid_volume = getattr(self, f"bid_volume_{i}")
            
            if ask_price < 0 or bid_price < 0:
                raise ValueError(f"盘口价格不能为负数: ask_price_{i}={ask_price}, bid_price_{i}={bid_price}")
            
            if ask_volume < 0 or bid_volume < 0:
                raise ValueError(f"盘口数量不能为负数: ask_volume_{i}={ask_volume}, bid_volume_{i}={bid_volume}")

    @property
    def spread(self) -> float:
        """买卖价差 = 卖一价 - 买一价"""
        if self.ask_price_1 == 0 or self.bid_price_1 == 0:
            return 0.0
        return self.ask_price_1 - self.bid_price_1

    @property
    def spread_pct(self) -> float:
        """买卖价差百分比"""
        if self.bid_price_1 == 0:
            return 0.0
        return (self.spread / self.bid_price_1) * 100

    @property
    def total_ask_volume(self) -> float:
        """卖盘总挂单量"""
        return sum(getattr(self, f"ask_volume_{i}") for i in range(1, 6))

    @property
    def total_bid_volume(self) -> float:
        """买盘总挂单量"""
        return sum(getattr(self, f"bid_volume_{i}") for i in range(1, 6))

    @property
    def volume_ratio(self) -> float:
        """买卖量比 = 买盘总量 / 卖盘总量"""
        if self.total_ask_volume == 0:
            return float('inf') if self.total_bid_volume > 0 else 1.0
        return self.total_bid_volume / self.total_ask_volume

    @property
    def weighted_bid_price(self) -> float:
        """买盘加权价格"""
        total_volume = self.total_bid_volume
        if total_volume == 0:
            return 0.0
        
        weighted_sum = sum(
            getattr(self, f"bid_price_{i}") * getattr(self, f"bid_volume_{i}")
            for i in range(1, 6)
        )
        return weighted_sum / total_volume

    @property
    def weighted_ask_price(self) -> float:
        """卖盘加权价格"""
        total_volume = self.total_ask_volume
        if total_volume == 0:
            return 0.0
        
        weighted_sum = sum(
            getattr(self, f"ask_price_{i}") * getattr(self, f"ask_volume_{i}")
            for i in range(1, 6)
        )
        return weighted_sum / total_volume

    @property
    def mid_price(self) -> float:
        """中间价 = (买一价 + 卖一价) / 2"""
        if self.ask_price_1 == 0 or self.bid_price_1 == 0:
            return self.last_price
        return (self.ask_price_1 + self.bid_price_1) / 2

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"TickData: {self.vt_symbol}, {self.datetime}, "
            f"Last:{self.last_price}, "
            f"Bid:{self.bid_price_1}/{self.bid_volume_1}, "
            f"Ask:{self.ask_price_1}/{self.ask_volume_1}"
        )