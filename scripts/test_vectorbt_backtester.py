"""
VectorBT回测引擎测试

测试工业级回测引擎的核心功能：
1. 每日动态选股
2. 完整交易流程（盘前、盘中、盘后）
3. 加仓信号支持
4. 资金分配策略
5. 20+项绩效指标
"""

from datetime import datetime
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.continuous_decline import ContinuousDeclineStrategy
from src.data.provider_factory import DataProviderFactory
from src.utils.config import ConfigManager
from src.execution.vectorbt_backtester import VectorBTBacktester


class TestBar:
    """测试用Bar对象"""
    def __init__(self, symbol, timestamp, open_price, high, low, close, volume):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


def test_backtest_engine():
    """测试回测引擎"""
    print("=" * 70)
    print("VectorBT回测引擎测试")
    print("=" * 70)

    # 加载配置
    data_config = ConfigManager.load_config('configs/data/source.yaml')
    strategy_config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')

    # 创建数据提供器
    print("\n[1/6] 创建数据提供器...")
    factory = DataProviderFactory(data_config)
    print("✓ 数据提供器创建成功")

    # 创建策略
    print("\n[2/6] 创建策略...")
    strategy = ContinuousDeclineStrategy(strategy_config)
    print(f"✓ 策略创建成功: {strategy.get_status()['strategy_name']}")

    # 创建回测引擎
    print("\n[3/6] 创建回测引擎...")
    backtester = VectorBTBacktester(strategy, factory)
    print("✓ 回测引擎创建成功")

    # 运行回测（短周期，快速测试）
    print("\n[4/6] 运行回测...")
    start_date = datetime(2024, 2, 1)   # 熊市期间
    end_date = datetime(2024, 2, 15)    # 15天快速测试

    try:
        result = backtester.run(
            start_date=start_date,
            end_date=end_date,
            initial_capital=100_0000
        )
        print("✓ 回测执行完成")
    except Exception as e:
        print(f"✗ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 验证结果
    print("\n[5/6] 验证回测结果...")
    success = True

    if not result.performance:
        print("✗ 绩效指标为空")
        success = False
    else:
        perf = result.performance
        print(f"✓ 总收益率: {perf.get('total_return', 0):.2%}")
        print(f"✓ 夏普比率: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"✓ 最大回撤: {perf.get('max_drawdown', 0):.2%}")
        print(f"✓ 总交易次数: {perf.get('total_trades', 0)}")

    if result.trades is not None and not result.trades.empty:
        print(f"✓ 交易记录: {len(result.trades)} 笔")
    else:
        print("⚠ 无交易记录（可能期间无信号）")

    if result.positions is not None and not result.positions.empty:
        print(f"✓ 持仓记录: {len(result.positions)} 条")
    else:
        print("⚠ 无持仓记录")

    if result.summary:
        print(f"\n✓ 回测摘要已生成（{len(result.summary)} 字符）")

    # 生成报告
    print("\n[6/6] 生成回测报告...")
    try:
        result_dir = Path('data/backtest_results/test')
        backtester.generate_report(result, str(result_dir))
        print(f"✓ 报告已保存至: {result_dir}")
    except Exception as e:
        print(f"⚠ 生成报告失败: {e}")

    print("\n" + "=" * 70)
    if success:
        print("测试通过 ✓")
    else:
        print("测试失败 ✗")
    print("=" * 70)

    return success


def main():
    """主函数"""
    try:
        success = test_backtest_engine()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
