"""
测试最大持仓限制逻辑

验证：
1. 持仓满时跳过选股（before_trading）
2. 持仓满时不生成买入信号（on_bar）
3. 资金分配正确
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.continuous_decline import ContinuousDeclineStrategy
from src.core.position.position_manager import PositionManager
from src.utils.config import ConfigManager


class MockBar:
    """模拟K线数据"""
    def __init__(self, symbol, close, timestamp=None):
        self.symbol = symbol
        self.close = close
        self.timestamp = timestamp or datetime.now()
        self.open = close * 0.99
        self.high = close * 1.01
        self.low = close * 0.99
        self.volume = 10000


def test_position_limit():
    """测试最大持仓限制"""
    print("\n" + "=" * 70)
    print("测试最大持仓限制逻辑")
    print("=" * 70)

    # 加载配置
    strategy_config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')

    # 创建策略
    strategy = ContinuousDeclineStrategy(strategy_config)

    # 初始化策略（重要：必须调用initialize获取logger）
    from src.utils.logger import setup_logger
    context = {
        'logger': setup_logger('test'),
        'data_provider_factory': None  # 测试中不需要
    }
    strategy.initialize(context)

    # 验证配置读取
    max_position_count = strategy.risk_params.get('max_position_count', 10)
    print(f"\n配置的最大持仓数量: {max_position_count}")

    # 创建模拟持仓管理器
    strategy.position_manager = PositionManager(
        total_capital=1_000_000,
        params={'initial_position_size': 0.20, 'position_percent_per_layer': 0.10, 'max_layers': 8}
    )

    # 测试1: 持仓未满（初始化后）
    print("\n[测试1] 持仓未满时的选股")
    current_count = len(strategy.position_manager.get_all_positions())
    print(f"当前持仓: {current_count}/{max_position_count}")

    # 创建上下文
    context = {'current_date': datetime(2024, 2, 1), 'backtest_mode': True}

    try:
        strategy.before_trading(datetime(2024, 2, 1), context)
        print(f"选股结果: {len(strategy.candidate_stocks)} 只候选股票")
        if len(strategy.candidate_stocks) > 0:
            print(f"✓ 候选股票示例: {strategy.candidate_stocks[:3]}")
    except Exception as e:
        print(f"Note: 选股失败（可能没有网络或数据），这是正常的: {e}")

    # 测试2: 模拟持仓满的情况
    print(f"\n[测试2] 持仓满时的行为（模拟）")

    # 手动添加持仓，达到上限
    for i in range(max_position_count):
        symbol = f"000{i:03d}.SZ"
        strategy.position_manager.open_position(symbol, price=10.0, percent=0.20)

    current_count = len(strategy.position_manager.get_all_positions())
    print(f"模拟后持仓: {current_count}/{max_position_count}")

    # 调用before_trading，应该跳过选股
    strategy.before_trading(datetime(2024, 2, 1), context)
    print(f"选股结果: {len(strategy.candidate_stocks)} 只候选股票")

    if len(strategy.candidate_stocks) == 0:
        print("✓ 持仓满时正确跳过选股")
    else:
        print("✗ 持仓满时仍然选股（错误！）")

    # 测试3: 持仓满时不生成买入信号
    print(f"\n[测试3] 持仓满时买入信号生成")

    # 创建一个候选股票
    strategy.candidate_stocks = ['000001.SZ']
    bar = MockBar(symbol='000001.SZ', close=10.0)

    signal = strategy._check_buy_signal(bar, context)

    if signal is None:
        print("✓ 持仓满时正确阻止买入信号")
    else:
        print("✗ 持仓满时仍然生成买入信号（错误！）")

    # 测试4: 清仓后恢复选股
    print(f"\n[测试4] 清仓1只后恢复选股")

    # 平掉1只持仓
    closed_position = strategy.position_manager.close_position('000000.SZ', price=11.0)
    if closed_position is not None:
        current_count = len(strategy.position_manager.get_all_positions())
        print(f"平仓后持仓: {current_count}/{max_position_count}")

        # 应该可以选部分股票了
        strategy.before_trading(datetime(2024, 2, 2), context)
        print(f"选股结果: {len(strategy.candidate_stocks)} 只候选股票")

        if len(strategy.candidate_stocks) > 0:
            print("✓ 持仓不满时恢复选股")
        else:
            print("⚠ 选股结果为空（可能是数据问题）")
    else:
        print("⚠ 平仓失败（可能股票不存在）")

    print("\n" + "=" * 70)
    print("最大持仓限制测试完成")
    print("=" * 70)

    return True


def main():
    """主函数"""
    try:
        test_position_limit()
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
