#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测运行脚本

使用VectorBT引擎进行策略回测

Usage:
    python run_backtest.py                                   # 使用默认配置
    python run_backtest.py --config <config_path>            # 指定配置文件
    python run_backtest.py --symbols "000001.SZ,600000.SH"   # 指定股票
    python run_backtest.py --start 2020-01-01 --end 2023-12-31  # 指定时间范围
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.utils.config import ConfigManager
from src.data.provider_factory import DataProviderFactory


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='持续下跌策略回测工具')

    parser.add_argument(
        '--config',
        type=str,
        default='configs/strategy/continuous_decline.yaml',
        help='策略配置文件路径（默认：configs/strategy/continuous_decline.yaml）'
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

    parser.add_argument(
        '--symbols',
        type=str,
        default=None,
        help='回测股票代码（用逗号分隔，如："000001.SZ,600000.SH"）'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='回测结果输出目录'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 设置日志
    logger = setup_logger(name='backtest')

    # 加载配置
    logger.info("加载配置文件...")
    try:
        # 先加载数据源配置（基础配置）
        base_config = ConfigManager.load_config('configs/data/source.yaml')

        # 再加载策略配置（覆盖基础配置）
        strategy_config = ConfigManager.load_config(args.config)

        # 合并配置（策略配置优先）
        import copy
        config = copy.deepcopy(base_config)

        # 递归合并函数
        def merge_config(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_config(base[key], value)
                else:
                    base[key] = value

        merge_config(config, strategy_config)

        logger.info(f"[OK] 配置加载成功（合并 source.yaml + {args.config}）")
    except Exception as e:
        logger.error(f"加载配置文件失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 命令行参数覆盖配置文件
    if args.start:
        config['backtest']['start_date'] = args.start
    if args.end:
        config['backtest']['end_date'] = args.end
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        config['backtest']['symbols']['type'] = 'LIST'
        config['backtest']['symbols']['list'] = symbols

    # 设置输出目录 - 为每次回测创建唯一文件夹
    import time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_date_str = config['backtest']['start_date'].replace('-', '')
    end_date_str = config['backtest']['end_date'].replace('-', '')
    strategy_name = Path(args.config).stem  # 获取配置文件名（不含扩展名）
    
    if args.output:
        base_output_dir = Path(args.output)
    else:
        base_output_dir = Path("data/backtest_results")
    
    # 创建唯一输出目录：base_dir/strategy_name_start_end_timestamp
    output_dir_name = f"{strategy_name}_{start_date_str}_{end_date_str}_{timestamp}"
    config['backtest']['output_dir'] = str(base_output_dir / output_dir_name)

    logger.info("=" * 60)
    logger.info("持续下跌策略回测开始")
    logger.info("=" * 60)
    logger.info(f"策略配置：{args.config}")
    logger.info(f"开始日期：{config['backtest']['start_date']}")
    logger.info(f"结束日期：{config['backtest']['end_date']}")
    logger.info(f"输出目录：{config['backtest']['output_dir']}")
    logger.info("=" * 60)

    # 数据提供商配置兼容性处理
    logger.info("配置数据提供商...")
    try:
        # 兼容旧格式：data.provider -> data.primary_provider
        if 'provider' in config.get('data', {}) and 'primary_provider' not in config['data']:
            provider_name = config['data']['provider']
            config['data']['primary_provider'] = provider_name
            # 启用对应的数据源
            if provider_name not in config['data']:
                config['data'][provider_name] = {}
            config['data'][provider_name]['enabled'] = True
            logger.info(f"[OK] 已配置主数据源: {provider_name}")
    except Exception as e:
        logger.error(f"[ERROR] 数据提供商配置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 检查依赖
    logger.info("检查依赖...")
    try:
        import vectorbt
        logger.info(f"[OK] VectorBT {vectorbt.__version__} 已安装")
    except ImportError:
        logger.error("[ERROR] VectorBT未安装，请先运行：pip install vectorbt")
        sys.exit(1)

    try:
        import pandas
        logger.info(f"[OK] Pandas {pandas.__version__} 已安装")
    except ImportError:
        logger.error("[ERROR] Pandas未安装，请先运行：pip install pandas")
        sys.exit(1)

    try:
        import numpy
        logger.info(f"[OK] NumPy {numpy.__version__} 已安装")
    except ImportError:
        logger.error("[ERROR] NumPy未安装，请先运行：pip install numpy")
        sys.exit(1)

    # 检查数据提供商依赖
    primary_provider = config['data'].get('primary_provider', 'tushare')
    if primary_provider == 'tushare':
        try:
            import tushare
            logger.info("[OK] Tushare已安装")
        except ImportError:
            logger.warning("[WARNING] Tushare未安装，将尝试使用Akshare")
            config['data']['primary_provider'] = 'akshare'
    elif primary_provider == 'akshare':
        try:
            import akshare
            logger.info("[OK] Akshare已安装")
        except ImportError:
            logger.error("[ERROR] Akshare未安装，请先运行：pip install akshare")
            sys.exit(1)

    # 初始化策略
    logger.info("初始化策略...")
    try:
        from src.strategy.continuous_decline import ContinuousDeclineStrategy
        # 传递策略配置（config['strategy']），而不是整个config
        strategy = ContinuousDeclineStrategy(config['strategy'])
        logger.info("[OK] 策略初始化成功")
    except Exception as e:
        logger.error(f"[ERROR] 策略初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 初始化回测引擎
    logger.info("初始化回测引擎...")
    try:
        # 创建数据提供器工厂（传入完整配置，包含'data'键）
        data_provider_factory = DataProviderFactory(config)

        # 检查provider是否创建成功
        if 'local_csv' not in data_provider_factory.providers:
            logger.warning("local_csv提供器未自动创建，尝试手动创建")
            from src.data.local_csv_provider import LocalCSVDataProvider
            data_dir = config['data']['local_csv']['data_dir']
            cache_config = config['data']['local_csv'].get('cache', {})

            data_provider_factory.providers['local_csv'] = LocalCSVDataProvider(
                data_dir=data_dir,
                cache_size=cache_config.get('max_size', 100),
                validate_tscode=config['data']['local_csv'].get('validate_tscode', True),
                filter_future=config['data']['local_csv'].get('filter_future', True),
                file_format=config['data']['local_csv'].get('file_format', 'csv')
            )
            logger.info(f"[OK] 手动初始化LocalCSV提供器")
            logger.info(f"  数据目录: {data_dir}")

        from src.execution.vectorbt_backtester import VectorBTBacktester
        backtester = VectorBTBacktester(strategy, data_provider_factory)
        logger.info("[OK] 回测引擎初始化成功")
    except Exception as e:
        logger.error(f"[ERROR] 回测引擎初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 运行回测
    logger.info("运行回测...")
    try:
        import pandas as pd
        start_date = pd.to_datetime(config['backtest']['start_date'])
        end_date = pd.to_datetime(config['backtest']['end_date'])

        symbols = config['backtest']['symbols']
        if symbols['type'] == 'A_SHARE':
            symbol_list = None  # 使用全市场
        elif symbols['type'] == 'LIST':
            symbol_list = symbols['list']
        else:
            symbol_list = None

        results = backtester.run(
            start_date=start_date,
            end_date=end_date,
            symbols=symbol_list
        )

        logger.info("[OK] 回测运行完成")
    except Exception as e:
        logger.error(f"[ERROR] 回测运行失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 保存结果
    logger.info("保存回测结果...")
    try:
        output_dir = config['backtest']['output_dir']
        backtester.generate_report(results, output_dir)
        logger.info(f"  结果已保存到: {output_dir}")
    except Exception as e:
        logger.warning(f"保存结果失败：{e}")

    logger.info("=" * 60)
    logger.info("回测完成！")
    logger.info("=" * 60)

    # 打印关键指标
    if hasattr(results, 'performance') and results.performance:
        perf = results.performance
        logger.info("\n📊 回测关键指标：\n")
        logger.info(f"  总收益率: {perf.get('total_return', 0):.2%}")
        logger.info(f"  年化收益率: {perf.get('annual_return', 0):.2%}")
        logger.info(f"  最大回撤: {perf.get('max_drawdown', 0):.2%}")
        logger.info(f"  夏普比率: {perf.get('sharpe_ratio', 0):.2f}")
        logger.info(f"  总交易次数: {perf.get('total_trades', 0)}")
        if isinstance(perf.get('win_rate'), (int, float)):
            logger.info(f"  胜率: {perf['win_rate']:.2%}")
    else:
        logger.info("\n📊 回测完成")


if __name__ == '__main__':
    main()
