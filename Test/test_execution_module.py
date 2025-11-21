"""
执行模块测试
测试 Execution 模块与现有系统的集成
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
from DataManager.schema.bar import BarData
from DataManager.schema.constant import Exchange, Interval
from Engine.engine import BacktestEngine
from Strategies.simple_strategy import SimpleMomentumStrategy
from Portfolio.portfolio import BacktestPortfolio
from Execution.simulator import SimulatedExecution
from config.settings import settings

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_execution_module():
    """测试执行模块集成"""
    print("=" * 80)
    print("执行模块集成测试")
    print("=" * 80)
    
    # 准备测试数据
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    test_symbols = ["000001.SZSE", "000002.SZSE"]
    
    try:
        # 创建数据加载器
        loader = LocalCSVLoader(csv_root_path)
        print(f"✅ CSV加载器创建成功")
        
        # 创建数据处理器
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        print(f"✅ 数据处理器创建成功")
        
        # 创建执行器
        execution = SimulatedExecution(
            data_handler=handler,
            commission_rate=0.0003,
            slippage_rate=0.001
        )
        print(f"✅ 模拟执行器创建成功")
        
        # 测试1: 市价单执行
        print(f"\n测试1: 市价单执行")
        print("-" * 40)
        
        # 先推进时间，确保有数据
        event_generator = handler.update_bars()
        for _ in range(5):  # 推进5个事件
            try:
                next(event_generator)
            except StopIteration:
                break
        
        # 创建市价单
        market_order = OrderEvent(
            symbol="000001.SZSE",
            datetime=datetime.now(),
            order_type=OrderType.MARKET,
            direction=Direction.LONG,
            volume=1000
        )
        
        # 执行市价单
        fill_event = execution.execute_order(market_order)
        
        if fill_event:
            print(f"✅ 市价单执行成功")
            print(f"   股票: {fill_event.symbol}")
            print(f"   数量: {fill_event.volume}")
            print(f"   价格: {fill_event.price:.2f}")
            print(f"   手续费: {fill_event.commission:.2f}")
            print(f"   净成交额: {fill_event.net_value:.2f}")
        else:
            print(f"❌ 市价单执行失败")
            return False
        
        # 测试2: 限价单执行
        print(f"\n测试2: 限价单执行")
        print("-" * 40)
        
        # 创建限价单
        limit_order = OrderEvent(
            symbol="000002.SZSE",
            datetime=datetime.now(),
            order_type=OrderType.LIMIT,
            direction=Direction.LONG,
            volume=500,
            limit_price=10.0  # 限价10.0元
        )
        
        # 执行限价单
        fill_event = execution.execute_order(limit_order)
        
        if fill_event:
            print(f"✅ 限价单执行成功")
            print(f"   股票: {fill_event.symbol}")
            print(f"   数量: {fill_event.volume}")
            print(f"   价格: {fill_event.price:.2f}")
            print(f"   限价: {limit_order.limit_price:.2f}")
            print(f"   手续费: {fill_event.commission:.2f}")
        else:
            print(f"❌ 限价单执行失败")
            return False
        
        # 测试3: 无效订单处理
        print(f"\n测试3: 无效订单处理")
        print("-" * 40)
        
        # 创建无效订单（数量为0）
        invalid_order = OrderEvent(
            symbol="000001.SZSE",
            datetime=datetime.now(),
            order_type=OrderType.MARKET,
            direction=Direction.LONG,
            volume=0  # 无效数量
        )
        
        # 执行无效订单
        fill_event = execution.execute_order(invalid_order)
        
        if fill_event is None:
            print(f"✅ 无效订单正确被拒绝")
        else:
            print(f"❌ 无效订单错误被接受")
            return False
        
        # 测试4: 执行器统计
        print(f"\n测试4: 执行器统计")
        print("-" * 40)
        
        stats = execution.get_execution_stats()
        print(f"✅ 执行器统计信息:")
        print(f"   接收订单: {stats['orders_received']}")
        print(f"   执行订单: {stats['orders_executed']}")
        print(f"   拒绝订单: {stats['orders_rejected']}")
        print(f"   执行率: {stats['execution_rate']:.2%}")
        print(f"   总手续费: {stats['total_commission']:.2f}")
        print(f"   平均手续费: {stats['avg_commission']:.2f}")
        
        # 测试5: 完整回测流程集成
        print(f"\n测试5: 完整回测流程集成")
        print("-" * 40)
        
        # 重置执行器统计
        execution.reset_stats()
        
        # 创建完整的回测系统
        strategy = SimpleMomentumStrategy(handler, deque())
        portfolio = BacktestPortfolio(handler, initial_capital=100000.0)
        
        # 建立策略和投资组合的连接
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
        print(f"✅ 完整回测流程运行成功")
        
        # 获取各模块统计
        engine_status = engine.get_status()
        strategy_info = strategy.get_strategy_info()
        portfolio_info = portfolio.get_portfolio_info()
        execution_stats = execution.get_execution_stats()
        
        print(f"\n📊 最终统计:")
        print(f"   引擎总事件: {engine_status['total_events']}")
        print(f"   策略信号数: {strategy_info['signals_generated']}")
        print(f"   投资组合交易数: {portfolio_info['total_trades']}")
        print(f"   执行器订单数: {execution_stats['orders_received']}")
        print(f"   执行器成交数: {execution_stats['orders_executed']}")
        print(f"   最终资金: {portfolio.get_cash():,.2f}")
        print(f"   总资产: {portfolio.get_equity():,.2f}")
        print(f"   总收益率: {portfolio_info['return_rate']:.2f}%")
        
        # 验证事件流转
        if (execution_stats['orders_received'] == execution_stats['orders_executed'] and
            execution_stats['orders_executed'] == portfolio_info['fills_processed']):
            print(f"✅ 事件流转验证通过")
        else:
            print(f"❌ 事件流转验证失败")
            return False
        
        print(f"\n🎉 执行模块集成测试全部通过！")
        return True
        
    except Exception as e:
        print(f"❌ 执行模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_execution_module()
    
    if success:
        print(f"\n🚀 Execution模块集成成功，系统架构完整闭环！")
        print(f"📈 QuantBacktest V1.0 核心骨架已完成")
    else:
        print(f"\n💥 Execution模块集成测试失败")
