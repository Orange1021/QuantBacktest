"""
仓位管理策略模块
定义各种资金分配策略（Sizer）

职责：
1. 计算每个信号的目标持仓金额
2. 支持等权重、固定比例、信号强度加权等策略
3. 抽象策略模式，易于扩展新的分配方式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from Infrastructure.events import SignalEvent


class BaseSizer(ABC):
    """
    仓位管理策略基类

    所有具体的仓位策略都必须实现 calculate_target_value 方法
    """

    def __init__(self, **kwargs):
        """
        初始化参数

        Args:
            **kwargs: 子类需要的参数
        """
        self.params = kwargs
        self.logger = None

    def set_logger(self, logger):
        """设置日志记录器"""
        self.logger = logger

    @abstractmethod
    def calculate_target_value(
        self,
        portfolio,
        signal: SignalEvent,
        data_handler
    ) -> float:
        """
        计算本次交易的目标资金额度

        Args:
            portfolio: 投资组合对象，提供资金和持仓信息
            signal: 信号事件，提供股票代码和信号强度
            data_handler: 数据处理器，用于查询历史数据

        Returns:
            float: 目标持仓金额（例如 20000.0 表示买入 2万元）
                    返回 0 表示不买入
        """
        pass

    def get_param(self, key: str, default: Any = None) -> Any:
        """
        获取参数值

        Args:
            key: 参数名
            default: 默认值

        Returns:
            参数值或默认值
        """
        return self.params.get(key, default)


class EqualWeightSizer(BaseSizer):
    """
    等权重分配策略

    每只股票分配相同的资金额度
    目标金额 = 总资金 / 最大持仓数量
    """

    def calculate_target_value(
        self,
        portfolio,
        signal: SignalEvent,
        data_handler
    ) -> float:
        """
        计算等权重目标金额

        Args:
            portfolio: 投资组合对象
            signal: 信号事件（未使用）
            data_handler: 数据处理器（未使用）

        Returns:
            float: 每只股票的目标持仓金额
        """
        # 获取最大持仓数，默认5只
        max_positions = self.get_param('max_positions', 5)

        if max_positions == 0:
            if self.logger:
                self.logger.warning("最大持仓数配置为0")
            return 0.0

        # 计算每只股票的目标金额
        target_value = portfolio.total_equity / max_positions

        # 确保不超过可用现金（扣除预留部分）
        cash_reserve_ratio = self.get_param('cash_reserve_ratio', 0.10)
        max_usable_cash = portfolio.current_cash * (1 - cash_reserve_ratio)

        target_value = min(target_value, max_usable_cash)

        if self.logger:
            self.logger.debug(
                f"等权重分配: {portfolio.total_equity:,.2f} / {max_positions} = "
                f"{target_value:,.2f}"
            )

        return target_value


class FixedRatioSizer(BaseSizer):
    """
    固定比例分配策略

    每只股票分配固定比例的资金
    目标金额 = 总资金 * 固定比例
    """

    def calculate_target_value(
        self,
        portfolio,
        signal: SignalEvent,
        data_handler
    ) -> float:
        """
        计算固定比例目标金额

        Args:
            portfolio: 投资组合对象
            signal: 信号事件（未使用）
            data_handler: 数据处理器（未使用）

        Returns:
            float: 目标持仓金额
        """
        # 获取固定比例，默认10%
        ratio = self.get_param('ratio', 0.10)

        # 确保不超过可用现金（扣除预留部分）
        cash_reserve_ratio = self.get_param('cash_reserve_ratio', 0.10)
        max_usable_cash = portfolio.current_cash * (1 - cash_reserve_ratio)

        target_value = portfolio.total_equity * ratio
        target_value = min(target_value, max_usable_cash)

        if self.logger:
            self.logger.debug(
                f"固定比例分配: {portfolio.total_equity:,.2f} * {ratio:.2%} = "
                f"{target_value:,.2f}"
            )

        return target_value


class SignalWeightedSizer(BaseSizer):
    """
    信号强度加权分配策略

    根据信号强度分配不同比例的仓位
    信号强度1.0 → 100%基准仓位
    信号强度0.5 → 50%基准仓位
    """

    def calculate_target_value(
        self,
        portfolio,
        signal: SignalEvent,
        data_handler
    ) -> float:
        """
        计算信号加权目标金额

        Args:
            portfolio: 投资组合对象
            signal: 信号事件（使用信号强度）
            data_handler: 数据处理器（未使用）

        Returns:
            float: 目标持仓金额
        """
        # 获取基准比例，默认10%
        base_ratio = self.get_param('base_ratio', 0.10)

        # 获取信号强度
        strength = getattr(signal, 'strength', 1.0)

        # 信号强度加权
        target_value = portfolio.total_equity * base_ratio * strength

        # 确保不超过可用现金（扣除预留部分）
        cash_reserve_ratio = self.get_param('cash_reserve_ratio', 0.10)
        max_usable_cash = portfolio.current_cash * (1 - cash_reserve_ratio)

        target_value = min(target_value, max_usable_cash)

        if self.logger:
            self.logger.debug(
                f"信号加权分配: {portfolio.total_equity:,.2f} * {base_ratio:.2%} * "
                f"{strength:.2f} = {target_value:,.2f}"
            )

        return target_value


class ATRSizer(BaseSizer):
    """
    ATR波动率仓位管理策略

    根据股票的历史波动率(ATR)动态调整仓位
    波动率高的股票分配较少资金，波动率低的股票分配较多资金
    """

    def calculate_target_value(
        self,
        portfolio,
        signal: SignalEvent,
        data_handler
    ) -> float:
        """
        计算ATR目标金额

        Args:
            portfolio: 投资组合对象
            signal: 信号事件
            data_handler: 数据处理器（用于查询ATR）

        Returns:
            float: 目标持仓金额
        """
        # 获取ATR周期，默认20
        atr_period = self.get_param('atr_period', 20)

        # 查询ATR值
        try:
            atr_data = data_handler.get_latest_n_bars(signal.symbol, atr_period)
            if atr_data is None or len(atr_data) < atr_period:
                if self.logger:
                    self.logger.warning(
                        f"{signal.symbol} 数据不足，无法计算ATR，使用默认值"
                    )
                return 0.0

            # 计算ATR（简化版本，实际应该使用talib或pandas_ta）
            import numpy as np
            closes = np.array([bar.close_price for bar in atr_data])
            highs = np.array([bar.high_price for bar in atr_data])
            lows = np.array([bar.low_price for bar in atr_data])

            # ATR = 平均真实波幅
            tr = np.maximum(highs - lows, np.maximum(
                abs(highs - np.roll(closes, 1)),
                abs(lows - np.roll(closes, 1))
            ))
            atr = np.mean(tr[1:])  # 跳过第一个NaN

            # 获取基准风险金额（例如每单位风险对应1万元）
            base_risk_amount = self.get_param('base_risk_amount', 10000.0)
            risk_per_unit = self.get_param('risk_per_unit', 0.01)  # 1%风险

            # ATR加权：波动率越高，仓位越小
            # 目标金额 = 基准风险金额 / (ATR / 股价)
            latest_price = data_handler.get_latest_bar(signal.symbol).close_price
            volatility_ratio = atr / latest_price

            if volatility_ratio == 0:
                return 0.0

            target_value = base_risk_amount / volatility_ratio * risk_per_unit

            # 确保不超过可用现金
            cash_reserve_ratio = self.get_param('cash_reserve_ratio', 0.10)
            max_usable_cash = portfolio.current_cash * (1 - cash_reserve_ratio)

            target_value = min(target_value, max_usable_cash)

            if self.logger:
                self.logger.debug(
                    f"ATR分配: ATR={atr:.4f}, 股价={latest_price:.2f}, "
                    f"波幅比={volatility_ratio:.4f}, "
                    f"目标金额={target_value:,.2f}"
                )

            return target_value

        except Exception as e:
            if self.logger:
                self.logger.error(f"计算ATR失败: {e}")
            return 0.0


def create_sizer(sizer_type: str, **kwargs) -> BaseSizer:
    """
    工厂函数：根据类型创建仓位管理器

    Args:
        sizer_type: 仓位管理器类型
        **kwargs: 参数

    Returns:
        BaseSizer: 仓位管理器实例
    """
    sizers = {
        'equal_weight': EqualWeightSizer,
        'fixed_ratio': FixedRatioSizer,
        'signal_weighted': SignalWeightedSizer,
        'atr': ATRSizer,
    }

    if sizer_type not in sizers:
        raise ValueError(f"未知的仓位管理器类型: {sizer_type}")

    return sizers[sizer_type](**kwargs)
