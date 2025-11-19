#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试本地CSV数据提供器
"""

import sys
from pathlib import Path
from datetime import datetime

# 将src目录添加到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.local_csv_provider import LocalCSVDataProvider
from src.utils.config import ConfigManager

def test_local_csv_provider():
    """测试本地CSV数据提供器"""
    print("开始测试本地CSV数据提供器...")
    
    # 加载配置
    config = ConfigManager.load_config('configs/data/source.yaml')
    data_dir = config['data']['local_csv']['data_dir']
    cache_size = config['data']['local_csv']['cache']['max_size']
    validate_tscode = config['data']['local_csv']['cleaning']['validate_tscode']
    filter_future = config['data']['local_csv']['cleaning']['filter_future']
    file_format = config['data']['local_csv']['file_format']
    
    print(f"数据目录: {data_dir}")
    print(f"缓存大小: {cache_size}")
    print(f"验证TS代码: {validate_tscode}")
    print(f"过滤未来日期: {filter_future}")
    print(f"文件格式: {file_format}")
    
    try:
        # 创建数据提供器
        provider = LocalCSVDataProvider(
            data_dir=data_dir,
            cache_size=cache_size,
            validate_tscode=validate_tscode,
            filter_future=filter_future,
            file_format=file_format
        )
        print("✓ 数据提供器创建成功")
    except Exception as e:
        print(f"✗ 数据提供器创建失败: {e}")
        return False

    # 测试获取数据
    test_symbol = "000001.SZ"  # 平安银行
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    
    print(f"\n测试获取 {test_symbol} 的数据 ({start_date.date()} - {end_date.date()})")
    
    try:
        df = provider.get_daily_bars(test_symbol, start_date, end_date)
        print(f"✓ 成功获取数据，共 {len(df)} 条记录")
        if len(df) > 0:
            print("数据预览:")
            print(df.head())
        else:
            print("⚠ 数据为空，可能该股票在指定日期范围内没有数据或数据文件不存在")
    except FileNotFoundError as e:
        print(f"✗ 文件未找到: {e}")
        print("  请检查数据目录是否存在，以及股票代码对应的文件是否存在")
        return False
    except Exception as e:
        print(f"✗ 获取数据失败: {e}")
        return False

    # 测试缓存信息
    stats = provider.get_stats()
    print(f"\n缓存统计:")
    print(f"  命中次数: {stats['cache_hits']}")
    print(f"  未命中次数: {stats['cache_misses']}")
    print(f"  命中率: {stats['hit_rate']:.2%}")
    print(f"  当前缓存大小: {stats['cache_size']}")

    # 测试其他股票以验证缓存命中
    print(f"\n再次获取相同股票数据以验证缓存...")
    try:
        df2 = provider.get_daily_bars(test_symbol, start_date, end_date)
        print(f"✓ 再次获取成功，缓存应已命中")
        stats2 = provider.get_stats()
        print(f"  新的命中次数: {stats2['cache_hits']}")
        print(f"  新的命中率: {stats2['hit_rate']:.2%}")
    except Exception as e:
        print(f"✗ 再次获取失败: {e}")

    print("\n本地CSV数据提供器测试完成！")
    return True

if __name__ == '__main__':
    test_local_csv_provider()