"""
策略基类测试
验证 BaseStrategy 的功能和接口规范
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Strategies.base import BaseStrategy
from Infrastructure.events import MarketEvent, SignalEvent
from Infrastructure.enums import Direction
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from DataManager.schema.bar import BarData
from DataManager.schema.constant import Exchange, Interval
from config.settings import settings


class TestStrategy(BaseStrategy):
    """测试策略类，继承自BaseStrategy"""
    
    def __init__(self, data_handler, event_queue):
        super().__init__(data_handler, event_queue)
        self.buy_signals = 0
        self.sell_signals = 0
    
    def on_market_data(self, event: MarketEvent) -> None:
        """
        简单的测试策略逻辑：
        - 涨幅超过1%时买入
        - 跌幅超过1%时卖出
        """
        bar = event.bar
        price_change_pct = self.get_price_change_pct(bar.symbol)
        
        if price_change_pct is None:
            return
        
        if price_change_pct > 1.0:  # 涨幅超过1%
            self.send_signal(bar.symbol, Direction.LONG, strength=0.8)
            self.buy_signals += 1
        
        elif price_change_pct < -1.0:  # 跌幅超过1%
            self.send_signal(bar.symbol, Direction.SHORT, strength=0.8)
            self.sell_signals += 1


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


def test_strategy_base_functionality():
    """测试策略基类功能"""
    print("=" * 80)
    print("策略基类功能测试")
    print("=" * 80)
    
    # 1. 准备测试环境
    print("\n步骤1: 准备测试环境")
    print("-" * 40)
    
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE"]
    
    try:
        loader = LocalCSVLoader(csv_root_path)
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        event_queue = deque()
        strategy = TestStrategy(handler, event_queue)
        
        print("✅ 测试环境准备完成")
        print(f"📋 测试股票: {test_symbols}")
        
    except Exception as e:
        print(f"❌ 测试环境准备失败: {e}")
        return False
    
    # 2. 测试策略初始化
    print(f"\n步骤2: 测试策略初始化")
    print("-" * 40)
    
    try:
        info = strategy.get_strategy_info()
        print(f"✅ 策略名称: {info['strategy_name']}")
        print(f"✅ 初始化状态: {info['is_initialized']}")
        print(f"✅ 生成信号数: {info['signals_generated']}")
        print(f"✅ 处理行情数: {info['market_data_processed']}")
        
    except Exception as e:
        print(f"❌ 策略初始化测试失败: {e}")
        return False
    
    # 3. 预处理数据（为策略提供数据基础）
    print(f"\n步骤3: 预处理数据")
    print("-" * 40)
    
    try:
        event_count = 0
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                # 只处理前5个事件，为策略提供数据基础
                if event_count >= 5:
                    break
        
        print(f"✅ 预处理了 {event_count} 个行情事件")
        
    except Exception as e:
        print(f"❌ 数据预处理失败: {e}")
        return False
    
    # 4. 测试数据访问方法
    print(f"\n步骤4: 测试数据访问方法")
    print("-" * 40)
    
    try:
        test_symbol = test_symbols[0]
        
        # 测试获取最新K线
        latest_bar = strategy.get_latest_bar(test_symbol)
        if latest_bar:
            print(f"✅ 获取最新K线: {latest_bar.symbol} @ {latest_bar.datetime}, 价格: {latest_bar.close_price:.2f}")
        else:
            print("❌ 获取最新K线失败")
            return False
        
        # 测试获取历史K线
        latest_bars = strategy.get_latest_bars(test_symbol, 3)
        if latest_bars:
            print(f"✅ 获取最近3根K线: 数量={len(latest_bars)}")
            prices = [bar.close_price for bar in latest_bars]
            print(f"   价格序列: {[f'{p:.2f}' for p in prices]}")
        else:
            print("❌ 获取历史K线失败")
            return False
        
        # 测试获取当前价格
        current_price = strategy.get_current_price(test_symbol)
        if current_price:
            print(f"✅ 获取当前价格: {current_price:.2f}")
        else:
            print("❌ 获取当前价格失败")
            return False
        
        # 测试计算SMA
        sma5 = strategy.calculate_sma(test_symbol, 5)
        if sma5:
            print(f"✅ 计算SMA5: {sma5:.2f}")
        else:
            print("⚠️ SMA5计算失败（数据不足）")
        
        # 测试价格变动百分比
        price_change = strategy.get_price_change_pct(test_symbol)
        if price_change is not None:
            print(f"✅ 价格变动: {price_change:.2f}%")
        else:
            print("❌ 价格变动计算失败")
            return False
        
    except Exception as e:
        print(f"❌ 数据访问方法测试失败: {e}")
        return False
    
    # 5. 测试信号生成
    print(f"\n步骤5: 测试信号生成")
    print("-" * 40)
    
    try:
        event_count = 0
        
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                
                # 使用策略处理行情数据
                strategy._process_market_data(event)
                
                # 显示前5个事件的详细信息
                if event_count <= 5:
                    bar = event.bar
                    price_change = strategy.get_price_change_pct(bar.symbol)
                    price_change_str = f"{price_change:.2f}%" if price_change is not None else "N/A"
                    print(f"   事件{event_count}: {bar.symbol} @ {bar.datetime.strftime('%Y-%m-%d')}, "
                          f"价格: {bar.close_price:.2f}, 变动: {price_change_str}")
                
                # 限制处理事件数量
                if event_count >= 15:
                    break
        
        print(f"✅ 处理了 {event_count} 个行情事件")
        
    except Exception as e:
        print(f"❌ 信号生成测试失败: {e}")
        return False
    
    # 6. 验证信号队列
    print(f"\n步骤6: 验证信号队列")
    print("-" * 40)
    
    try:
        print(f"📊 策略统计:")
        print(f"  买入信号数: {strategy.buy_signals}")
        print(f"  卖出信号数: {strategy.sell_signals}")
        print(f"  总信号数: {strategy.signals_generated}")
        print(f"  队列中信号数: {len(event_queue)}")
        
        # 显示队列中的信号
        signal_count = 0
        while event_queue and signal_count < 5:
            signal = event_queue.popleft()
            signal_count += 1
            print(f"  信号{signal_count}: {signal.symbol} {signal.direction.value} @ {signal.datetime.strftime('%Y-%m-%d')}, 强度: {signal.strength:.2f}")
        
        if signal_count == 0:
            print("  ⚠️ 没有生成信号（可能没有触发策略条件）")
        
    except Exception as e:
        print(f"❌ 信号队列验证失败: {e}")
        return False
    
    # 7. 测试策略状态
    print(f"\n步骤7: 测试策略状态")
    print("-" * 40)
    
    try:
        final_info = strategy.get_strategy_info()
        print(f"✅ 最终策略状态:")
        print(f"  初始化状态: {final_info['is_initialized']}")
        print(f"  当前时间: {final_info['current_time']}")
        print(f"  生成信号数: {final_info['signals_generated']}")
        print(f"  处理行情数: {final_info['market_data_processed']}")
        
        # 验证策略已正确初始化
        if not final_info['is_initialized']:
            print("❌ 策略未正确初始化")
            return False
        
        if final_info['market_data_processed'] == 0:
            print("❌ 策略未处理任何行情数据")
            return False
        
    except Exception as e:
        print(f"❌ 策略状态测试失败: {e}")
        return False
    
    # 最终总结
    print(f"\n" + "=" * 80)
    print("策略基类测试总结")
    print("=" * 80)
    
    print("✅ 步骤1: 准备测试环境 - 通过")
    print("✅ 步骤2: 测试策略初始化 - 通过")
    print("✅ 步骤3: 预处理数据 - 通过")
    print("✅ 步骤4: 测试数据访问方法 - 通过")
    print("✅ 步骤5: 测试信号生成 - 通过")
    print("✅ 步骤6: 验证信号队列 - 通过")
    print("✅ 步骤7: 测试策略状态 - 通过")
    
    print(f"\n🎉 策略基类测试全部通过！")
    print(f"📊 处理行情事件: {final_info['market_data_processed']}")
    print(f"📈 生成交易信号: {final_info['signals_generated']}")
    print(f"🔧 策略基类功能完备，可以开始实现具体策略！")
    
    return True


if __name__ == "__main__":
    success = test_strategy_base_functionality()
    
    if success:
        print(f"\n🚀 策略抽象层已准备就绪，可以开始实现具体策略！")
    else:
        print(f"\n💥 策略基类测试失败，请检查实现")