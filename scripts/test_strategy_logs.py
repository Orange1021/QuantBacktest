#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试策略日志是否正常工作
"""

import sys
from pathlib import Path
import yaml

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from src.strategy.continuous_decline import ContinuousDeclineStrategy
from src.utils.logger import setup_logger
from src.data.provider_factory import DataProviderFactory

# 加载配置
config_file = Path(project_root) / 'configs' / 'strategy' / 'continuous_decline.yaml'
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=" * 70)
print("测试策略日志")
print("=" * 70)

# 设置日志
logger = setup_logger('test_strategy')
logger.setLevel('INFO')

# 创建数据提供器工厂
data_provider_factory = DataProviderFactory(config)

# 创建策略
print("\n[1/3] 创建策略...")
strategy = ContinuousDeclineStrategy(config['strategy'])
print("[OK] 策略创建成功")

# 初始化策略
print("\n[2/3] 初始化策略...")
context = {
    'logger': logger,
    'data_provider': data_provider_factory.create_proxy(),
    'data_provider_factory': data_provider_factory,
    'current_date': datetime(2023, 1, 3)
}
strategy.initialize(context)
print("[OK] 策略初始化完成")

# 调用before_trading
print("\n[3/3] 调用before_trading...")
test_date = datetime(2023, 1, 3)
strategy.before_trading(test_date, context)
print(f"[OK] before_trading完成")
print(f"候选股票数: {len(strategy.candidate_stocks)}")
if strategy.candidate_stocks:
    print(f"股票列表: {strategy.candidate_stocks}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
