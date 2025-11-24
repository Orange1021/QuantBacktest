"""
现货回测投资组合实现
具体的资金管理和风控逻辑
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from .base import BasePortfolio
from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from Infrastructure.enums import Direction, OrderType
from DataManager.handlers.handler import BaseDataHandler
from DataManager.schema.bar import BarData
from Portfolio.sizers import create_sizer


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

        # 交易统计（补充初始化）
        self.total_trades = 0
        self.total_commission = 0.0

        # 资金曲线记录
        self.equity_curve = []  # 记录每日资金变化

        # 成交历史记录（补充初始化）
        self.fill_history = []  # 记录所有成交事件

        # 仓位管理参数（可配置）
        self.max_positions = 10  # 最大同时持仓数量
        self.cash_reserve_ratio = 0.10  # 现金预留比例（10%）

        # 初始化仓位管理器（等权重策略）
        try:
            from config.settings import settings
            sizer_type = settings.get_config('portfolio.sizer.type', 'equal_weight')
            sizer_params = settings.get_config('portfolio.sizer.params', {})
            self.sizer = create_sizer(sizer_type, **sizer_params)
            self.sizer.set_logger(logging.getLogger(__name__))
            self.logger.info(f"仓位管理器初始化成功: {sizer_type}")
        except Exception as e:
            self.logger.warning(f"从配置加载Sizer失败 ({e})，使用默认等权重策略")
            self.sizer = create_sizer('equal_weight', max_positions=self.max_positions)
            self.sizer.set_logger(logging.getLogger(__name__))

        self.logger.info(f"BacktestPortfolio 初始化完成")
        self.logger.info(f"初始资金: {self.current_cash:,.2f}")
        self.logger.info(f"最大持仓数: {self.max_positions}")
        self.logger.info(f"现金预留比例: {self.cash_reserve_ratio:.2%}")
    
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
            
            # 记录资金曲线
            self._record_equity_curve(event.bar.datetime, positions_value)
            
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
        使用修复后的 FillEvent.net_value 属性，确保手续费计算正确。
        
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
            net_value = event.net_value   # 净值（已正确计算手续费）
            
            # 资金变动前的余额，用于验证
            cash_before = self.current_cash
            
            self.logger.info(
                f"成交处理: {symbol} {direction.value} {volume}股 "
                f"@{price:.2f}, 成交额:{trade_value:.2f}, 手续费:{commission:.2f}, 净值:{net_value:.2f}"
            )
            
            if direction == Direction.LONG:
                # 买入成交：现金减少 = 成交金额 + 手续费
                self.current_cash -= net_value  # net_value 已包含手续费
                self.positions[symbol] = self.positions.get(symbol, 0) + volume
                self.total_commission += commission
                
                # 验证资金计算正确性
                expected_cash = cash_before - trade_value - commission
                if abs(self.current_cash - expected_cash) > 0.01:  # 1分钱误差容忍
                    self.logger.error(
                        f"资金计算错误！期望:{expected_cash:.2f}, 实际:{self.current_cash:.2f}, "
                        f"差异:{abs(self.current_cash - expected_cash):.2f}"
                    )
                
                self.logger.info(
                    f"买入完成: {symbol} 持仓增至 {self.positions[symbol]}股, "
                    f"现金余额: {self.current_cash:,.2f} (减少:{net_value:.2f})"
                )
            
            elif direction == Direction.SHORT:
                # 卖出成交：现金增加 = 成交金额 - 手续费
                self.current_cash += net_value  # net_value 已扣除手续费
                self.positions[symbol] = self.positions.get(symbol, 0) - volume
                self.total_commission += commission
                
                # 验证资金计算正确性
                expected_cash = cash_before + trade_value - commission
                if abs(self.current_cash - expected_cash) > 0.01:  # 1分钱误差容忍
                    self.logger.error(
                        f"资金计算错误！期望:{expected_cash:.2f}, 实际:{self.current_cash:.2f}, "
                        f"差异:{abs(self.current_cash - expected_cash):.2f}"
                    )
                
                # 如果持仓为0或负数，从字典中删除
                if self.positions[symbol] <= 0:
                    del self.positions[symbol]
                    self.logger.info(f"卖出完成: {symbol} 持仓清零")
                else:
                    self.logger.info(
                        f"卖出完成: {symbol} 持仓减至 {self.positions[symbol]}股, "
                        f"现金余额: {self.current_cash:,.2f} (增加:{net_value:.2f})"
                    )
            
            else:
                self.logger.warning(f"未知的交易方向: {direction}")
                return
            
            # 更新总资产
            self._update_total_equity()
            
            # 新增：保存成交记录
            self._record_fill(event)
            
            # 资金安全检查
            if self.current_cash < 0:
                self.logger.error(f"警告：现金余额为负数！{self.current_cash:.2f}")
        
        except Exception as e:
            self.logger.error(f"成交处理失败: {e}")
            # 记录错误状态，但不中断整个回测
            self.logger.error(f"错误时的资金状态: 现金={self.current_cash:.2f}, 持仓={self.positions}")
    
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
        处理买入信号（使用Sizer策略模式）

        逻辑：
        1. 委托Sizer计算目标资金
        2. 投资组合执行最终风控
        3. 应用A股规则（100股倍数）

        Args:
            event: 买入信号事件

        Returns:
            买入订单事件，或None
        """
        symbol = event.symbol

        # 风控检查1：是否已达到最大持仓数量
        if len(self.positions) >= self.max_positions:
            self.logger.info(
                f"已达最大持仓数({self.max_positions})，忽略买入信号 {symbol}。"
                f"当前持仓: {len(self.positions)}只"
            )
            return None

        # 风控检查2：检查是否已有该股票持仓（避免重复建仓）
        if symbol in self.positions and self.positions[symbol] > 0:
            self.logger.info(
                f"已有持仓，忽略买入信号 {symbol}。"
                f"当前持仓:{self.positions[symbol]}股"
            )
            return None

        # 查询当前价格
        latest_bar = self.data_handler.get_latest_bar(symbol)
        if not latest_bar:
            self.logger.warning(f"无法获取 {symbol} 的当前价格，忽略买入信号")
            return None

        current_price = latest_bar.close_price

        # 使用Sizer计算目标金额（单位：元）
        target_value = self.sizer.calculate_target_value(
            portfolio=self,
            signal=event,
            data_handler=self.data_handler
        )

        if target_value <= 0:
            self.logger.info(
                f"Sizer返回的目标金额为0，忽略买入信号 {symbol}"
            )
            return None

        # 将目标金额转换为股数
        target_volume = int(target_value / current_price)

        # 应用A股规则：向下取整到100的倍数
        target_volume = (target_volume // 100) * 100

        # 风控检查3：数量必须大于0
        if target_volume == 0:
            self.logger.info(
                f"计算出的买入数量为0，忽略买入信号 {symbol}。"
                f"目标金额:{target_value:.2f}, 价格:{current_price:.2f}"
            )
            return None

        # 风控检查4：预估总成本不能超过可用现金
        estimated_commission = max(target_volume * current_price * 0.0003, 5.0)
        estimated_total = target_volume * current_price + estimated_commission

        if estimated_total > self.current_cash:
            # 重新计算可买数量（All-in remaining cash）
            max_affordable = int((self.current_cash - 5.0) / (current_price * 1.0003))
            target_volume = (max_affordable // 100) * 100

            if target_volume == 0:
                self.logger.info(
                    f"资金不足，忽略买入信号 {symbol}。"
                    f"现金:{self.current_cash:.2f}, 预估总成本:{estimated_total:.2f}"
                )
                return None

            # 重新计算金额
            estimated_commission = max(target_volume * current_price * 0.0003, 5.0)
            estimated_total = target_volume * current_price + estimated_commission

        # 生成买入订单
        order = OrderEvent(
            symbol=symbol,
            datetime=event.datetime,
            order_type=OrderType.MARKET,
            direction=Direction.LONG,
            volume=target_volume,
            limit_price=0.0  # 市价单
        )

        actual_cost = estimated_total

        self.logger.info(
            f"生成买入订单: {symbol} {target_volume}股 "
            f"@约{current_price:.2f}, 预计金额:{target_volume * current_price:.2f}, "
            f"手续费:{estimated_commission:.2f}, 总成本:{actual_cost:.2f}, "
            f"剩余现金: {self.current_cash - actual_cost:,.2f}"
        )

        return order
    
    def _process_sell_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """
        处理卖出信号
        
        逻辑：
        1. 检查是否有持仓
        2. 如果有，生成卖出全部持仓的订单
        3. 风控检查：避免频繁交易
        
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
        
        # 获取当前价格用于预估
        latest_bar = self.data_handler.get_latest_bar(symbol)
        if not latest_bar:
            self.logger.warning(f"无法获取 {symbol} 的当前价格，忽略卖出信号")
            return None
        
        current_price = latest_bar.close_price
        
        # 风控检查：预估卖出后的资金，避免过度频繁交易
        estimated_proceeds = current_position * current_price
        estimated_commission = max(estimated_proceeds * 0.0003, 5.0)  # 0.03%或5元取大
        estimated_net = estimated_proceeds - estimated_commission
        
        # 如果卖出金额太小（比如低于1000元），可能不值得交易
        if estimated_net < 1000.0:
            self.logger.info(
                f"持仓价值过低，忽略卖出信号 {symbol}。"
                f"预估净收入:{estimated_net:.2f}, 持仓:{current_position}股"
            )
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
        
        self.logger.info(
            f"生成卖出订单: {symbol} {current_position}股（清仓）"
            f"@约{current_price:.2f}, 预估收入:{estimated_net:.2f}, 手续费:{estimated_commission:.2f}"
        )
        
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
    
    def _record_equity_curve(self, current_time: datetime, positions_value: float) -> None:
        """
        记录资金曲线数据
        
        Args:
            current_time: 当前时间
            positions_value: 持仓市值
        """
        equity_point = {
            'datetime': current_time,
            'total_equity': self.total_equity,
            'cash': self.current_cash,
            'positions_value': positions_value
        }
        
        self.equity_curve.append(equity_point)
    
    def _update_total_equity(self) -> None:
        """
        更新总资产
        
        总资产 = 现金 + 持仓市值
        """
        positions_value = 0.0
        
        for symbol, volume in self.positions.items():
            if volume > 0:
                latest_bar = self.data_handler.get_latest_bar(symbol)
                if latest_bar:
                    positions_value += latest_bar.close_price * volume
                else:
                    self.logger.warning(f"无法获取 {symbol} 的最新价格，市值计算可能不准确")
        
        self.total_equity = self.current_cash + positions_value

    def _record_fill(self, event: FillEvent) -> None:
        """
        记录成交事件到历史记录
        
        Args:
            event: 成交事件
        """
        fill_record = {
            'datetime': event.datetime,
            'symbol': event.symbol,
            'direction': event.direction.value,
            'volume': event.volume,
            'price': event.price,
            'commission': event.commission,
            'trade_value': event.trade_value,
            'net_value': event.net_value
        }
        
        self.fill_history.append(fill_record)
        
        self.logger.debug(
            f"记录成交: {event.symbol} {event.direction.value} {event.volume}股 "
            f"@{event.price:.2f}, 手续费:{event.commission:.2f}"
        )
    
    def get_fill_history(self) -> List[Dict[str, Any]]:
        """
        获取成交历史记录
        
        Returns:
            成交记录列表的副本
        """
        return self.fill_history.copy()
    
    def get_equity_curve(self) -> list:
        """
        获取资金曲线数据
        
        Returns:
            资金曲线数据列表
        """
        return self.equity_curve.copy()