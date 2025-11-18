# vn.py 和 VectorBT 核心功能对比

> 说明：以下功能需要在电脑上安装后才能使用

---

## 一、VectorBT（回测引擎）

### 1.1 核心概念

VectorBT是一个基于Pandas和NumPy的高性能回测库，使用向量化操作加速计算。

### 1.2 核心类和方法

#### **1.2.1 Portfolio.from_signals()**
**用途**：从买卖信号快速创建回测组合

```python
import vectorbt as vbt

# 创建回测组合
pf = vbt.Portfolio.from_signals(
    close=price_data,              # 价格数据（pandas Series/DataFrame）
    entries=buy_signals,           # 买入信号（布尔值或索引）
    exits=sell_signals,            # 卖出信号（布尔值或索引）
    size=100,                      # 每次交易数量
    init_cash=100000,              # 初始资金
    fees=0.001,                    # 手续费率
    slippage=0.001,                # 滑点
    freq='1D'                      # 数据频率
)

# 获取回测结果
total_return = pf.total_return()          # 总收益率
sharpe_ratio = pf.sharpe_ratio()          # 夏普比率
max_drawdown = pf.max_drawdown()          # 最大回撤
pnl = pf.pnl()                            # 盈亏序列
```

**常用参数**：
- `close`: 收盘价序列（必需）
- `entries`: 买入信号（布尔序列或索引）
- `exits`: 卖出信号（布尔序列或索引）
- `size`: 交易数量（可以是固定值或序列）
- `size_type`: 数量类型（'shares', 'cash', 'percent'）
- `init_cash`: 初始资金
- `fees`: 手续费率（默认0）
- `slippage`: 滑点比例（默认0）
- `freq`: 数据频率（'D', 'W', 'M'等）

---

#### **1.2.2 Portfolio.from_orders()**
**用途**：从订单列表创建回测组合，更灵活

```python
pf = vbt.Portfolio.from_orders(
    close=price_data,
    size=order_sizes,              # 订单数量（正表示买入，负表示卖出）
    init_cash=100000,
    fees=0.001
)

stats = pf.stats()                # 获取统计摘要
drawdown = pf.drawdown()          # 回撤序列
cum_returns = pf.cum_returns()    # 累计收益
```

---

#### **1.2.3 PFAccessor（指标计算）**

```python
import vectorbt as vbt

# SMA（简单移动平均线）
sma = vbt.MA.run(close, window=20)      # 20日均线
sma.ma                                    # 均线值

# RSI（相对强弱指标）
rsi = vbt.RSI.run(close, window=14)     # 14日RSI
rsi.rsi                                   # RSI值

# MACD
macd = vbt.MACD.run(close)
macd.macd                                 # MACD线
macd.signal                               # 信号线
macd.hist                                 # 柱状图

# Bollinger Bands（布林带）
bb = vbt.BBANDS.run(close, window=20, alpha=2)
bb.upper                                  # 上轨
bb.middle                                 # 中轨
bb.lower                                  # 下轨

# ATR（平均真实波幅）
atr = vbt.ATR.run(high, low, close, window=14)
atr.atr                                   # ATR值
```

---

#### **1.2.4 信号生成**

```python
# 交叉信号
trend = vbt.MA.run(close, 20).ma         # 20日均线
trend_long = vbt.MA.run(close, 50).ma    # 50日均线

# 金叉买入信号
cross_up = vbt.signals.trend_up(trend, trend_long)

# 死叉卖出信号
cross_down = vbt.signals.trend_down(trend, trend_long)

# 百分比变化信号
entries = vbt.ohlcv.perc_change(close) < -0.05   # 下跌5%买入
exits = vbt.ohlcv.perc_change(close) > 0.1       # 上涨10%卖出

# 布林带突破
entries = close < bb.lower               # 触及下轨买入
exits = close > bb.upper                 # 触及上轨卖出
```

---

#### **1.2.5 回测分析**

```python
# 获取回测统计
stats = pf.stats()
print(stats)

# 获取特定指标
metrics = {
    '总收益率': pf.total_return(),
    '年化收益率': pf.annualized_return(),
    '最大回撤': pf.max_drawdown(),
    '夏普比率': pf.sharpe_ratio(),
    '胜敗率': pf.win_rate(),
    '盈利次数': pf.win_count(),
    '亏损次数': pf.loss_count(),
    '平均盈利': pf.avg_win(),
    '平均亏损': pf.avg_loss(),
    '盈亏比': pf.profit_factor(),
    '交易次数': pf.trade_count(),
    '持仓天数': pf.duration().mean()
}

# 可视化
pf.plot()
# 图表包括：
# - 价格与持仓状态
# - 资金曲线
# - 回撤曲线
# - 月度收益热力图
```

**支持的统计指标**：
- `total_return`: 总收益率
- `annualized_return`: 年化收益率
- `max_drawdown`: 最大回撤
- `sharpe_ratio`: 夏普比率
- `sortino_ratio`: 索提诺比率
- `calmar_ratio`: Calmar比率
- `win_rate`: 胜率
- `profit_factor`: 盈亏比
- `expectancy`: 期望值
- `trade_count`: 交易次数
- `duration`: 持仓周期

---

#### **1.2.6 参数优化**

```python
import numpy as np

# 定义参数范围
param_product = vbt.utils.params.create_param_product(
    (range(5, 30), range(10, 50), range(20, 100)),  # 三个参数的范围
    names=['fast_window', 'slow_window', 'exit_window']
)

# 批量回测
pf = vbt.Portfolio.from_signals(
    close,
    entries=entries,
    exits=exits,
    init_cash=100000,
    param_product=param_product
)

# 找到最优参数
best_idx = pf.sharpe_ratio().idxmax()
best_params = param_product.loc[best_idx]
```

---

#### **1.2.7 多标的回测**

```python
# 假设有多个股票的数据
data = {
    '000001.SZ': price_df1,
    '000002.SZ': price_df2,
    '600000.SH': price_df3
}

# 批量回测多个股票
for symbol, prices in data.items():
    pf = vbt.Portfolio.from_signals(
        close=prices['close'],
        entries=signals[symbol],
        init_cash=100000
    )
    print(f"{symbol}: {pf.total_return():.2%}")
```

---

### 1.4 VectorBT 在本项目中的使用场景

#### **场景1：策略回测**
```python
from src.strategy.continuous_decline import ContinuousDeclineStrategy
from src.execution.vectorbt_backtester import VectorBTBacktester

# 初始化策略
strategy = ContinuousDeclineStrategy(params)

# 初始化回测器
backtester = VectorBTBacktester(strategy)

# 运行回测
results = backtester.run(
    start_date='2020-01-01',
    end_date='2023-12-31',
    symbols=['000001.SZ', '600000.SH']
)

# 分析结果
backtester.analyze(results)
```

#### **场景2：快速公式回测**
```python
# 直接在研究中使用（适用于快速验证想法）
import vectorbt as vbt

# 加载数据
price_data = ...  # 获取股票数据
close = price_data['close']

# 生成信号（下跌8天连续）
def has_consecutive_decline(prices, days=8):
    """检查是否连续下跌N天"""
    returns = prices.pct_change()
    return (returns < 0).rolling(days).sum() == days

# 生成买卖信号
entries = has_consecutive_decline(close, days=8)
exits = vbt.signals.generate_random_exits(entries, n=1)  # 简单退出策略

# 回测
pf = vbt.Portfolio.from_signals(
    close=close,
    entries=entries,
    exits=exits,
    init_cash=1000000
)

# 获取结果
print(pf.stats())
pf.plot()
```

---

## 二、vn.py（实盘交易框架）

### 2.1 框架概述

vn.py是一个开源的Python量化交易框架，主要用于实盘交易。它提供了统一的API接口，支持多个交易网关（CTP、XTP、IB、富途等）。

### 2.2 核心模块

#### **2.2.1 Engine（引擎）**

```python
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

# 创建事件引擎
event_engine = EventEngine()

# 创建主引擎
main_engine = MainEngine(event_engine)

# 启动图形界面（可选）
qapp = create_qapp()
main_window = MainWindow(main_engine, event_engine)
main_window.showMaximized()
qapp.exec()
```

---

#### **2.2.2 CTA策略模块**

```python
from vnpy.trader.object import BarData
from vnpy.app.cta_strategy import CtaTemplate, BarGenerator, ArrayManager

class MyStrategy(CtaTemplate):
    """CTA策略模板"""

    author = "Your Name"

    # 策略参数
    fast_window = 10
    slow_window = 20

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_init(self):
        """策略初始化"""
        self.write_log("策略初始化")
        self.load_bar(10)  # 加载10天历史数据

    def on_start(self):
        """启动策略"""
        self.write_log("策略启动")

    def on_stop(self):
        """停止策略"""
        self.write_log("策略停止")

    def on_tick(self, tick):
        """收到Tick数据"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """收到K线数据"""
        self.am.update_bar(bar)

        if not self.am.inited:
            return

        # 计算指标
        fast_ma = self.am.sma(self.fast_window)
        slow_ma = self.am.sma(self.slow_window)

        # 生成信号
        if fast_ma > slow_ma and self.pos == 0:
            self.buy(bar.close_price, 100)

        elif fast_ma < slow_ma and self.pos > 0:
            self.sell(bar.close_price, self.pos)

    def on_order(self, order):
        """收到订单回报"""
        pass

    def on_trade(self, trade):
        """收到成交回报"""
        self.put_event()

    def on_stop_order(self, stop_order):
        """收到止损单回报"""
        pass
```

**关键方法**：
- `on_init()`: 策略初始化，加载历史数据
- `on_start()`: 策略启动
- `on_stop()`: 策略停止
- `on_tick()`: 收到Tick数据
- `on_bar()`: 收到K线数据（核心）
- `on_order()`: 订单回报
- `on_trade()`: 成交回报
- `buy()`: 买入
- `sell()`: 卖出
- `short()`: 卖出开仓（做空）
- `cover()`: 买入平仓（平空）

---

#### **2.2.3 BarGenerator（K线合成）**

```python
from vnpy.trader.object import TickData
from vnpy.app.cta_strategy import BarGenerator


class MyStrategy(CtaTemplate):
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 创建一个BarGenerator
        # 参数：
        # - on_bar: K线回调函数
        # - window: 窗口大小（分钟）
        # - on_window_bar: 窗口K线回调
        self.bg = BarGenerator(self.on_bar, 60, self.on_hour_bar)

    def on_tick(self, tick: TickData):
        """收到Tick"""
        # 将Tick数据更新到BarGenerator
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """收到1分钟K线"""
        # 将1分钟K线更新到BarGenerator
        self.bg.update_bar(bar)

    def on_hour_bar(self, bar: BarData):
        """收到1小时K线（由BarGenerator合成）"""
        pass
```

**支持的周期**：
- 1分钟、5分钟、15分钟、30分钟、60分钟
- 日K、周K

---

#### **2.2.4 ArrayManager（指标计算）**

```python
from vnpy.app.cta_strategy import ArrayManager


class MyStrategy(CtaTemplate):
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.am = ArrayManager(size=100)  # 保留100个数据点

    def on_bar(self, bar: BarData):
        """收到K线"""
        # 更新ArrayManager
        self.am.update_bar(bar)

        if not self.am.inited:
            return  # 数据不足，不执行策略

        # 技术指标计算
        sma = self.am.sma(20)                          # 简单移动平均线
        ema = self.am.ema(20)                          # 指数移动平均线
        std = self.am.std(20)                          # 标准差
        rsi = self.am.rsi(14)                          # RSI
        macd = self.am.macd()                          # MACD
        cci = self.am.cci(20)                          # CCI
        atr = self.am.atr(14)                          # ATR

        highest = self.am.highest(20)                  # 最高价
        lowest = self.am.lowest(20)                    # 最低价

        # 判断趋势
        if self.am.close[-1] > sma:
            # 当前价在均线上方，多头趋势
            pass
```

**常用指标**：
- `sma(n)`: 简单移动平均线
- `ema(n)`: 指数移动平均线
- `rsi(n)`: RSI指标
- `macd()`: MACD指标（返回快慢线、柱状图）
- `atr(n)`: ATR指标
- `std(n)`: 标准差
- `cci(n)`: CCI商品通道指标
- `highest(n)`: n周期最高价
- `lowest(n)`: n周期最低价

---

#### **2.2.5 Datafeed（数据服务）**

```python
from vnpy.trader.engine import MainEngine
from vnpy.gateway.ctp import CtpGateway
from vnpy.app.datafeed import DatafeedApp

# 添加数据服务
main_engine.add_app(DatafeedApp)

# 获取历史数据
req = HistoryRequest(
    symbol="au2406",
    exchange=Exchange.SHFE,
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31),
    interval=Interval.MINUTE
)

# 查询历史数据
datafeed = main_engine.get_app(DatafeedApp.app_name)
historical_data = datafeed.query_bar_history(req)
```

---

#### **2.2.6 交易网关（Gateway）**

vn.py支持多种交易接口：

```python
from vnpy.trader.engine import MainEngine
from vnpy.gateway.ctp import CtpGateway
from vnpy.gateway.xtp import XtpGateway
from vnpy.gateway.ib import IbGateway
from vnpy.gateway.futu import FutuGateway

# CTP期货接口
main_engine.add_gateway(CtpGateway)

# XTP股票接口（量化私募）
main_engine.add_gateway(XtpGateway)

# 富途牛牛（港股、美股）
main_engine.add_gateway(FutuGateway)

# Interactive Brokers（全球）
main_engine.add_gateway(IbGateway)
```

**各网关配置**：
- `CtpGateway`: 国内期货（仿真/实盘）
- `XtpGateway`: A股（需要XTP账号）
- `FutuGateway`: 港股、美股（富途牛牛）
- `IbGateway`: 全球市场（IBKR）

---

### 2.3 vn.py 在本项目中的使用场景

#### **场景1：实盘交易**

```python
from vnpy.app.cta_strategy import CtaApp
from vnpy.trader.engine import MainEngine
from src.strategy.continuous_decline_vnpy import ContinuousDeclineStrategy

# 创建引擎
main_engine = MainEngine()

# 添加CTA模块
cta_engine = main_engine.add_app(CtaApp)

# 初始化策略
setting = {
    "decline_days_threshold": 8,
    "market_cap_threshold": 1000000000,
    "decline_percent_per_layer": 0.10,
    "position_percent_per_layer": 0.10,
    "max_layers": 10
}

cta_engine.init_strategy(
    class_name="ContinuousDeclineStrategy",
    strategy_name="continuous_decline_01",
    vt_symbol="600000.SH",
    setting=setting
)

# 启动策略
cta_engine.start_strategy("continuous_decline_01")
```

#### **场景2：数据获取**

vn.py提供统一的数据接口，可以从多个数据源获取数据：

```python
from vnpy.app.datafeed import DatafeedApp
from vnpy.trader.object import HistoryRequest, Interval
from vnpy.trader.constant import Exchange
from datetime import datetime

# 获取10天的日线数据
req = HistoryRequest(
    symbol="600000",
    exchange=Exchange.SSE,  # 上交所
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 15),
    interval=Interval.DAILY  # 日线
)

# 查询历史数据
app = main_engine.get_app(DatafeedApp.app_name)
bars = app.query_bar_history(req)

# bars是BarData列表
for bar in bars:
    print(f"{bar.datetime} - O:{bar.open_price} H:{bar.high_price} L:{bar.low_price} C:{bar.close_price}")
```

---

## 三、VectorBT 和 vn.py 的对比

### 3.1 功能对比

| 功能 | VectorBT | vn.py |
|-----|---------|-------|
| **回测速度** | ⭐⭐⭐⭐⭐（向量计算，极快） | ⭐⭐⭐（事件驱动，较慢） |
| **回测精度** | ⭐⭐⭐（依赖数据质量） | ⭐⭐⭐⭐⭐（精细模拟） |
| **实盘交易** | ❌ 不支持 | ✅ 支持多种网关 |
| **多标的回测** | ✅ 支持 | ⚠️ 有限支持 |
| **参数优化** | ✅ 内置优化 | ⚠️ 需自行实现 |
| **指标库** | ✅ 非常完善 | ✅ 基本指标 |
| **事件模拟** | ❌ 简化处理 | ✅ 完整模拟 |
| **图形展示** | ✅ 内置图形 | ⚠️ 依赖外部库 |
| **学习曲线** | ⭐⭐（中等） | ⭐⭐⭐⭐（较陡） |

### 3.2 适用场景

**VectorBT 适用于**：
- 快速策略验证
- 大规模参数优化
- 学术研究
- 多标的批量回测
- 早期策略开发

**vn.py 适用于**：
- 实盘交易
- 高精度回测（考虑滑点、手续费等细节）
- 复杂事件驱动策略
- 需要对接交易所API
- 生产环境部署

### 3.3 本项目分工

基于两个框架的特点，本项目建议：

**回测阶段（策略开发）**：
- 使用 **VectorBT** 进行快速回测
- 批量测试多个股票
- 参数优化
- 性能分析

**实盘阶段（生产环境）**：
- 使用 **vn.py** 的 CTA 引擎
- 对接实盘交易网关（XTP、CTP等）
- 监控和风险管理
- 订单管理

---

## 四、结合使用的架构

### 4.1 数据流

```
┌─────────────────┐
│   历史数据       │
│  (CSV/数据库)    │
└────────┬────────┘
         │
         ▼
┌────────────────────────┐
│  VectorBT回测引擎      │
│  - 验证策略逻辑        │
│  - 参数优化            │
│  - 性能评估            │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  策略验证通过？        │
│  - 是 → 进入实盘       │
│  - 否 → 调整参数       │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│   vn.py CTA引擎        │
│  - 实盘交易            │
│  - 风险管理            │
│  - 订单执行            │
└────────────────────────┘
```

### 4.2 核心优势

- **快速迭代**：VectorBT快速验证策略想法
- **平滑过渡**：验证通过后，可以轻松迁移到vn.py实盘
- **统一接口**：两个框架都使用Pandas数据结构，易于转换
- **完整闭环**：从研究到生产，全程Python生态

---

## 五、环境要求

### 5.1 VectorBT 安装

```bash
# 基础安装（推荐）
pip install -U vectorbt

# 或完整安装（含所有依赖）
pip install -U "vectorbt[full]"

# 安装特定版本
pip install vectorbt==0.26.0
```

**依赖**：
- Python 3.7+
- NumPy (1.17.3+)
- Pandas (0.25.3+)
- Scipy (1.3.0+)
- Matplotlib (3.1.0+)

### 5.2 vn.py 安装

```bash
# 完整安装（推荐）
pip install vnpy

# 或从源码安装
git clone https://github.com/vnpy/vnpy.git
cd vnpy
bash install.sh  # Linux/macOS
# 或 install.bat  # Windows

# 安装特定网关（按需）
pip install vnpy_ctp      # CTP期货网关
pip install vnpy_xtp      # XTP美股网关
pip install vnpy_futu     # 富途网关
```

**依赖**（Linux环境）：
```bash
# Ubuntu/Debian
sudo apt-get install build-essential
sudo apt-get install python3-dev

# CentOS
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

**注意**：vn.py在Windows和部分Linux发行版上编译较容易，Termux上可能困难。

---

## 六、学习资源

### VectorBT
- **官方文档**: https://vectorbt.dev
- **GitHub**: https://github.com/polakowo/vectorbt
- **示例**: https://vectorbt.dev/docs/index.html

### vn.py
- **官方文档**: https://www.vnpy.com
- **GitHub**: https://github.com/vnpy/vnpy
- **社区**: https://www.vnpy.com/forum
- **示例策略**: https://github.com/vnpy/vnpy/tree/master/examples

---

**文档版本**: v1.0
**最后更新**: 2025-01-18
