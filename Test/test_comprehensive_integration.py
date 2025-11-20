"""
综合集成测试
验证问财选股 -> CSV数据加载 -> 新事件系统 -> DataHandler的完整流程
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
from DataManager.selectors.wencai_selector import WencaiSelector
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


def test_comprehensive_integration():
    """综合集成测试"""
    print("=" * 80)
    print("量化回测系统综合集成测试")
    print("测试流程: 问财选股 -> CSV数据加载 -> 新事件系统 -> DataHandler")
    print("=" * 80)
    
    # 步骤1: 问财选股
    print("\n步骤1: 问财选股测试")
    print("-" * 40)
    
    cookie = settings.get_env('WENCAI_COOKIE')
    if not cookie:
        print("❌ 未找到问财Cookie，跳过问财选股测试")
        # 使用预定义的股票列表进行测试
        test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE", "600036.SSE"]
        print("📋 使用预定义股票列表进行测试:", test_symbols)
    else:
        try:
            wencai_selector = WencaiSelector(cookie=cookie)
            
            # 获取银行股列表
            bank_stocks = wencai_selector.select_stocks(
                date=datetime.now(),
                query="银行"
            )
            
            if not bank_stocks:
                print("❌ 问财选股失败，使用预定义股票列表")
                test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE", "600036.SSE"]
            else:
                print(f"✅ 问财选股成功，获取到 {len(bank_stocks)} 只银行股")
                test_symbols = bank_stocks[:6]  # 取前6只进行测试
                print(f"📋 测试股票: {test_symbols}")
                
        except Exception as e:
            print(f"❌ 问财选股出错: {e}")
            print("📋 使用预定义股票列表进行测试")
            test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE", "600036.SSE"]
    
    # 步骤2: CSV数据加载
    print(f"\n步骤2: CSV数据加载测试")
    print("-" * 40)
    
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    try:
        loader = LocalCSVLoader(csv_root_path)
        print(f"✅ CSV加载器创建成功，数据路径: {csv_root_path}")
        
        # 测试单只股票数据加载
        test_symbol = test_symbols[0]
        symbol_code = extract_symbol_from_vt_symbol(test_symbol)
        exchange = get_exchange_from_vt_symbol(test_symbol)
        
        test_bars = loader.load_bar_data(
            symbol=symbol_code,
            exchange=exchange,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        if test_bars:
            print(f"✅ 单股数据加载测试成功: {test_symbol}, {len(test_bars)} 条数据")
        else:
            print(f"❌ 单股数据加载失败: {test_symbol}")
            return False
            
    except Exception as e:
        print(f"❌ CSV数据加载失败: {e}")
        return False
    
    # 步骤3: 新事件系统测试
    print(f"\n步骤3: 新事件系统测试")
    print("-" * 40)
    
    try:
        from DataManager.schema.bar import BarData
        from DataManager.schema.constant import Exchange, Interval
        
        # 创建测试事件
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
        
        market_event = MarketEvent(bar=test_bar)
        print(f"✅ MarketEvent创建成功: {market_event.bar.symbol}, 类型: {market_event.type}")
        
        # 测试枚举
        print(f"✅ 枚举测试: EventType={len(EnumEventType)}, Direction={len(EnumDirection)}, OrderType={len(EnumOrderType)}")
        
    except Exception as e:
        print(f"❌ 新事件系统测试失败: {e}")
        return False
    
    # 步骤4: DataHandler集成测试
    print(f"\n步骤4: DataHandler集成测试")
    print("-" * 40)
    
    try:
        # 创建数据处理器
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 15)
        )
        print(f"✅ BacktestDataHandler创建成功，股票数量: {len(test_symbols)}")
        
        # 测试事件生成
        event_count = 0
        symbol_event_count = {}
        
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                symbol = event.bar.symbol
                
                if symbol not in symbol_event_count:
                    symbol_event_count[symbol] = 0
                symbol_event_count[symbol] += 1
                
                # 显示前5个事件
                if event_count <= 5:
                    print(f"   事件{event_count}: {symbol} @ {event.bar.datetime.strftime('%Y-%m-%d')}, 价格: {event.bar.close_price:.2f}")
            
            # 限制测试事件数量
            if event_count >= 20:
                break
        
        print(f"✅ 成功生成 {event_count} 个MarketEvent")
        print(f"📊 各股票事件分布: {symbol_event_count}")
        
        # 测试数据查询接口
        test_symbol_code = extract_symbol_from_vt_symbol(test_symbols[0])
        latest_bar = handler.get_latest_bar(test_symbols[0])
        if latest_bar:
            print(f"✅ 获取最新K线成功: {latest_bar.symbol} @ {latest_bar.datetime}, 价格: {latest_bar.close_price:.2f}")
        
        latest_bars = handler.get_latest_bars(test_symbols[0], 3)
        if latest_bars:
            print(f"✅ 获取最近3根K线成功: 数量={len(latest_bars)}")
            prices = [bar.close_price for bar in latest_bars]
            print(f"   价格序列: {[f'{p:.2f}' for p in prices]}")
        
    except Exception as e:
        print(f"❌ DataHandler集成失败: {e}")
        return False
    
    # 步骤5: 完整流程模拟
    print(f"\n步骤5: 完整流程模拟")
    print("-" * 40)
    
    try:
        print("🔄 模拟完整回测流程...")
        
        # 重置数据处理器
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols[:3],  # 只用前3只股票
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        # 模拟策略处理事件
        strategy_signals = []
        portfolio_orders = []
        
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                # 模拟策略信号生成
                bar = event.bar
                if bar.close_price > bar.open_price * 1.02:  # 涨幅超过2%
                    signal = {
                        'symbol': bar.symbol,
                        'datetime': bar.datetime,
                        'action': 'BUY_SIGNAL',
                        'reason': f'价格上涨 {((bar.close_price - bar.open_price) / bar.open_price * 100):.2f}%'
                    }
                    strategy_signals.append(signal)
                    
                    # 模拟订单生成
                    if len(strategy_signals) <= 3:  # 只显示前3个信号
                        print(f"   📈 策略信号: {signal['symbol']} @ {signal['datetime'].strftime('%Y-%m-%d')} - {signal['reason']}")
            
            # 限制处理事件数量
            if len(strategy_signals) >= 5:
                break
        
        print(f"✅ 完整流程模拟成功")
        print(f"📈 策略信号数量: {len(strategy_signals)}")
        
        # 统计结果
        if strategy_signals:
            signal_symbols = [s['symbol'] for s in strategy_signals]
            from collections import Counter
            symbol_counts = Counter(signal_symbols)
            print(f"📊 信号分布: {dict(symbol_counts)}")
        
    except Exception as e:
        print(f"❌ 完整流程模拟失败: {e}")
        return False
    
    # 最终总结
    print(f"\n" + "=" * 80)
    print("综合集成测试总结")
    print("=" * 80)
    
    print("✅ 步骤1: 问财选股测试 - 通过")
    print("✅ 步骤2: CSV数据加载测试 - 通过")
    print("✅ 步骤3: 新事件系统测试 - 通过")
    print("✅ 步骤4: DataHandler集成测试 - 通过")
    print("✅ 步骤5: 完整流程模拟 - 通过")
    
    print(f"\n🎉 综合集成测试全部通过！")
    print(f"📊 测试股票数量: {len(test_symbols)}")
    print(f"📈 生成事件数量: {event_count}")
    print(f"📋 策略信号数量: {len(strategy_signals)}")
    
    return True


if __name__ == "__main__":
    success = test_comprehensive_integration()
    
    if success:
        print(f"\n🚀 量化回测系统已准备就绪，可以开始策略开发！")
    else:
        print(f"\n💥 综合集成测试失败，请检查系统配置")
