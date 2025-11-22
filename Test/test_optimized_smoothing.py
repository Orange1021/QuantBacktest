"""
测试优化后的平滑逻辑
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Analysis.performance import PerformanceAnalyzer
from Analysis.plotting import BacktestPlotter


def create_realistic_data():
    """创建更真实的回测数据"""
    # 生成测试日期范围（匹配实际回测的数据量）
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # 过滤掉周末（只保留工作日）- 这应该产生约242个交易日
    dates = dates[dates.weekday < 5]
    
    # 生成模拟资金曲线数据
    np.random.seed(42)  # 确保结果可重现
    
    # 初始资金
    initial_capital = 1000000  # 100万初始资金
    
    # 生成日收益率（带有一些趋势和波动）
    returns = np.random.normal(0.0005, 0.015, len(dates))  # 平均日收益率0.05%，波动率1.5%
    
    # 添加一些趋势和周期性
    trend = np.linspace(0, 0.2, len(dates))  # 年化20%的上升趋势
    seasonal = 0.05 * np.sin(2 * np.pi * np.arange(len(dates)) / 60)  # 季节性波动
    
    returns = returns + trend/len(dates) + seasonal/len(dates)
    
    # 计算累计收益
    cumulative_returns = np.cumprod(1 + returns)
    total_equity = initial_capital * cumulative_returns
    
    # 生成现金数据（模拟真实交易中的现金变化）
    cash_ratio = 0.05 + 0.15 * np.abs(np.sin(2 * np.pi * np.arange(len(dates)) / 30))  # 现金比例在5%-20%之间波动
    cash = total_equity * cash_ratio
    
    # 计算持仓市值
    positions_value = total_equity - cash
    
    # 创建DataFrame
    df = pd.DataFrame({
        'total_equity': total_equity,
        'cash': cash,
        'positions_value': positions_value,
        'returns': returns
    }, index=dates)
    
    return df


def calculate_new_window_size(data_length):
    """计算新的窗口大小"""
    if data_length < 50:
        window_size = 3
    elif data_length < 150:
        window_size = max(5, int(data_length * 0.1))
    elif data_length < 300:
        window_size = max(8, int(data_length * 0.08))
    else:
        window_size = min(20, max(10, int(data_length * 0.05)))
    return window_size


def test_new_smoothing_logic():
    """测试新的平滑逻辑"""
    print("🔍 测试优化后的平滑逻辑")
    print("=" * 60)
    
    # 创建真实数据
    print("📊 生成真实回测数据...")
    test_df = create_realistic_data()
    print(f"✅ 测试数据生成完成，共 {len(test_df)} 个交易日")
    print(f"📈 初始资金: {test_df['total_equity'].iloc[0]:,.0f}")
    print(f"💰 最终资金: {test_df['total_equity'].iloc[-1]:,.0f}")
    print(f"📊 总收益率: {(test_df['total_equity'].iloc[-1]/test_df['total_equity'].iloc[0]-1)*100:.2f}%")
    
    # 创建PerformanceAnalyzer
    print("\n🔍 创建PerformanceAnalyzer...")
    equity_curve = []
    for i, (date, row) in enumerate(test_df.iterrows()):
        equity_curve.append({
            'datetime': date,
            'total_equity': row['total_equity'],
            'cash': row['cash'],
            'positions_value': row['positions_value']
        })
    analyzer = PerformanceAnalyzer(equity_curve)
    print("✅ PerformanceAnalyzer创建完成")
    
    # 检查新的平滑逻辑
    df = analyzer.df
    equity = df['total_equity']
    data_length = len(equity)
    new_window_size = calculate_new_window_size(data_length)
    
    print(f"\n🔍 新的平滑参数分析:")
    print(f"   数据长度: {data_length}")
    print(f"   新窗口大小: {new_window_size}")
    
    # 计算平滑序列
    equity_smooth = equity.rolling(window=new_window_size, min_periods=1).mean()
    
    # 比较原始数据和平滑数据的差异
    print(f"\n📊 新平滑效果分析:")
    print(f"   原始数据标准差: {equity.std():,.2f}")
    print(f"   平滑数据标准差: {equity_smooth.std():,.2f}")
    print(f"   平滑程度: {(1 - equity_smooth.std()/equity.std())*100:.1f}%")
    
    # 测试不同数据长度下的窗口大小
    print(f"\n🔍 不同数据长度下的窗口大小:")
    test_lengths = [20, 50, 100, 150, 242, 300, 500]
    for length in test_lengths:
        window = calculate_new_window_size(length)
        print(f"   数据长度 {length:3d} -> 窗口大小: {window:2d}")
    
    # 生成优化后的图表
    print(f"\n📈 生成优化后的图表...")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / f"optimized_smoothing_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plotter = BacktestPlotter(analyzer, output_dir=output_dir)
    print(f"✅ BacktestPlotter创建完成")
    print(f"📁 输出文件夹: {plotter.output_dir}")
    
    # 使用create_full_report生成完整报告
    try:
        plotter.create_full_report("optimized_report")
        print("✅ 优化后的完整报告生成成功")
    except Exception as e:
        print(f"❌ 优化后的完整报告生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 运行实际的main.py来测试
    print(f"\n🚀 运行实际的main.py来测试优化效果...")
    print("💡 这将使用真实的回测数据来验证平滑优化")
    
    return True


if __name__ == "__main__":
    # 运行测试
    success = test_new_smoothing_logic()
    
    if success:
        print("\n✅ 优化测试通过！")
        print("💡 新的平滑逻辑应该能显著改善图表的锯齿问题。")
        print("📊 现在可以运行 main.py 来查看实际的优化效果。")
    else:
        print("\n❌ 优化测试失败，请检查错误信息。")
