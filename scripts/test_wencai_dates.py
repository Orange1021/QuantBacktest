#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试问财在不同日期的行为（特别是历史日期）
"""

import sys
from pathlib import Path
import yaml
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from src.core.filter.wencai_stock_filter import WencaiStockFilter

# 加载配置
config_file = Path(project_root) / 'configs' / 'strategy' / 'continuous_decline.yaml'
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

cookie = config['strategy']['filter_params']['wencai_params']['cookie']
decline_days = config['strategy']['filter_params']['decline_days_threshold']
market_cap = config['strategy']['filter_params']['market_cap_threshold']

wencai = WencaiStockFilter(cookie)

print("=" * 80)
print("测试问财在不同日期的查询结果")
print("=" * 80)

# 测试历史日期（回测中用到的）
historical_dates = [
    datetime(2023, 1, 1),
    datetime(2023, 1, 2),
    datetime(2023, 1, 3),
    datetime(2023, 1, 4),
    datetime(2023, 1, 5),
]

# 测试当前日期
today = datetime.now()
recent_dates = [
    today - timedelta(days=7),
    today - timedelta(days=3),
    today - timedelta(days=1),
]

print("\n1. 测试历史日期（回测使用）:")
print("-" * 80)
for test_date in historical_dates:
    try:
        print(f"\n查询日期: {test_date.strftime('%Y-%m-%d')}")
        print(f"查询语句: {test_date.year}年{test_date.month}月{test_date.day}日连续下跌>={decline_days}天...")

        results = wencai.get_eligible_stocks(
            date=test_date,
            decline_days_threshold=decline_days,
            market_cap_threshold=market_cap
        )

        print(f"结果数量: {len(results)}")
        if results:
            print(f"前3只股票: {results[:3]}")
        else:
            print("[WARNING] 返回0只股票")

        # 休息2秒，避免限流
        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")

print("\n2. 测试近期日期:")
print("-" * 80)
for test_date in recent_dates:
    try:
        print(f"\n查询日期: {test_date.strftime('%Y-%m-%d')}")
        print(f"查询语句: {test_date.year}年{test_date.month}月{test_date.day}日连续下跌>={decline_days}天...")

        results = wencai.get_eligible_stocks(
            date=test_date,
            decline_days_threshold=decline_days,
            market_cap_threshold=market_cap
        )

        print(f"结果数量: {len(results)}")
        if results:
            print(f"前3只股票: {results[:3]}")
        else:
            print("[WARNING] 返回0只股票")

        # 休息2秒，避免限流
        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
