"""
策略基类

所有策略必须继承此类，并实现抽象方法
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional


class BaseStrategy(ABC):
    """
    策略基类

    定义了策略的标准生命周期接口，所有具体策略必须实现这些方法

    生命周期：
        initialize() → before_trading() → [on_bar()...] → after_trading()

    Attributes:
        params: 策略参数字典
        name: 策略名称
        context: 运行上下文（包含data_provider, position_manager等）
    """

    def __init__(self, params: Dict[str, Any]):
        """
        初始化策略

        Args:
            params: 策略参数字典
                应包含策略运行所需的所有参数

        Example:
            params = {
                'name': 'MyStrategy',
                'fast_window': 20,
                'slow_window': 50,
                'stop_loss': 0.10
            }
        """
        self.params = params
        self.name = params.get('name', self.__class__.__name__)
        self.context: Optional[Dict[str, Any]] = None
        self.is_initialized: bool = False

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        设置运行上下文

        Args:
            context: 上下文字典，通常包含：
                - data_provider: 数据提供器
                - position_manager: 仓位管理器
                - risk_manager: 风险管理器
                - executor: 执行引擎
                - logger: 日志记录器

        Note:
            通常在策略初始化后、执行前调用
        """
        self.context = context

    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        策略初始化

        在策略开始运行前调用一次，用于：
        - 加载历史数据
        - 初始化指标
        - 创建辅助对象

        Args:
            context: 运行上下文

        Example:
            def initialize(self, context):
                self.data_provider = context['data_provider']
                self.position_manager = context['position_manager']
                self.indicator_cache = {}  # 缓存计算的指标
        """
        pass

    @abstractmethod
    def before_trading(self, date: datetime, context: Dict[str, Any]) -> None:
        """
        盘前处理

        在每个交易日开始前调用，用于：
        - 获取当日候选股票池
        - 计算盘前指标
        - 清理过期数据

        Args:
            date: 交易日期
            context: 运行上下文

        Example:
            def before_trading(self, date, context):
                # 筛选当天可以交易的股票
                self.universe = context['stock_filter'].get_universe(date)
                self.logger.info(f"今日候选股票: {len(self.universe)} 只")
        """
        pass

    @abstractmethod
    def on_bar(self, bar: Any, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        K线处理（核心方法）

        每收到一个K线数据调用一次，用于：
        - 生成交易信号
        - 更新持仓状态
        - 执行交易逻辑

        Args:
            bar: K线数据（BarData对象）
            context: 运行上下文

        Returns:
            可选的信号字典，格式：
            {
                'signals': [Signal1, Signal2, ...],
                'metadata': {...}
            }
            返回None表示不生成信号

        Example:
            def on_bar(self, bar, context):
                # 检查是否满足买入条件
                if self.should_buy(bar):
                    signal = self.generate_buy_signal(bar)
                    return {'signals': [signal]}

                # 检查是否满足卖出条件
                if self.should_sell(bar):
                    signal = self.generate_sell_signal(bar)
                    return {'signals': [signal]}

                return None
        """
        pass

    @abstractmethod
    def after_trading(self, date: datetime, context: Dict[str, Any]) -> None:
        """
        盘后处理

        在每个交易日结束后调用，用于：
        - 计算当日盈亏
        - 生成交易报告
        - 保存中间结果

        Args:
            date: 交易日期
            context: 运行上下文

        Example:
            def after_trading(self, date, context):
                # 生成当日交易报告
                report = self.generate_daily_report(date)
                context['logger'].info(f"当日盈亏: {report['pnl']}")
        """
        pass

    def on_order(self, order: Any, context: Dict[str, Any]) -> None:
        """
        订单回调（可选）

        当订单状态发生变化时调用，用于：
        - 更新订单状态
        - 处理成交
        - 记录日志

        Args:
            order: 订单对象（Order）
            context: 运行上下文

        Note:
            不是所有策略都需要，提供默认空实现
        """
        pass

    def on_trade(self, trade: Any, context: Dict[str, Any]) -> None:
        """
        成交回调（可选）

        当有成交发生时调用，用于：
        - 更新持仓
        - 计算成本
        - 记录日志

        Args:
            trade: 成交对象（Trade）
            context: 运行上下文

        Note:
            不是所有策略都需要，提供默认空实现
        """
        pass

    def terminate(self, context: Dict[str, Any]) -> None:
        """
        策略终止

        在策略停止运行时调用，用于：
        - 清理资源
        - 保存最终结果
        - 关闭连接

        Args:
            context: 运行上下文

        Example:
            def terminate(self, context):
                # 保存最终绩效报告
                final_report = self.generate_final_report()
                self.save_report(final_report)
                context['logger'].info("策略已停止")
        """
        pass

    def validate_params(self) -> List[str]:
        """
        验证策略参数

        在策略初始化时调用，用于检查参数合法性

        Returns:
            错误信息列表，空列表表示验证通过

        Example:
            def validate_params(self):
                errors = []
                if self.params.get('fast_window', 0) >= self.params.get('slow_window', 0):
                    errors.append("快线窗口必须小于慢线窗口")
                if self.params.get('stop_loss', 0) > 0.5:
                    errors.append("止损比例不能超过50%")
                return errors
        """
        return []

    def get_status(self) -> Dict[str, Any]:
        """
        获取策略状态

        运行时调用，用于监控策略状态

        Returns:
            状态字典，包含策略运行的关键信息

        Example:
            def get_status(self):
                return {
                    'is_running': True,
                    'position_count': len(self.position_manager.positions),
                    'today_pnl': self.calculate_today_pnl(),
                    'signal_count': len(self.today_signals)
                }
        """
        return {
            'name': self.name,
            'is_initialized': self.is_initialized,
            'params': self.params
        }


class StrategyContext:
    """
    策略上下文类

    封装策略运行所需的所有组件，避免使用dict

    Attributes:
        data_provider: 数据提供器
        position_manager: 仓位管理器
        risk_manager: 风险管理器
        executor: 执行引擎
        logger: 日志记录器
        event_bus: 事件总线（可选）
    """

    def __init__(
        self,
        data_provider: Any,
        position_manager: Any,
        risk_manager: Any,
        executor: Any,
        logger: Any,
        event_bus: Optional[Any] = None
    ):
        self.data_provider = data_provider
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.executor = executor
        self.logger = logger
        self.event_bus = event_bus

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data_provider': self.data_provider,
            'position_manager': self.position_manager,
            'risk_manager': self.risk_manager,
            'executor': self.executor,
            'logger': self.logger,
            'event_bus': self.event_bus
        }
