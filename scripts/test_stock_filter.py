#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试StockFilter模块

验证选股逻辑是否正确
"""

import sys
from pathlib import Path
from datetime import datetime

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.filter.stock_filter import StockFilter
from src.data.provider_factory import DataProviderFactory
from src.utils.config import ConfigManager


def test_filter():
    """测试StockFilter"""
    print("=" * 60)
    print("StockFilter 测试")
    print("=" * 60)

    # 加载配置
    print("\n1. 加载配置...")
    config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')
    print("[OK] 配置加载成功")

    # 创建数据提供器工厂
    print("\n2. 创建数据提供器工厂...")
    data_config = ConfigManager.load_config('configs/data/source.yaml')
    factory = DataProviderFactory(data_config)
    print("[OK] 数据提供器工厂创建成功")

    # 创建筛选器
    print("\n3. 创建StockFilter...")
    stock_filter = StockFilter(factory)
    print("[OK] StockFilter创建成功")

    # 测试单只股票（调试用）
    print("\n4. 测试单只股票...")
    test_symbol = "000001.SZ"  # 平安银行
    test_date = datetime(2024, 8, 1)

    result = stock_filter.test_single_stock(
        symbol=test_symbol,
        date=test_date,
        decline_days=7
    )

    if 'error' in result:
        print(f"[FAIL] 测试失败: {result['error']}")
    else:
        print(f"股票: {result['symbol']}")
        print(f"日期: {result['date'].strftime('%Y-%m-%d')}")
        print(f"是否连续下跌{result['decline_days']}天: {result['is_decline']}")
        print(f"\n最近价格:")
        for i, (date, price) in enumerate(result['prices'], 1):
            if i > 1:
                prev_price = result['prices'][i-2][1]
                change = (price - prev_price) / prev_price * 100
                print(f"  {i-1}. {date} - ¥{price:.2f} ({change:+.2f}%)")
            else:
                print(f"  {i-1}. {date} - ¥{price:.2f}")

    # 批量筛选测试
    print("\n" + "=" * 60)
    print("5. 批量筛选测试...")
    print("=" * 60)

    # 使用小范围数据测试（提高速度）
    test_symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600519.SH", "300750.SZ"]

    print(f"测试股票: {test_symbols}")
    print(f"筛选日期: 2024-08-01")
    print(f"筛选条件: 连续下跌>=7天")

    print("\n注意：当前演示使用少量测试股票。要测试全市场筛选，")
    print("请确保 data/raw 目录有CSV数据文件，或配置Tushare/Akshare")

    eligible_stocks = stock_filter.get_eligible_stocks(
        date=test_date,
        decline_days_threshold=7,
        market_cap_threshold=1e9,
        stock_universe="A_SHARE"
    )

    print(f"\n[OK] 筛选完成！符合条件的股票: {len(eligible_stocks)} 只")

    if eligible_stocks:
        print("\n符合条件的股票列表:")
        for i, symbol in enumerate(eligible_stocks, 1):
            print(f"  {i:2d}. {symbol}")

    # 性能测试
    print("\n" + "=" * 60)
    print("6. 性能测试...")
    print("=" * 60)

    import time

    start_time = time.time()

    # 第一次查询（无缓存）
    stocks1 = stock_filter.get_eligible_stocks(
        date=datetime(2024, 8, 1),
        decline_days_threshold=7,
        market_cap_threshold=1e9
    )

    first_query_time = time.time() - start_time
    print(f"第一次查询（无缓存）: {first_query_time:.2f}秒，找到 {len(stocks1)} 只股票")

    # 第二次查询（有缓存）
    start_time = time.time()

    stocks2 = stock_filter.get_eligible_stocks(
        date=datetime(2024, 8, 1),
        decline_days_threshold=7,
        market_cap_threshold=1e9
    )

    cached_query_time = time.time() - start_time
    print(f"第二次查询（有缓存）: {cached_query_time:.2f}秒，找到 {len(stocks2)} 只股票")
    print(f"缓存加速比: {first_query_time / cached_query_time:.1f}x")

    # 验证缓存有效性
    if stocks1 == stocks2:
        print("[OK] 缓存结果一致")
    else:
        print("[FAIL] 缓存结果不一致！")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    test_filter()
