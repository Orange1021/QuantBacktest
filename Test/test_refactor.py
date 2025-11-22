#!/usr/bin/env python3
"""
验证 Engine 和 Strategy 重构后的功能
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Infrastructure.events import MarketEvent, SignalEvent, Direction
from Infrastructure.enums import EventType
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from DataManager.schema.bar import BarData
from Engine.engine import BacktestEngine
from Strategies.simple_strategy import SimpleMomentumStrategy
from Portfolio.portfolio import BacktestPortfolio
from Execution.simulator import SimulatedExecution


def test_strategy_interface():
    """测试策略接口实现"""
    print("=== 测试策略接口实现 ===")
    
    # 创建模拟数据处理器
    loader = LocalCSVLoader("C:/Users/123/A股数据/个股数据")
    handler = BacktestDataHandler(
        loader=loader,
        symbol_list=["000001.SZ"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 5)
    )
    
    # 创建策略（不再需要传入队列）
    strategy = SimpleMomentumStrategy(handler)
    
    # 验证策略没有内部队列
    assert strategy.event_queue is None, "策略初始化时不应该有事件队列"
    
    # 创建外部队列并设置
    external_queue = deque()
    strategy.set_event_queue(external_queue)
    
    # 验证队列设置成功
    assert strategy.event_queue is external_queue, "事件队列设置失败"
    
    print("✅ 策略接口测试通过")
    return True


def test_engine_strategy_integration():
    """测试引擎和策略的集成"""
    print("\n=== 测试引擎和策略集成 ===")
    
    # 创建模拟数据处理器
    loader = LocalCSVLoader("C:/Users/123/A股数据/个股数据")
    handler = BacktestDataHandler(
        loader=loader,
        symbol_list=["000001.SZ"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 5)
    )
    
    # 创建策略
    strategy = SimpleMomentumStrategy(handler)
    
    # 创建其他组件
    portfolio = BacktestPortfolio(handler, initial_capital=100000.0)
    execution = SimulatedExecution(handler)
    
    # 创建引擎 - 引擎应该自动设置策略的事件队列
    engine = BacktestEngine(handler, strategy, portfolio, execution)
    
    # 验证策略的事件队列已设置
    assert strategy.event_queue is engine.event_queue, "引擎未正确设置策略的事件队列"
    
    print("✅ 引擎和策略集成测试通过")
    return True


def test_signal_flow():
    """测试信号流向"""
    print("\n=== 测试信号流向 ===")
    
    # 创建模拟数据处理器
    loader = LocalCSVLoader("C:/Users/123/A股数据/个股数据")
    handler = BacktestDataHandler(
        loader=loader,
        symbol_list=["000001.SZ"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 5)
    )
    
    # 创建策略
    strategy = SimpleMomentumStrategy(handler)
    
    # 创建外部队列
    event_queue = deque()
    strategy.set_event_queue(event_queue)
    
    # 创建模拟市场事件
    bar = BarData(
        symbol="000001",
        exchange="SZSE",
        datetime=datetime.now(),
        open_price=10.0,
        high_price=10.9,  # 最高价要大于收盘价
        low_price=9.8,
        close_price=10.8,  # 涨幅 8%，应该触发买入信号
        volume=1000000,
        turnover=10800000
    )
    market_event = MarketEvent(bar=bar)
    
    # 模拟数据处理器返回当前时间
    def mock_get_current_time():
        return market_event.bar.datetime
    
    handler.get_current_time = mock_get_current_time
    
    # 处理市场事件
    strategy._process_market_data(market_event)
    
    # 验证信号直接进入外部队列
    assert len(event_queue) > 0, "信号未进入事件队列"
    
    signal_event = event_queue.popleft()
    assert isinstance(signal_event, SignalEvent), "队列中的不是信号事件"
    assert signal_event.direction == Direction.LONG, "信号方向错误"
    
    print(f"✅ 信号流向测试通过，生成信号: {signal_event}")
    return True


def test_template_method():
    """测试模板方法模式"""
    print("\n=== 测试模板方法模式 ===")
    
    # 创建模拟数据处理器
    loader = LocalCSVLoader("C:/Users/123/A股数据/个股数据")
    handler = BacktestDataHandler(
        loader=loader,
        symbol_list=["000001.SZ"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 5)
    )
    
    # 创建策略
    strategy = SimpleMomentumStrategy(handler)
    event_queue = deque()
    strategy.set_event_queue(event_queue)
    
    # 验证策略未初始化
    assert not strategy.is_initialized, "策略不应该已初始化"
    
    # 创建模拟市场事件
    bar = BarData(
        symbol="000001",
        exchange="SZSE",
        datetime=datetime.now(),
        open_price=10.0,
        high_price=10.3,  # 最高价要大于收盘价
        low_price=9.8,
        close_price=10.2,
        volume=1000000,
        turnover=10200000
    )
    market_event = MarketEvent(bar=bar)
    
    # 模拟数据处理器返回当前时间
    def mock_get_current_time():
        return market_event.bar.datetime
    
    handler.get_current_time = mock_get_current_time
    
    # 调用模板方法
    strategy._process_market_data(market_event)
    
    # 验证策略已初始化
    assert strategy.is_initialized, "模板方法未正确初始化策略"
    assert strategy.current_time == market_event.bar.datetime, "模板方法未正确更新时间"
    
    print("✅ 模板方法模式测试通过")
    return True


def main():
    """主测试函数"""
    print("开始验证 Engine 和 Strategy 重构...\n")
    
    success = True
    success &= test_strategy_interface()
    success &= test_engine_strategy_integration()
    success &= test_signal_flow()
    success &= test_template_method()
    
    print('\n' + '='*50)
    if success:
        print('🎉 所有重构测试通过！Engine 和 Strategy 交互已正确重构。')
    else:
        print('❌ 重构测试失败，需要进一步检查。')
    
    return success


if __name__ == '__main__':
    main()