#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测运行脚本 v2（支持多策略）

使用策略工厂动态加载策略，无需硬编码策略类

使用示例：
    # 查看所有可用策略
    python run_backtest_v2.py --list

    # 运行指定策略
    python run_backtest_v2.py --strategy continuous_decline

    # 使用自定义配置
    python run_backtest_v2.py --strategy ma_crossover --config ma_crossover.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import List

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.utils.config import ConfigManager
from src.strategy.factory import StrategyRegistry, StrategyFactory


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='多策略回测工具（支持动态加载策略）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有策略
  python %(prog)s --list

  # 运行持续下跌策略
  python %(prog)s --strategy continuous_decline

  # 运行均线交叉策略（自定义配置）
  python %(prog)s --strategy ma_crossover --config configs/strategy/ma_crossover.yaml

  # 指定股票和时间范围
  python %(prog)s --strategy continuous_decline --symbols "000001.SZ,600000.SH" --start 2022-01-01 --end 2022-12-31
        """
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有已注册的策略'
    )

    parser.add_argument(
        '--strategy', '-s',
        type=str,
        default=None,
        help='策略名称（如：continuous_decline）'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='configs/strategy/continuous_decline.yaml',
        help='策略配置文件路径'
    )

    parser.add_argument(
        '--symbols',
        type=str,
        default=None,
        help='回测股票代码（用逗号分隔）'
    )

    parser.add_argument(
        '--start',
        type=str,
        default=None,
        help='回测开始日期（YYYY-MM-DD）'
    )

    parser.add_argument(
        '--end',
        type=str,
        default=None,
        help='回测结束日期（YYYY-MM-DD）'
    )

    return parser.parse_args()


def list_strategies():
    """列出所有已注册的策略"""
    strategies = StrategyRegistry.list_strategies()

    print("\n" + "=" * 60)
    print("已注册的策略")
    print("=" * 60)

    if not strategies:
        print("  暂无策略（请在src/strategy/目录下创建策略类）")
        return

    for name, strategy_class in strategies.items():
        print(f"  {name:<25} -> {strategy_class.__name__}")

    print("=" * 60)
    print(f"总计: {len(strategies)} 个策略")
    print("=" * 60 + "\n")


def check_dependencies() -> bool:
    """检查必要的依赖"""
    logger = setup_logger('dependency_check')

    print("\n" + "=" * 60)
    print("检查依赖项")
    print("=" * 60)

    all_good = True

    # 检查基础库
    try:
        import numpy
        print(f"✅ NumPy {numpy.__version__}")
    except ImportError:
        print("❌ NumPy未安装")
        all_good = False

    try:
        import pandas
        print(f"✅ Pandas {pandas.__version__}")
    except ImportError:
        print("❌ Pandas未安装")
        all_good = False

    try:
        import vectorbt
        print(f"✅ VectorBT {vectorbt.__version__}")
    except ImportError:
        print("❌ VectorBT未安装")
        all_good = False

    # 检查数据提供商
    try:
        import akshare
        print(f"✅ AkShare（数据提供商）")
    except ImportError:
        try:
            import tushare
            print(f"✅ Tushare（数据提供商）")
        except ImportError:
            print("⚠️  AkShare和Tushare均未安装，无法获取数据")
            all_good = False

    print("=" * 60 + "\n")

    if not all_good:
        logger.error("依赖项检查失败，请安装缺失的库")
        print("\n💡 安装命令：")
        print("  pip install -r requirements.txt")
        return False

    return True


def run_backtest(
    strategy_name: str,
    config_path: str,
    symbols: List[str],
    start_date: str,
    end_date: str
):
    """运行回测"""
    logger = setup_logger('backtest')

    print("\n" + "=" * 60)
    print("回测开始")
    print("=" * 60)
    print(f"策略: {strategy_name}")
    print(f"配置: {config_path}")
    print("=" * 60)

    # 加载配置
    try:
        config = ConfigManager.load_config(config_path)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        sys.exit(1)

    # 创建策略
    try:
        factory = StrategyFactory()
        strategy = factory.create_strategy(strategy_name, config.get('strategy', {}))
        logger.info(f"✅ 策略实例创建成功: {strategy_name}")
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 创建上下文
    # TODO: 初始化data_provider, position_manager等组件
    # context = StrategyContext(...)
    # strategy.set_context(context)

    print("\n📊 回测功能即将实现...")
    print("  当前框架已支持多策略加载")
    print("  下一步：实现VectorBT回测引擎集成\n")


def main():
    """主函数"""
    args = parse_args()

    # 设置日志
    logger = setup_logger(name='run_backtest_v2')

    # 列出所有策略
    if args.list:
        list_strategies()
        return

    # 检查策略名称
    if not args.strategy:
        logger.error("请指定策略名称（--strategy）或使用 --list 查看可用策略")
        print("\n💡 提示：运行以下命令查看策略列表")
        print("  python scripts/run_backtest_v2.py --list\n")
        sys.exit(1)

    # 检查策略是否已注册
    if not StrategyRegistry.is_registered(args.strategy):
        logger.error(f"策略未注册: {args.strategy}")
        print("\n💡 提示：运行以下命令查看所有可用策略")
        print("  python scripts/run_backtest_v2.py --list\n")
        sys.exit(1)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 解析股票列表
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]

    # 运行回测
    run_backtest(
        strategy_name=args.strategy,
        config_path=args.config,
        symbols=symbols,
        start_date=args.start,
        end_date=args.end
    )


if __name__ == '__main__':
    main()
