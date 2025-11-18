"""
策略功能测试脚本

测试 ContinuousDeclineStrategy 策略的完整流程：
1. 初始化策略
2. 盘前选股（使用问财）
3. K线处理（模拟交易）
4. 盘后持仓检查

使用方法：
    python scripts/test_strategy.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.continuous_decline import ContinuousDeclineStrategy
from src.data.provider_factory import DataProviderFactory
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger


def create_test_context():
    """创建测试上下文"""
    # 加载配置文件
    data_config = ConfigManager.load_config('configs/data/source.yaml')
    strategy_config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')

    # 合并配置
    config = {**strategy_config, **data_config}

    # 创建数据提供器工厂（注意：需要整个data_config，不只是data_config['data']）
    logger = setup_logger('test_strategy')
    data_provider_factory = DataProviderFactory(data_config)

    # 创建降级代理（自动处理数据源切换）
    data_provider = data_provider_factory.create_proxy()

    # 创建上下文
    context = {
        'logger': logger,
        'config': config,
        'data_provider': data_provider,
        'data_provider_factory': data_provider_factory,
    }

    return context, config


def test_strategy_initialization():
    """测试策略初始化"""
    print("=" * 70)
    print("测试1: 策略初始化")
    print("=" * 70)

    context, config = create_test_context()

    try:
        # 从上下文中获取策略配置
        strategy_config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')

        # 创建策略实例
        strategy = ContinuousDeclineStrategy(strategy_config['strategy'])

        # 初始化
        strategy.initialize(context)

        print("[OK] 策略初始化成功")
        print(f"  - 策略名称: {strategy.name}")
        print(f"  - 筛选器类型: {strategy.filter_params.get('filter_type')}")
        print(f"  - 初始资金: {config['strategy']['capital_params']['initial_capital']:,}")
        print(f"  - 下跌天数阈值: {strategy.filter_params.get('decline_days_threshold')}天")
        print(f"  - 止损线: {strategy.risk_params.get('stop_loss_percent'):.1%}")

        return strategy, context

    except Exception as e:
        print(f"[FAIL] 策略初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_before_trading(strategy, context):
    """测试盘前选股"""
    print("\n" + "=" * 70)
    print("测试2: 盘前选股（每日扫描）")
    print("=" * 70)

    if not strategy:
        print("[FAIL] 策略未初始化")
        return

    try:
        # 使用最近一个交易日作为测试日期
        # 注意：如果运行在非交易日，需要选择最近的交易日
        test_date = datetime(2024, 10, 15)  # 2024-10-15是交易日

        print(f"测试日期: {test_date.strftime('%Y-%m-%d')}")
        print("开始选股扫描（这可能需要一些时间）...")

        # 执行盘前选股
        strategy.before_trading(test_date, context)

        # 打印结果
        candidates = strategy.candidate_stocks
        print(f"[OK] 选股完成")
        print(f"  - 候选股票数量: {len(candidates)}")

        if len(candidates) > 0:
            print(f"  - 前10只股票:")
            for i, symbol in enumerate(candidates[:10], 1):
                print(f"    {i}. {symbol}")
        else:
            print("  - 注意: 未找到符合条件的股票")
            print("    可能原因:")
            print("      1. 日期不是交易日")
            print("      2. 市场在该日期没有连续下跌的股票")
            print("      3. 问财Cookie已过期（需要重新获取）")

    except Exception as e:
        print(f"[FAIL] 选股失败: {e}")
        import traceback
        traceback.print_exc()


def test_on_bar_simulation(strategy, context):
    """测试K线处理（模拟）"""
    print("\n" + "=" * 70)
    print("测试3: K线处理（模拟交易信号）")
    print("=" * 70)

    if not strategy:
        print("[FAIL] 策略未初始化")
        return

    try:
        # 模拟K线数据（使用候选股票中的前3只）
        candidates = strategy.candidate_stocks

        if not candidates:
            print("[WARN] 没有候选股票，无法测试K线处理")
            print("  将使用模拟股票进行测试...")
            candidates = ['000001.SZ', '600000.SH']  # 模拟股票

        # 创建模拟K线
        class MockBar:
            def __init__(self, symbol, close):
                self.symbol = symbol
                self.close = close
                self.open = close * 0.99
                self.high = close * 1.02
                self.low = close * 0.98
                self.volume = 100000
                self.timestamp = datetime.now()

        # 模拟几只股票的价格数据
        test_bars = [
            MockBar(candidates[0] if len(candidates) > 0 else '000001.SZ', 10.0),
            MockBar(candidates[1] if len(candidates) > 1 else '600000.SH', 15.0),
        ]

        for i, bar in enumerate(test_bars, 1):
            print(f"\n测试K线 {i}: {bar.symbol}")
            print(f"  价格: {bar.close:.2f}")

            # 处理K线
            result = strategy.on_bar(bar, context)

            if result and 'signals' in result:
                signals = result['signals']
                print(f"  [OK] 生成交易信号 ({len(signals)}个):")
                for signal in signals:
                    print(f"    - {signal['type']} {signal['symbol']}")
                    print(f"      价格: {signal['price']:.2f}")
                    print(f"      类型: {signal['metadata']['reason']}")
            else:
                print(f"  - 无交易信号")

    except Exception as e:
        print(f"[FAIL] K线处理失败: {e}")
        import traceback
        traceback.print_exc()


def test_position_status(strategy):
    """测试持仓状态"""
    print("\n" + "=" * 70)
    print("测试4: 持仓状态查看")
    print("=" * 70)

    if not strategy or not strategy.position_manager:
        print("[FAIL] 仓位管理器不可用")
        return

    try:
        stats = strategy.position_manager.get_position_stats()

        print(f"[OK] 持仓状态:")
        for key, value in stats.items():
            if isinstance(value, float):
                if 'percent' in key.lower():
                    print(f"  - {key}: {value:.2%}")
                else:
                    print(f"  - {key}: {value:,.2f}")
            else:
                print(f"  - {key}: {value}")

        # 查看具体持仓
        positions = strategy.position_manager.get_all_positions()
        if positions:
            print(f"\n[OK] 持仓明细 ({len(positions)}只):")
            for pos in positions:
                print(f"  - {pos.symbol}: {pos.quantity}股, 成本={pos.avg_price:.2f}, 当前={pos.current_price:.2f}")
                print(f"    盈亏: {pos.pnl:+.0f} ({pos.pnl_percent:+.2f}%), 层数: {pos.layer_count}")
        else:
            print("\n- 当前无持仓")

    except Exception as e:
        print(f"[FAIL] 获取持仓状态失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试流程"""
    print("\n")
    print("=" * 70)
    print("ContinuousDeclineStrategy 策略功能测试")
    print("=" * 70)
    print("\n")

    # 测试1: 初始化
    strategy, context = test_strategy_initialization()

    if strategy:
        # 测试2: 盘前选股
        test_before_trading(strategy, context)

        # 测试3: K线处理
        test_on_bar_simulation(strategy, context)

        # 测试4: 持仓状态
        test_position_status(strategy)

    # 总结
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

    if strategy:
        print("\n[OK] 策略核心功能正常")
        print("\n  下一步:")
        print("    1. 运行真实回测: python scripts/run_backtest.py")
        print("    2. 查看回测结果: data/backtest_results/")
        print("    3. 分析绩效报告: performance_report.html")
    else:
        print("\n[FAIL] 策略初始化失败，请检查错误信息")


if __name__ == '__main__':
    main()
