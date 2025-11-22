#!/usr/bin/env python3
"""
测试底层定义修改
"""

from Infrastructure.enums import Direction, EventType, OrderType
from Infrastructure.events import FillEvent, SignalEvent
from datetime import datetime

def test_direction_enum():
    """测试 Direction 枚举"""
    print('=== Direction 枚举测试 ===')
    print(f'LONG: {Direction.LONG}')
    print(f'SHORT: {Direction.SHORT}')
    
    # 确保没有 BUY 和 SELL
    try:
        _ = Direction.BUY
        print('❌ Direction.BUY 仍然存在')
        return False
    except AttributeError:
        print('✅ Direction.BUY 已正确移除')
    
    try:
        _ = Direction.SELL
        print('❌ Direction.SELL 仍然存在')
        return False
    except AttributeError:
        print('✅ Direction.SELL 已正确移除')
    
    return True

def test_fill_event_net_value():
    """测试 FillEvent.net_value 计算逻辑"""
    print('\n=== FillEvent.net_value 计算测试 ===')
    
    # 测试买入
    buy_fill = FillEvent(
        symbol='000001.SZ',
        datetime=datetime.now(),
        direction=Direction.LONG,
        volume=1000,
        price=10.0,
        commission=3.0
    )
    expected_buy_net = 10000.0 + 3.0  # 成交额 + 手续费
    actual_buy_net = buy_fill.net_value
    
    print(f'买入: 成交额={buy_fill.trade_value}, 手续费={buy_fill.commission}, 净额={actual_buy_net}')
    if actual_buy_net == expected_buy_net:
        print('✅ 买入净额计算正确')
    else:
        print(f'❌ 买入净额计算错误，期望 {expected_buy_net}，实际 {actual_buy_net}')
        return False
    
    # 测试卖出
    sell_fill = FillEvent(
        symbol='000001.SZ', 
        datetime=datetime.now(),
        direction=Direction.SHORT,
        volume=1000,
        price=10.0,
        commission=3.0
    )
    expected_sell_net = 10000.0 - 3.0  # 成交额 - 手续费
    actual_sell_net = sell_fill.net_value
    
    print(f'卖出: 成交额={sell_fill.trade_value}, 手续费={sell_fill.commission}, 净额={actual_sell_net}')
    if actual_sell_net == expected_sell_net:
        print('✅ 卖出净额计算正确')
    else:
        print(f'❌ 卖出净额计算错误，期望 {expected_sell_net}，实际 {actual_sell_net}')
        return False
    
    return True

def main():
    """主测试函数"""
    print('开始验证底层定义修改...\n')
    
    success = True
    success &= test_direction_enum()
    success &= test_fill_event_net_value()
    
    print('\n' + '='*50)
    if success:
        print('🎉 所有测试通过！底层定义修改成功。')
    else:
        print('❌ 测试失败，需要进一步检查。')
    
    return success

if __name__ == '__main__':
    main()