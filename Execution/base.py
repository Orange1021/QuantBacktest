"""
执行模块抽象基类
定义执行器的标准接口，确保与Engine的交互规范
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from Infrastructure.events import OrderEvent, FillEvent
from Infrastructure.enums import Direction


class BaseExecutor(ABC):
    """执行器抽象基类
    
    定义执行器的标准接口。执行器负责：
    1. 接收订单事件(OrderEvent)
    2. 模拟或实际执行订单
    3. 生成成交事件(FillEvent)或返回None(未成交)
    
    设计原则：
    - 策略和投资组合不需要知道"怎么下单"
    - 只需要知道"下了单"的结果
    - 支持回测模拟和实盘交易的切换
    """
    
    def __init__(self, **kwargs):
        """初始化执行器
        
        Args:
            **kwargs: 配置参数，具体参数由子类定义
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 从kwargs中提取通用配置
        self.commission_rate = kwargs.get('commission_rate', 0.0003)  # 默认0.03%手续费
        self.slippage_rate = kwargs.get('slippage_rate', 0.001)      # 默认0.1%滑点
        self.min_commission = kwargs.get('min_commission', 5.0)      # 默认最小手续费5元
        
        self.logger.info(f"{self.__class__.__name__} 初始化完成")
        self.logger.info(f"手续费率: {self.commission_rate:.4f}, 滑点率: {self.slippage_rate:.4f}")
    
    @abstractmethod
    def execute_order(self, order_event: OrderEvent) -> Optional[FillEvent]:
        """执行订单
        
        Args:
            order_event: 订单事件
            
        Returns:
            Optional[FillEvent]: 成交事件，如果订单未成交则返回None
        """
        pass
    
    def calculate_commission(self, price: float, volume: int) -> float:
        """计算手续费
        
        Args:
            price: 成交价格
            volume: 成交数量
            
        Returns:
            float: 手续费金额
        """
        commission = price * volume * self.commission_rate
        return max(commission, self.min_commission)
    
    def calculate_slippage(self, price: float, direction) -> float:
        """计算滑点
        
        Args:
            price: 基准价格
            direction: 交易方向
            
        Returns:
            float: 滑点后的价格
        """
        # 买入时价格上浮，卖出时价格下浮
        if direction == Direction.LONG:
            return price * (1 + self.slippage_rate)
        else:
            return price * (1 - self.slippage_rate)
    
    def validate_order(self, order_event: OrderEvent) -> bool:
        """验证订单有效性
        
        Args:
            order_event: 订单事件
            
        Returns:
            bool: 订单是否有效
        """
        if not order_event.symbol:
            self.logger.error("订单缺少股票代码")
            return False
        
        if order_event.volume <= 0:
            self.logger.error(f"订单数量无效: {order_event.volume}")
            return False
        
        if order_event.order_type.value not in ['MARKET', 'LIMIT']:
            self.logger.error(f"不支持的订单类型: {order_event.order_type}")
            return False
        
        return True