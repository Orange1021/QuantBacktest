#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试pywencai集成

测试WencaiStockFilter的功能是否正常

Usage:
    python test_wencai.py                             # 使用配置文件中的cookie
    python test_wencai.py --date 2023-01-10           # 指定日期
    python test_wencai.py --days 5                    # 指定下跌天数
    python test_wencai.py --cookie "your_cookie"      # 指定cookie
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.filter.wencai_stock_filter import WencaiStockFilter
from src.utils.config import ConfigManager


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='测试pywencai集成')

    parser.add_argument(
        '--config',
        type=str,
        default='configs/strategy/continuous_decline.yaml',
        help='配置文件路径（默认：configs/strategy/continuous_decline.yaml）'
    )

    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='查询日期（YYYY-MM-DD，默认：今天）'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=8,
        help='连续下跌天数阈值（默认：8）'
    )

    parser.add_argument(
        '--cookie',
        type=str,
        default=None,
        help='问财Cookie（如不指定，从配置文件中读取）'
    )

    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='仅测试连接，不查询股票'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print("=" * 60)
    print("pywencai集成测试")
    print("=" * 60)

    # 加载配置
    print("加载配置文件...")
    try:
        config = ConfigManager.load_config(args.config)
    except Exception as e:
        print(f"❌ 加载配置文件失败：{e}")
        sys.exit(1)

    # 获取Cookie
    if args.cookie:
        cookie = args.cookie
        print(f"使用命令行提供的Cookie: {cookie[:50]}...")
    else:
        try:
            wencai_config = config['strategy']['filter_params']['wencai_params']
            cookie = wencai_config['cookie']
            print(f"使用配置文件的Cookie: {cookie[:50]}...")
        except KeyError:
            print("❌ 未找到wencai配置，请检查配置文件")
            print("在 strategy.filter_params.wencai_params.cookie 中配置")
            sys.exit(1)

    # 创建筛选器
    print("\n初始化WencaiStockFilter...")
    try:
        from src.core.filter.wencai_stock_filter import WencaiStockFilter
        filter = WencaiStockFilter(cookie=cookie)
        print("✅ 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 测试连接
    print("\n测试连接...")
    try:
        if filter.test_connection():
            print("✅ 连接成功")
        else:
            print("❌ 连接失败（Cookie可能已过期）")
            print("建议：更新Cookie后重试")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 测试连接失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 如果仅测试连接，退出
    if args.test_connection:
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        sys.exit(0)

    # 查询股票
    query_date = datetime.strptime(args.date, '%Y-%m-%d')
    print(f"\n查询日期: {query_date.strftime('%Y-%m-%d')}")
    print(f"下跌天数: {args.days}天")

    try:
        import time
        start_time = time.time()

        stocks = filter.get_eligible_stocks(
            date=query_date,
            decline_days_threshold=args.days
        )

        elapsed = time.time() - start_time

        print(f"\n✅ 查询成功！耗时：{elapsed:.2f}秒")
        print(f"符合条件的股票数量: {len(stocks)}")

        # 显示结果
        if stocks:
            print("\n股票列表：")
            for i, symbol in enumerate(stocks, 1):
                print(f"  {i:3d}. {symbol}")

            # 保存到文件
            output_file = Path(f"wencai_stocks_{args.date}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"问财筛选结果 - {args.date}\n")
                f.write(f"筛选条件: 连续下跌>={args.days}天\n")
                f.write(f"股票数量: {len(stocks)}\n\n")
                for symbol in stocks:
                    f.write(f"{symbol}\n")

            print(f"\n结果已保存到: {output_file}")
        else:
            print("\n未找到符合条件的股票")

    except Exception as e:
        print(f"\n❌ 查询失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
