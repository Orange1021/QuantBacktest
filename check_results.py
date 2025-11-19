#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查回测结果，特别关注资金情况
"""

import sys
from pathlib import Path

# 将src目录添加到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd

def check_backtest_results():
    """检查回测结果文件"""
    print("检查回测结果...")
    
    # 读取详细交易记录
    detailed_trades_path = "data/backtest_results/detailed_trades.csv"
    detailed_df = pd.read_csv(detailed_trades_path)
    print(f"详细交易记录数量: {len(detailed_df)}")
    print(f"交易方向分布: {detailed_df['direction'].value_counts()}")
    print(f"交易类型分布: {detailed_df['type'].value_counts()}")
    print(f"平均交易金额: {detailed_df['value'].mean():.2f}")
    print()
    
    # 读取VectorBT交易记录
    vectorbt_trades_path = "data/backtest_results/trades.csv"
    try:
        vectorbt_df = pd.read_csv(vectorbt_trades_path)
        print(f"VectorBT交易记录数量: {len(vectorbt_df)}")
        print(f"VectorBT交易概览:")
        print(vectorbt_df[['entry_price', 'exit_price', 'pnl', 'return']].describe())
        print()
    except Exception as e:
        print(f"读取VectorBT交易记录失败: {e}")
        print()
    
    # 读取持仓记录
    positions_path = "data/backtest_results/positions.csv"
    try:
        positions_df = pd.read_csv(positions_path)
        print(f"持仓记录数量: {len(positions_df)}")
        if len(positions_df) > 0:
            print(f"持仓概览:")
            print(positions_df.head())
        print()
    except Exception as e:
        print(f"读取持仓记录失败: {e}")
        print()
    
    # 读取性能摘要
    perf_summary_path = "data/backtest_results/performance_summary.txt"
    try:
        with open(perf_summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("性能摘要内容:")
            print(content)
    except Exception as e:
        print(f"读取性能摘要失败: {e}")

if __name__ == '__main__':
    check_backtest_results()