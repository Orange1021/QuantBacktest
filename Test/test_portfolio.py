"""
投资组合测试
验证 Portfolio 的资金管理和风控功能
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Portfolio.portfolio import BacktestPortfolio
from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from Infrastructure.enums import Direction, OrderType
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from DataManager.schema.bar import BarData
from DataManager.schema.constant import Exchange, Interval
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


def test_portfolio_functionality():
    """测试投资组合功能"""
    print("=" * 80)
    print("投资组合功能测试")
    print("=" * 80)
    
    # 1. 准备测试环境
    print("\n步骤1: 准备测试环境")
    print("-" * 40)
    
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    test_symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
    initial_capital = 100000.0
    
    try:
        loader = LocalCSVLoader(csv_root_path)
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        
        portfolio = BacktestPortfolio(handler, initial_capital)
        
        print("✅ 投资组合创建成功")
        print(f"📋 测试股票: {test_symbols}")
        print(f"💰 初始资金: {initial_capital:,.2f}")
        
    except Exception as e:
        print(f"❌ 测试环境准备失败: {e}")
        return False
    
    # 2. 测试投资组合初始化
    print(f"\n步骤2: 测试投资组合初始化")
    print("-" * 40)
    
    try:
        info = portfolio.get_portfolio_info()
        print(f"✅ 投资组合名称: {info['portfolio_name']}")
        print(f"✅ 初始资金: {info['initial_capital']:,.2f}")
        print(f"✅ 当前现金: {portfolio.get_cash():,.2f}")
        print(f"✅ 总资产: {portfolio.get_equity():,.2f}")
        print(f"✅ 持仓数量: {info['positions_count']}")
        
    except Exception as e:
        print(f"❌ 投资组合初始化测试失败: {e}")
        return False
    
    # 3. 预处理数据（为投资组合提供数据基础）
    print(f"\n步骤3: 预处理数据")
    print("-" * 40)
    
    try:
        event_count = 0
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                event_count += 1
                # 只处理前5个事件，为投资组合提供数据基础
                if event_count >= 5:
                    break
        
        print(f"✅ 预处理了 {event_count} 个行情事件")
        
    except Exception as e:
        print(f"❌ 数据预处理失败: {e}")
        return False
    
    # 4. 测试信号处理（买入）
    print(f"\n步骤4: 测试信号处理（买入）")
    print("-" * 40)
    
    try:
        test_symbol = test_symbols[0]
        
        # 创建买入信号
        buy_signal = SignalEvent(
            symbol=test_symbol,
            datetime=datetime.now(),
            direction=Direction.LONG,
            strength=0.8
        )
        
        # 处理买入信号
        buy_order = portfolio.process_signal(buy_signal)
        
        if buy_order:
            print(f"✅ 生成买入订单: {buy_order.symbol} {buy_order.volume}股")
            print(f"   订单类型: {buy_order.order_type}")
            print(f"   交易方向: {buy_order.direction}")
            
            # 模拟成交
            latest_bar = handler.get_latest_bar(test_symbol)
            if latest_bar:
                fill_price = latest_bar.close_price
                commission = fill_price * buy_order.volume * 0.0003  # 0.03%手续费
                
                fill_event = FillEvent(
                    symbol=buy_order.symbol,
                    datetime=buy_order.datetime,
                    direction=buy_order.direction,
                    volume=buy_order.volume,
                    price=fill_price,
                    commission=commission
                )
                
                # 处理成交
                portfolio.update_on_fill(fill_event)
                
                print(f"✅ 模拟成交完成: 价格 {fill_price:.2f}, 手续费 {commission:.2f}")
                print(f"   当前现金: {portfolio.get_cash():,.2f}")
                print(f"   持仓: {portfolio.get_positions()}")
        else:
            print("❌ 未生成买入订单")
            return False
        
    except Exception as e:
        print(f"❌ 买入信号处理测试失败: {e}")
        return False
    
    # 5. 测试信号处理（卖出）
    print(f"\n步骤5: 测试信号处理（卖出）")
    print("-" * 40)
    
    try:
        # 创建卖出信号
        sell_signal = SignalEvent(
            symbol=test_symbol,
            datetime=datetime.now(),
            direction=Direction.SHORT,
            strength=0.8
        )
        
        # 处理卖出信号
        sell_order = portfolio.process_signal(sell_signal)
        
        if sell_order:
            print(f"✅ 生成卖出订单: {sell_order.symbol} {sell_order.volume}股")
            
            # 模拟成交
            latest_bar = handler.get_latest_bar(test_symbol)
            if latest_bar:
                fill_price = latest_bar.close_price
                commission = fill_price * sell_order.volume * 0.0003  # 0.03%手续费
                
                fill_event = FillEvent(
                    symbol=sell_order.symbol,
                    datetime=sell_order.datetime,
                    direction=sell_order.direction,
                    volume=sell_order.volume,
                    price=fill_price,
                    commission=commission
                )
                
                # 处理成交
                portfolio.update_on_fill(fill_event)
                
                print(f"✅ 模拟成交完成: 价格 {fill_price:.2f}, 手续费 {commission:.2f}")
                print(f"   当前现金: {portfolio.get_cash():,.2f}")
                print(f"   持仓: {portfolio.get_positions()}")
        else:
            print("❌ 未生成卖出订单")
            return False
        
    except Exception as e:
        print(f"❌ 卖出信号处理测试失败: {e}")
        return False
    
    # 6. 测试行情更新（盯市）
    print(f"\n步骤6: 测试行情更新（盯市）")
    print("-" * 40)
    
    try:
        # 处理一些行情事件，测试盯市功能
        market_updates = 0
        for event in handler.update_bars():
            if isinstance(event, MarketEvent):
                market_updates += 1
                portfolio.update_on_market(event)
                
                if market_updates >= 5:
                    break
        
        print(f"✅ 处理了 {market_updates} 个行情更新")
        print(f"   当前现金: {portfolio.get_cash():,.2f}")
        print(f"   总资产: {portfolio.get_equity():,.2f}")
        
    except Exception as e:
        print(f"❌ 行情更新测试失败: {e}")
        return False
    
    # 7. 测试风控逻辑
    print(f"\n步骤7: 测试风控逻辑")
    print("-" * 40)
    
    try:
        # 测试资金不足的情况
        current_cash = portfolio.get_cash()
        print(f"当前现金: {current_cash:.2f}")
        
        # 创建一个需要大量资金的买入信号
        expensive_signal = SignalEvent(
            symbol="999999.SZ",  # 不存在的股票
            datetime=datetime.now(),
            direction=Direction.LONG,
            strength=0.8
        )
        
        # 处理信号（应该因为无法获取价格而失败）
        order = portfolio.process_signal(expensive_signal)
        if order is None:
            print("✅ 风控测试通过：无法获取价格的信号被正确忽略")
        
        # 测试无持仓卖出信号
        no_position_signal = SignalEvent(
            symbol="888888.SZ",  # 不存在的股票
            datetime=datetime.now(),
            direction=Direction.SHORT,
            strength=0.8
        )
        
        order = portfolio.process_signal(no_position_signal)
        if order is None:
            print("✅ 风控测试通过：无持仓的卖出信号被正确忽略")
        
    except Exception as e:
        print(f"❌ 风控逻辑测试失败: {e}")
        return False
    
    # 8. 最终统计
    print(f"\n步骤8: 最终统计")
    print("-" * 40)
    
    try:
        final_info = portfolio.get_portfolio_info()
        print(f"✅ 最终投资组合状态:")
        print(f"   初始资金: {final_info['initial_capital']:,.2f}")
        print(f"   当前现金: {final_info['current_cash']:,.2f}")
        print(f"   总资产: {final_info['total_equity']:,.2f}")
        print(f"   持仓数量: {final_info['positions_count']}")
        print(f"   总交易次数: {final_info['total_trades']}")
        print(f"   总手续费: {final_info['total_commission']:,.2f}")
        print(f"   收益率: {final_info['return_rate']:.2f}%")
        
        # 验证资金平衡
        expected_equity = final_info['current_cash'] + final_info['positions_value']
        if abs(final_info['total_equity'] - expected_equity) > 0.01:
            print(f"❌ 资金平衡检查失败: {final_info['total_equity']:.2f} != {expected_equity:.2f}")
            return False
        else:
            print("✅ 资金平衡检查通过")
        
    except Exception as e:
        print(f"❌ 最终统计测试失败: {e}")
        return False
    
    # 最终总结
    print(f"\n" + "=" * 80)
    print("投资组合测试总结")
    print("=" * 80)
    
    print("✅ 步骤1: 准备测试环境 - 通过")
    print("✅ 步骤2: 测试投资组合初始化 - 通过")
    print("✅ 步骤3: 预处理数据 - 通过")
    print("✅ 步骤4: 测试信号处理（买入） - 通过")
    print("✅ 步骤5: 测试信号处理（卖出） - 通过")
    print("✅ 步骤6: 测试行情更新（盯市） - 通过")
    print("✅ 步骤7: 测试风控逻辑 - 通过")
    print("✅ 步骤8: 最终统计 - 通过")
    
    print(f"\n🎉 投资组合测试全部通过！")
    print(f"💰 当前资金: {final_info['current_cash']:,.2f}")
    print(f"📊 总资产: {final_info['total_equity']:,.2f}")
    print(f"📈 收益率: {final_info['return_rate']:.2f}%")
    print(f"🔧 投资组合模块功能完备，可以与引擎集成！")
    
    return True


if __name__ == "__main__":
    success = test_portfolio_functionality()
    
    if success:
        print(f"\n🚀 投资组合模块已准备就绪，可以与引擎集成！")
    else:
        print(f"\n💥 投资组合测试失败，请检查实现")
