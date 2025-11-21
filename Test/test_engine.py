"""
回测引擎测试
验证 BacktestEngine 的核心功能和事件循环
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Engine.engine import BacktestEngine
from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent, FillEvent, EventType, Direction, OrderType
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.sources.local_csv import LocalCSVLoader
from config.settings import settings


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MockStrategy:
    """模拟策略类"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockStrategy")
        self.market_data_count = 0
        self.signals_generated = 0
    
    def on_market_data(self, event: MarketEvent) -> None:
        """处理行情数据"""
        self.market_data_count += 1
        bar = event.bar
        
        # 简单策略：涨幅超过2%时生成买入信号
        if bar.close_price > bar.open_price * 1.02:
            signal = SignalEvent(
                symbol=bar.symbol,
                datetime=bar.datetime,
                direction=Direction.LONG,
                strength=0.8
            )
            
            # 在实际系统中，这里应该通过事件总线发送信号
            # 为了测试，我们直接将信号添加到引擎的队列中
            # 这里先记录信号信息
            self.signals_generated += 1
            self.logger.info(f"策略生成买入信号: {bar.symbol} @ {bar.datetime.strftime('%Y-%m-%d')}, 涨幅: {((bar.close_price - bar.open_price) / bar.open_price * 100):.2f}%")
            
            # 返回信号供测试使用
            return signal
        
        return None


class MockPortfolio:
    """模拟投资组合类"""
    
    def __init__(self, initial_capital: float = 1000000.0):
        self.logger = logging.getLogger(f"{__name__}.MockPortfolio")
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # symbol: quantity
        self.market_updates = 0
        self.signals_processed = 0
        self.orders_generated = 0
        self.fills_processed = 0
    
    def update_on_market(self, event: MarketEvent) -> None:
        """更新持仓市值"""
        self.market_updates += 1
        # 在实际系统中，这里会更新持仓的市值
        # 测试中只记录调用次数
    
    def process_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        """处理信号，生成订单"""
        self.signals_processed += 1
        
        # 简单风控：只处理前3个信号
        if self.signals_processed <= 3:
            order = OrderEvent(
                symbol=event.symbol,
                datetime=event.datetime,
                order_type=OrderType.MARKET,
                direction=event.direction,
                volume=1000,  # 固定买入1000股
                limit_price=0.0  # 市价单
            )
            
            self.orders_generated += 1
            self.logger.info(f"投资组合生成订单: {order.symbol}, 数量: {order.volume}, 方向: {order.direction}")
            return order
        
        return None
    
    def update_on_fill(self, event: FillEvent) -> None:
        """更新成交信息"""
        self.fills_processed += 1
        trade_value = event.trade_value
        commission = event.commission
        net_value = event.net_value
        
        # 更新资金和持仓
        if event.direction == Direction.LONG:
            self.current_capital -= net_value
            self.positions[event.symbol] = self.positions.get(event.symbol, 0) + event.volume
        else:
            self.current_capital += net_value
            self.positions[event.symbol] = self.positions.get(event.symbol, 0) - event.volume
        
        self.logger.info(f"成交更新: {event.symbol}, 数量: {event.volume}, 价格: {event.price:.2f}, 成交额: {trade_value:.2f}, 手续费: {commission:.2f}")


class MockExecution:
    """模拟执行器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockExecution")
        self.orders_received = 0
        self.fills_generated = 0
    
    def execute_order(self, event: OrderEvent) -> Optional[FillEvent]:
        """执行订单，生成成交"""
        self.orders_received += 1
        
        # 简单撮合：所有订单都立即成交，价格假设为当前价格+0.1%滑点
        fill_price = 10.0 * 1.001  # 假设价格为10元，加0.1%滑点
        commission = fill_price * event.volume * 0.0003  # 0.03%手续费
        
        fill = FillEvent(
            symbol=event.symbol,
            datetime=event.datetime,
            direction=event.direction,
            volume=event.volume,
            price=fill_price,
            commission=commission
        )
        
        self.fills_generated += 1
        self.logger.info(f"执行器生成成交: {fill.symbol}, 数量: {fill.volume}, 价格: {fill_price:.2f}")
        return fill


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


def test_engine_basic_functionality():
    """测试引擎基本功能"""
    print("=" * 80)
    print("回测引擎基本功能测试")
    print("=" * 80)
    
    # 1. 准备测试数据
    print("\n步骤1: 准备测试数据")
    print("-" * 40)
    
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    # 使用预定义股票列表
    test_symbols = ["000001.SZSE", "000002.SZSE", "600000.SSE", "600036.SSE"]
    print(f"📋 测试股票: {test_symbols[:3]}")  # 只用前3只
    
    try:
        # 创建数据加载器和处理器
        loader = LocalCSVLoader(csv_root_path)
        handler = BacktestDataHandler(
            loader=loader,
            symbol_list=test_symbols[:3],  # 只用前3只股票
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10)
        )
        print("✅ 数据处理器创建成功")
        
    except Exception as e:
        print(f"❌ 数据准备失败: {e}")
        return False
    
    # 2. 创建模拟组件
    print(f"\n步骤2: 创建模拟组件")
    print("-" * 40)
    
    try:
        strategy = MockStrategy()
        portfolio = MockPortfolio(initial_capital=1000000.0)
        execution = MockExecution()
        print("✅ 模拟组件创建成功")
        
    except Exception as e:
        print(f"❌ 模拟组件创建失败: {e}")
        return False
    
    # 3. 创建回测引擎
    print(f"\n步骤3: 创建回测引擎")
    print("-" * 40)
    
    try:
        engine = BacktestEngine(
            data_handler=handler,
            strategy=strategy,
            portfolio=portfolio,
            execution=execution
        )
        print("✅ 回测引擎创建成功")
        
    except Exception as e:
        print(f"❌ 回测引擎创建失败: {e}")
        return False
    
    # 4. 运行回测
    print(f"\n步骤4: 运行回测")
    print("-" * 40)
    
    try:
        engine.run()
        print("✅ 回测运行完成")
        
    except Exception as e:
        print(f"❌ 回测运行失败: {e}")
        return False
    
    # 5. 验证结果
    print(f"\n步骤5: 验证结果")
    print("-" * 40)
    
    status = engine.get_status()
    print("📊 引擎状态:")
    print(f"  总事件数: {status['total_events']}")
    print(f"  行情事件: {status['market_events']}")
    print(f"  信号事件: {status['signal_events']}")
    print(f"  订单事件: {status['order_events']}")
    print(f"  成交事件: {status['fill_events']}")
    
    print("\n📈 策略统计:")
    print(f"  处理行情数据: {strategy.market_data_count}")
    print(f"  生成信号数量: {strategy.signals_generated}")
    
    print("\n💼 投资组合统计:")
    print(f"  市场更新次数: {portfolio.market_updates}")
    print(f"  处理信号数量: {portfolio.signals_processed}")
    print(f"  生成订单数量: {portfolio.orders_generated}")
    print(f"  处理成交数量: {portfolio.fills_processed}")
    print(f"  当前资金: {portfolio.current_capital:.2f}")
    print(f"  当前持仓: {portfolio.positions}")
    
    print("\n⚙️ 执行器统计:")
    print(f"  接收订单数量: {execution.orders_received}")
    print(f"  生成成交数量: {execution.fills_generated}")
    
    # 6. 验证事件流转
    print(f"\n步骤6: 验证事件流转")
    print("-" * 40)
    
    # 验证事件流转的完整性
    if (status['market_events'] > 0 and 
        portfolio.market_updates == status['market_events'] and
        strategy.market_data_count == status['market_events']):
        print("✅ MarketEvent 事件流转正常")
    else:
        print("❌ MarketEvent 事件流转异常")
        return False
    
    if (strategy.signals_generated == portfolio.signals_processed and
        portfolio.orders_generated == execution.orders_received and
        execution.fills_generated == portfolio.fills_processed):
        print("✅ 信号->订单->成交 事件流转正常")
    else:
        print("❌ 信号->订单->成交 事件流转异常")
        return False
    
    # 最终总结
    print(f"\n" + "=" * 80)
    print("回测引擎测试总结")
    print("=" * 80)
    
    print("✅ 步骤1: 准备测试数据 - 通过")
    print("✅ 步骤2: 创建模拟组件 - 通过")
    print("✅ 步骤3: 创建回测引擎 - 通过")
    print("✅ 步骤4: 运行回测 - 通过")
    print("✅ 步骤5: 验证结果 - 通过")
    print("✅ 步骤6: 验证事件流转 - 通过")
    
    print(f"\n🎉 回测引擎测试全部通过！")
    print(f"📊 总处理事件: {status['total_events']}")
    print(f"📈 生成信号: {strategy.signals_generated}")
    print(f"💼 生成订单: {portfolio.orders_generated}")
    print(f"✅ 完成成交: {portfolio.fills_processed}")
    
    return True


if __name__ == "__main__":
    success = test_engine_basic_functionality()
    
    if success:
        print(f"\n🚀 回测引擎已准备就绪，可以开始策略开发！")
    else:
        print(f"\n💥 回测引擎测试失败，请检查实现")