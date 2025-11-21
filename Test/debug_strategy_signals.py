"""
调试策略信号生成
检查为什么策略没有生成信号
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Strategies.simple_strategy import SimpleMomentumStrategy
from Portfolio.portfolio import BacktestPortfolio
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from Infrastructure.events import MarketEvent
from config.settings import settings


def debug_strategy_signals():
    """调试策略信号生成"""
    print("=" * 80)
    print("调试策略信号生成")
    print("=" * 80)
    
    # 准备测试环境
    csv_root_path = settings.get_config('data.csv_root_path')
    test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE"]
    
    try:
        loader = LocalCSVLoader(csv_root_path)
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        portfolio = BacktestPortfolio(handler, initial_capital=100000.0)
        strategy = SimpleMomentumStrategy(handler, deque())
        strategy.set_portfolio(portfolio)
        
        print(f"📋 测试股票: {test_symbols}")
        print(f"📅 时间范围: 2025-01-01 到 2025-01-10")
        
        # 处理所有行情事件，检查价格变动
        event_count = 0
        signal_count = 0
        price_changes = []
        
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                bar = event.bar
                
                # 计算价格变动百分比
                price_change_pct = ((bar.close_price - bar.open_price) / bar.open_price) * 100
                price_changes.append(price_change_pct)
                
                print(f"事件{event_count}: {bar.symbol} @ {bar.datetime.strftime('%Y-%m-%d')}")
                print(f"  开盘: {bar.open_price:.2f}, 收盘: {bar.close_price:.2f}")
                print(f"  涨幅: {price_change_pct:.2f}%")
                
                # 检查是否会触发信号
                if price_change_pct > 0.3:
                    print(f"  🚨 应该触发买入信号！涨幅 {price_change_pct:.2f}% > 0.3%")
                    
                    # 手动调用策略逻辑
                    strategy._process_market_data(event)
                    
                    # 检查策略队列
                    while len(strategy.event_queue) > 0:
                        signal = strategy.event_queue.popleft()
                        signal_count += 1
                        print(f"  ✅ 生成信号: {signal.symbol} {signal.direction.value}")
                
                elif price_change_pct < -0.3:
                    print(f"  🚨 应该触发卖出信号！跌幅 {price_change_pct:.2f}% < -0.3%")
                    
                    # 手动调用策略逻辑
                    strategy._process_market_data(event)
                    
                    # 检查策略队列
                    while len(strategy.event_queue) > 0:
                        signal = strategy.event_queue.popleft()
                        signal_count += 1
                        print(f"  ✅ 生成信号: {signal.symbol} {signal.direction.value}")
                
                print()
                
                # 限制处理事件数量
                if event_count >= 15:
                    break
        
        print(f"📊 统计结果:")
        print(f"  总事件数: {event_count}")
        print(f"  价格变动范围: {min(price_changes):.2f}% 到 {max(price_changes):.2f}%")
        print(f"  平均变动: {sum(price_changes)/len(price_changes):.2f}%")
        print(f"  生成信号数: {signal_count}")
        
        # 检查策略状态
        strategy_info = strategy.get_strategy_info()
        print(f"  策略统计: {strategy_info}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_strategy_signals()