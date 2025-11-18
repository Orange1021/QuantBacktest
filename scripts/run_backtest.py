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
        config = ConfigManager.load_config(args.config)
    except Exception as e:
        logger.error(f"加载配置文件失败：{e}")
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

    # 设置输出目录
    if args.output:
        config['backtest']['output_dir'] = args.output

    logger.info("=" * 60)
    logger.info("持续下跌策略回测开始")
    logger.info("=" * 60)
    logger.info(f"策略配置：{args.config}")
    logger.info(f"开始日期：{config['backtest']['start_date']}")
    logger.info(f"结束日期：{config['backtest']['end_date']}")
    logger.info(f"输出目录：{config['backtest']['output_dir']}")
    logger.info("=" * 60)

    # 检查依赖
    logger.info("检查依赖...")
    try:
        import vectorbt
        logger.info(f"✅ VectorBT {vectorbt.__version__} 已安装")
    except ImportError:
        logger.error("❌ VectorBT未安装，请先运行：pip install vectorbt")
        sys.exit(1)

    try:
        import pandas
        logger.info(f"✅ Pandas {pandas.__version__} 已安装")
    except ImportError:
        logger.error("❌ Pandas未安装，请先运行：pip install pandas")
        sys.exit(1)

    try:
        import numpy
        logger.info(f"✅ NumPy {numpy.__version__} 已安装")
    except ImportError:
        logger.error("❌ NumPy未安装，请先运行：pip install numpy")
        sys.exit(1)

    # 数据提供商
    data_provider_config = config['data']['provider']
    if data_provider_config == 'tushare':
        try:
            import tushare
            logger.info(f"✅ Tushare已安装")
        except ImportError:
            logger.warning("⚠️ Tushare未安装，将尝试使用Akshare")
            config['data']['provider'] = 'akshare'
    elif data_provider_config == 'akshare':
        try:
            import akshare
            logger.info(f"✅ Akshare已安装")
        except ImportError:
            logger.error("❌ Akshare未安装，请先运行：pip install akshare")
            sys.exit(1)

    # 初始化策略
    logger.info("初始化策略...")
    try:
        from src.strategy.continuous_decline import ContinuousDeclineStrategy
        strategy = ContinuousDeclineStrategy(config)
        logger.info("✅ 策略初始化成功")
    except Exception as e:
        logger.error(f"❌ 策略初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 初始化回测引擎
    logger.info("初始化回测引擎...")
    try:
        from src.execution.vectorbt_backtester import VectorBTBacktester
        backtester = VectorBTBacktester(strategy)
        logger.info("✅ 回测引擎初始化成功")
    except Exception as e:
        logger.error(f"❌ 回测引擎初始化失败：{e}")
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

        logger.info("✅ 回测运行完成")
    except Exception as e:
        logger.error(f"❌ 回测运行失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 分析结果
    logger.info("分析回测结果...")
    try:
        analysis = backtester.analyze(results)
        logger.info("✅ 回测分析完成")
    except Exception as e:
        logger.error(f"❌ 回测分析失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 保存结果
    logger.info("保存回测结果...")
    try:
        output_dir = Path(config['backtest']['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存交易记录
        if config['backtest']['save_trades'] and 'trades' in results:
            trades_file = output_dir / 'trades.csv'
            results['trades'].to_csv(trades_file, index=False)
            logger.info(f"  - 交易记录已保存：{trades_file}")

        # 保存持仓记录
        if config['backtest']['save_positions'] and 'positions' in results:
            positions_file = output_dir / 'positions.csv'
            results['positions'].to_csv(positions_file, index=False)
            logger.info(f"  - 持仓记录已保存：{positions_file}")

        # 保存绩效报告
        if 'performance_report' in analysis:
            report_file = output_dir / 'performance_report.html'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(analysis['performance_report'])
            logger.info(f"  - 绩效报告已保存：{report_file}")

        logger.info("=" * 60)
        logger.info("回测完成！")
        logger.info("=" * 60)

        # 打印关键指标
        if 'metrics' in analysis:
            metrics = analysis['metrics']
            logger.info("\n📊 回测关键指标：\n")
            logger.info(f"  总收益率: {metrics.get('total_return', 'N/A')}")
            logger.info(f"  年化收益率: {metrics.get('annualized_return', 'N/A')}")
            logger.info(f"  最大回撤: {metrics.get('max_drawdown', 'N/A')}")
            logger.info(f"  夏普比率: {metrics.get('sharpe_ratio', 'N/A')}")
            logger.info(f"  交易次数: {metrics.get('trade_count', 'N/A')}")
            logger.info(f"  胜率: {metrics.get('win_rate', 'N/A')}")

    except Exception as e:
        logger.error(f"❌ 保存结果失败：{e}")
        import traceback
        traceback.print_exc()

    logger.info("=" * 60)
    logger.info("所有任务完成！")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
