"""
验证资金分配逻辑修改
测试单票配额计算是否正确
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.position.position_manager import PositionManager
from src.utils.config import ConfigManager


def test_per_stock_allocation():
    """测试单票配额计算"""
    print("\n" + "=" * 70)
    print("测试单票配额计算")
    print("=" * 70)

    # 测试1: 100万资金，10只持仓
    print("\n[测试1] 100万资金，10只持仓")
    pm1 = PositionManager(
        total_capital=1_000_000,
        params={
            'initial_position_size': 0.20,
            'position_percent_per_layer': 0.10,
            'max_layers': 8,
            'max_position_count': 10
        }
    )

    print(f"  总资金: {pm1.total_capital:,.0f}")
    print(f"  最大持仓数: {pm1.max_position_count}")
    print(f"  单票配额: {pm1.per_stock_allocation:,.0f}")

    assert pm1.per_stock_allocation == 100_000, f"期望10万, 实际{pm1.per_stock_allocation}"
    print("  ✓ 单票配额计算正确 (10万)")

    # 测试初始建仓计算
    quantity = pm1.calculate_initial_position_size(price=10.0)
    expected = 2_000  # 10万 * 20% / 10 = 2万 / 10 = 2000股
    print(f"  初始建仓（价格10元）: {quantity}股")
    assert quantity == expected, f"期望{expected}股, 实际{quantity}股"
    print(f"  ✓ 初始建仓计算正确 ({expected}股)")

    # 测试加仓计算
    add_quantity = pm1.calculate_add_position_size('000001.SZ', price=10.0, layer=1)
    expected_add = 1_000  # 10万 * 10% / 10 = 1万股
    print(f"  加仓（价格10元）: {add_quantity}股")
    assert add_quantity == expected_add, f"期望{expected_add}股, 实际{add_quantity}股"
    print(f"  ✓ 加仓计算正确 ({expected_add}股)")

    # 测试2: 100万资金，5只持仓
    print("\n[测试2] 100万资金，5只持仓")
    pm2 = PositionManager(
        total_capital=1_000_000,
        params={
            'initial_position_size': 0.20,
            'position_percent_per_layer': 0.10,
            'max_layers': 8,
            'max_position_count': 5
        }
    )

    print(f"  总资金: {pm2.total_capital:,.0f}")
    print(f"  最大持仓数: {pm2.max_position_count}")
    print(f"  单票配额: {pm2.per_stock_allocation:,.0f}")

    assert pm2.per_stock_allocation == 200_000, f"期望20万, 实际{pm2.per_stock_allocation}"
    print("  ✓ 单票配额计算正确 (20万)")

    # 测试3: 验证配置读取
    print("\n[测试3] 验证配置读取")
    config = ConfigManager.load_config('configs/strategy/continuous_decline.yaml')
    max_position_count = config['strategy']['risk_params'].get('max_position_count', 10)

    print(f"  配置文件max_position_count: {max_position_count}")
    assert max_position_count == 10, f"期望10, 实际{max_position_count}"
    print("  ✓ 配置读取正确")

    print("\n" + "=" * 70)
    print("所有测试通过 ✓")
    print("=" * 70)


def test_multiple_stocks():
    """测试多股票场景"""
    print("\n" + "=" * 70)
    print("测试多股票场景")
    print("=" * 70)

    pm = PositionManager(
        total_capital=1_000_000,
        params={
            'initial_position_size': 0.20,
            'position_percent_per_layer': 0.10,
            'max_layers': 8,
            'max_position_count': 10
        }
    )

    # 建仓10只股票
    total_cost = 0
    for i in range(10):
        symbol = f'000{i:03d}.SZ'
        success = pm.open_position(symbol, price=10.0)

        if success:
            position = pm.get_position(symbol)
            total_cost += position.total_cost
            print(f"  {symbol}: 建仓成功，数量={position.quantity}, 成本={position.total_cost:.0f}")
        else:
            print(f"  {symbol}: 建仓失败")

    print(f"\n  总成本: {total_cost:.0f}")
    print(f"  可用资金: {pm.available_capital:.0f}")
    print(f"  资金使用: {((1_000_000 - pm.available_capital) / 1_000_000 * 100):.1f}%")

    # 验证资金精确匹配
    expected_cost = 10 * (100_000 * 0.20)  # 10只 * (10万 * 20%)
    tolerance = 1000  # 允许1000元的误差（因为股数是整数）

    assert abs(total_cost - expected_cost) < tolerance, f"资金不匹配: 期望{expected_cost}, 实际{total_cost}"
    print(f"\n  ✓ 资金精确匹配 (期望{expected_cost:.0f}, 实际{total_cost:.0f})")

    print("\n" + "=" * 70)
    print("多股票测试通过 ✓")
    print("=" * 70)


def main():
    """主函数"""
    try:
        test_per_stock_allocation()
        test_multiple_stocks()
        print("\n" + "=" * 70)
        print("所有测试完成 ✓✓✓")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
