"""
测试新的事件系统与DataHandler的集成
验证重构后的事件系统是否正常工作
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Infrastructure.events import MarketEvent, EventType, Direction, OrderType
from Infrastructure.enums import EventType as EnumEventType, Direction as EnumDirection, OrderType as EnumOrderType
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from config.settings import settings


def test_new_event_system():
    """测试新的事件系统"""
    print("=" * 60)
    print("新事件系统测试")
    print("=" * 60)
    
    # 1. 测试枚举导入
    print("1. 测试枚举导入")
    try:
        print(f"   EventType: {list(EnumEventType)}")
        print(f"   Direction: {list(EnumDirection)}")
        print(f"   OrderType: {list(EnumOrderType)}")
        print("   ✅ 枚举导入成功")
    except Exception as e:
        print(f"   ❌ 枚举导入失败: {e}")
        return False
    
    # 2. 测试事件类创建
    print("\n2. 测试事件类创建")
    try:
        from DataManager.schema.bar import BarData
        from DataManager.schema.constant import Exchange, Interval
        
        # 创建一个测试BarData
        test_bar = BarData(
            symbol="000001",
            exchange=Exchange.SZSE,
            datetime=datetime(2025, 1, 1),
            interval=Interval.DAILY,
            open_price=10.0,
            high_price=11.0,
            low_price=9.5,
            close_price=10.5,
            volume=1000000,
            turnover=10500000
        )
        
        # 创建MarketEvent
        market_event = MarketEvent(bar=test_bar)
        print(f"   MarketEvent类型: {market_event.type}")
        print(f"   MarketEvent股票: {market_event.bar.symbol}")
        print("   ✅ MarketEvent创建成功")
        
    except Exception as e:
        print(f"   ❌ 事件类创建失败: {e}")
        return False
    
    # 3. 测试DataHandler集成
    print("\n3. 测试DataHandler集成")
    try:
        # 获取配置
        csv_root_path = settings.get_config('data.csv_root_path')
        if not csv_root_path:
            print("   ❌ 未配置CSV数据路径")
            return False
        
        # 创建数据加载器
        loader = LocalCSVLoader(csv_root_path)
        
        # 创建数据处理器
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=["000001.SZSE", "000002.SZSE"],
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        print("   ✅ BacktestDataHandler创建成功")
        
        # 测试事件生成
        event_count = 0
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                # 只显示前3个事件
                if event_count <= 3:
                    print(f"   事件{event_count}: {event.bar.symbol} @ {event.bar.datetime}, 价格: {event.bar.close_price}")
            
            # 限制测试事件数量
            if event_count >= 10:
                break
        
        print(f"   ✅ 成功生成 {event_count} 个MarketEvent")
        
        # 测试数据查询接口
        latest_bar = handler.get_latest_bar("000001.SZSE")
        if latest_bar:
            print(f"   ✅ 获取最新K线成功: {latest_bar.symbol} @ {latest_bar.datetime}")
        
        latest_bars = handler.get_latest_bars("000001.SZSE", 3)
        if latest_bars:
            print(f"   ✅ 获取最近3根K线成功: 数量={len(latest_bars)}")
        
    except Exception as e:
        print(f"   ❌ DataHandler集成失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("新事件系统测试全部通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_new_event_system()
    
    if success:
        print("\n🎉 新事件系统与DataHandler集成成功！")
    else:
        print("\n💥 集成测试失败，请检查代码")