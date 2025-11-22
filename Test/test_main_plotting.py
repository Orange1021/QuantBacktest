"""
测试main.py中的BacktestPlotter创建方式
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


def create_test_data():
    """创建测试数据"""
    # 生成测试日期范围
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # 过滤掉周末（只保留工作日）
    dates = dates[dates.weekday < 5]
    
    # 生成模拟资金曲线数据
    np.random.seed(42)  # 确保结果可重现
    
    # 初始资金
    initial_capital = 100000
    
    # 生成日收益率（带有一些趋势和波动）
    returns = np.random.normal(0.0005, 0.02, len(dates))  # 平均日收益率0.05%，波动率2%
    
    # 添加一些趋势和周期性
    trend = np.linspace(0, 0.3, len(dates))  # 年化30%的上升趋势
    seasonal = 0.1 * np.sin(2 * np.pi * np.arange(len(dates)) / 60)  # 季节性波动
    
    returns = returns + trend/len(dates) + seasonal/len(dates)
    
    # 计算累计收益
    cumulative_returns = np.cumprod(1 + returns)
    total_equity = initial_capital * cumulative_returns
    
    # 生成现金数据（随机波动，但保持一定比例）
    cash_ratio = 0.1 + 0.2 * np.abs(np.sin(2 * np.pi * np.arange(len(dates)) / 30))  # 现金比例在10%-30%之间波动
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


def test_main_vs_standalone():
    """对比main.py方式和独立测试方式的差异"""
    print("🔍 对比main.py方式和独立测试方式的差异")
    print("=" * 60)
    
    # 创建测试数据
    print("📊 生成测试数据...")
    test_df = create_test_data()
    print(f"✅ 测试数据生成完成，共 {len(test_df)} 个交易日")
    
    # 创建PerformanceAnalyzer
    print("🔍 创建PerformanceAnalyzer...")
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
    
    # 测试1: 模拟main.py方式（传入output_dir）
    print("\n📈 测试1: 模拟main.py方式（传入output_dir）...")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / f"test_main_style_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plotter1 = BacktestPlotter(analyzer, output_dir=output_dir)
    print(f"✅ BacktestPlotter创建完成")
    print(f"📁 输出文件夹: {plotter1.output_dir}")
    
    # 检查平滑逻辑
    df = analyzer.df
    equity = df['total_equity']
    window_size = min(max(len(equity) // 100, 5), 10)
    print(f"🔍 平滑窗口大小: {window_size}, 数据长度: {len(equity)}")
    
    # 生成图表
    try:
        main_chart_path = plotter1.output_dir / "test_main.png"
        plotter1.show_analysis_plot(str(main_chart_path))
        print("✅ 主分析图生成成功")
    except Exception as e:
        print(f"❌ 主分析图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 模拟独立测试方式（不传入output_dir）
    print("\n📈 测试2: 模拟独立测试方式（不传入output_dir）...")
    plotter2 = BacktestPlotter(analyzer)  # 不传入output_dir
    print(f"✅ BacktestPlotter创建完成")
    print(f"📁 输出文件夹: {plotter2.output_dir}")
    
    # 检查平滑逻辑
    df2 = analyzer.df
    equity2 = df2['total_equity']
    window_size2 = min(max(len(equity2) // 100, 5), 10)
    print(f"🔍 平滑窗口大小: {window_size2}, 数据长度: {len(equity2)}")
    
    # 生成图表
    try:
        main_chart_path2 = plotter2.output_dir / "test_main.png"
        plotter2.show_analysis_plot(str(main_chart_path2))
        print("✅ 主分析图生成成功")
    except Exception as e:
        print(f"❌ 主分析图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 检查不同数据长度下的平滑效果
    print("\n📈 测试3: 检查不同数据长度下的平滑效果...")
    
    # 创建较短的数据集（10个数据点）
    short_df = test_df.head(10)
    short_equity_curve = []
    for i, (date, row) in enumerate(short_df.iterrows()):
        short_equity_curve.append({
            'datetime': date,
            'total_equity': row['total_equity'],
            'cash': row['cash'],
            'positions_value': row['positions_value']
        })
    short_analyzer = PerformanceAnalyzer(short_equity_curve)
    
    # 计算平滑窗口
    short_df_analyzed = short_analyzer.df
    short_equity = short_df_analyzed['total_equity']
    short_window_size = min(max(len(short_equity) // 100, 5), 10)
    print(f"🔍 短数据集 - 平滑窗口大小: {short_window_size}, 数据长度: {len(short_equity)}")
    
    # 创建中等长度的数据集（50个数据点）
    medium_df = test_df.head(50)
    medium_equity_curve = []
    for i, (date, row) in enumerate(medium_df.iterrows()):
        medium_equity_curve.append({
            'datetime': date,
            'total_equity': row['total_equity'],
            'cash': row['cash'],
            'positions_value': row['positions_value']
        })
    medium_analyzer = PerformanceAnalyzer(medium_equity_curve)
    
    # 计算平滑窗口
    medium_df_analyzed = medium_analyzer.df
    medium_equity = medium_df_analyzed['total_equity']
    medium_window_size = min(max(len(medium_equity) // 100, 5), 10)
    print(f"🔍 中等数据集 - 平滑窗口大小: {medium_window_size}, 数据长度: {len(medium_equity)}")
    
    print("\n🎉 测试完成！")
    print(f"📊 数据长度对比:")
    print(f"   - 短数据集 (10点): 窗口大小 = {short_window_size}")
    print(f"   - 中等数据集 (50点): 窗口大小 = {medium_window_size}")
    print(f"   - 原始数据集 ({len(test_df)}点): 窗口大小 = {window_size}")
    
    return True


if __name__ == "__main__":
    # 运行测试
    success = test_main_vs_standalone()
    
    if success:
        print("\n✅ 测试通过！")
        print("💡 请检查生成的图表以确认平滑效果是否一致。")
    else:
        print("\n❌ 测试失败，请检查错误信息。")
