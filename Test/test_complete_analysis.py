"""
完整回测分析演示
展示从数据加载到绩效分析的完整流程
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent, EventType, Direction, OrderType
from Infrastructure.enums import EventType as EnumEventType, Direction as EnumDirection, OrderType as EnumOrderType
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from DataManager.selectors.wencai_selector import WencaiSelector
from Engine.engine import BacktestEngine
from Strategies.simple_strategy import SimpleMomentumStrategy
from Portfolio.portfolio import BacktestPortfolio
from Execution.simulator import SimulatedExecution
from Analysis.performance import PerformanceAnalyzer
from Analysis.plotting import BacktestPlotter
from config.settings import settings

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def run_complete_backtest_analysis():
    """运行完整的回测分析流程"""
    print("=" * 80)
    print("量化回测完整分析演示")
    print("流程: 数据加载 -> 策略回测 -> 绩效分析 -> 可视化")
    print("=" * 80)
    
    # 准备测试数据
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE", "600036.SSE"]
    
    try:
        # 步骤1: 数据准备
        print(f"\n📊 步骤1: 数据准备")
        print("-" * 40)
        
        loader = LocalCSVLoader(csv_root_path)
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31)
        )
        print(f"✅ 数据处理器创建成功，股票数量: {len(test_symbols)}")
        
        # 步骤2: 创建回测组件
        print(f"\n🔄 步骤2: 创建回测组件")
        print("-" * 40)
        
        strategy = SimpleMomentumStrategy(handler)
        portfolio = BacktestPortfolio(handler, initial_capital=100000.0)
        execution = SimulatedExecution(
            data_handler=handler,
            commission_rate=0.0003,
            slippage_rate=0.001
        )
        
        # 建立连接
        strategy.set_portfolio(portfolio)
        
        engine = BacktestEngine(
            data_handler=handler,
            strategy=strategy,
            portfolio=portfolio,
            execution=execution
        )
        print(f"✅ 回测组件创建完成")
        
        # 步骤3: 运行回测
        print(f"\n🚀 步骤3: 运行回测")
        print("-" * 40)
        
        engine.run()
        print(f"✅ 回测运行完成")
        
        # 获取回测统计
        engine_status = engine.get_status()
        strategy_info = strategy.get_strategy_info()
        portfolio_info = portfolio.get_portfolio_info()
        execution_stats = execution.get_execution_stats()
        
        print(f"\n📈 回测统计:")
        print(f"   总事件数: {engine_status['total_events']}")
        print(f"   策略信号: {strategy_info['signals_generated']}")
        print(f"   执行订单: {execution_stats['orders_executed']}")
        print(f"   最终资产: {portfolio.get_equity():,.2f}")
        print(f"   收益率: {portfolio_info['return_rate']:.2f}%")
        
        # 步骤4: 绩效分析
        print(f"\n📊 步骤4: 绩效分析")
        print("-" * 40)
        
        # 获取资金曲线数据
        equity_curve = portfolio.equity_curve
        print(f"   资金曲线数据点: {len(equity_curve)}")
        
        # 创建绩效分析器
        analyzer = PerformanceAnalyzer(equity_curve)
        
        # 打印详细分析报告
        analyzer.print_summary()
        
        # 获取关键指标
        summary = analyzer.get_summary()
        print(f"\n🎯 关键指标:")
        print(f"   夏普比率: {summary['sharpe_ratio']:.3f}")
        print(f"   最大回撤: {summary['max_drawdown_pct']:.2f}%")
        print(f"   年化收益: {summary['annualized_return_pct']:.2f}%")
        print(f"   胜率: {summary['win_rate_pct']:.2f}%")
        
        # 步骤5: 可视化分析
        print(f"\n📈 步骤5: 可视化分析")
        print("-" * 40)
        
        # 创建图表绘制器
        plotter = BacktestPlotter(analyzer)
        
        # 显示主分析图
        print("📊 正在生成主分析图...")
        plotter.show_analysis_plot()
        
        # 生成完整报告
        print("📊 正在生成完整分析报告...")
        plotter.create_full_report("demo_backtest")
        
        # 额外分析
        print("📊 正在生成收益分布图...")
        plotter.plot_returns_distribution()
        
        print("📊 正在生成滚动指标图...")
        plotter.plot_rolling_metrics(window=20)
        
        print(f"\n🎉 完整回测分析演示成功！")
        print(f"📁 分析图表已保存到 output/ 目录")
        print(f"📋 所有模块协同工作正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整回测分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_complete_backtest_analysis()
    
    if success:
        print(f"\n🚀 QuantBacktest 完整分析系统已就绪！")
        print(f"📈 现在可以进行专业的量化回测分析了")
    else:
        print(f"\n💥 完整回测分析演示失败")
