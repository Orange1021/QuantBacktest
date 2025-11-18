#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试PositionManager模块

验证加仓逻辑是否正确
"""

import sys
from pathlib import Path
from datetime import datetime

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.position.position_manager import PositionManager
from src.utils.config import ConfigManager


def test_position_manager():
    """测试PositionManager"""
    print("=" * 60)
    print("PositionManager 测试")
    print("=" * 60)

    # 加载配置
    print("\n1. 加载配置...")
    config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')
    print("[OK] 配置加载成功")

    # 创建PositionManager
    print("\n2. 创建PositionManager...")
    params = {
        'initial_position_size': 0.20,  # 初始20%
        'position_percent_per_layer': 0.10,  # 每层补仓10% (基于总资金)
        'max_layers': 8
    }
    pm = PositionManager(total_capital=1000000, params=params)  # 100万初始资金
    print("[OK] PositionManager创建成功")
    print(f"   总资金: {pm.total_capital:,.0f}元")
    print(f"   可用资金: {pm.available_capital:,.0f}元")

    # 测试初始建仓
    print("\n3. 测试初始建仓...")
    print("-" * 60)
    symbol = "000001.SZ"
    price = 10.0

    quantity = pm.calculate_initial_position_size(price)
    print(f"股票: {symbol}, 价格: {price:.2f}元")
    print(f"计算初始仓位: {quantity}股")

    success = pm.open_position(symbol, price=price)
    if success:
        print("[OK] 建仓成功")
        position = pm.get_position(symbol)
        print(f"   持仓数量: {position.quantity}股")
        print(f"   持仓成本: {position.cost_value:,.0f}元")
        print(f"   剩余可用资金: {pm.available_capital:,.0f}元")
    else:
        print("[FAIL] 建仓失败")
        return False

    # 测试加仓逻辑
    print("\n4. 测试分层加仓...")
    print("-" * 60)

    # 模拟价格下跌，触发补仓
    test_scenarios = [
        (1, 9.9, "第1层补仓（跌1%）"),
        (2, 9.8, "第2层补仓（跌2%）"),
        (3, 9.7, "第3层补仓（跌3%）"),
        (4, 9.6, "第4层补仓（跌4%）"),
    ]

    for layer, price, desc in test_scenarios:
        quantity = pm.calculate_add_position_size(symbol, price, layer)
        print(f"\n{desc}:")
        print(f"   价格: {price:.2f}元")
        print(f"   计算加仓数量: {quantity}股")

        success = pm.add_position(symbol, price=price, layer=layer)
        if success:
            position = pm.get_position(symbol)
            print(f"   [OK] 加仓成功")
            print(f"   新持仓数量: {position.quantity}股")
            print(f"   新持仓成本: {position.avg_price:.2f}元")
            print(f"   加仓层数: {position.layer_count}")
            print(f"   剩余可用资金: {pm.available_capital:,.0f}元")
        else:
            print(f"   [FAIL] 加仓失败")
            return False

    # 测试持仓统计
    print("\n5. 测试持仓统计...")
    print("-" * 60)
    stats = pm.get_position_stats()
    print(f"持仓数量: {stats['position_count']}")
    print(f"总持仓市值: {stats['total_value']:,.0f}元")
    print(f"总持仓成本: {stats['total_cost']:,.0f}元")
    print(f"总盈亏: {stats['total_pnl']:+.0f}元 ({stats['pnl_percent']:+.2f}%)")
    print(f"资金使用率: {stats['exposure']:.1%}")
    print(f"剩余可用资金: {stats['available_capital']:,.0f}元")

    # 测试价格更新
    print("\n6. 测试价格更新...")
    print("-" * 60)

    # 价格上涨
    new_price = 10.5
    pm.update_position_price(symbol, new_price)
    position = pm.get_position(symbol)
    print(f"价格上涨到 {new_price:.2f}元:")
    print(f"   市值: {position.market_value:,.0f}元")
    print(f"   盈亏: {position.pnl:+.0f}元 ({position.pnl_percent*100:+.2f}%)")
    print(f"   是否上涨过: {position.has_risen}")

    # 价格下跌
    new_price = 9.5
    pm.update_position_price(symbol, new_price)
    position = pm.get_position(symbol)
    print(f"\n价格下跌到 {new_price:.2f}元:")
    print(f"   市值: {position.market_value:,.0f}元")
    print(f"   盈亏: {position.pnl:+.0f}元 ({position.pnl_percent*100:+.2f}%)")
    print(f"   是否上涨过: {position.has_risen} (一旦为True，不会变回False)")

    # 测试平仓
    print("\n7. 测试平仓...")
    print("-" * 60)
    close_price = 10.8
    print(f"平仓价格: {close_price:.2f}元")

    pnl = pm.close_position(symbol, close_price)
    if pnl is not None:
        print(f"[OK] 平仓成功")
        print(f"   平仓盈亏: {pnl:+.0f}元")
        print(f"   剩余持仓数: {stats['position_count']}")
        print(f"   最终可用资金: {pm.available_capital:,.0f}元")
    else:
        print("[FAIL] 平仓失败")
        return False

    # 测试风险控制
    print("\n8. 测试风险控制...")
    print("-" * 60)

    # 重新建仓
    pm.open_position('000002.SZ', price=20.0, percent=0.20)

    # 检查持仓限制（默认30%）
    is_valid = pm.check_position_limit('000002.SZ', max_percent=0.30)
    print(f"单票持仓限制(30%): {is_valid}")

    # 检查总仓位暴露
    is_valid = pm.check_total_exposure(max_exposure=0.80)
    print(f"总仓位暴露限制(80%): {is_valid}")

    # 测试多只股票持仓
    print("\n9. 测试多股票持仓...")
    print("-" * 60)

    pm.open_position('600000.SH', price=15.0, percent=0.15)
    pm.open_position('600519.SH', price=1800.0, percent=0.10)

    stats = pm.get_position_stats()
    print(f"持仓股票数: {stats['position_count']}")
    print(f"总持仓市值: {stats['total_value']:,.0f}元")
    print(f"总仓位暴露: {stats['exposure']:.1%}")

    # 打印所有持仓
    print("\n持仓明细:")
    for pos in pm.get_all_positions():
        print(f"  {pos.symbol}: {pos.quantity}股, 成本{pos.avg_price:.2f}, "
              f"当前{pos.current_price:.2f}, 盈亏{pos.pnl_percent*100:+.2f}%")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = test_position_manager()
    sys.exit(0 if success else 1)
