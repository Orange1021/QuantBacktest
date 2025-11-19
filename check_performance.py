#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查回测结果，特别关注收益率计算逻辑
"""

import sys
from pathlib import Path

# 将src目录添加到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd

def check_backtest_performance():
    """检查回测性能指标"""
    print("检查回测性能指标...")
    
    # 读取VectorBT交易记录
    vectorbt_trades_path = "data/backtest_results/continuous_decline_20230101_20230110_20251119_155644/trades.csv"
    try:
        vectorbt_df = pd.read_csv(vectorbt_trades_path)
        print(f"VectorBT交易记录数量: {len(vectorbt_df)}")
        print(f"交易盈亏详情:")
        print(vectorbt_df[['entry_price', 'exit_price', 'pnl', 'return']].describe())
        print()
        
        # 计算总盈利/亏损
        total_pnl = vectorbt_df['pnl'].sum()
        positive_pnl = vectorbt_df[vectorbt_df['pnl'] > 0]['pnl'].sum()  # 总盈利
        negative_pnl = vectorbt_df[vectorbt_df['pnl'] < 0]['pnl'].sum()  # 总亏损（负数）
        
        print(f"实际总盈利: {positive_pnl:.2f}")
        print(f"实际总亏损: {negative_pnl:.2f}")
        print(f"净盈利: {total_pnl:.2f}")
        print()
        
    except Exception as e:
        print(f"读取VectorBT交易记录失败: {e}")
        print()
    
    # 读取性能摘要
    perf_summary_path = "data/backtest_results/continuous_decline_20230101_20230110_20251119_155644/performance_summary.txt"
    try:
        with open(perf_summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("性能摘要内容:")
            print(content)
    except Exception as e:
        print(f"读取性能摘要失败: {e}")

if __name__ == '__main__':
    check_backtest_performance()