"""
简单策略实现
用于集成测试的具体策略
"""

import logging
from typing import Optional

from .base import BaseStrategy
from Infrastructure.events import MarketEvent
from Infrastructure.enums import Direction


class SimpleMomentumStrategy(BaseStrategy):
    """
    简单动量策略
    
    策略逻辑：
    - 涨幅超过0.8%时买入
    - 跌幅超过0.8%时卖出（如果有持仓）
    """
    
    def __init__(self, data_handler, event_queue):
        super().__init__(data_handler, event_queue)
        self.buy_signals = 0
        self.sell_signals = 0
        self.portfolio = None  # 将在引擎中设置
    
    def set_portfolio(self, portfolio):
        """设置投资组合引用，用于查询持仓"""
        self.portfolio = portfolio
    
    def on_market_data(self, event: MarketEvent) -> None:
        """
        处理行情数据
        
        Args:
            event: 行情事件
        """
        bar = event.bar
        
        # 直接从当前K线计算价格变动百分比
        price_change_pct = ((bar.close_price - bar.open_price) / bar.open_price) * 100
        
        # 涨幅超过0.3%时买入（降低阈值以便测试）
        if price_change_pct > 0.3:
            self.send_signal(bar.symbol, Direction.LONG, strength=0.8)
            self.buy_signals += 1
        
        # 跌幅超过0.3%时卖出
        elif price_change_pct < -0.3:
            # 对于测试，即使没有持仓也生成卖出信号
            # 在实际系统中，这里应该检查持仓
            self.send_signal(bar.symbol, Direction.SHORT, strength=0.8)
            self.sell_signals += 1
    
    def get_position(self, symbol: str) -> int:
        """
        获取持仓
        
        Args:
            symbol: 股票代码
            
        Returns:
            持仓数量
        """
        if self.portfolio:
            return self.portfolio.get_position(symbol)
        return 0
    
    def get_strategy_info(self) -> dict:
        """获取策略信息"""
        base_info = super().get_strategy_info()
        base_info.update({
            'buy_signals': self.buy_signals,
            'sell_signals': self.sell_signals
        })
        return base_info