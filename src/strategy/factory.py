"""
策略工厂

提供策略注册、创建和管理功能，支持通过配置动态加载策略
"""

from typing import Dict, Type, Any
from src.strategy.base_strategy import BaseStrategy
from src.utils.logger import get_logger


class StrategyRegistry:
    """
    策略注册表

    管理所有可用的策略类，支持装饰器注册和手动注册

    使用示例：
        @StrategyRegistry.register('my_strategy')
        class MyStrategy(BaseStrategy):
            pass

    或者：
        StrategyRegistry.register('my_strategy', MyStrategy)
    """

    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _logger = get_logger('StrategyRegistry')

    @classmethod
    def register(cls, name: str):
        """
        装饰器方式注册策略

        Args:
            name: 策略名称，用于后续创建实例

        Returns:
            装饰器函数

        示例：
            @StrategyRegistry.register('my_strategy')
            class MyStrategy(BaseStrategy):
                def on_bar(self, bar, context):
                    pass
        """
        def decorator(strategy_class: Type[BaseStrategy]):
            if not issubclass(strategy_class, BaseStrategy):
                raise TypeError(f"策略类必须继承BaseStrategy: {strategy_class}")

            cls._strategies[name] = strategy_class
            cls._logger.info(f"✅ 策略已注册: {name} -> {strategy_class.__name__}")
            return strategy_class
        return decorator

    @classmethod
    def register_class(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """
        手动注册策略类

        Args:
            name: 策略名称
            strategy_class: 策略类

        示例：
            StrategyRegistry.register_class('my_strategy', MyStrategy)
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError(f"策略类必须继承BaseStrategy: {strategy_class}")

        cls._strategies[name] = strategy_class
        cls._logger.info(f"✅ 策略已注册: {name} -> {strategy_class.__name__}")

    @classmethod
    def get_strategy(cls, name: str) -> Type[BaseStrategy]:
        """
        根据名称获取策略类

        Args:
            name: 策略名称

        Returns:
            策略类

        Raises:
            KeyError: 策略未注册

        示例：
            strategy_class = StrategyRegistry.get_strategy('my_strategy')
            strategy = strategy_class(params)
        """
        if name not in cls._strategies:
            available = list(cls._strategies.keys())
            raise KeyError(
                f"策略 '{name}' 未注册。可用策略: {available}"
            )
        return cls._strategies[name]

    @classmethod
    def list_strategies(cls) -> Dict[str, Type[BaseStrategy]]:
        """
        获取所有已注册的策略

        Returns:
            字典，{策略名称: 策略类}

        示例：
            strategies = StrategyRegistry.list_strategies()
            for name, cls in strategies.items():
                print(f"{name}: {cls.__name__}")
        """
        return cls._strategies.copy()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查策略是否已注册

        Args:
            name: 策略名称

        Returns:
            是否已注册

        示例：
            if StrategyRegistry.is_registered('my_strategy'):
                print("策略已存在")
        """
        return name in cls._strategies

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        取消注册策略（主要用于测试）

        Args:
            name: 策略名称

        示例：
            StrategyRegistry.unregister('my_strategy')
        """
        if name in cls._strategies:
            del cls._strategies[name]
            cls._logger.info(f"🗑️ 策略已取消注册: {name}")

    @classmethod
    def clear(cls) -> None:
        """
        清空所有已注册的策略（主要用于测试）

        警告：谨慎使用，会清空所有策略！

        示例：
            StrategyRegistry.clear()
        """
        cls._strategies.clear()
        cls._logger.warning("🗑️ 所有策略已清空")


class StrategyFactory:
    """
    策略工厂

    根据配置创建策略实例，支持参数验证和预处理

    使用示例：
        factory = StrategyFactory()
        strategy = factory.create_strategy('my_strategy', config)
    """

    def __init__(self):
        self._logger = get_logger('StrategyFactory')

    def create_strategy(self, name: str, params: Dict[str, Any] = None) -> BaseStrategy:
        """
        创建策略实例

        Args:
            name: 策略名称
            params: 策略参数（字典）

        Returns:
            策略实例

        Raises:
            KeyError: 策略未注册
            TypeError: 参数错误
            ValueError: 参数验证失败

        示例：
            # 从配置文件创建
            config = ConfigManager.load_config('strategy.yaml')
            factory = StrategyFactory()
            strategy = factory.create_strategy('ma_crossover', config['strategy']['params'])

            # 直接使用参数字典
            params = {
                'name': 'ma_crossover',
                'fast_window': 20,
                'slow_window': 50,
                'stop_loss': 0.10
            }
            strategy = factory.create_strategy('ma_crossover', params)
        """
        if params is None:
            params = {}

        # 设置策略名称
        params['name'] = name

        # 获取策略类
        strategy_class = StrategyRegistry.get_strategy(name)

        # 创建实例
        try:
            strategy = strategy_class(params)
            self._logger.info(f"✅ 策略实例创建成功: {name}")
        except Exception as e:
            self._logger.error(f"❌ 策略实例创建失败: {name} - {e}")
            raise

        # 验证参数（如果策略实现了validate_params）
        if hasattr(strategy, 'validate_params'):
            errors = strategy.validate_params()
            if errors:
                error_msg = "参数验证失败:\n  - " + "\n  - ".join(errors)
                self._logger.error(error_msg)
                raise ValueError(error_msg)

        return strategy

    def create_from_config(self, config: Dict[str, Any]) -> BaseStrategy:
        """
        从配置字典创建策略

        Args:
            config: 配置字典，格式：
                {
                    'strategy': {
                        'name': 'strategy_name',
                        'params': {...}
                    }
                }

        Returns:
            策略实例

        示例：
            config = {
                'strategy': {
                    'name': 'ma_crossover',
                    'params': {
                        'fast_window': 20,
                        'slow_window': 50
                    }
                }
            }
            factory = StrategyFactory()
            strategy = factory.create_from_config(config)
        """
        if 'strategy' not in config:
            raise ValueError("配置字典必须包含 'strategy' 键")

        strategy_config = config['strategy']
        name = strategy_config.get('name')

        if not name:
            raise ValueError("配置中必须指定 strategy.name")

        params = strategy_config.get('params', {})

        return self.create_strategy(name, params)


def register_builtin_strategies() -> None:
    """
    注册内置策略

    在模块加载时自动注册所有内置策略

    注意：
        这是一个内部函数，通常不需要手动调用。
        它会在导入strategy模块时自动执行。

    示例：
        from src.strategy.factory import register_builtin_strategies
        register_builtin_strategies()
    """
    try:
        # 导入并注册持续下跌策略
        from src.strategy.continuous_decline import ContinuousDeclineStrategy
        StrategyRegistry.register_class('continuous_decline', ContinuousDeclineStrategy)
    except ImportError as e:
        get_logger('factory').warning(f"无法注册持续下跌策略: {e}")

    try:
        # 导入并注册均线交叉策略（如果存在）
        from src.strategy.ma_crossover import MACrossoverStrategy
        StrategyRegistry.register_class('ma_crossover', MACrossoverStrategy)
    except ImportError:
        pass  # 策略可能还未实现

    logger = get_logger('factory')
    registered = StrategyRegistry.list_strategies()
    logger.info(f"已注册 {len(registered)} 个内置策略: {list(registered.keys())}")


# 模块加载时自动注册内置策略
try:
    register_builtin_strategies()
except Exception as e:
    # 避免导入时出错影响整个应用
    import traceback
    traceback.print_exc()
