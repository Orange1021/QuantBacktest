"""
QuantBacktest 系统主入口
负责命令行参数解析和应用程序调用
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from app import BacktestApplication


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='量化回测系统')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--start-date', type=str, help='回测开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='回测结束日期 (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, help='初始资金')
    parser.add_argument('--symbols', nargs='+', help='股票代码列表')
    return parser.parse_args()


def apply_argument_overrides(args):
    """应用命令行参数覆盖配置"""
    if args.start_date:
        settings._config_data.setdefault('backtest', {})['start_date'] = args.start_date
    if args.end_date:
        settings._config_data.setdefault('backtest', {})['end_date'] = args.end_date
    if args.capital:
        settings._config_data.setdefault('backtest', {})['initial_capital'] = args.capital
    if args.symbols:
        settings._config_data.setdefault('backtest', {})['default_symbols'] = args.symbols


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 应用参数覆盖
    apply_argument_overrides(args)
    
    # 导入策略类
    from Strategies.simple_strategy import SimpleMomentumStrategy
    
    # 定义默认股票列表
    default_symbols = [
        "000001.SZ",  # 平安银行
        "000002.SZ",  # 万科A
        "600000.SH",  # 浦发银行
        "600036.SH",  # 招商银行
    ]
    
    try:
        # 创建应用实例
        app = BacktestApplication()
        
        # 运行回测
        results = app.run(
            strategy_class=SimpleMomentumStrategy,
            symbol_list=default_symbols
        )
        
        print("\n🎉 回测完成！查看 output/ 目录获取详细报告。")
        
    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        sys.exit(1)
