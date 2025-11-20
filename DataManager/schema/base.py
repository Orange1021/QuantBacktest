"""
基础数据类定义
提供所有数据类型的通用属性和方法
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

from .constant import Exchange


@dataclass
class BaseData:
    """
    基础数据类，所有数据类型的父类
    包含所有数据共有的元数据字段
    """
    gateway_name: str = ""      # 数据来源接口名称
    symbol: str = ""            # 标的代码
    exchange: Exchange = Exchange.LOCAL  # 交易所
    datetime: datetime = None   # 带时区信息的时间戳
    extra: Dict[str, Any] = field(default_factory=dict)  # 扩展字段

    def __post_init__(self):
        """数据类初始化后处理"""
        if self.extra is None:
            self.extra = {}

    @property
    def vt_symbol(self) -> str:
        """
        虚拟标的代码，格式为 symbol.exchange
        作为系统内的唯一标识符，用于哈希表、字典索引等
        """
        return f"{self.symbol}.{self.exchange.value}"

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}: {self.vt_symbol}, {self.datetime}"

    def __repr__(self) -> str:
        """调试用字符串表示"""
        return (
            f"{self.__class__.__name__}("
            f"symbol={self.symbol}, "
            f"exchange={self.exchange.value}, "
            f"datetime={self.datetime}, "
            f"gateway_name={self.gateway_name}"
            f")"
        )

    def update_extra(self, key: str, value: Any) -> None:
        """
        更新扩展字段
        
        Args:
            key: 字段名
            value: 字段值
        """
        self.extra[key] = value

    def get_extra(self, key: str, default: Any = None) -> Any:
        """
        获取扩展字段
        
        Args:
            key: 字段名
            default: 默认值
            
        Returns:
            字段值或默认值
        """
        return self.extra.get(key, default)