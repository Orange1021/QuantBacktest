#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试wencai配置
"""

import sys
from pathlib import Path
import yaml

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from src.core.filter.wencai_stock_filter import WencaiStockFilter

# 加载配置
config_file = Path(project_root) / 'configs' / 'strategy' / 'continuous_decline.yaml'
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=" * 80)
print("测试wencai配置读取")
print("=" * 80)

# 检查filter_params配置
filter_params = config['strategy']['filter_params']
print("\nfilter_params:")
for key, value in filter_params.items():
    print(f"  {key}: {value}")

# 检查wencai_params
wencai_params = filter_params.get('wencai_params', {})
print("\nwencai_params:")
for key, value in wencai_params.items():
    if key == 'cookie':
        print(f"  {key}: {value[:50]}... (length: {len(value)})")
    else:
        print(f"  {key}: {value}")

# 检查filter_type
filter_type = filter_params.get('filter_type', 'stock_filter')
print(f"\nfilter_type: {filter_type}")

cookie = wencai_params['cookie']
print(f"\ncookie长度: {len(cookie)}")
print(f"cookie前50字符: {cookie[:50]}")
print(f"cookie最后10字符: {cookie[-10:]}")

# 创建wencai筛选器
print("\n创建WencaiStockFilter...")
wencai = WencaiStockFilter(cookie)
print(f"wencai对象: {wencai}")
print(f"wencai.cookie: {wencai.cookie[:50]}...")

# 测试调用
test_date = datetime(2023, 1, 3)
print(f"\n测试日期: {test_date}")

try:
    results = wencai.get_eligible_stocks(
        date=test_date,
        decline_days_threshold=7,
        market_cap_threshold=1000000000
    )
    print(f"结果数量: {len(results)}")
    if results:
        print(f"前3只: {results[:3]}")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
