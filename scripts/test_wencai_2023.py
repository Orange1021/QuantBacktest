#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试问财筛选器（2023年1月1日）
"""

import sys
from pathlib import Path

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from src.core.filter.wencai_stock_filter import WencaiStockFilter
from src.utils.logger import setup_logger

# 配置问财Cookie（从配置文件读取）
import yaml
config_file = Path(project_root) / 'configs' / 'strategy' / 'continuous_decline.yaml'
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

cookie = config['strategy']['filter_params']['wencai_params']['cookie']

print("=" * 70)
print("测试问财筛选器")
print("=" * 70)
print(f"测试日期: 2023-01-01")
print(f"筛选条件: 连续下跌>=7天, 市值>=10亿, 非ST")
print("=" * 70)

# 创建问财筛选器
print("\n[1/3] 创建问财筛选器...")
try:
    wencai = WencaiStockFilter(cookie)
    print("[OK] 问财筛选器创建成功")
except Exception as e:
    print(f"[ERROR] 创建失败: {e}")
    sys.exit(1)

# 执行查询
print("\n[2/3] 查询问财...")
print("注意: 这可能需要5-10秒...")

try:
    test_date = datetime(2023, 1, 1)
    query = "连续下跌7天，市值大于10亿，非ST"

    print(f"查询语句: {query}")
    print(f"查询日期: {test_date.strftime('%Y-%m-%d')}")

    results = wencai.get_eligible_stocks(
        date=test_date,
        decline_days_threshold=7,  # 7天连续下跌
        market_cap_threshold=1000000000  # 10亿市值
    )

    print("\n[3/3] 查询结果:")
    print("=" * 70)
    print(f"符合条件的股票数: {len(results)}")

    if results:
        print("\n股票列表:")
        for i, stock in enumerate(results[:20], 1):  # 显示前20只
            print(f"{i:2d}. {stock}")
        if len(results) > 20:
            print(f"... 还有 {len(results) - 20} 只")
    else:
        print("没有找到符合条件的股票")
    print("=" * 70)

    # 保存结果
    if results:
        output_file = Path(project_root) / 'data' / 'wencai_test_2023_01_01.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"问财查询结果 - 2023-01-01\n")
            f.write(f"查询条件: {query}\n")
            f.write(f"股票数量: {len(results)}\n")
            f.write("\n股票列表:\n")
            for stock in results:
                f.write(f"{stock}\n")
        print(f"\n结果已保存到: {output_file}")

except Exception as e:
    print(f"\n[ERROR] 查询失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] 测试完成")
