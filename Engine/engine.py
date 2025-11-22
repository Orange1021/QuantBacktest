"""
回测引擎核心实现
BacktestEngine - 事件驱动的量化回测引擎
"""

import logging
from collections import deque
from typing import Any, Optional, Deque
from datetime import datetime

# 导入现有模块
from Infrastructure.enums import EventType
from Infrastructure.events import (
    MarketEvent, 
    SignalEvent, 
    OrderEvent, 
    FillEvent
)
from DataManager.handlers.handler import BaseDataHandler


class BacktestEngine:
    """
    回测引擎核心
    
    职责：
    1. 维护事件队列和事件循环
    2. 协调数据处理器、策略、投资组合和执行器之间的交互
    3. 严格按时间顺序处理事件，防止未来函数
    4. 提供统一的回测启动和管理接口
    """
    
    def __init__(
        self,
        data_handler: BaseDataHandler,
        strategy: Any,  # 策略实例，实现 IStrategy 接口
        portfolio: Any,  # 投资组合实例，未来替换为具体的投资组合类
        execution: Any   # 执行器实例，未来替换为具体的执行器类
    ):
        """
        初始化回测引擎
        
        Args:
            data_handler: 数据处理器，提供历史数据流
            strategy: 策略实例，负责生成交易信号
            portfolio: 投资组合实例，负责资金和持仓管理
            execution: 执行器实例，负责订单撮合
        """
        self.logger = logging.getLogger(__name__)
        
        # 核心依赖
        self.data_handler = data_handler
        self.strategy = strategy
        self.portfolio = portfolio
        self.execution = execution
        
        # 统一事件队列 - 先进先出
        self.event_queue: Deque[Any] = deque()
        
        # 设置策略的事件队列引用
        if hasattr(strategy, 'set_event_queue'):
            strategy.set_event_queue(self.event_queue)
        else:
            raise AttributeError("策略必须实现 set_event_queue 方法")
        
        # 回测状态
        self.is_running = False
        self.current_time: Optional[datetime] = None
        
        # 统计信息
        self.total_events = 0
        self.market_events = 0
        self.signal_events = 0
        self.order_events = 0
        self.fill_events = 0
        
        self.logger.info("BacktestEngine 初始化完成")
    
    def run(self) -> None:
        """
        运行回测
        
        这是回测的主入口，负责：
        1. 遍历历史数据
        2. 将 MarketEvent 加入队列
        3. 处理每个时间点的所有衍生事件
        4. 维护回测进度和统计
        """
        self.logger.info("=" * 60)
        self.logger.info("回测引擎启动")
        self.logger.info("=" * 60)
        
        self.is_running = True
        start_time = datetime.now()
        
        try:
            # 主循环：遍历历史数据流
            for event in self.data_handler.update_bars():
                if not isinstance(event, MarketEvent):
                    self.logger.warning(f"收到非 MarketEvent 类型事件: {type(event)}")
                    continue
                
                # 更新当前时间
                self.current_time = event.bar.datetime
                
                # 将 MarketEvent 加入队列
                self.event_queue.append(event)
                self.market_events += 1
                
                # 处理当前时间点的所有事件
                self._process_queue()
                
                # 显示进度（每100个事件显示一次）
                if self.total_events % 100 == 0 and self.total_events > 0:
                    self._show_progress()
            
            # 回测结束
            self.is_running = False
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("=" * 60)
            self.logger.info("回测完成")
            self.logger.info(f"总耗时: {duration}")
            self._show_statistics()
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"回测过程中发生错误: {e}")
            self.is_running = False
            raise
    
    def _process_queue(self) -> None:
        """
        处理事件队列
        
        持续处理队列中的事件，直到队列为空。
        这确保了同一时间点的所有事件都被处理完毕，
        然后才会进入下一个时间点。
        """
        while len(self.event_queue) > 0:
            event = self.event_queue.popleft()
            self.total_events += 1
            
            try:
                self._handle_event(event)
            except Exception as e:
                self.logger.error(f"处理事件时发生错误: {e}, 事件类型: {type(event)}")
                # 继续处理其他事件，不中断整个回测
    
    def _handle_event(self, event: Any) -> None:
        """
        事件分发处理器
        
        根据事件类型调用相应的处理方法。
        这里定义了引擎与各模块之间的交互契约。
        
        Args:
            event: 待处理的事件
        """
        if isinstance(event, MarketEvent):
            self._handle_market_event(event)
        elif isinstance(event, SignalEvent):
            self._handle_signal_event(event)
        elif isinstance(event, OrderEvent):
            self._handle_order_event(event)
        elif isinstance(event, FillEvent):
            self._handle_fill_event(event)
        else:
            self.logger.warning(f"未知事件类型: {type(event)}")
    
    def _handle_market_event(self, event: MarketEvent) -> None:
        """
        处理行情事件
        
        1. 更新投资组合的持仓市值
        2. 调用策略的模板方法处理行情数据
        3. 策略直接将信号发送到引擎队列，无需转移
        """
        # 更新投资组合的市值信息
        self.portfolio.update_on_market(event)
        
        # 策略处理行情数据 - 使用模板方法确保状态更新
        self.strategy._process_market_data(event)
        
        # 注意：策略现在直接将信号发送到引擎队列，无需转移
    
    def _handle_signal_event(self, event: SignalEvent) -> None:
        """
        处理信号事件
        
        1. 将信号传递给投资组合进行风控和资金计算
        2. 如果投资组合返回订单事件，加入队列
        """
        self.signal_events += 1
        
        # 投资组合处理信号，可能生成订单
        order_event = self.portfolio.process_signal(event)
        
        # 如果生成了订单，加入队列
        if order_event is not None:
            if isinstance(order_event, OrderEvent):
                self.event_queue.append(order_event)
                self.order_events += 1
                self.logger.debug(f"投资组合订单已加入队列: {order_event.symbol}")
            else:
                self.logger.warning(f"Portfolio.process_signal 返回了非 OrderEvent 类型: {type(order_event)}")
    
    def _handle_order_event(self, event: OrderEvent) -> None:
        """
        处理订单事件
        
        1. 将订单传递给执行器进行撮合
        2. 如果执行器返回成交事件，加入队列
        """
        # 注意：order_events 在 process_signal 中已经计数了，这里不再重复计数
        
        # 执行器处理订单，可能生成成交
        fill_event = self.execution.execute_order(event)
        
        # 如果生成了成交，加入队列
        if fill_event is not None:
            if isinstance(fill_event, FillEvent):
                self.event_queue.append(fill_event)
                self.logger.debug(f"执行器成交已加入队列: {fill_event.symbol}")
            else:
                self.logger.warning(f"Execution.execute_order 返回了非 FillEvent 类型: {type(fill_event)}")
    
    def _handle_fill_event(self, event: FillEvent) -> None:
        """
        处理成交事件
        
        1. 更新投资组合的持仓和资金
        """
        self.fill_events += 1
        
        # 投资组合更新成交信息
        self.portfolio.update_on_fill(event)
    
    def _show_progress(self) -> None:
        """显示回测进度"""
        if self.current_time:
            self.logger.info(
                f"进度: {self.current_time.strftime('%Y-%m-%d')} | "
                f"总事件: {self.total_events} | "
                f"行情: {self.market_events} | "
                f"信号: {self.signal_events} | "
                f"订单: {self.order_events} | "
                f"成交: {self.fill_events}"
            )
    
    def _show_statistics(self) -> None:
        """显示回测统计信息"""
        self.logger.info("回测统计:")
        self.logger.info(f"  总事件数: {self.total_events}")
        self.logger.info(f"  行情事件: {self.market_events}")
        self.logger.info(f"  信号事件: {self.signal_events}")
        self.logger.info(f"  订单事件: {self.order_events}")
        self.logger.info(f"  成交事件: {self.fill_events}")
        
        if self.market_events > 0:
            signal_rate = (self.signal_events / self.market_events) * 100
            order_rate = (self.order_events / self.signal_events) * 100 if self.signal_events > 0 else 0
            fill_rate = (self.fill_events / self.order_events) * 100 if self.order_events > 0 else 0
            
            self.logger.info(f"  信号生成率: {signal_rate:.2f}%")
            self.logger.info(f"  订单转化率: {order_rate:.2f}%")
            self.logger.info(f"  成交率: {fill_rate:.2f}%")
    
    def get_status(self) -> dict:
        """
        获取引擎当前状态
        
        Returns:
            包含状态信息的字典
        """
        return {
            'is_running': self.is_running,
            'current_time': self.current_time,
            'queue_size': len(self.event_queue),
            'total_events': self.total_events,
            'market_events': self.market_events,
            'signal_events': self.signal_events,
            'order_events': self.order_events,
            'fill_events': self.fill_events
        }