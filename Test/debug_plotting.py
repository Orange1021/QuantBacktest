# -*- coding: utf-8 -*-
"""
调试绘图问题
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from Engine.engine import BacktestEngine
from Strategies.simple_strategy import SimpleMomentumStrategy
from Portfolio.portfolio import BacktestPortfolio
from Execution.simulator import SimulatedExecution
from Analysis.performance import PerformanceAnalyzer
from Analysis.plotting import BacktestPlotter
from config.settings import settings

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_plotting():
    """调试绘图问题"""
    print("=" * 80)
    print("Debug Plotting Issues")
    print("=" * 80)
    
    # 准备测试数据
    csv_root_path = settings.get_config('data.csv_root_path')
    test_symbols = ["000001.SZSE", "000002.SZSE"]
    
    try:
        # 创建数据处理器
        loader = LocalCSVLoader(csv_root_path)
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        # 创建回测组件
        strategy = SimpleMomentumStrategy(handler, deque())
        portfolio = BacktestPortfolio(handler, initial_capital=100000.0)
        execution = SimulatedExecution(data_handler=handler)
        
        # 建立连接
        strategy.set_portfolio(portfolio)
        
        # 创建回测引擎
        engine = BacktestEngine(
            data_handler=handler,
            strategy=strategy,
            portfolio=portfolio,
            execution=execution
        )
        
        # 运行回测
        engine.run()
        print("✅ Backtest completed")
        
        # 获取资金曲线数据
        equity_curve = portfolio.get_equity_curve()
        print(f"📊 Equity curve data points: {len(equity_curve)}")
        
        if len(equity_curve) < 2:
            print("❌ Insufficient equity curve data")
            return
        
        # 打印前几个数据点
        print("\nFirst 5 equity curve data points:")
        for i, point in enumerate(equity_curve[:5]):
            print(f"  {i+1}: {point['datetime']} - Total Equity: {point['total_equity']:.2f}")
        
        # 创建绩效分析器
        analyzer = PerformanceAnalyzer(equity_curve)
        print("✅ PerformanceAnalyzer created successfully")
        
        # 检查DataFrame
        print(f"\n📊 DataFrame info:")
        print(f"  Shape: {analyzer.df.shape}")
        print(f"  Columns: {list(analyzer.df.columns)}")
        print(f"  Index range: {analyzer.df.index[0]} to {analyzer.df.index[-1]}")
        
        # 检查数据
        print(f"\n📊 Data check:")
        print(f"  Total Equity range: {analyzer.df['total_equity'].min():.2f} - {analyzer.df['total_equity'].max():.2f}")
        print(f"  Cash range: {analyzer.df['cash'].min():.2f} - {analyzer.df['cash'].max():.2f}")
        print(f"  Positions range: {analyzer.df['positions_value'].min():.2f} - {analyzer.df['positions_value'].max():.2f}")
        
        # 创建图表绘制器
        plotter = BacktestPlotter(analyzer)
        print("✅ BacktestPlotter created successfully")
        
        # 调试绘图
        print("\n🔧 Starting debug plotting...")
        
        # 手动创建图表进行调试
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        df = analyzer.df
        
        print(f"📊 Plotting data: {len(df)} data points")
        
        # 绘制资金曲线
        ax1.plot(df.index, df['total_equity'], label='Total Equity', linewidth=2, color='blue')
        ax1.plot(df.index, df['cash'], label='Cash', linewidth=1, color='red', alpha=0.7)
        ax1.plot(df.index, df['positions_value'], label='Positions', linewidth=1, color='green', alpha=0.7)
        
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Asset Value', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 绘制回撤
        drawdown_series = analyzer.get_drawdown_series()
        ax2.fill_between(drawdown_series.index, 0, drawdown_series * 100,
                       color='red', alpha=0.3, label='Drawdown Area')
        ax2.plot(drawdown_series.index, drawdown_series * 100,
               color='red', linewidth=1, label='Drawdown Curve')
        
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.legend(loc='lower right')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 格式化x轴
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 保存图表
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / "debug_plot.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"📊 Debug plot saved to: {filepath}")
        
        # 显示图表
        plt.show()
        
        print("✅ Debug completed")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_plotting()