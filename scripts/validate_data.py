#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据验证脚本

验证数据源的可用性和数据质量。
支持测试本地CSV、Tushare、Akshare等多种数据源。

Usage:
    python verify_data.py                           # 验证所有数据源
    python verify_data.py --provider local_csv      # 验证本地CSV
    python verify_data.py --provider tushare        # 验证Tushare
    python verify_data.py --profile                 # 性能测试
    python verify_data.py --detailed                # 详细报告
"""

import argparse
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import ConfigManager
from src.utils.logger import setup_logger
from src.data import DataProviderFactory


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='数据验证工具')

    parser.add_argument(
        '--config',
        type=str,
        default='configs/data/source.yaml',
        help='数据源配置文件路径'
    )

    parser.add_argument(
        '--provider',
        type=str,
        choices=['local_csv', 'tushare', 'akshare', 'all'],
        default='all',
        help='要验证的数据源'
    )

    parser.add_argument(
        '--symbol',
        type=str,
        default='000001.SZ',
        help='测试用的股票代码'
    )

    parser.add_argument(
        '--profile',
        action='store_true',
        help='运行性能测试'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='生成详细报告'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出报告文件（JSON格式）'
    )

    return parser.parse_args()


def test_connection(provider_name, provider, symbol, start_date, end_date):
    """
    测试数据源连接

    Args:
        provider_name: 数据源名称
        provider: 数据提供器实例
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        测试结果字典
    """
    result = {
        "provider": provider_name,
        "status": "unknown",
        "message": "",
        "latency_ms": 0,
        "data_shape": None,
        "columns": None
    }

    try:
        start_time = time.time()
        df = provider.get_daily_bars(symbol, start_date, end_date)
        elapsed = time.time() - start_time

        if df is None or df.empty:
            result["status"] = "warning"
            result["message"] = "返回空数据"
        else:
            result["status"] = "success"
            result["message"] = f"成功获取 {len(df)} 条数据"
            result["data_shape"] = list(df.shape)
            result["columns"] = list(df.columns)

        result["latency_ms"] = round(elapsed * 1000, 2)

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
        result["latency_ms"] = -1

    return result


def run_basic_tests(args, logger):
    """
    运行基础测试

    Args:
        args: 命令行参数
        logger: 日志记录器

    Returns:
        测试结果列表
    """
    logger.info("=" * 70)
    logger.info("数据验证报告")
    logger.info("=" * 70)
    logger.info(f"测试时间: {datetime.now()}")
    logger.info(f"配置文件: {args.config}")
    logger.info("-" * 70)

    # 加载配置
    config = ConfigManager.load_config(args.config)

    # 创建工厂
    factory = DataProviderFactory(config)

    # 测试参数
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    symbol = args.symbol

    logger.info(f"测试股票: {symbol}")
    logger.info(f"日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    logger.info("-" * 70)

    # 测试结果
    results = []

    # 测试数据源
    providers_to_test = []

    if args.provider == 'all':
        # 测试所有可用的数据源
        for name, provider in factory.providers.items():
            providers_to_test.append((name, provider))
    else:
        # 测试指定的数据源
        provider = factory.get_provider(args.provider)
        if provider:
            providers_to_test.append((args.provider, provider))
        else:
            logger.error(f"数据源不可用: {args.provider}")
            return results

    # 执行测试
    for provider_name, provider in providers_to_test:
        logger.info(f"\n测试数据源: {provider_name}")
        logger.info("-" * 70)

        result = test_connection(provider_name, provider, symbol, start_date, end_date)

        # 记录结果
        results.append(result)

        # 显示结果
        status_symbol = {
            "success": "[OK]",
            "warning": "[WARN]",
            "error": "[ERROR]"
        }.get(result["status"], "[?]")

        logger.info(f"{status_symbol} {result['message']}")
        logger.info(f"延迟: {result['latency_ms']} ms")

        if result['columns']:
            logger.info(f"列: {result['columns']}")

        if result['data_shape']:
            logger.info(f"数据形状: {result['data_shape']}")

    return results


def run_detailed_tests(args, logger):
    """
    运行详细测试

    Args:
        args: 命令行参数
        logger: 日志记录器

    Returns:
    None
    """
    logger.info("\n" + "=" * 70)
    logger.info("详细测试")
    logger.info("=" * 70)

    config = ConfigManager.load_config(args.config)
    factory = DataProviderFactory(config)

    # 获取本地CSV提供器（专门测试）
    local_provider = factory.get_provider('local_csv')

    if not local_provider:
        logger.warning("本地CSV提供器不可用，跳过详细测试")
        return

    # 测试数据目录
    data_dir = Path(local_provider.data_dir)
    logger.info(f"数据目录: {data_dir}")

    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return

    # 扫描文件
    csv_files = list(data_dir.glob('*.csv'))
    logger.info(f"CSV文件数量: {len(csv_files)}")

    if not csv_files:
        logger.warning("未找到CSV文件")
        return

    # 随机抽查几个文件
    sample_files = csv_files[:5]
    logger.info("抽查文件:")

    for file in sample_files:
        try:
            import pandas as pd
            df = pd.read_csv(file)

            logger.info(f"  - {file.name}")
            logger.info(f"    行数: {len(df)}")
            logger.info(f"    列数: {len(df.columns)}")
            logger.info(f"    日期范围: {df['交易日期'].min()} ~ {df['交易日期'].max()}")

            # 检查空值
            null_counts = df.isnull().sum()
            if null_counts.any():
                logger.info(f"    空值: {null_counts[null_counts > 0].to_dict()}")

        except Exception as e:
            logger.error(f"  - {file.name}: 读取失败 - {e}")


def run_performance_test(args, logger):
    """
    运行性能测试

    Args:
        args: 命令行参数
        logger: 日志记录器

    Returns:
        性能测试结果
    """
    logger.info("\n" + "=" * 70)
    logger.info("性能测试")
    logger.info("=" * 70)

    config = ConfigManager.load_config(args.config)
    factory = DataProviderFactory(config)

    # 测试数据
    symbols = ['000001.SZ', '600000.SH', '000002.SZ', '600519.SH']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    results = []

    for name, provider in factory.providers.items():
        logger.info(f"\n测试性能: {name}")
        logger.info("-" * 70)

        # 单只股票测试
        times = []
        for _ in range(3):  # 测试3次取平均
            start = time.time()
            try:
                provider.get_daily_bars(symbols[0], start_date, end_date)
                elapsed = time.time() - start
                times.append(elapsed)
            except:
                times.append(-1)

        avg_time = sum([t for t in times if t > 0]) / len([t for t in times if t > 0]) if times else -1
        logger.info(f"单只股票（平均）: {avg_time * 1000:.2f} ms")

        # 批量测试（如果支持）
        batch_time = None
        if hasattr(provider, 'get_daily_bars_batch'):
            start = time.time()
            try:
                provider.get_daily_bars_batch(symbols, start_date, end_date)
                batch_time = time.time() - start
                logger.info(f"批量（4只）: {batch_time * 1000:.2f} ms")
            except:
                pass

        results.append({
            "provider": name,
            "single_stock_ms": avg_time * 1000 if avg_time > 0 else -1,
            "batch_ms": batch_time * 1000 if batch_time else -1
        })

    return results


def save_report(results, output_file):
    """
    保存报告

    Args:
        results: 测试结果
        output_file: 输出文件路径
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    args = parse_args()

    # 设置日志
    logger = setup_logger(
        name='data_validator',
        level='INFO',
        log_file='logs/data_validator.log'
    )

    # 运行测试
    results = []

    try:
        # 基础测试
        basic_results = run_basic_tests(args, logger)
        results.extend(basic_results)

        # 详细测试
        if args.detailed:
            run_detailed_tests(args, logger)

        # 性能测试
        if args.profile:
            perf_results = run_performance_test(args, logger)
            results.extend(perf_results)

        # 保存报告
        if args.output:
            save_report(results, args.output)
            logger.info(f"\n报告已保存到: {args.output}")

        # 汇总
        logger.info("\n" + "=" * 70)
        logger.info("测试完成")
        logger.info("=" * 70)

        success_count = sum(1 for r in results if r['status'] == 'success')
        warning_count = sum(1 for r in results if r['status'] == 'warning')
        error_count = sum(1 for r in results if r['status'] == 'error')

        logger.info(f"总计: {len(results)} 个数据源")
        logger.info(f"成功: {success_count}")
        logger.info(f"警告: {warning_count}")
        logger.info(f"错误: {error_count}")

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
