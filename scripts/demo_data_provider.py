#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据提供器演示脚本

演示如何使用参数化数据提供器获取股票数据。
展示本地CSV、Tushare、降级代理等功能。

Example:
    python demo_data_provider.py
    python demo_data_provider.py --config configs/data/source.yaml
    python demo_data_provider.py --provider tushare
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data import DataProviderFactory
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger


def demo_basic_usage():
    """演示基本用法"""
    print("\n" + "=" * 70)
    print("演示1: 基本用法")
    print("=" * 70)

    # 加载配置
    config = ConfigManager.load_config('configs/data/source.yaml')

    # 创建工厂
    factory = DataProviderFactory(config)

    # 获取主数据源
    provider = factory.get_primary_provider()

    print(f"主数据源: {provider.__class__.__name__}")

    # 获取数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    symbol = "000001.SZ"

    print(f"\n查询股票: {symbol}")
    print(f"日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    df = provider.get_daily_bars(symbol, start_date, end_date)

    print(f"\n获取数据: {len(df)} 条记录")
    print("\n前5条数据:")
    print(df.head())

    # 显示数据信息
    print(f"\n数据列: {list(df.columns)}")
    print(f"日期范围: {df.index[0]} ~ {df.index[-1]}")


def demo_fallback_proxy():
    """演示降级代理"""
    print("\n" + "=" * 70)
    print("演示2: 降级代理")
    print("=" * 70)

    # 加载配置
    config = ConfigManager.load_config('configs/data/source.yaml')

    # 创建工厂
    factory = DataProviderFactory(config)

    # 创建代理（自动降级）
    proxy = factory.create_proxy()

    print("数据源配置:")
    print(f"  主数据源: {config.get('primary_provider')}")
    print(f"  降级链: {len(config.get('fallback_chain', []))} 个备用源")
    print(f"  自动降级: {'启用' if config.get('auto_fallback') else '禁用'}")

    # 测试降级
    print("\n开始查询（会自动处理降级）...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    symbols = ["000001.SZ", "600000.SH", "000002.SZ"]

    for symbol in symbols:
        try:
            print(f"\n查询: {symbol}")
            df = proxy.get_daily_bars(symbol, start_date, end_date)
            print(f"  [OK] 成功获取 {len(df)} 条数据")
        except Exception as e:
            print(f"  [ERROR] 失败: {str(e)[:50]}")

    # 显示降级统计
    stats = proxy.get_fallback_stats()
    print(f"\n降级统计:")
    print(f"  总计: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['fail']}")


def demo_provider_switching():
    """演示切换数据源"""
    print("\n" + "=" * 70)
    print("演示3: 切换数据源")
    print("=" * 70)

    # 加载配置
    config = ConfigManager.load_config('configs/data/source.yaml')

    # 创建工厂
    factory = DataProviderFactory(config)

    # 列出可用的数据源
    print("\n可用数据源:")
    providers_info = factory.list_providers()
    for name, info in providers_info.items():
        print(f"  - {name}: {info['type']}")

    # 切换不同的数据源
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    symbol = "000001.SZ"

    print(f"\n查询股票: {symbol}")
    print("-" * 70)

    for name in providers_info.keys():
        try:
            provider = factory.get_provider(name)
            if not provider:
                continue

            start_time = datetime.now()
            df = provider.get_daily_bars(symbol, start_date, end_date)
            elapsed = (datetime.now() - start_time).total_seconds()

            print(f"{name:15s}: {len(df):5d}条, {elapsed*1000:6.2f}ms")

        except Exception as e:
            print(f"{name:15s}: 错误 - {str(e)[:30]}")


def demo_cache_stats():
    """演示缓存统计"""
    print("\n" + "=" * 70)
    print("演示4: 缓存统计")
    print("=" * 70)

    config = ConfigManager.load_config('configs/data/source.yaml')
    factory = DataProviderFactory(config)
    provider = factory.get_primary_provider()

    # 检查是否有缓存功能
    if hasattr(provider, 'get_stats'):
        # 第一次查询
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        symbol = "000001.SZ"

        print("\n第一次查询（应缓存未命中）:")
        provider.get_daily_bars(symbol, start_date, end_date)
        stats = provider.get_stats()
        print(f"  缓存命中: {stats['cache_hits']}")
        print(f"  缓存未命中: {stats['cache_misses']}")
        print(f"  命中率: {stats['hit_rate']:.2%}")

        # 第二次查询（相同股票）
        print("\n第二次查询（应缓存命中）:")
        provider.get_daily_bars(symbol, start_date, end_date)
        stats = provider.get_stats()
        print(f"  缓存命中: {stats['cache_hits']}")
        print(f"  缓存未命中: {stats['cache_misses']}")
        print(f"  命中率: {stats['hit_rate']:.2%}")

        print(f"\n  总共读取文件: {stats['files_read']}")
        print(f"  总共读取字节: {stats['bytes_read'] / 1024 / 1024:.2f} MB")
    else:
        print("当前数据源不支持缓存统计")


def demo_stock_universe():
    """演示获取股票池"""
    print("\n" + "=" * 70)
    print("演示5: 获取股票池")
    print("=" * 70)

    config = ConfigManager.load_config('configs/data/source.yaml')
    factory = DataProviderFactory(config)
    provider = factory.get_primary_provider()

    print("\n获取A股股票池...")
    end_date = datetime.now()

    try:
        symbols = provider.get_stock_universe(end_date, market='A_SHARE')

        print(f"股票数量: {len(symbols)}")

        # 显示前10个和后10个
        print("\n前10只股票:")
        for symbol in symbols[:10]:
            print(f"  - {symbol}")

        print("\n后10只股票:")
        for symbol in symbols[-10:]:
            print(f"  - {symbol}")

    except Exception as e:
        print(f"获取股票池失败: {e}")


def main():
    """主函数"""
    print("=" * 70)
    print("数据提供器演示")
    print("=" * 70)

    # 设置日志
    setup_logger(name='demo', level='INFO')

    # 运行所有演示
    try:
        demo_basic_usage()
        demo_fallback_proxy()
        demo_provider_switching()
        demo_cache_stats()
        demo_stock_universe()

        print("\n" + "=" * 70)
        print("演示完成")
        print("=" * 70)

    except Exception as e:
        print(f"\n演示失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
