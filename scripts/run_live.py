#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
实盘运行脚本

使用vn.py引擎进行实盘交易

⚠️ 警告：实盘交易有风险，请确保充分测试后再运行！

Usage:
    python run_live.py                                    # 使用默认账户配置
    python run_live.py --config <config_path>             # 指定策略配置
    python run_live.py --account <account_config>         # 指定账户配置
"""

import argparse
import sys
import os
from pathlib import Path

# 将src目录添加到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.utils.config import ConfigManager


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='持续下跌策略实盘工具')

    parser.add_argument(
        '--config',
        type=str,
        default='configs/strategy/continuous_decline.yaml',
        help='策略配置文件路径'
    )

    parser.add_argument(
        '--account',
        type=str,
        default='configs/live/account.yaml',
        help='账户配置文件路径'
    )

    parser.add_argument(
        '--symbols',
        type=str,
        default=None,
        help='交易标的（用逗号分隔）'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 设置日志
    logger = setup_logger(name='live_trading')

    logger.info="=" * 60)
    logger.info("⚠️  实盘交易模式启动")
    logger.info="=" * 60)
    logger.info("重要提示：实盘交易有风险，请确保：")
    logger.info("  1. 充分理解策略逻辑")
    logger.info("  2. 使用小资金测试")
    logger.info("  3. 设置好止损线")
    logger.info("=" * 60)

    # 检查vn.py是否安装
    logger.info("检查vn.py...")
    try:
        from vnpy.trader.engine import MainEngine
        logger.info("✅ vn.py已安装")
    except ImportError:
        logger.error("❌ vn.py未安装，请先运行：pip install vnpy")
        logger.error("如果安装失败，请参考：https://www.vnpy.com/docs/cn/quickstart.html")
        sys.exit(1)

    # 用户确认
    try:
        from src.utils.config import confirm_user
        confirm_user(
            message="\n确认开始实盘交易吗？",
            choices=["开始实盘", "取消"]
        )
    except Exception as e:
        logger.info("用户取消")
        sys.exit(0)

    # 加载策略配置
    logger.info("加载策略配置...")
    try:
        strategy_config = ConfigManager.load_config(args.config)
        logger.info("✅ 策略配置加载成功")
    except Exception as e:
        logger.error(f"❌ 策略配置加载失败：{e}")
        sys.exit(1)

    # 加载账户配置
    logger.info("加载账户配置...")
    try:
        account_config = ConfigManager.load_config(args.account)
        logger.info("✅ 账户配置加载成功")
    except Exception as e:
        logger.error(f"❌ 账户配置加载失败：{e}")
        logger.error("请确保已配置账户文件：configs/live/account.yaml")
        sys.exit(1)

    # 账户配置检查
    if "account" not in account_config:
        logger.error("❌ 账户配置不正确，请检查配置文件格式")
        logger.error("参考：account.example.yaml")
        sys.exit(1)

    # 初始化vn.py引擎
    logger.info("初始化vn.py引擎...")
    try:
        from src.execution.vnpy_executor import VnPyExecutor
        executor = VnPyExecutor(strategy_config, account_config)
        logger.info("✅ vn.py引擎初始化成功")
    except Exception as e:
        logger.error(f"❌ vn.py引擎初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 启动策略
    logger.info("正在启动策略...")
    try:
        executor.start()
        logger.info("✅ 策略启动成功")
    except Exception as e:
        logger.error(f"❌ 策略启动失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info="=" * 60)
    logger.info("实盘策略已启动！")
    logger.info("按 Ctrl+C 停止策略")
    logger.info="=" * 60)

    try:
        import signal
        import sys

        def signal_handler(sig, frame):
            logger.info="\n收到停止信号，正在退出...")
            executor.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # 保持运行
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info="\n用户手动停止")
    finally:
        executor.stop()

    logger.info("实盘程序已退出")


if __name__ == '__main__':
    main()
