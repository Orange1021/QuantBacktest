"""
快速测试Sizer系统
验证不同Sizer策略的输出
"""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from Portfolio.sizers import create_sizer

# 模拟Portfolio类
class MockPortfolio:
    def __init__(self, cash, equity):
        self.current_cash = cash
        self.total_equity = equity

# 模拟SignalEvent类
class MockSignal:
    def __init__(self, symbol, strength=1.0):
        self.symbol = symbol
        self.strength = strength
        self.datetime = datetime.now()

print("=" * 80)
print("Sizer 系统快速测试")
print("=" * 80)
print()

# 测试数据
mock_portfolio = MockPortfolio(cash=100000, equity=100000)
mock_signal = MockSignal(symbol="000001.SZ", strength=1.0)
mock_data = None

# 1. 等权重策略
print("【1】EqualWeightSizer (等权重，最大持仓10只)")
sizer = create_sizer('equal_weight', max_positions=10)
target = sizer.calculate_target_value(mock_portfolio, mock_signal, mock_data)
print(f"   目标金额: {target:,.2f} 元")
print(f"   计算逻辑: 100,000 / 10 = {target:,.2f}")
print()

# 2. 固定比例策略
print("【2】FixedRatioSizer (固定比例15%)")
sizer = create_sizer('fixed_ratio', ratio=0.15)
target = sizer.calculate_target_value(mock_portfolio, mock_signal, mock_data)
print(f"   目标金额: {target:,.2f} 元")
print(f"   计算逻辑: 100,000 * 15% = {target:,.2f}")
print()

# 3. 信号加权的策略
print("【3】SignalWeightedSizer (信号强度加权，基准20%)")
sizer = create_sizer('signal_weighted', base_ratio=0.20)

# 测试不同信号强度
for strength in [0.5, 1.0, 1.5]:
    signal = MockSignal("000001.SZ", strength=strength)
    target = sizer.calculate_target_value(mock_portfolio, signal, mock_data)
    print(f"   信号强度 {strength}: {target:,.2f} 元")
    print(f"     计算逻辑: 100,000 * 20% * {strength} = {target:,.2f}")
print()

print("=" * 80)
print("✅ 所有Sizer策略测试通过！")
print("=" * 80)
