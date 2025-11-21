"""
现货回测投资组合实现
具体的资金管理和风控逻辑
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from .base import BasePortfolio
from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from Infrastructure.enums import Direction, OrderType
from DataManager.handlers.handler import BaseDataHandler
from DataManager.schema.bar import BarData


class BacktestPortfolio(BasePortfolio):
    """
    现货回测投资组合
    
    这是系统的"会计师兼风控官"，负责：
    1. 资金管理 (Capital Management)：维护现金和持仓
    2. 信号转化 (Signal -> Order)：将策略建议转化为具体订单
    3. 成交处理 (Fill Processing)：实际扣款、记账
    4. 盯市 (Mark-to-Market)：更新总资产
    """
    
    def __init__(self, data_handler: BaseDataHandler, initial_capital: float = 100000.0):
        """
        初始化投资组合
        
        Args:
            data_handler: 数据处理器，用于查询当前价格
            initial_capital: 初始资金，默认10万
        """
        super().__init__(data_handler, initial_capital)
        
        # 核心状态
        self.current_cash = initial_capital  # 当前可用现金
        self.positions: Dict[str, int] = {}  # 持仓字典 {symbol: volume}
        self.total_equity = initial_capital  # 总资产 = 现金 + 持仓市值
        
        # 交易统计
        self.total_trades = 0
        self.total_commission = 0.0
        
        self.logger.info(f"BacktestPortfolio 初始化完成")
        self.logger.info(f"初始资金: {self.current_cash:,.2f}")
    
    def update_on_market(self, event: MarketEvent) -> None:
        """
        行情更新时调用（盯市）
        
        重新计算总资产，用于观察资金曲线。
        这不是用来交易的，是用来画资金曲线的。
        
        Args:
            event: 行情事件
        """
        self.market_updates += 1
        
        try:
            # 计算持仓总市值
            positions_value = 0.0
            
            for symbol, volume in self.positions.items():
                if volume > 0:
                    latest_bar = self.data_handler.get_latest_bar(symbol)
                    if latest_bar:
                        positions_value += latest_bar.close_price * volume
                    else:
                        self.logger.warning(f"无法获取 {symbol} 的最新价格")
            
            # 更新总资产
            self.total_equity = self.current_cash + positions_value
            
            # 每100次更新显示一次
            if self.market_updates % 100 == 0:
                self.logger.debug(
                    f"盯市更新 #{self.market_updates}: "
                    f"现金={self.current_cash:,.2f}, "
                    f"持仓={positions_value:,.2f}, "
                    f"总资产={self.total_equity:,.2f}"
                )
        
        except Exception as e:
            self.logger.error(f"盯市更新失败: {e}")
    
    def update_on_fill(self, event: FillEvent) -> None:
        """
        成交时调用（记账逻辑）
        
        这是最关键的记账逻辑，必须确保资金计算准确。
        无论买卖，都要从现金中减去手续费。
        
        Args:
            event: 成交事件
        """
        self.fills_processed += 1
        self.total_trades += 1
        
        try:
            symbol = event.symbol
            direction = event.direction
            volume = event.volume
            price = event.price
            commission = event.commission
            
            trade_value = price * volume  # 成交金额
            net_value = event.net_value   # 净值（扣除手续费后）
            
            self.logger.info(
                f"成交处理: {symbol} {direction.value} {volume}股 "
                f"@{price:.2f}, 成交额:{trade_value:.2f}, 手续费:{commission:.2f}"
            )
            
            if direction == Direction.LONG:
                # 买入成交：扣钱，加仓
                self.current_cash -= net_value  # 扣除成交金额和手续费
                self.positions[symbol] = self.positions.get(symbol, 0) + volume
                self.total_commission += commission
                
                self.logger.info(
                    f"买入完成: {symbol} 持仓增至 {self.positions[symbol]}股, "
                    f"现金余额: {self.current_cash:,.2f}"
                )
            
            elif direction == Direction.SHORT:
                # 卖出成交：加钱，减仓
                self.current_cash += net_value  # 加上成交净值（已扣除手续费）
                self.positions[symbol] = self.positions.get(symbol, 0) - volume
                self.total_commission += commission
                
                # 如果持仓为0，从字典中删除
                if self.positions[symbol] <= 0:
                    del self.positions[symbol]
                    self.logger.info(f"卖出完成: {symbol} 持仓清零")
                else:
                    self.logger.info(
                        f"卖出完成: {symbol} 持仓减至 {self.positions[symbol]}股, "
                        f"现金余额: {self.current_cash:,.2f}"
                    )
            
            else:
                self.logger.warning(f"未知的交易方向: {direction}")
        
        except Exception as e:
            self.logger.error(f"成交处理失败: {e}")
    
    def process_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """
        处理信号，返回订单（信号转订单逻辑）
        
        这是最复杂的逻辑，涉及仓位计算和风控检查。
        
        Args:
            event: 信号事件
            
        Returns:
            订单事件，如果不符合条件则返回None
        """
        self.signals_processed += 1
        
        try:
            symbol = event.symbol
            direction = event.direction
            strength = event.strength
            
            self.logger.debug(
                f"处理信号: {symbol} {direction.value} "
                f"强度:{strength:.2f} @ {event.datetime}"
            )
            
            if direction == Direction.LONG:
                return self._process_buy_signal(event)
            elif direction == Direction.SHORT:
                return self._process_sell_signal(event)
            else:
                self.logger.warning(f"未知的信号方向: {direction}")
                return None
        
        except Exception as e:
            self.logger.error(f"信号处理失败: {e}")
            return None
    
    def _process_buy_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """
        处理买入信号
        
        逻辑：
        1. 查询当前价格
        2. 计算可买入数量（全仓买入）
        3. 应用A股规则，向下取整到100的倍数
        4. 风控检查：钱不够则忽略信号
        
        Args:
            event: 买入信号事件
            
        Returns:
            买入订单事件，或None
        """
        symbol = event.symbol
        
        # 尝试不同的股票代码格式来获取价格
        latest_bar = self.data_handler.get_latest_bar(symbol)
        if not latest_bar:
            # 尝试添加交易所后缀
            for suffix in ['.SH', '.SZSE', '.SSE', '.SZ']:
                test_symbol = symbol + suffix
                latest_bar = self.data_handler.get_latest_bar(test_symbol)
                if latest_bar:
                    symbol = test_symbol  # 更新为正确的格式
                    break
        if not latest_bar:
            self.logger.warning(f"无法获取 {symbol} 的当前价格，忽略买入信号")
            return None
        
        current_price = latest_bar.close_price
        
        # 计算最大可买入数量（全仓买入）
        max_shares = int(self.current_cash / current_price)
        
        # 应用A股规则：向下取整到100的倍数
        target_volume = (max_shares // 100) * 100
        
        # 风控检查
        if target_volume == 0:
            self.logger.info(
                f"资金不足，忽略买入信号 {symbol}。"
                f"现金:{self.current_cash:.2f}, 价格:{current_price:.2f}, "
                f"最多买:{max_shares}股（不足100股）"
            )
            return None
        
        # 生成买入订单
        order = OrderEvent(
            symbol=symbol,
            datetime=event.datetime,
            order_type=OrderType.MARKET,
            direction=Direction.LONG,
            volume=target_volume,
            limit_price=0.0  # 市价单
        )
        
        self.logger.info(
            f"生成买入订单: {symbol} {target_volume}股 "
            f"@约{current_price:.2f}, 预计金额:{target_volume * current_price:.2f}"
        )
        
        return order
    
    def _process_sell_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """
        处理卖出信号
        
        逻辑：
        1. 检查是否有持仓
        2. 如果有，生成卖出全部持仓的订单
        
        Args:
            event: 卖出信号事件
            
        Returns:
            卖出订单事件，或None
        """
        symbol = event.symbol
        
        # 检查持仓
        current_position = self.positions.get(symbol, 0)
        
        if current_position <= 0:
            self.logger.info(f"无持仓，忽略卖出信号 {symbol}")
            return None
        
        # 生成卖出订单（卖出全部持仓）
        order = OrderEvent(
            symbol=symbol,
            datetime=event.datetime,
            order_type=OrderType.MARKET,
            direction=Direction.SHORT,
            volume=current_position,
            limit_price=0.0  # 市价单
        )
        
        self.logger.info(f"生成卖出订单: {symbol} {current_position}股（清仓）")
        
        return order
    
    def get_position(self, symbol: str) -> int:
        """
        获取指定股票的持仓数量
        
        Args:
            symbol: 股票代码
            
        Returns:
            持仓数量，0表示没有持仓
        """
        return self.positions.get(symbol, 0)
    
    def get_positions(self) -> Dict[str, int]:
        """
        获取所有持仓
        
        Returns:
            持仓字典的副本
        """
        return self.positions.copy()
    
    def get_cash(self) -> float:
        """
        获取当前现金
        
        Returns:
            当前可用现金
        """
        return self.current_cash
    
    def get_equity(self) -> float:
        """
        获取总资产
        
        Returns:
            总资产（现金 + 持仓市值）
        """
        return self.total_equity
    
    def get_portfolio_info(self) -> dict:
        """
        获取详细的投资组合信息
        
        Returns:
            包含完整投资组合状态的字典
        """
        base_info = super().get_portfolio_info()
        
        # 计算持仓市值
        positions_value = 0.0
        positions_detail = {}
        
        for symbol, volume in self.positions.items():
            if volume > 0:
                latest_bar = self.data_handler.get_latest_bar(symbol)
                if latest_bar:
                    market_value = latest_bar.close_price * volume
                    positions_value += market_value
                    positions_detail[symbol] = {
                        'volume': volume,
                        'current_price': latest_bar.close_price,
                        'market_value': market_value
                    }
        
        # 更新总资产
        self.total_equity = self.current_cash + positions_value
        
        portfolio_info = {
            **base_info,
            'current_cash': self.current_cash,
            'total_equity': self.total_equity,
            'positions_value': positions_value,
            'positions_count': len(self.positions),
            'positions_detail': positions_detail,
            'total_trades': self.total_trades,
            'total_commission': self.total_commission,
            'return_rate': ((self.total_equity - self.initial_capital) / self.initial_capital) * 100
        }
        
        return portfolio_info