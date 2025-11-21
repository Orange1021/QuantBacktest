"""
模拟执行器实现
用于回测的模拟交易所，处理订单撮合和成本计算
"""

from typing import Optional
from datetime import datetime

from Infrastructure.events import OrderEvent, FillEvent, EventType
from Infrastructure.enums import OrderType, Direction
from .base import BaseExecutor


class SimulatedExecution(BaseExecutor):
    """回测模拟执行器
    
    模拟交易所的订单撮合逻辑：
    1. 接收OrderEvent
    2. 根据当前行情判断成交价格
    3. 计算手续费和滑点
    4. 生成FillEvent
    
    特点：
    - 假设无限流动性，订单总是能全额成交
    - 支持市价单和限价单
    - 考虑手续费和滑点成本
    """
    
    def __init__(self, data_handler, **kwargs):
        """初始化模拟执行器
        
        Args:
            data_handler: 数据处理器，用于获取当前价格
            **kwargs: 其他配置参数
        """
        super().__init__(**kwargs)
        self.data_handler = data_handler
        
        # 模拟执行器统计
        self.orders_received = 0
        self.orders_executed = 0
        self.orders_rejected = 0
        self.total_commission = 0.0
        
        self.logger.info("SimulatedExecution 初始化完成")
    
    def execute_order(self, order_event: OrderEvent) -> Optional[FillEvent]:
        """执行订单
        
        Args:
            order_event: 订单事件
            
        Returns:
            Optional[FillEvent]: 成交事件，失败返回None
        """
        self.orders_received += 1
        
        # 验证订单有效性
        if not self.validate_order(order_event):
            self.orders_rejected += 1
            self.logger.error(f"订单验证失败: {order_event}")
            return None
        
        try:
            # 获取成交价格
            fill_price = self._get_fill_price(order_event)
            if fill_price is None:
                self.logger.warning(f"无法获取成交价格: {order_event.symbol}")
                self.orders_rejected += 1
                return None
            
            # 应用滑点
            fill_price = self.calculate_slippage(fill_price, order_event.direction)
            
            # 计算手续费
            commission = self.calculate_commission(fill_price, order_event.volume)
            self.total_commission += commission
            
            # 获取当前回测时间
            current_time = self._get_current_time()
            if current_time is None:
                current_time = order_event.datetime
            
            # 创建成交事件
            fill_event = FillEvent(
                symbol=order_event.symbol,
                datetime=current_time,
                direction=order_event.direction,
                volume=order_event.volume,
                price=fill_price,
                commission=commission
            )
            
            self.orders_executed += 1
            
            self.logger.info(
                f"订单执行成功: {order_event.symbol} {order_event.direction.value} "
                f"{order_event.volume}股 @ {fill_price:.2f}, 手续费: {commission:.2f}"
            )
            
            return fill_event
            
        except Exception as e:
            self.logger.error(f"订单执行异常: {e}")
            self.orders_rejected += 1
            return None
    
    def _get_fill_price(self, order_event: OrderEvent) -> Optional[float]:
        """获取成交价格
        
        Args:
            order_event: 订单事件
            
        Returns:
            Optional[float]: 成交价格
        """
        if order_event.order_type == OrderType.MARKET:
            # 市价单：使用最新收盘价
            latest_bar = self.data_handler.get_latest_bar(order_event.symbol)
            if latest_bar:
                return latest_bar.close_price
            else:
                self.logger.error(f"无法获取 {order_event.symbol} 的最新价格")
                return None
                
        elif order_event.order_type == OrderType.LIMIT:
            # 限价单：使用订单指定价格
            if order_event.limit_price <= 0:
                self.logger.error(f"限价单价格无效: {order_event.limit_price}")
                return None
            
            # 简化处理：假设限价单总能成交
            # 实际应该检查当前价格是否在限价范围内
            return order_event.limit_price
        
        else:
            self.logger.error(f"不支持的订单类型: {order_event.order_type}")
            return None
    
    def _get_current_time(self) -> Optional[datetime]:
        """获取当前回测时间
        
        Returns:
            Optional[datetime]: 当前时间
        """
        try:
            return self.data_handler.get_current_time()
        except AttributeError:
            # 如果data_handler没有get_current_time方法，使用当前系统时间
            return datetime.now()
        except Exception as e:
            self.logger.warning(f"获取当前时间失败: {e}")
            return datetime.now()
    
    def get_execution_stats(self) -> dict:
        """获取执行统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            'orders_received': self.orders_received,
            'orders_executed': self.orders_executed,
            'orders_rejected': self.orders_rejected,
            'execution_rate': self.orders_executed / max(self.orders_received, 1),
            'total_commission': self.total_commission,
            'avg_commission': self.total_commission / max(self.orders_executed, 1)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.orders_received = 0
        self.orders_executed = 0
        self.orders_rejected = 0
        self.total_commission = 0.0
        self.logger.info("执行器统计信息已重置")