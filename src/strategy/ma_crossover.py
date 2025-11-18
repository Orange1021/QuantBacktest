"""
均线交叉策略示例（MA Crossover Strategy）

演示如何使用策略基类和工厂创建新策略

策略逻辑：
    1. 选择所有股票（或指定股票池）
    2. 计算短期均线（如20日）和长期均线（如50日）
    3. 金叉（短期上穿长期）→ 买入
    4. 死叉（短期下穿长期）→ 卖出
    5. 设置止损线
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from src.strategy.base_strategy import BaseStrategy
from src.strategy.factory import StrategyRegistry
from src.data.models import Signal, SignalType


@StrategyRegistry.register('ma_crossover')
class MACrossoverStrategy(BaseStrategy):
    """
    均线交叉策略

    参数：
        fast_window: 短期均线窗口（默认20日）
        slow_window: 长期均线窗口（默认50日）
        stop_loss: 止损比例（默认0.10，即10%）
        position_size: 仓位大小（默认0.10，即10%）
        use_atr_stop: 是否使用ATR止损（默认false）
        atr_window: ATR窗口（默认14日）
        atr_multiplier: ATR倍数（默认2.0）

    示例配置：
        strategy:
          name: "ma_crossover"
          params:
            fast_window: 20
            slow_window: 50
            stop_loss: 0.10
            position_size: 0.10
    """

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)

        # 参数设置
        self.fast_window = int(params.get('fast_window', 20))
        self.slow_window = int(params.get('slow_window', 50))
        self.stop_loss = float(params.get('stop_loss', 0.10))
        self.position_size = float(params.get('position_size', 0.10))
        self.use_atr_stop = bool(params.get('use_atr_stop', False))
        self.atr_window = int(params.get('atr_window', 14))
        self.atr_multiplier = float(params.get('atr_multiplier', 2.0))

        # 缓存
        self.indicator_cache: Dict[str, pd.DataFrame] = {}
        self.cache_size = 100  # 缓存最近100天的数据

        # 持仓记录
        self.active_positions: Dict[str, dict] = {}

    def validate_params(self) -> List[str]:
        """参数验证"""
        errors = []

        if self.fast_window >= self.slow_window:
            errors.append(f"快线窗口（{self.fast_window}）必须小于慢线窗口（{self.slow_window}）")

        if self.fast_window < 2:
            errors.append("快线窗口必须大于等于2")

        if self.slow_window < 5:
            errors.append("慢线窗口必须大于等于5")

        if self.stop_loss <= 0 or self.stop_loss > 0.5:
            errors.append("止损比例必须在0-0.5之间")

        if self.position_size <= 0 or self.position_size > 1:
            errors.append("仓位大小必须在0-1之间")

        return errors

    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化"""
        self.logger = context.get('logger')
        self.data_provider = context.get('data_provider')
        self.position_manager = context.get('position_manager')
        self.risk_manager = context.get('risk_manager')

        if self.logger:
            self.logger.info(f"均线交叉策略初始化: {self.fast_window}/{self.slow_window}")

    def before_trading(self, date, context: Dict[str, Any]) -> None:
        """盘前处理"""
        # 清理过期缓存
        if len(self.indicator_cache) > 1000:
            self.indicator_cache.clear()
            if self.logger:
                self.logger.debug("清理指标缓存")

    def calculate_indicators(self, symbol: str, end_date) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            symbol: 股票代码
            end_date: 结束日期

        Returns:
            DataFrame包含：close, ma_fast, ma_slow, atr（可选）
        """
        # 检查缓存
        cache_key = f"{symbol}_{end_date.date()}"
        if cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        # 计算开始日期
        start_date = end_date - pd.Timedelta(days=self.slow_window + self.atr_window + 10)

        # 获取历史数据
        df = self.data_provider.get_daily_bars(symbol, start_date, end_date)

        if len(df) < self.slow_window:
            return pd.DataFrame()

        # 计算均线
        df['ma_fast'] = df['close'].rolling(window=self.fast_window, min_periods=self.fast_window).mean()
        df['ma_slow'] = df['close'].rolling(window=self.slow_window, min_periods=self.slow_window).mean()

        # 计算ATR（如果启用）
        if self.use_atr_stop:
            # 计算TR
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

            # 计算ATR
            df['atr'] = df['tr'].rolling(window=self.atr_window, min_periods=self.atr_window).mean()

            # 清理中间列
            df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1, inplace=True)

        # 保存到缓存
        self.indicator_cache[cache_key] = df.tail(self.cache_size).copy()

        return self.indicator_cache[cache_key]

    def should_buy(self, symbol: str, current_date) -> bool:
        """判断是否满足买入条件"""
        df = self.calculate_indicators(symbol, current_date)

        if len(df) < 2:
            return False

        current = df.iloc[-1]
        prev = df.iloc[-2]

        # 金叉：前一日快线 <= 慢线，当日快线 > 慢线
        if (pd.isna(prev['ma_fast']) or pd.isna(prev['ma_slow']) or
            pd.isna(current['ma_fast']) or pd.isna(current['ma_slow'])):
            return False

        return prev['ma_fast'] <= prev['ma_slow'] and current['ma_fast'] > current['ma_slow']

    def should_sell(self, symbol: str, current_date, position) -> bool:
        """判断是否满足卖出条件"""
        df = self.calculate_indicators(symbol, current_date)

        if len(df) < 2:
            return False

        current = df.iloc[-1]
        prev = df.iloc[-2]

        # 基本条件：数据完整
        if (pd.isna(prev['ma_fast']) or pd.isna(prev['ma_slow']) or
            pd.isna(current['ma_fast']) or pd.isna(current['ma_slow'])):
            return False

        # 条件1：死叉（短期下穿长期）
        death_cross = prev['ma_fast'] >= prev['ma_slow'] and current['ma_fast'] < current['ma_slow']

        # 条件2：止损
        stop_loss_triggered = False
        if position and hasattr(position, 'pnl_percent'):
            stop_loss_triggered = position.pnl_percent <= -self.stop_loss

        # 条件3：ATR跟踪止损（如果启用）
        atr_stop_triggered = False
        if (self.use_atr_stop and position and
            'atr' in current and not pd.isna(current['atr'])):
            stop_price = position.avg_price - self.atr_multiplier * current['atr']
            atr_stop_triggered = current['close'] <= stop_price

        return death_cross or stop_loss_triggered or atr_stop_triggered

    def on_bar(self, bar, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """K线处理"""
        symbol = bar.symbol

        # 检查是否需要交易
        position = self.position_manager.get_position(symbol) if self.position_manager else None

        signals = []

        # 检查买入
        if position is None and self.should_buy(symbol, bar.datetime):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=bar.close,
                quantity=int(self.position_size * 100),  # 简化计算
                timestamp=bar.datetime,
                metadata={
                    'reason': 'golden_cross',
                    'ma_fast': self.fast_window,
                    'ma_slow': self.slow_window
                }
            )
            signals.append(signal)

            if self.logger:
                self.logger.info(f"📈 买入信号: {symbol} @ {bar.close:.2f} (金叉)")

        # 检查卖出
        elif position is not None and self.should_sell(symbol, bar.datetime, position):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                price=bar.close,
                quantity=position.quantity,
                timestamp=bar.datetime,
                metadata={
                    'reason': 'death_cross_or_stop_loss',
                    'pnl_percent': getattr(position, 'pnl_percent', 0)
                }
            )
            signals.append(signal)

            if self.logger:
                reason = "死叉" if position.pnl_percent > -self.stop_loss else "止损"
                self.logger.info(f"📉 卖出信号: {symbol} @ {bar.close:.2f} ({reason})")

        # 返回信号
        if signals:
            return {
                'signals': signals,
                'metadata': {
                    'symbol': symbol,
                    'timestamp': bar.datetime
                }
            }

        return None

    def after_trading(self, date, context: Dict[str, Any]) -> None:
        """盘后处理"""
        # 清理缓存数据
        if len(self.indicator_cache) > 1000:
            # 保留最近20个交易日的缓存
            keys_to_delete = list(self.indicator_cache.keys())[:-20]
            for key in keys_to_delete:
                del self.indicator_cache[key]

        if self.logger:
            self.logger.debug(f"盘后处理: {date.date()}")

    def get_status(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            'name': self.name,
            'is_initialized': self.is_initialized,
            'fast_window': self.fast_window,
            'slow_window': self.slow_window,
            'stop_loss': self.stop_loss,
            'position_size': self.position_size,
            'cache_size': len(self.indicator_cache),
            'use_atr_stop': self.use_atr_stop
        }


# 策略说明文档
__strategy_doc__ = """
均线交叉策略（MA Crossover Strategy）

这是一个经典的趋势跟踪策略，使用两条移动平均线（快线和慢线）来捕捉趋势。

策略参数（params）：
    fast_window (int): 短期均线窗口，默认20日
    slow_window (int): 长期均线窗口，默认50日
    stop_loss (float): 止损比例，默认0.10（10%）
    position_size (float): 仓位大小，默认0.10（10%资金）
    use_atr_stop (bool): 是否启用ATR跟踪止损，默认False
    atr_window (int): ATR计算窗口，默认14日
    atr_multiplier (float): ATR倍数，默认2.0

使用示例：
    1. 配置文件：
        strategy:
          name: "ma_crossover"
          params:
            fast_window: 20
            slow_window: 50
            stop_loss: 0.10
            position_size: 0.10
            use_atr_stop: false

    2. Python代码：
        from src.strategy.factory import StrategyFactory

        params = {
            'fast_window': 20,
            'slow_window': 50,
            'stop_loss': 0.10
        }
        strategy = StrategyFactory().create_strategy('ma_crossover', params)

回测命令：
    python scripts/run_backtest_v2.py --strategy ma_crossover
"""
