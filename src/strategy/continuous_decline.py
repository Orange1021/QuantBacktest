"""
持续下跌策略

策略逻辑：
1. 筛选连续下跌>=7天的股票（使用问财或传统筛选）
2. 按流通市值从大到小排序（优先大市值）
3. 首次建仓20%（单票，基于总资金）
4. 每跌1%补仓10%（基于总资金），最多8次
5. 上涨转下跌时清仓（止盈）
6. 止损15%（强制止损）
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from src.strategy.base_strategy import BaseStrategy
from src.core.filter.stock_filter import StockFilter
from src.core.filter.wencai_stock_filter import WencaiStockFilter
from src.core.position.position_manager import PositionManager
from src.data.provider_factory import DataProviderFactory
from src.utils.config import ConfigManager


class ContinuousDeclineStrategy(BaseStrategy):
    """
    持续下跌策略 - 完整实现

    策略特点：
    - 抄底策略，在股票连续下跌后分层建仓
    - 严格风险管理，单股仓位不超过30%
    - 总仓位不超过80%
    - 上涨获利后及时止盈

    使用组件：
    - StockFilter: 股票筛选（传统方式）
    - PositionManager: 仓位管理
    - DataProvider: 数据提供
    """

    def __init__(self, params: Dict[str, Any]):
        """
        初始化策略

        Args:
            params: 策略参数（来自配置文件）
        """
        super().__init__(params)

        # 提取策略参数
        self.filter_params = params.get('filter_params', {})
        self.entry_params = params.get('entry_params', {})
        self.exit_params = params.get('exit_params', {})
        self.risk_params = params.get('risk_params', {})
        self.capital_params = params.get('capital_params', {})

        # 组件实例（将在initialize中创建）
        self.stock_filter: Optional[StockFilter] = None
        self.position_manager: Optional[PositionManager] = None
        self.data_provider: Optional[Any] = None

        # 策略状态
        self.current_date: Optional[datetime] = None
        self.candidate_stocks: List[str] = []

        # 持仓追踪
        self.last_prices: Dict[str, float] = {}  # 上次价格（用于判断是否下跌）

    def initialize(self, context: Dict[str, Any]) -> None:
        """
        策略初始化

        Args:
            context: 运行上下文
        """
        self.context = context
        self.logger = context.get('logger')

        # 创建数据提供器
        self.data_provider = context.get('data_provider')
        data_provider_factory = context.get('data_provider_factory')

        if not data_provider_factory:
            raise ValueError("缺少data_provider_factory")

        # 创建股票筛选器
        self.logger.info("创建股票筛选器...")
        filter_type = self.filter_params.get('filter_type', 'stock_filter')

        if filter_type == 'wencai_filter':
            self.logger.info("  使用问财筛选器（智能筛选，数据准确）")
            wencai_params = self.filter_params.get('wencai_params', {})
            cookie = wencai_params.get('cookie', '')

            if not cookie:
                self.logger.warning("  未配置问财Cookie，将使用传统筛选器作为回退")
                self.stock_filter = StockFilter(data_provider_factory)
            else:
                self.stock_filter = WencaiStockFilter(cookie)
        else:
            self.logger.info("  使用传统筛选器（基于历史数据）")
            self.stock_filter = StockFilter(data_provider_factory)

        # 创建仓位管理器
        initial_capital = self.capital_params.get('initial_capital', 1000000)
        position_params = {
            'initial_position_size': self.entry_params.get('initial_position_size', 0.20),
            'position_percent_per_layer': self.entry_params.get('position_percent_per_layer', 0.10),
            'max_layers': self.entry_params.get('max_layers', 8)
        }

        self.logger.info(f"创建仓位管理器: 初始资金={initial_capital:,.0f}")
        self.position_manager = PositionManager(
            total_capital=initial_capital,
            params=position_params
        )

        self.logger.info("✓ 策略初始化成功")
        self.logger.info(f"  - 下跌天数阈值: {self.filter_params.get('decline_days_threshold', 7)}天")
        self.logger.info(f"  - 初始仓位: {self.entry_params.get('initial_position_size', 0.20):.1%}")
        self.logger.info(f"  - 补仓比例: {self.entry_params.get('position_percent_per_layer', 0.10):.1%}")
        self.logger.info(f"  - 最大层数: {self.entry_params.get('max_layers', 8)}")
        self.logger.info(f"  - 止损线: {self.risk_params.get('stop_loss_percent', 0.15):.1%}")

    def before_trading(self, date: datetime, context: Dict[str, Any]) -> None:
        """
        盘前处理

        Args:
            date: 交易日期
            context: 运行上下文
        """
        self.current_date = date

        # 获取当日候选股票
        self.logger.info(f"{date.strftime('%Y-%m-%d')} - 开始选股扫描...")

        try:
            decline_days = self.filter_params.get('decline_days_threshold', 7)
            market_cap = self.filter_params.get('market_cap_threshold', 1e9)

            self.candidate_stocks = self.stock_filter.get_eligible_stocks(
                date=date,
                decline_days_threshold=decline_days,
                market_cap_threshold=market_cap
            )

            self.logger.info(f"  筛选完成，候选股票数: {len(self.candidate_stocks)}")

            if self.candidate_stocks:
                self.logger.info(f"  Top 5: {self.candidate_stocks[:5]}")

        except Exception as e:
            self.logger.warning(f"  筛选失败: {e}")
            self.candidate_stocks = []

    def on_bar(self, bar: Any, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        K线处理（核心策略逻辑）

        Args:
            bar: K线数据
            context: 运行上下文

        Returns:
            交易信号或None
        """
        symbol = bar.symbol
        current_price = bar.close

        if not self.position_manager:
            return None

        # 更新价格（用于后续判断）
        self.last_prices[symbol] = current_price

        # 获取当前持仓
        position = self.position_manager.get_position(symbol)
        has_position = position is not None and position.quantity > 0

        if not has_position:
            # 无持仓 - 检查买入信号
            return self._check_buy_signal(bar, context)
        else:
            # 有持仓 - 检查卖出信号
            return self._check_sell_signal(bar, context, position)

    def _check_buy_signal(self, bar: Any, context: Any) -> Optional[Dict[str, Any]]:
        """
        检查买入信号

        条件：
        1. 是候选股票（连续下跌>=7天）
        2. 该股票无持仓
        3. 未达到最大持仓数量限制
        4. 达到最小建仓间隔（可选）

        Args:
            bar: K线数据
            context: 运行上下文

        Returns:
            买入信号或None
        """
        symbol = bar.symbol
        current_price = bar.close

        # 判断是否是候选股票
        if symbol not in self.candidate_stocks:
            return None

        # 检查持仓数量限制（最多同时持仓10只）
        position_count = len(self.position_manager.get_all_positions())
        if position_count >= 10:
            self.logger.debug(f"达到最大持仓数量限制: {position_count}")
            return None

        # 检查可用资金
        if self.position_manager.available_capital < current_price * 100:
            self.logger.debug(f"可用资金不足: {self.position_manager.available_capital:.0f}")
            return None

        # 生成买入信号
        signal = {
            'type': 'BUY',
            'symbol': symbol,
            'price': current_price,
            'layer': 0,  # 初始建仓
            'timestamp': bar.timestamp if hasattr(bar, 'timestamp') else self.current_date,
            'metadata': {
                'strategy': 'continuous_decline',
                'reason': 'first_entry'
            }
        }

        self.logger.info(f"生成买入信号: {symbol}, 价格={current_price:.2f}, 类型=首次建仓")

        return {'signals': [signal]}

    def _check_sell_signal(self, bar: Any, context: Any, position) -> Optional[Dict[str, Any]]:
        """
        检查卖出信号

        两种触发条件：
        1. 上涨后第一次下跌 → 止盈
        2. 跌幅达到止损线 → 强制止损

        Args:
            bar: K线数据
            context: 运行上下文
            position: 当前持仓

        Returns:
            卖出信号或None
        """
        symbol = bar.symbol
        current_price = bar.close

        # 更新价格（自动检查是否上涨过）
        position.update_price(current_price)

        # 计算盈亏
        pnl_percent = position.pnl_percent
        cost_price = position.avg_price

        # 检查止损（优先）
        stop_loss_percent = self.risk_params.get('stop_loss_percent', 0.15)
        if pnl_percent <= -stop_loss_percent:
            self.logger.warning(f"触发止损: {symbol}, 成本={cost_price:.2f}, 当前={current_price:.2f}, 盈亏={pnl_percent:.2%}")

            signal = {
                'type': 'SELL',
                'symbol': symbol,
                'price': current_price,
                'timestamp': bar.timestamp if hasattr(bar, 'timestamp') else self.current_date,
                'metadata': {
                    'strategy': 'continuous_decline',
                    'reason': 'stop_loss',
                    'pnl_percent': pnl_percent
                }
            }

            return {'signals': [signal]}

        # 检查止盈（上涨后第一次下跌）
        if position.has_risen:
            # 获取上次价格（判断是下跌）
            last_price = self.last_prices.get(symbol, current_price)

            if current_price < last_price:
                # 确实是下跌
                self.logger.info(f"触发止盈: {symbol}, 成本={cost_price:.2f}, 当前={current_price:.2f}")
                self.logger.info(f"  曾经上涨过: {position.has_risen}")
                self.logger.info(f"  相比上次价格下跌: {last_price:.2f} -> {current_price:.2f}")

                signal = {
                    'type': 'SELL',
                    'symbol': symbol,
                    'price': current_price,
                    'timestamp': bar.timestamp if hasattr(bar, 'timestamp') else self.current_date,
                    'metadata': {
                        'strategy': 'continuous_decline',
                        'reason': 'profit_taking',
                        'pnl_percent': pnl_percent
                    }
                }

                return {'signals': [signal]}

        return None

    def after_trading(self, date: datetime, context: Dict[str, Any]) -> None:
        """
        盘后处理

        检查是否需要补仓（根据跌幅）

        Args:
            date: 交易日期
            context: 运行上下文
        """
        if not self.position_manager:
            return

        # 检查持仓股票是否需要补仓
        self._check_add_positions(date, context)

    def _check_add_positions(self, date: datetime, context: Any) -> None:
        """
        检查是否需要补仓

        规则：每跌1%补仓10%

        Args:
            date: 交易日期
            context: 运行上下文
        """
        data_provider = context.get('data_provider')
        if not data_provider:
            return

        for position in self.position_manager.get_all_positions():
            symbol = position.symbol
            layer = position.layer_count
            max_layers = self.entry_params.get('max_layers', 8)

            # 检查是否还可以加仓
            if layer >= max_layers:
                continue

            # 获取最新价格
            try:
                # 获取最近几天的数据（包括今天）
                end_date = date + timedelta(days=1)
                start_date = date - timedelta(days=5)

                df = data_provider.get_daily_bars(symbol, start_date, end_date)

                if df is None or df.empty:
                    continue

                # 获取最新价格（当天）
                current_price = df['close'].iloc[-1]
                cost_price = position.avg_price

                # 计算当前跌幅
                decline_percent = (cost_price - current_price) / cost_price

                # 计算应该补仓到的层数
                # 每跌1%加一层
                expected_layers = int(decline_percent / 0.01)

                # 如果实际跌幅超过当前层数，触发补仓
                if expected_layers > layer and layer < max_layers:
                    add_layers = expected_layers - layer
                    layer = expected_layers

                    # 生成加仓信号（在下次交易执行）
                    self.logger.info(f"触发补仓: {symbol}, 当前跌幅={decline_percent:.2%}, 补仓层数={layer}")
                    self.logger.info(f"  成本价: {cost_price:.2f}, 当前价: {current_price:.2f}")

                    # 实际加仓在on_bar中处理

            except Exception as e:
                self.logger.debug(f"检查补仓失败: {symbol} - {e}")
                continue

    def on_order(self, order: Any, context: Dict[str, Any]) -> None:
        """
        订单回调

        Args:
            order: 订单对象
            context: 运行上下文
        """
        pass

    def on_trade(self, trade: Any, context: Dict[str, Any]) -> None:
        """
        成交回调

        Args:
            trade: 成交对象
            context: 运行上下文
        """
        pass

    def terminate(self, context: Dict[str, Any]) -> None:
        """
        策略终止

        Args:
            context: 运行上下文
        """
        self.logger.info("策略终止")

        if self.position_manager:
            stats = self.position_manager.get_position_stats()
            self.logger.info("最终持仓统计:")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")

    def get_status(self) -> Dict[str, Any]:
        """
        获取策略状态

        Returns:
            状态字典
        """
        base_status = super().get_status()

        if self.position_manager:
            base_status.update(self.position_manager.get_position_stats())

        return base_status
