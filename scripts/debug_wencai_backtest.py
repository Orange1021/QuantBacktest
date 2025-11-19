#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试wencai在回测中的调用问题
"""

import sys
from pathlib import Path
import yaml

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from src.core.filter.wencai_stock_filter import WencaiStockFilter
from src.utils.logger import setup_logger

# 加载配置
config_file = Path(project_root) / 'configs' / 'strategy' / 'continuous_decline.yaml'
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

cookie = config['strategy']['filter_params']['wencai_params']['cookie']
decline_days = config['strategy']['filter_params']['decline_days_threshold']
market_cap = config['strategy']['filter_params']['market_cap_threshold']

print("=" * 70)
print("调试wencai在回测中的调用")
print("=" * 70)
print(f"配置参数:")
print(f"  - decline_days_threshold: {decline_days}")
print(f"  - market_cap_threshold: {market_cap}")
print(f"  - cookie: {cookie[:50]}...")
print("=" * 70)

# 创建wencai筛选器
print("\n[1/3] 创建WencaiStockFilter...")
wencai = WencaiStockFilter(cookie)
print("[OK] 创建成功")

# 测试几个常用的回测日期
test_dates = [
    datetime(2024, 8, 1),
    datetime(2024, 8, 5),
    datetime(2024, 9, 1),
    datetime(2024, 10, 8),
]

print("\n[2/3] 测试多个日期...")
for test_date in test_dates:
    print(f"\n测试日期: {test_date.strftime('%Y-%m-%d')}")
    print("-" * 70)

    try:
        # 检查日期格式
        formatted_date = f"{test_date.year}年{test_date.month}月{test_date.day}日"
        print(f"格式化日期: {formatted_date}")

        # 调用wencai
        results = wencai.get_eligible_stocks(
            date=test_date,
            decline_days_threshold=decline_days,
            market_cap_threshold=market_cap
        )

        print(f"结果数量: {len(results)}")
        if results:
            print(f"前5只股票: {results[:5]}")
        else:
            print("[WARNING] 返回0只股票")

    except Exception as e:
        print(f"[ERROR] 失败: {e}")
        import traceback
        traceback.print_exc()

print("\n[3/3] 测试完成")
print("=" * 70)

# 对比单独测试的调用方式
print("\n对比单独测试的调用方式...")
print("-" * 70)
test_date_2023 = datetime(2023, 1, 1)
results_2023 = wencai.get_eligible_stocks(
    date=test_date_2023,
    decline_days_threshold=7,
    market_cap_threshold=1000000000
)
print(f"2023-01-01 结果数量: {len(results_2023)}")
if results_2023:
    print(f"前5只股票: {results_2023[:5]}")