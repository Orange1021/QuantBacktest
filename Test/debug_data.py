"""
调试数据内容
检查为什么策略没有生成信号
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Infrastructure.events import MarketEvent
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from config.settings import settings


def extract_symbol_from_vt_symbol(vt_symbol: str) -> str:
    """从vt_symbol中提取股票代码"""
    if '.' in vt_symbol:
        return vt_symbol.split('.')[0]
    return vt_symbol


def get_exchange_from_vt_symbol(vt_symbol: str) -> str:
    """从vt_symbol中提取交易所代码"""
    if '.' in vt_symbol:
        suffix = vt_symbol.split('.')[1]
        if suffix in ['SH', 'SSE']:
            return 'SSE'
        elif suffix in ['SZ', 'SZSE']:
            return 'SZSE'
        elif suffix in ['BJ', 'BSE']:
            return 'BSE'
    return 'SZSE'  # 默认


def debug_data_content():
    """调试数据内容"""
    print("=" * 80)
    print("调试数据内容")
    print("=" * 80)
    
    # 准备测试数据
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
        
        print(f"📋 调试股票: {test_symbols}")
        print(f"📅 时间范围: 2025-01-01 到 2025-01-10")
        
        # 检查每根K线数据
        event_count = 0
        price_change_count = 0
        
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                bar = event.bar
                
                # 计算价格变动
                price_change_pct = ((bar.close_price - bar.open_price) / bar.open_price) * 100
                
                print(f"事件{event_count}: {bar.symbol} @ {bar.datetime.strftime('%Y-%m-%d')}")
                print(f"  开盘: {bar.open_price:.2f}, 收盘: {bar.close_price:.2f}")
                print(f"  涨幅: {price_change_pct:.2f}%")
                
                if price_change_pct > 2.0:
                    price_change_count += 1
                    print(f"  🚨 检测到涨幅超过2%！")
                
                print()
                
                # 限制显示数量
                if event_count >= 15:
                    break
        
        print(f"📊 统计结果:")
        print(f"  总事件数: {event_count}")
        print(f"  涨幅超过2%的事件数: {price_change_count}")
        print(f"  信号触发率: {(price_change_count / event_count * 100) if event_count > 0 else 0:.2f}%")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")


if __name__ == "__main__":
    debug_data_content()