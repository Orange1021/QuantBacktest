"""
调试策略数据访问
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from config.settings import settings


def debug_data_handler():
    """调试数据处理器"""
    print("=" * 80)
    print("调试数据处理器")
    print("=" * 80)
    
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
        
        print("✅ 数据处理器创建成功")
        
        # 测试数据访问
        test_symbol = test_symbols[0]
        print(f"\n📋 测试股票: {test_symbol}")
        
        # 尝试获取最新K线（先处理一些数据）
        event_count = 0
        for event in handler.update_bars():
            event_count += 1
            print(f"处理事件{event_count}: {event.bar.symbol} @ {event.bar.datetime}")
            
            # 处理3个事件后测试数据访问
            if event_count >= 3:
                break
        
        # 现在测试数据访问
        latest_bar = handler.get_latest_bar(test_symbol)
        if latest_bar:
            print(f"✅ 获取最新K线成功: {latest_bar.symbol} @ {latest_bar.datetime}, 价格: {latest_bar.close_price:.2f}")
        else:
            print(f"❌ 获取最新K线失败: {test_symbol}")
        
        latest_bars = handler.get_latest_bars(test_symbol, 3)
        if latest_bars:
            print(f"✅ 获取最近3根K线成功: 数量={len(latest_bars)}")
        else:
            print(f"❌ 获取最近3根K线失败: {test_symbol}")
        
        current_time = handler.get_current_time()
        print(f"✅ 当前时间: {current_time}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_data_handler()