# QuantBacktest - 量化交易回测系统 V1.0

一个完整的量化交易回测框架，采用事件驱动架构设计，支持多种数据源、策略类型和分析工具。

## 🎯 V1.0 新特性

- **🚀 生产级系统入口** - `main.py` 一键启动完整回测流程
- **⚙️ 命令行接口** - 灵活的参数配置，支持批量回测
- **🛡️ 边界异常处理** - 数据IO、网络API、配置读取的友好错误提示
- **📊 专业报告生成** - 自动生成时间戳命名的分析图表
- **🔧 配置驱动架构** - 支持命令行参数覆盖配置文件
- **📈 动态策略加载** - 轻松扩展和测试新策略

## ✨ 核心特性

- **事件驱动架构** - 模块间松耦合，易于扩展
- **多数据源支持** - 本地CSV、问财选股、Tushare、Yahoo Finance等
- **完整数据管道** - 从选股到策略执行的完整流程
- **防未来函数机制** - 严格的时间对齐和数据访问控制
- **工业级代码标准** - 完整的异常处理和日志记录
- **配置化管理** - YAML配置文件和环境变量支持
- **标准化数据格式** - 统一使用 Backtrader/VeighNa 标准 (代码.交易所)
- **精确资金管理** - 工业级精度的资金计算和风控机制
- **模块化架构** - 基于抽象基类的可扩展设计

## 📁 项目结构

```
QuantBacktest/

├── .env                         # 环境变量配置文件

├── .gitignore                   # Git忽略文件配置

├── PROJECT_SPECIFICATION.md     # 项目说明书

├── README.md                    # 项目说明文档

├── requirements.txt             # 项目依赖文件

├── config/                       # 配置管理模块

│   ├── config.yaml               # 业务配置文件

│   ├── settings.py               # 配置读取类

│   └── __init__.py

├── DataManager/                  # 数据管理模块

│   ├── api.py                    # 数据管理API接口

│   ├── __init__.py

│   ├── feeds/                    # 数据流处理

│   │   ├── base_feed.py          # 基础数据流类

│   │   ├── lazy_feed.py          # 懒加载数据流

│   │   ├── mem_feed.py           # 内存数据流

│   │   └── __init__.py

│   ├── handlers/                 # 数据驱动层

│   │   ├── handler.py            # 数据处理器实现（已重构）

│   │   └── __init__.py

│   ├── processors/               # 数据处理器

│   │   ├── adjuster.py           # 数据调整器

│   │   ├── cleaner.py            # 数据清洗器

│   │   ├── merger.py             # 数据合并器

│   │   ├── resampler.py          # 数据重采样器

│   │   └── __init__.py

│   ├── schema/                   # 数据结构定义

│   │   ├── base.py               # 基础数据类

│   │   ├── bar.py                # K线数据类

│   │   ├── constant.py           # 常量定义

│   │   ├── fundamental.py        # 财务数据类

│   │   ├── tick.py               # Tick数据类

│   │   └── __init__.py

│   ├── selectors/                # 选股器模块

│   │   ├── base.py               # 选股器基类

│   │   ├── tushare_selector.py   # Tushare选股器

│   │   ├── wencai_selector.py    # 问财选股器

│   │   └── __init__.py

│   ├── sources/                  # 数据源适配器

│   │   ├── base_source.py        # 数据源基类

│   │   ├── binance.py            # 币安数据源

│   │   ├── local_csv.py          # 本地CSV数据源

│   │   ├── tushare.py            # Tushare数据源

│   │   ├── yfinance.py           # Yahoo Finance数据源

│   │   └── __init__.py

│   └── storage/                  # 数据存储模块

│       ├── base_store.py         # 存储基类

│       ├── csv_store.py          # CSV存储

│       ├── hdf5_store.py         # HDF5存储

│       ├── influx_store.py       # InfluxDB存储

│       ├── mysql_store.py        # MySQL存储

│       └── __init__.py

├── Engine/                       # 回测引擎模块（已完成）

│   ├── engine.py                 # 回测引擎核心

│   └── __init__.py

├── Execution/                    # 撮合执行模块（已完成）

│   ├── base.py                   # 执行器基类

│   ├── simulator.py              # 模拟执行器

│   └── __init__.py

├── Infrastructure/               # 基础设施模块

│   ├── enums.py                  # 枚举定义（新增）

│   ├── events.py                 # 事件系统定义（已重构）

│   └── __init__.py

├── Portfolio/                    # 投资组合模块（已完成）

│   ├── base.py                   # 投资组合基类

│   ├── portfolio.py              # 投资组合实现

│   └── __init__.py

├── Strategies/                   # 策略模块（已完成）

│   ├── base.py                   # 策略基类

│   ├── simple_strategy.py        # 简单策略示例

│   └── __init__.py

├── Analysis/                     # 分析模块（已完成）

│   ├── performance.py            # 绩效分析器

│   ├── plotting.py               # 图表绘制器

│   └── __init__.py

├── Test/                         # 测试模块

│   ├── debug_data.py             # 数据调试脚本

│   ├── debug_plotting.py         # 图表调试脚本

│   ├── debug_strategy.py         # 策略调试脚本

│   ├── debug_strategy_signals.py # 策略信号调试脚本

│   ├── test_complete_analysis.py # 完整分析测试

│   ├── test_comprehensive_integration.py  # 综合集成测试

│   ├── test_engine.py            # 引擎测试

│   ├── test_execution_module.py  # 执行模块测试

│   ├── test_new_event_system.py  # 新事件系统测试

│   ├── test_portfolio.py         # 投资组合测试

│   ├── test_strategy_base.py     # 策略基类测试

│   └── test_wencai_csv_integration.py  # 问财CSV集成测试

├── output/                       # 输出目录（图表、报告）

└── txt/                          # 文档文件夹
```

## 🛠️ 安装

### 环境要求

- Python 3.8+
- pandas
- pywencai (问财选股)
- pyyaml
- matplotlib (图表生成)
- seaborn (图表美化)

### 安装依赖

```bash
pip install pandas pywencai pyyaml matplotlib seaborn
```

## ⚙️ 配置

### 1. 环境变量配置

复制 `.env` 文件并配置必要的信息：

```bash
# 问财Cookie（用于选股）
WENCAI_COOKIE=your_wencai_cookie_here

# Tushare Token（可选）
TUSHARE_TOKEN=your_tushare_token_here

# 数据路径
CSV_ROOT_PATH=C:/path/to/your/csv/data
```

### 2. 业务配置

编辑 `config/config.yaml` 文件：

```yaml
# 回测基本设置
backtest:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  initial_capital: 1000000.0

# 数据路径配置
data:
  csv_root_path: "C:/Users/123/A股数据/个股数据"
  output_path: "./output"

# 选股配置
selector:
  default_type: "wencai"
  wencai:
    retry_count: 3
    sleep_time: 2
```

## 🎯 快速开始

### 1. 完整回测流程

```python
from Engine.engine import BacktestEngine
from Strategies.simple_strategy import SimpleMomentumStrategy
from Portfolio.portfolio import BacktestPortfolio
from DataManager.handlers import BacktestDataHandler
from DataManager.sources import LocalCSVLoader
from collections import deque
from datetime import datetime

# 1. 准备数据
loader = LocalCSVLoader("C:/path/to/csv/data")
data_handler = BacktestDataHandler(
    loader=loader,
    symbol_list=["000001.SZSE", "000002.SZSE"],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# 2. 创建策略
event_queue = deque()
strategy = SimpleMomentumStrategy(data_handler, event_queue)

# 3. 创建投资组合
portfolio = BacktestPortfolio(data_handler, initial_capital=100000.0)

# 4. 创建执行器（简单市价执行）
class SimpleExecution:
    def execute_order(self, order_event):
        from Infrastructure.events import FillEvent
        from Infrastructure.enums import Direction
        
        # 简单市价成交模拟
        latest_bar = data_handler.get_latest_bar(order_event.symbol)
        if latest_bar:
            # 计算手续费 (0.03%)
            commission = order_event.volume * latest_bar.close_price * 0.0003
            
            return FillEvent(
                symbol=order_event.symbol,
                datetime=latest_bar.datetime,
                direction=order_event.direction,
                volume=order_event.volume,
                price=latest_bar.close_price,
                commission=commission
            )
        return None

execution = SimpleExecution()

# 5. 创建并运行回测引擎
engine = BacktestEngine(data_handler, strategy, portfolio, execution)
engine.run()

# 6. 查看回测结果
portfolio_info = portfolio.get_portfolio_info()
print(f"总资产: {portfolio_info['total_equity']:,.2f}")
print(f"总收益率: {portfolio_info['return_rate']:.2f}%")
print(f"总交易次数: {portfolio_info['total_trades']}")
```

### 2. 自定义策略开发

```python
from Strategies.base import BaseStrategy
from Infrastructure.events import MarketEvent, Direction

class MyCustomStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> None:
        """处理行情数据，实现策略逻辑"""
        bar = event.bar
        symbol = bar.symbol
        
        # 获取最近5根K线计算技术指标
        bars = self.get_latest_bars(symbol, 5)
        if len(bars) < 5:
            return
        
        # 计算简单移动平均线
        sma5 = self.calculate_sma(symbol, 5)
        if sma5 is None:
            return
        
        # 策略逻辑：价格突破SMA5时买入
        if bar.close_price > sma5:
            # 检查当前是否有持仓
            current_position = self.get_current_price(symbol)  # 这里需要扩展BaseStrategy
            
            # 策略信号：突破买入
            self.send_signal(symbol, Direction.LONG, strength=0.8)
        
        # 策略逻辑：价格跌破SMA5时卖出
        elif bar.close_price < sma5:
            self.send_signal(symbol, Direction.SHORT, strength=0.8)

# 使用自定义策略
strategy = MyCustomStrategy(data_handler, event_queue)
```

### 3. 投资组合管理

```python
from Portfolio.portfolio import BacktestPortfolio
from Infrastructure.events import SignalEvent, Direction
from datetime import datetime

# 创建投资组合
portfolio = BacktestPortfolio(data_handler, initial_capital=100000.0)

# 模拟信号事件
buy_signal = SignalEvent(
    symbol="000001.SZSE",
    datetime=datetime.now(),
    direction=Direction.LONG,
    strength=0.8
)

# 处理信号，生成订单
order_event = portfolio.process_signal(buy_signal)
if order_event:
    print(f"生成订单: {order_event.symbol} {order_event.direction.value} {order_event.volume}股")

# 查看投资组合状态
portfolio_info = portfolio.get_portfolio_info()
print(f"当前现金: {portfolio_info['current_cash']:,.2f}")
print(f"总资产: {portfolio_info['total_equity']:,.2f}")
print(f"持仓数量: {portfolio_info['positions_count']}")
```

### 4. 测试本地数据加载

```python
from DataManager.sources import LocalCSVLoader
from datetime import datetime

# 创建数据加载器
loader = LocalCSVLoader("C:/path/to/csv/data")

# 加载股票数据
bars = loader.load_bar_data(
    symbol="000001",
    exchange="SZSE", 
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

print(f"加载了 {len(bars)} 条K线数据")
```

### 2. 使用问财选股

```python
from DataManager.selectors import WencaiSelector
from datetime import datetime

# 创建选股器
selector = WencaiSelector()

# 选股
bank_stocks = selector.select_stocks(
    date=datetime.now(),
    query="银行"
)

print(f"选到 {len(bank_stocks)} 只银行股")
```

### 3. 新事件系统测试

```python
from Infrastructure.events import MarketEvent, SignalEvent, EventType, Direction
from Infrastructure.enums import EventType, Direction, OrderType
from DataManager.schema.bar import BarData
from datetime import datetime

# 创建K线数据
bar = BarData(
    symbol="000001",
    exchange="SZSE",
    datetime=datetime.now(),
    open_price=10.0,
    high_price=11.0,
    low_price=9.5,
    close_price=10.5,
    volume=1000000,
    turnover=10500000
)

# 创建行情事件
market_event = MarketEvent(bar=bar)
print(f"行情事件: {market_event.bar.symbol}, 类型: {market_event.type}")

# 创建信号事件
signal_event = SignalEvent(
    symbol="000001.SZ",
    datetime=datetime.now(),
    direction=Direction.LONG,
    strength=0.8
)
print(f"信号事件: {signal_event}")
```

### 4. 数据驱动层使用

```python
from DataManager.handlers import BacktestDataHandler
from DataManager.sources import LocalCSVLoader
from datetime import datetime

# 创建数据加载器
loader = LocalCSVLoader("C:/path/to/csv/data")

# 创建数据处理器
handler = BacktestDataHandler(
    loader=loader,
    symbol_list=["000001.SZSE", "000002.SZSE"],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# 生成事件流
event_count = 0
for event in handler.update_bars():
    if isinstance(event, MarketEvent):
        event_count += 1
        print(f"事件{event_count}: {event.bar.symbol} @ {event.bar.datetime}, 价格: {event.bar.close_price}")
    
    # 限制处理事件数量
    if event_count >= 10:
        break

# 查询最新数据
latest_bar = handler.get_latest_bar("000001.SZSE")
if latest_bar:
    print(f"最新K线: {latest_bar.symbol} @ {latest_bar.datetime}, 价格: {latest_bar.close_price}")

latest_bars = handler.get_latest_bars("000001.SZSE", 5)
print(f"最近5根K线: {len(latest_bars)} 条")
```

## 📊 示例用法

### 完整的选股+回测流程

```python
from DataManager.selectors import WencaiSelector
from DataManager.handlers import BacktestDataHandler
from DataManager.sources import LocalCSVLoader
from Infrastructure.events import MarketEvent, Direction
from config.settings import settings
from datetime import datetime

# 1. 选股
cookie = settings.get_env('WENCAI_COOKIE')
selector = WencaiSelector(cookie=cookie)
stocks = selector.select_stocks(datetime.now(), query="银行股")

print(f"选到 {len(stocks)} 只银行股: {stocks[:5]}")

# 2. 数据准备
loader = LocalCSVLoader("C:/path/to/csv/data")
handler = BacktestDataHandler(
    loader=loader,
    symbol_list=stocks[:6],  # 取前6只进行测试
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 15)
)

# 3. 简单策略模拟
strategy_signals = []

for event in handler.update_bars():
    if isinstance(event, MarketEvent):
        bar = event.bar
        
        # 策略逻辑：涨幅超过2%发出买入信号
        if bar.close_price > bar.open_price * 1.02:
            signal = {
                'symbol': bar.symbol,
                'datetime': bar.datetime,
                'price_change_pct': ((bar.close_price - bar.open_price) / bar.open_price) * 100,
                'action': 'BUY_SIGNAL'
            }
            strategy_signals.append(signal)
            print(f"策略信号: {bar.symbol} @ {bar.datetime.strftime('%Y-%m-%d')} - 涨幅 {signal['price_change_pct']:.2f}%")
    
    # 限制处理事件数量
    if len(strategy_signals) >= 5:
        break

print(f"总共产生 {len(strategy_signals)} 个策略信号")
```

### 综合集成测试

```bash
# 运行完整的集成测试，验证所有模块协同工作
python Test/test_comprehensive_integration.py
```

测试流程: 问财选股 → CSV数据加载 → 新事件系统 → DataHandler → 策略模拟

## 🧪 测试

运行测试用例验证系统功能：

```bash
# 测试CSV数据加载
python Test/test_csv_loader.py

# 测试问财选股
python Test/test_wencai_selector.py

# 测试集成功能
python Test/test_wencai_csv_integration.py

# 测试新事件系统
python Test/test_new_event_system.py

# 综合集成测试（推荐）
python Test/test_comprehensive_integration.py
```

### 测试覆盖范围

- ✅ 枚举定义和事件类创建
- ✅ 问财选股功能（42只银行股）
- ✅ CSV数据加载和解析
- ✅ 数据处理器事件生成（20个MarketEvent）
- ✅ 防未来函数机制
- ✅ 时间对齐和多股票处理
- ✅ 策略信号生成（涨幅超过2%检测）

## 📊 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据源模块     │    │   系统入口模块     │    │   分析报告模块     │
│                │    │                │    │                │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ LocalCSV    │ │    │ │ main.py     │ │    │ │ Performance │ │
│ │ Wencai      │ │    │ │             │ │    │ │ Analyzer   │ │
│ │ Tushare     │ │    │ │             │    │ │ Plotter     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘�    └─────────────────┘    └─────────────────┘
        │                   │                   │                   │
        ▼ MarketEvent      ▼ SignalEvent       ▼ Analysis Results
        ▼                  ▼                  ▼
        ▼                  ▼ OrderEvent        ▼ Charts & Logs
        ▼                  ▼                  ▼
        ▼ FillEvent         ▼ Portfolio Update  ▼
```

## 📈 支持的数据源

| 数据源 | 状态 | 说明 | V1.0特性 |
|--------|------|------|----------|
| 本地CSV | ✅ | 支持标准格式的股票数据文件 | 增强异常处理 |
| 问财选股 | ✅ | 自然语言选股，需要Cookie | 网络重试机制 |
| Tushare | 🚧 | 计划支持，需要Token | - |
| Yahoo Finance | 🚧 | 计划支持，国际市场数据 | - |
| Binance | 🚧 | 计划支持，加密货币数据 | - |

## 🎨 策略开发

### 创建自定义策略

```python
from Infrastructure.events import MarketEvent, SignalEvent, Direction, OrderType
from DataManager.handlers import BacktestDataHandler

class MyStrategy:
    def __init__(self, handler: BacktestDataHandler):
        self.handler = handler
        self.position = {}
        
    def on_market_data(self, event: MarketEvent):
        """处理行情数据"""
        bar = event.bar
        symbol = bar.symbol
        
        # 获取历史数据用于技术指标计算
        latest_bars = self.handler.get_latest_bars(symbol, 5)
        if len(latest_bars) < 5:
            return
            
        # 计算简单移动平均线
        prices = [b.close_price for b in latest_bars]
        ma5 = sum(prices) / 5
        
        # 策略逻辑：价格突破MA5且涨幅超过2%
        if bar.close_price > ma5 and bar.close_price > bar.open_price * 1.02:
            self.send_buy_signal(bar)
            
    def send_buy_signal(self, bar):
        """发送买入信号"""
        signal = SignalEvent(
            symbol=bar.symbol,
            datetime=bar.datetime,
            direction=Direction.LONG,
            strength=0.8
        )
        print(f"买入信号: {signal}")
        # 在实际系统中，这里会将信号发送到Portfolio模块
        return signal

# 使用策略
handler = BacktestDataHandler(loader, symbol_list, start_date, end_date)
strategy = MyStrategy(handler)

for event in handler.update_bars():
    if isinstance(event, MarketEvent):
        strategy.on_market_data(event)
```

## 📋 开发计划



- [x] 数据结构和事件系统

- [x] 本地CSV数据加载

- [x] 问财选股器

- [x] 数据驱动层重构

- [x] 新事件系统架构

- [x] 综合集成测试

- [x] 回测引擎核心

- [x] 策略框架

- [x] 投资组合管理

- [x] 撮合执行系统

- [x] 性能分析工具

- [x] 图表生成模块

## 🎯 当前系统状态

### 已完成模块

- **数据结构层** - 完整的BarData、TickData、FundamentalData模型，支持标准化交易所格式

- **数据源层** - LocalCSVLoader，自动转换交易所代码 (SZSE→SZ, SSE→SH)

- **选股器层** - WencaiSelector，自然语言选股

- **事件系统** - EventType枚举和MarketEvent、SignalEvent、OrderEvent、FillEvent，修复了FillEvent.net_value计算逻辑

- **数据处理器** - BacktestDataHandler，时间对齐和防未来函数

- **配置管理** - YAML配置文件和环境变量支持

- **回测引擎** - BacktestEngine，重构了策略信号机制，使用统一事件队列

- **策略框架** - BaseStrategy抽象基类，采用模板方法模式，通过IStrategy接口强制约束

- **投资组合管理** - BacktestPortfolio，工业级资金管理，多层风控机制，精确的手续费计算

- **执行系统** - SimulatedExecution，订单处理、手续费、滑点模拟

- **分析系统** - PerformanceAnalyzer和BacktestPlotter，绩效分析和图表生成

### 架构特点

- **事件驱动** - 通过事件实现模块解耦，统一的事件队列管理

- **防未来函数** - 策略只能访问当前视图数据

- **时间对齐** - 多股票统一时间轴处理

- **生成器模式** - 高效的事件流生成

- **工业级代码** - 完整的异常处理和日志记录

- **完整回测** - 从选股到绩效分析的完整链条

- **标准化接口** - 基于抽象基类的模块化设计

- **精确计算** - 修复了资金计算中的手续费逻辑错误

### 最新架构改进 (v2.0)

1. **策略信号机制重构** - 移除双重队列管理，使用统一事件队列
2. **模块接口标准化** - 使用ABC强制定义接口，移除runtime检查
3. **数据格式统一** - 全系统采用 Backtrader/VeighNa 标准格式 (代码.交易所)
4. **资金管理完善** - 工业级精度，多层风控，详细验证机制
5. **Direction枚举简化** - 移除BUY/SELL冗余，统一使用LONG/SHORT
6. **FillEvent修复** - 正确的net_value计算：买入加手续费，卖出减手续费


## 🏗️ 系统架构

### 事件流转图

```
DataManager (数据源) 
    ↓ MarketEvent
BacktestDataHandler (时间对齐)
    ↓ MarketEvent  
Strategy (策略逻辑) ✅
    ↓ SignalEvent (统一事件队列)
Portfolio (风控+仓位) ✅
    ↓ OrderEvent
Execution (撮合执行) ✅
    ↓ FillEvent (修复net_value计算)
Portfolio (持仓更新) ✅
```

### 核心设计原则

1. **事件驱动架构** - 所有模块通过事件通信，松耦合设计
2. **防未来函数** - 策略只能访问`_latest_data`，严禁访问未来数据
3. **时间对齐机制** - 多股票数据按统一时间轴处理，解决停牌问题
4. **生成器模式** - `update_bars()`使用yield实现高效事件流
5. **单一职责原则** - 每个模块专注特定功能，易于维护和扩展
6. **依赖注入** - Engine负责组件初始化和依赖关系管理
7. **模板方法模式** - Strategy基类定义标准处理流程
8. **接口约束** - 使用ABC确保模块接口一致性

## 🎯 V1.0 成果展示

### 实际回测示例

```bash
# 运行3个月回测，2只股票，10万初始资金
python main.py --start-date 2024-01-01 --end-date 2024-03-31 --capital 100000 --symbols 000001.SZ 600036.SH
```

**输出结果：**
```
步骤6: 分析回测结果
========================================
累计收益率: 4.09%
年化收益率: 16.36%
最大回撤: -2.15%
夏普比率: 1.23
年化波动率: 18.45%
交易天数: 60
胜率: 52.3%
卡尔玛比率: 7.61
📊 Chart saved to: output/backtest_main_20251122_190951.png
📊 Chart saved to: output/backtest_returns_20251122_190951.png

🎉 回测完成！查看 output/ 目录获取详细报告。
```

### 系统性能指标

- **处理速度**：242个交易日，2000+个事件，3秒内完成
- **内存效率**：生成器模式，内存占用优化
- **稳定性**：三层异常处理，优雅降级机制
- **扩展性**：模块化设计，易于添加新策略

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发规范

1. 遵循单一职责原则
2. 添加适当的异常处理和日志记录
3. 编写单元测试和集成测试
4. 更新相关文档（PROJECT_SPECIFICATION.md和README.md）
5. **严禁引入未来函数** - 策略代码只能通过DataHandler接口访问数据

### V1.1 开发计划

1. **策略注册机制** - 支持配置文件选择策略
2. **多策略批量回测** - 并行运行多个策略对比
3. **扩展数据源** - Tushare、Yahoo Finance、Binance等数据源
4. **Web界面** - 基于Flask的Web管理界面
5. **分布式回测** - 支持集群并行回测

## 📄 许可证

MIT License

## 📞 联系

如有问题或建议，请提交Issue或联系项目维护者。

---

**注意**: 本项目仅用于学习和研究目的，不构成投资建议。使用本系统进行实际交易的风险由用户自行承担。

**最近更新**: 2025-11-22 - 完成系统主入口、边界异常处理增强和文档更新