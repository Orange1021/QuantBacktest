"""
测试事件系统与数据驱动层
验证事件创建、数据处理器功能是否正常
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent, EventType
from DataManager.handlers import BacktestDataHandler
from DataManager.sources import LocalCSVLoader
from DataManager.schema.constant import Exchange


def test_events():
    """测试事件类创建和属性"""
    print("=" * 60)
    print("测试事件系统")
    print("=" * 60)
    
    # 创建模拟BarData
    from DataManager.schema.bar import BarData, Interval
    mock_bar = BarData(
        gateway_name="Test",
        symbol="000001",
        exchange=Exchange.SZSE,
        datetime=datetime.now(),
        interval=Interval.DAILY,
        open_price=10.0,
        high_price=11.0,
        low_price=9.5,
        close_price=10.5,
        volume=1000000,
        turnover=10500000
    )
    
    # 测试MarketEvent
    market_event = MarketEvent(bar=mock_bar)
    print(f"✅ MarketEvent创建成功: {market_event}")
    print(f"   事件类型: {market_event.type}")
    print(f"   股票代码: {market_event.bar.symbol}")
    print(f"   收盘价: {market_event.bar.close_price}")
    
    # 测试SignalEvent
    signal_event = SignalEvent(
        symbol="000001",
        direction="LONG",
        strength=0.8,
        datetime=datetime.now()
    )
    print(f"\n✅ SignalEvent创建成功: {signal_event}")
    print(f"   事件类型: {signal_event.type}")
    print(f"   信号强度: {signal_event.strength}")
    
    # 测试OrderEvent
    order_event = OrderEvent(
        symbol="000001",
        order_type="MARKET",
        direction="BUY",
        volume=1000,
        price=0.0  # 市价单
    )
    print(f"\n✅ OrderEvent创建成功: {order_event}")
    print(f"   事件类型: {order_event.type}")
    print(f"   下单数量: {order_event.volume}")
    
    # 测试FillEvent
    fill_event = FillEvent(
        symbol="000001",
        datetime=datetime.now(),
        direction="BUY",
        volume=1000,
        price=10.52,
        commission=5.26
    )
    print(f"\n✅ FillEvent创建成功: {fill_event}")
    print(f"   事件类型: {fill_event.type}")
    print(f"   成交金额: {fill_event.trade_value:,.2f}")
    print(f"   净金额: {fill_event.net_value:,.2f}")
    
    return True


def test_data_handler():
    """测试数据处理器"""
    print("\n" + "=" * 60)
    print("测试数据处理器")
    print("=" * 60)
    
    try:
        # 配置参数
        csv_root_path = r"C:\Users\123\A股数据\个股数据"
        symbol_list = ["000001.SZSE"]  # 使用带交易所的格式
        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now()
        
        print(f"测试股票: {symbol_list}")
        print(f"日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        # 创建数据源
        data_source = LocalCSVLoader(csv_root_path)
        
        # 创建数据处理器
        data_handler = BacktestDataHandler(
            data_source=data_source,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✅ 数据处理器创建成功")
        print(f"   时间轴长度: {len(data_handler.timeline)} 个交易日")
        print(f"   加载股票数: {len(data_handler.symbol_data)}")
        
        # 测试获取最新K线
        latest_bar = data_handler.get_latest_bar("000001.SZSE")
        if latest_bar:
            print(f"✅ 获取最新K线成功: {latest_bar.datetime.strftime('%Y-%m-%d')}, 收盘价: {latest_bar.close_price}")
        
        # 测试获取最近N根K线
        latest_bars = data_handler.get_latest_bars("000001.SZSE", 3)
        if latest_bars:
            print(f"✅ 获取最近3根K线成功:")
            for i, bar in enumerate(latest_bars):
                print(f"   第{i+1}根: {bar.datetime.strftime('%Y-%m-%d')}, 收盘价: {bar.close_price}")
        
        # 测试事件流生成
        print(f"\n开始测试事件流生成（前5个事件）:")
        event_count = 0
        for event in data_handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                print(f"   事件{event_count}: {event.bar.symbol} @ {event.bar.datetime.strftime('%Y-%m-%d')}, "
                      f"收盘价: {event.bar.close_price}")
                
                if event_count >= 5:  # 只显示前5个事件
                    break
        
        print(f"✅ 事件流生成测试完成")
        
        # 重置数据处理器
        data_handler.reset()
        print(f"✅ 数据处理器重置成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """测试事件系统集成"""
    print("\n" + "=" * 60)
    print("测试系统集成")
    print("=" * 60)
    
    try:
        # 配置参数
        csv_root_path = r"C:\Users\123\A股数据\个股数据"
        symbol_list = ["000001.SZSE"]
        start_date = datetime.now() - timedelta(days=15)  # 扩大日期范围
        end_date = datetime.now()
        
        # 创建组件
        data_source = LocalCSVLoader(csv_root_path)
        data_handler = BacktestDataHandler(
            data_source=data_source,
            symbol_list=symbol_list,
            start_date=start_date,
            end_date=end_date
        )
        
        print("模拟事件驱动流程:")
        
        # 模拟事件循环
        event_queue = []
        
        # 1. 数据处理器推送行情事件
        for market_event in data_handler.update_bars():
            event_queue.append(market_event)
            
            # 2. 策略处理行情事件，生成信号事件
            if market_event.bar.close_price > 10.0:  # 简单的策略逻辑
                signal_event = SignalEvent(
                    symbol=market_event.bar.symbol,
                    direction="LONG",
                    strength=0.5,
                    datetime=market_event.bar.datetime
                )
                event_queue.append(signal_event)
                
                # 3. Portfolio处理信号事件，生成订单事件
                order_event = OrderEvent(
                    symbol=signal_event.symbol,
                    order_type="MARKET",
                    direction="BUY",
                    volume=100,
                    datetime=signal_event.datetime
                )
                event_queue.append(order_event)
                
                # 4. Execution处理订单事件，生成成交事件
                fill_event = FillEvent(
                    symbol=order_event.symbol,
                    datetime=order_event.datetime,
                    direction=order_event.direction,
                    volume=order_event.volume,
                    price=market_event.bar.close_price * 1.001,  # 模拟滑点
                    commission=order_event.volume * market_event.bar.close_price * 0.0003  # 模拟手续费
                )
                event_queue.append(fill_event)
                
                print(f"   完整事件链: 行情 -> 信号 -> 订单 -> 成交")
                print(f"   成交价格: {fill_event.price:.2f}, 手续费: {fill_event.commission:.2f}")
                break  # 只演示一个完整流程
        
        print(f"✅ 系统集成测试完成，共处理 {len(event_queue)} 个事件")
        return True
        
    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始测试事件系统与数据驱动层...\n")
    
    # 测试事件系统
    events_ok = test_events()
    
    # 测试数据处理器
    handler_ok = test_data_handler()
    
    # 测试系统集成
    integration_ok = test_integration()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if events_ok and handler_ok and integration_ok:
        print("🎉 所有测试通过！事件系统与数据驱动层工作正常")
    else:
        print("💥 部分测试失败，请检查错误信息")
        print(f"   事件系统: {'✅' if events_ok else '❌'}")
        print(f"   数据处理器: {'✅' if handler_ok else '❌'}")
        print(f"   系统集成: {'✅' if integration_ok else '❌'}")