"""
专门测试锯齿问题的脚本
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


def test_plotting_difference():
    """测试绘图差异"""
    print("🔍 测试锯齿问题的根本原因")
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
    
    # 检查平滑逻辑的细节
    df = analyzer.df
    equity = df['total_equity']
    window_size = min(max(len(equity) // 100, 5), 10)
    print(f"\n🔍 平滑参数分析:")
    print(f"   数据长度: {len(equity)}")
    print(f"   计算窗口: len(equity) // 100 = {len(equity) // 100}")
    print(f"   最终窗口大小: min(max({len(equity) // 100}, 5), 10) = {window_size}")
    
    # 计算平滑序列
    equity_smooth = equity.rolling(window=window_size, min_periods=1).mean()
    
    # 比较原始数据和平滑数据的差异
    print(f"\n📊 平滑效果分析:")
    print(f"   原始数据标准差: {equity.std():,.2f}")
    print(f"   平滑数据标准差: {equity_smooth.std():,.2f}")
    print(f"   平滑程度: {(1 - equity_smooth.std()/equity.std())*100:.1f}%")
    
    # 测试1: 模拟main.py方式（传入output_dir，使用create_full_report）
    print("\n📈 测试1: 模拟main.py方式（传入output_dir，使用create_full_report）...")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / f"main_style_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plotter1 = BacktestPlotter(analyzer, output_dir=output_dir)
    print(f"✅ BacktestPlotter创建完成")
    print(f"📁 输出文件夹: {plotter1.output_dir}")
    
    # 使用create_full_report生成完整报告
    try:
        plotter1.create_full_report("backtest_report")
        print("✅ 完整报告生成成功")
    except Exception as e:
        print(f"❌ 完整报告生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 模拟独立测试方式（不传入output_dir，只生成主图）
    print("\n📈 测试2: 模拟独立测试方式（不传入output_dir，只生成主图）...")
    plotter2 = BacktestPlotter(analyzer)  # 不传入output_dir
    print(f"✅ BacktestPlotter创建完成")
    print(f"📁 输出文件夹: {plotter2.output_dir}")
    
    # 只生成主分析图
    try:
        plotter2.show_analysis_plot("test_main.png")
        print("✅ 主分析图生成成功")
    except Exception as e:
        print(f"❌ 主分析图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 测试不同窗口大小的效果
    print("\n📈 测试3: 测试不同窗口大小的效果...")
    
    # 创建不同的窗口大小进行对比
    window_sizes = [3, 5, 10, 20]
    
    for ws in window_sizes:
        print(f"\n   测试窗口大小: {ws}")
        test_output_dir = Path("output") / f"window_test_{ws}_{timestamp}"
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        test_plotter = BacktestPlotter(analyzer, output_dir=test_output_dir)
        
        # 手动修改窗口大小进行测试
        # 这里我们需要临时修改_plot_equity_curve方法中的window_size
        # 为了测试，我们创建一个自定义的绘图方法
        
        # 保存原始方法
        original_plot_equity = test_plotter._plot_equity_curve
        
        def custom_plot_equity(ax):
            """自定义的资金曲线绘制方法，使用指定的窗口大小"""
            df = test_plotter.analyzer.df
            
            # Set labels
            total_equity_label = 'Total Equity'
            cash_label = 'Cash'
            positions_label = 'Positions Value'
            title = f'Equity Curve (Window: {ws})'
            ylabel = 'Asset Value'
            initial_label = 'Initial Capital'
            raw_label = 'Raw'
            trend_label = f'Trend (MA{ws})'
            
            # 步骤 A (准备数据): 获取原始资金序列并创建平滑序列
            equity = df['total_equity']
            # 使用指定的窗口大小
            equity_smooth = equity.rolling(window=ws, min_periods=1).mean()
            
            # 步骤 B (绘制双线):
            # 原始线: 绘制 equity，颜色为灰色，线宽 lw=1，透明度 alpha=0.3
            ax.plot(df.index, equity, 
                    label=raw_label, linewidth=1, color='gray', alpha=0.3)
            
            # 平滑线: 绘制 equity_smooth，颜色为深蓝色，线宽 lw=2，透明度 alpha=1.0
            line_smooth = ax.plot(df.index, equity_smooth, 
                                 label=trend_label, linewidth=2, color='#2E86AB', alpha=1.0)[0]
            
            # 步骤 C (填充区域): 在平滑线下方填充淡淡的颜色
            ax.fill_between(df.index, test_plotter.analyzer.start_equity, equity_smooth, 
                           color=line_smooth.get_color(), alpha=0.1)
            
            # 绘制现金曲线
            ax.plot(df.index, df['cash'], 
                    label=cash_label, linewidth=1, color='#A23B72', alpha=0.7)
            
            # 绘制持仓市值曲线
            ax.plot(df.index, df['positions_value'], 
                    label=positions_label, linewidth=1, color='#F18F01', alpha=0.7)
            
            # 设置标题和标签
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=12)
            ax.legend(loc='upper left')
            
            # 格式化x轴
            import matplotlib.dates as mdates
            from matplotlib.ticker import FuncFormatter
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # 格式化y轴金额
            ax.yaxis.set_major_formatter(FuncFormatter(test_plotter._format_currency))
            
            # 添加网格
            ax.grid(True, alpha=0.3)
            
            # 添加零线
            ax.axhline(y=test_plotter.analyzer.start_equity, color='red', linestyle='--', 
                      alpha=0.5, label=f'{initial_label}: {test_plotter.analyzer.start_equity:,.0f}')
        
        # 临时替换方法
        test_plotter._plot_equity_curve = custom_plot_equity
        
        # 生成图表
        try:
            main_chart_path = test_plotter.output_dir / f"main_window_{ws}.png"
            test_plotter.show_analysis_plot(str(main_chart_path))
            print(f"   ✅ 窗口大小{ws}的图表生成成功")
        except Exception as e:
            print(f"   ❌ 窗口大小{ws}的图表生成失败: {e}")
        
        # 恢复原始方法
        test_plotter._plot_equity_curve = original_plot_equity
    
    print("\n🎉 测试完成！")
    print("💡 请检查生成的图表以确认不同窗口大小的平滑效果。")
    print("📁 生成的文件夹:")
    print(f"   - main_style_{timestamp} (模拟main.py方式)")
    print(f"   - backtest_{timestamp} (模拟独立测试方式)")
    print(f"   - window_test_*_{timestamp} (不同窗口大小测试)")
    
    return True


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # 运行测试
    success = test_plotting_difference()
    
    if success:
        print("\n✅ 测试通过！")
        print("💡 现在可以对比不同方式生成的图表效果。")
    else:
        print("\n❌ 测试失败，请检查错误信息。")
