#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试策略信号生成
"""

import sys
from pathlib import Path
from datetime import datetime

# 将src目录添加到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.strategy.continuous_decline import ContinuousDeclineStrategy
from src.data.provider_factory import DataProviderFactory
from src.utils.config import ConfigManager

def test_strategy_signals():
    """测试策略信号生成"""
    print("开始测试策略信号生成...")
    
    # 加载配置
    config = ConfigManager.load_config('configs/data/source.yaml')
    strategy_config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')
    
    # 合并配置
    import copy
    full_config = copy.deepcopy(config)
    def merge_config(base, override):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                merge_config(base[key], value)
            else:
                base[key] = value
    merge_config(full_config, strategy_config)
    
    print("✓ 配置加载成功")
    
    # 创建数据提供器工厂
    factory = DataProviderFactory(full_config)
    print("✓ 数据提供器工厂创建成功")
    
    # 创建策略实例
    strategy = ContinuousDeclineStrategy(full_config['strategy'])
    print("✓ 策略实例创建成功")
    
    # 初始化策略
    context = {
        'current_date': datetime(2023, 1, 4),
        'data_provider': factory.create_proxy(),
        'data_provider_factory': factory
    }
    
    strategy.initialize(context)
    print("✓ 策略初始化成功")
    
    # 测试选股
    test_date = datetime(2023, 1, 4)
    strategy.before_trading(test_date, context)
    print(f"✓ 选股完成，候选股票数量: {len(strategy.candidate_stocks)}")
    if strategy.candidate_stocks:
        print(f"  前5只候选股票: {strategy.candidate_stocks[:5]}")
    
    # 测试K线处理（模拟一个候选股票的K线数据）
    if strategy.candidate_stocks:
        # 创建一个模拟的bar对象
        from types import SimpleNamespace
        test_symbol = strategy.candidate_stocks[0]  # 使用第一只候选股票
        bar = SimpleNamespace(
            symbol=test_symbol,
            timestamp=test_date,
            open=10.0,
            high=10.5,
            low=9.8,
            close=10.2,  # 价格较低，可能触发买入
            volume=1000000
        )
        
        print(f"\n测试K线处理: {test_symbol} (价格: {bar.close})")
        signal_result = strategy.on_bar(bar, context)
        if signal_result and 'signals' in signal_result:
            for signal in signal_result['signals']:
                print(f"✓ 生成信号: {signal['type']} {signal['symbol']} 价格={signal['price']} 数量={signal.get('quantity', 'N/A')} 类型={signal.get('reason', 'N/A')}")
        else:
            print("未生成信号")
    else:
        print("没有候选股票，无法测试信号生成")
    
    print("\n策略信号生成测试完成！")
    return True

if __name__ == '__main__':
    test_strategy_signals()