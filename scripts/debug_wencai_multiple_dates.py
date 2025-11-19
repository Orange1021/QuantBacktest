#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试wencai在不同日期的返回结果，验证是否真的是数据问题
"""

import sys
from pathlib import Path
import yaml

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
print("测试wencai在不同时间段的返回结果")
print("=" * 80)
print(f"查询条件: 连续下跌>={decline_days}天, 市值>={market_cap/1e8:.0f}亿")
print("=" * 80)

# 测试不同年份和月份
test_periods = [
    ("2023-01", [1, 8, 15, 22, 29]),  # 2023年1月
    ("2023-06", [1, 8, 15, 22, 29]),  # 2023年6月
    ("2023-12", [1, 8, 15, 22, 29]),  # 2023年12月
    ("2024-01", [1, 8, 15, 22, 29]),  # 2024年1月
    ("2024-02", [1, 8, 15, 22, 29]),  # 2024年2月
    ("2024-03", [1, 8, 15, 22, 29]),  # 2024年3月
    ("2024-04", [1, 8, 15, 22, 29]),  # 2024年4月
    ("2024-05", [1, 8, 15, 22, 29]),  # 2024年5月
    ("2024-06", [1, 8, 15, 22, 29]),  # 2024年6月
    ("2024-07", [1, 8, 15, 22, 29]),  # 2024年7月
    ("2024-08", [1, 8, 15, 22, 29]),  # 2024年8月 - 回测期间
    ("2024-09", [1, 8, 15, 22, 29]),  # 2024年9月 - 回测期间
    ("2024-10", [1, 8, 15, 22, 29]),  # 2024年10月 - 回测期间
    ("2024-11", [1, 8, 15, 22, 29]),  # 2024年11月
]

total_queries = 0
zero_results = 0
results_summary = []

for period, days in test_periods:
    year, month = map(int, period.split('-'))
    print(f"\n{year}年{month}月:")
    print("-" * 80)

    monthly_non_zero = 0
    monthly_total = 0

    for day in days:
        try:
            test_date = datetime(year, month, day)
            total_queries += 1
            monthly_total += 1

            # 调用wencai
            results = wencai.get_eligible_stocks(
                date=test_date,
                decline_days_threshold=decline_days,
                market_cap_threshold=market_cap
            )

            count = len(results)
            if count > 0:
                monthly_non_zero += 1
                print(f"  {test_date.strftime('%Y-%m-%d')}: {count:2d}只")
            else:
                zero_results += 1
                print(f"  {test_date.strftime('%Y-%m-%d')}:  0只 ⚠️")

            results_summary.append({
                'date': test_date,
                'count': count,
                'stocks': results[:3] if results else []
            })

        except Exception as e:
            print(f"  {year}-{month:02d}-{day:02d}: ERROR - {str(e)[:50]}")

    print(f"  该月非零结果天数: {monthly_non_zero}/{monthly_total}")

print("\n" + "=" * 80)
print("汇总统计:")
print("=" * 80)
print(f"总查询次数: {total_queries}")
print(f"返回0只的次数: {zero_results}")
print(f"有结果的比例: {(total_queries - zero_results) / total_queries * 100:.1f}%")

print("\n" + "=" * 80)
print("详细结果（前20条）:")
print("=" * 80)
for i, item in enumerate(results_summary[:20], 1):
    print(f"{i:2d}. {item['date'].strftime('%Y-%m-%d')}: {item['count']:2d}只", end="")
    if item['stocks']:
        print(f" (e.g. {', '.join(item['stocks'])})")
    else:
        print()

# 保存结果到文件
output_file = Path(project_root) / 'data' / 'wencai_debug_summary.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("Wencai筛选器测试结果\n")
    f.write("=" * 80 + "\n")
    f.write(f"查询条件: 连续下跌>={decline_days}天, 市值>={market_cap/1e8:.0f}亿\n")
    f.write("=" * 80 + "\n\n")

    for item in results_summary:
        f.write(f"{item['date'].strftime('%Y-%m-%d')}: {item['count']}只\n")
        if item['stocks']:
            for stock in item['stocks']:
                f.write(f"  - {stock}\n")

    f.write(f"\n\n汇总:\n")
    f.write(f"总查询次数: {total_queries}\n")
    f.write(f"返回0只的次数: {zero_results}\n")
    f.write(f"有结果的比例: {(total_queries - zero_results) / total_queries * 100:.1f}%\n")

print(f"\n详细结果已保存到: {output_file}")
