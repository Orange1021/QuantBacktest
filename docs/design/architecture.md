# 持续下跌策略 - 系统架构设计文档

## 1. 项目概述

### 1.1 策略描述
本策略是一个均值回归型抄底策略，核心逻辑：
- **选股条件**：连续下跌8天且市值≥10亿
- **入场规则**：每下跌10%加仓10%（基于初始仓位）
- **出场规则**：上涨后持仓，直到第一次出现下跌即清仓

### 1.2 技术栈
- **回测引擎**：VectorBT
- **实盘交易**：vn.py
- **数据处理**：Pandas, NumPy
- **类型提示**：Python 3.8+
- **配置管理**：YAML

---

## 2. 系统架构

### 2.1 核心模块图

```
┌─────────────────────────────────────────────────────────────┐
│                        策略入口层                            │
│                   StrategyRunner / Backtester                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      策略管理层                              │
│               ContinuousDeclineStrategy                       │
└──────────┬──────────────────────┬───────────────────────────┘
           │                      │
┌──────────▼──────────┐  ┌────────▼──────────┐
│   选股过滤模块       │  │   仓位管理模块     │
│  StockFilter        │  │  PositionManager   │
└─────────────────────┘  └────────────────────┘
           │                      │
┌──────────▼──────────┐  ┌────────▼──────────┐
│   信号生成模块       │  │   风险控制模块     │
│  SignalGenerator    │  │  RiskManager       │
└─────────────────────┘  └────────────────────┘
           │                      │
┌──────────┴──────────┬─────────┴──────────┐
│                     │                     │
┌▼───────────────────▼┐  ┌────────────────▼┐
│   数据获取模块       │  │   执行引擎       │
│  DataProvider       │  │  ExecutionEngine │
└─────────────────────┘  └─────────────────┘
```

### 2.2 模块职责划分

#### 2.2.1 Core Layer（核心层）
- **filter**: 股票筛选逻辑
- **position**: 仓位管理
- **risk**: 风险控制

#### 2.2.2 Strategy Layer（策略层）
- **ContinuousDeclineStrategy**: 主策略类
- **StockSelector**: 股票选择器
- **SignalGenerator**: 信号生成器

#### 2.2.3 Data Layer（数据层）
- **DataProvider**: 数据获取统一接口
- **MarketData**: 市场数据模型

#### 2.2.4 Execution Layer（执行层）
- **VectorBTBacktester**: VectorBT回测引擎
- **VnPyExecutor**: vn.py实盘执行引擎

#### 2.2.5 Utils Layer（工具层）
- **Logger**: 日志管理
- **ConfigManager**: 配置管理
- **PerformanceMetrics**: 绩效计算

---

## 3. 核心类设计

### 3.1 核心基类

#### 3.1.1 BaseStrategy（策略基类）
```python
class BaseStrategy(ABC):
    """策略基类，定义通用接口"""

    @abstractmethod
    def on_init(self) -> None:
        """策略初始化"""
        pass

    @abstractmethod
    def on_bar(self, bar: BarData) -> None:
        """K线数据处理"""
        pass

    @abstractmethod
    def on_signal(self, signal: Signal) -> None:
        """信号处理"""
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> PositionData:
        """获取仓位"""
        pass
```

---

### 3.2 策略层类

#### 3.2.1 ContinuousDeclineStrategy
**职责**：主策略类，协调各个模块

**核心方法**：
```python
class ContinuousDeclineStrategy(BaseStrategy):
    """持续下跌策略主类"""

    def __init__(
        self,
        stock_filter: StockFilter,
        position_manager: PositionManager,
        signal_generator: SignalGenerator,
        risk_manager: RiskManager
    ):
        self.stock_filter = stock_filter
        self.position_manager = position_manager
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.active_positions: Dict[str, PositionData] = {}

    def on_init(self) -> None:
        """初始化策略参数"""
        pass

    def on_bar(self, bar: BarData) -> None:
        """
        主循环逻辑：
        1. 选股过滤
        2. 生成信号
        3. 风险控制
        4. 执行交易
        """
        pass

    def scan_stocks(self, date: datetime) -> List[str]:
        """扫描符合条件的股票"""
        pass

    def monitor_positions(self, bar: BarData) -> None:
        """监控持仓，处理出场逻辑"""
        pass
```

**关键属性**：
- `decline_days_threshold`: 下跌天数阈值（默认8天）
- `market_cap_threshold`: 市值阈值（默认10亿）
- `decline_percent_per_layer`: 每层下跌百分比（默认10%）
- `position_percent_per_layer`: 每层加仓百分比（默认10%）

#### 3.2.2 StockFilter（股票筛选器）
**职责**：筛选符合条件的股票

```python
class StockFilter:
    """股票筛选器"""

    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider

    def filter_by_decline(
        self,
        symbols: List[str],
        end_date: datetime,
        decline_days: int = 8
    ) -> List[str]:
        """
        筛选连续下跌N天的股票
        - 输入：股票列表、结束日期、下跌天数
        - 输出：符合条件的股票代码列表
        """
        pass

    def filter_by_market_cap(
        self,
        symbols: List[str],
        min_market_cap: float = 1e9
    ) -> List[str]:
        """
        筛选市值不小于阈值的股票
        - 输入：股票列表、最小市值（单位：元）
        - 输出：符合条件的股票代码列表
        """
        pass

    def get_eligible_stocks(
        self,
        date: datetime
    ) -> List[str]:
        """
        综合筛选：连续下跌 + 市值要求
        - 返回同时满足两个条件的股票
        """
        pass
```

#### 3.2.3 SignalGenerator（信号生成器）
**职责**：生成交易信号

```python
class Signal:
    """交易信号数据结构"""
    symbol: str
    signal_type: SignalType  # BUY / SELL
    price: float
    quantity: int
    timestamp: datetime
    metadata: Dict[str, Any]

class SignalGenerator:
    """信号生成器"""

    def __init__(self, params: SignalParams):
        self.params = params
        self.decline_tracker: Dict[str, DeclineTracker] = {}

    def generate_buy_signal(
        self,
        symbol: str,
        current_price: float,
        entry_price: float
    ) -> Optional[Signal]:
        """
        生成买入信号
        - 检查是否触发加仓条件（下跌10%）
        - 计算加仓数量
        """
        pass

    def generate_sell_signal(
        self,
        symbol: str,
        current_price: float,
        last_price: float
    ) -> Optional[Signal]:
        """
        生成卖出信号
        - 逻辑：上涨后第一次下跌即清仓
        - 需要在持仓中追踪"是否上涨过"状态
        """
        pass

    def update_price_tracker(self, symbol: str, price: float) -> None:
        """更新价格追踪器"""
        pass
```

**关键逻辑**：
- 使用 `decline_tracker` 追踪每只股票的下跌层数和基准价格
- 持仓中需要记录：`has_risen`（是否上涨过）状态

#### 3.2.4 PositionManager（仓位管理器）
**职责**：管理仓位和资金

```python
class PositionData:
    """持仓数据结构"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    has_risen: bool  # 关键字段：是否上涨过
    entry_date: datetime
    layer_count: int  # 加仓层数
    initial_position_size: float  # 初始仓位大小

class PositionManager:
    """仓位管理器"""

    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        self.available_capital = total_capital
        self.positions: Dict[str, PositionData] = {}

    def calculate_position_size(
        self,
        symbol: str,
        current_price: float,
        layer: int
    ) -> int:
        """
        计算加仓数量
        - 基于初始仓位的百分比
        - 考虑可用资金
        """
        pass

    def add_position(self, symbol: str, signal: Signal) -> None:
        """增加持仓"""
        pass

    def remove_position(self, symbol: str) -> None:
        """清仓"""
        pass

    def update_position_price(self, symbol: str, price: float) -> None:
        """更新持仓价格"""
        pass

    def get_position(self, symbol: str) -> Optional[PositionData]:
        """获取持仓信息"""
        pass

    def get_total_position_value(self) -> float:
        """获取总持仓市值"""
        pass
```

---

### 3.3 数据层类

#### 3.3.1 DataProvider（数据提供器）
```python
class DataProvider(ABC):
    """数据提供器基类"""

    @abstractmethod
    def get_daily_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """获取日K数据"""
        pass

    @abstractmethod
    def get_market_cap(
        self,
        symbols: List[str],
        date: datetime
    ) -> pd.Series:
        """获取市值数据"""
        pass

    @abstractmethod
    def get_stock_universe(self, date: datetime) -> List[str]:
        """获取股票池"""
        pass
```

#### 3.3.2 LocalDataProvider（本地数据）
```python
class LocalDataProvider(DataProvider):
    """本地数据提供器（CSV/Parquet）"""
    pass
```

#### 3.3.3 VnPyDataProvider（vn.py数据）
```python
class VnPyDataProvider(DataProvider):
    """vn.py数据接口"""
    pass
```

#### 3.3.4 TushareDataProvider（Tushare数据）
```python
class TushareDataProvider(DataProvider):
    """Tushare数据接口"""
    pass
```

---

### 3.4 风险控制类

#### 3.4.1 RiskManager（风险管理器）
```python
class RiskManager:
    """风险管理器"""

    def __init__(self, risk_params: RiskParams):
        self.params = risk_params

    def check_position_limit(self, symbol: str) -> bool:
        """检查单票持仓限制"""
        pass

    def check_total_exposure(self) -> bool:
        """检查总仓位暴露"""
        pass

    def check_daily_loss_limit(self, daily_pnl: float) -> bool:
        """检查单日亏损限制"""
        pass

    def check_stop_loss(
        self,
        symbol: str,
        current_price: float,
        entry_price: float
    ) -> bool:
        """检查止损"""
        pass
```

#### 3.4.2 RiskParams（风险参数）
```yaml
single_position_limit: 0.3      # 单票最大仓位30%
total_position_limit: 0.8       # 总仓位最大80%
max_layers: 5                   # 最大加仓层数
daily_loss_limit: 0.05          # 单日最大亏损5%
stop_loss_percent: 0.15         # 止损线15%
```

---

### 3.5 执行层类

#### 3.5.1 VectorBTBacktester（VectorBT回测器）
```python
class VectorBTBacktester:
    """VectorBT回测引擎封装"""

    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: List[str]
    ) -> BacktestResult:
        """运行回测"""
        pass

    def analyze_results(self, results: BacktestResult) -> PerformanceMetrics:
        """分析回测结果"""
        pass
```

#### 3.5.2 VnPyExecutor（vn.py实盘执行器）
```python
class VnPyExecutor:
    """vn.py实盘执行器"""

    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy

    def execute(self, signal: Signal) -> Order:
        """执行交易信号"""
        pass

    def get_order_status(self, order_id: str) -> OrderStatus:
        """查询订单状态"""
        pass
```

---

### 3.6 数据模型类

#### 3.6.1 BarData（K线数据）
```python
@dataclass
class BarData:
    symbol: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
```

#### 3.6.2 Order（订单）
```python
@dataclass
class Order:
    order_id: str
    symbol: str
    order_type: OrderType
    price: float
    quantity: int
    status: OrderStatus
    create_time: datetime
```

---

### 3.7 工具类

#### 3.7.1 ConfigManager（配置管理器）
```python
class ConfigManager:
    """配置管理器"""

    @staticmethod
    def load_strategy_config(path: str) -> StrategyConfig:
        """加载策略配置"""
        pass

    @staticmethod
    def load_market_config(path: str) -> MarketConfig:
        """加载市场配置"""
        pass
```

#### 3.7.2 Logger（日志管理器）
```python
class Logger:
    """日志管理器"""

    def __init__(self, name: str):
        pass

    def info(self, msg: str):
        pass

    def error(self, msg: str):
        pass

    def debug(self, msg: str):
        pass
```

#### 3.7.3 PerformanceMetrics（绩效计算）
```python
class PerformanceMetrics:
    """绩效指标计算器"""

    def __init__(self, returns: pd.Series):
        self.returns = returns

    def calculate_sharpe_ratio(self) -> float:
        """计算夏普比率"""
        pass

    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        pass

    def calculate_win_rate(self) -> float:
        """计算胜率"""
        pass

    def generate_report(self) -> PerformanceReport:
        """生成绩效报告"""
        pass
```

---

## 4. 核心业务流程

### 4.1 日级别回测流程

```
开始回测
    │
    ├─► 1. 初始化策略
    │   - 加载配置
    │   - 初始化各个模块
    │
    ├─► 2. 每日循环（遍历日期）
    │   │
    │   ├─► 2.1 选股扫描（开盘前）
    │   │   - StockFilter.get_eligible_stocks()
    │   │   - 返回候选股票列表
    │   │
    │   ├─► 2.2 遍历候选股票
    │   │   │
    │   │   ├─► 2.2.1 生成买入信号
    │   │   │   - SignalGenerator.generate_buy_signal()
    │   │   │   - 检查是否触发加仓
    │   │   │
    │   │   └─► 2.2.2 执行买入
    │   │       - 风险控制检查
    │   │       - 执行交易
    │   │
    │   └─► 2.3 监控现有持仓
    │       │
    │       ├─► 2.3.1 生成卖出信号
    │       │   - SignalGenerator.generate_sell_signal()
    │       │   - 逻辑：上涨后首次下跌
    │       │
    │       └─► 2.3.2 执行卖出
    │           - 清仓
    │
    └─► 3. 绩效分析
        - 计算各项指标
        - 生成报告
```

### 4.2 买入逻辑（加仓）

```python
# 伪代码
for symbol in eligible_stocks:
    current_price = get_price(symbol)
    position = position_manager.get_position(symbol)

    if position is None:
        # 首次建仓
        if is_first_entry(current_price, symbol):
            signal = generate_buy_signal(symbol, layer=0)
            execute(signal)
    else:
        # 检查是否触发加仓
        entry_price = position.avg_price
        decline_percent = (entry_price - current_price) / entry_price

        if decline_percent >= 0.1 * (position.layer_count + 1):
            # 下跌超过10%，加仓
            signal = generate_buy_signal(symbol, layer=position.layer_count + 1)
            execute(signal)
```

### 4.3 卖出逻辑（出场）

```python
# 伪代码
for symbol in active_positions:
    current_price = get_price(symbol)
    position = position_manager.get_position(symbol)

    if not position.has_risen:
        # 还没上涨过
        if current_price > position.avg_price:
            # 首次上涨，标记状态
            position.has_risen = True
    else:
        # 已经上涨过，检查是否下跌
        if current_price < position.current_price:
            # 第一次下跌，清仓
            signal = generate_sell_signal(symbol)
            execute(signal)
            position_manager.remove_position(symbol)

    # 更新当前价格
    position_manager.update_position_price(symbol, current_price)
```

---

## 5. 配置设计

### 5.1 策略配置文件

路径：`configs/strategy/continuous_decline.yaml`

```yaml
strategy:
  name: "ContinuousDeclineStrategy"
  description: "持续下跌抄底策略"

  # 选股参数
  filter_params:
    decline_days_threshold: 8          # 连续下跌天数
    market_cap_threshold: 1000000000   # 最小市值（10亿）
    stock_universe: "A_SHARE"          # 股票池：A股

  # 入场参数
  entry_params:
    decline_percent_per_layer: 0.10    # 每层下跌10%
    position_percent_per_layer: 0.10   # 每层加仓10%
    max_layers: 10                     # 最大加仓层数

  # 出场参数
  exit_params:
    exit_on_first_decline: true        # 上涨后首次下跌即清仓

  # 风险控制
  risk_params:
    single_position_limit: 0.30        # 单票最大仓位30%
    total_position_limit: 0.80         # 总仓位最大80%
    stop_loss_percent: 0.15            # 止损线15%
    daily_loss_limit: 0.05             # 单日最大亏损5%

  # 资金参数
  capital_params:
    initial_capital: 1000000           # 初始资金100万
    commission_rate: 0.0003            # 手续费万分之三
    slippage: 0.001                    # 滑点0.1%
```

### 5.2 市场配置文件

路径：`configs/market/market.yaml`

```yaml
market:
  trading_calendar: "china_stock"      # 交易日历
  trading_hours:
    open: "09:30"
    close: "15:00"

  limit:
    price_limit: 0.10                  # 涨跌幅限制10%
    min_order_value: 100               # 最小订单金额

  data:
    provider: "tushare"                 # 数据提供商
    price_field: "close"               # 使用收盘价
    adjust_type: "qfq"                 # 前复权
```

---

## 6. 数据流设计

### 6.1 数据表结构

#### 6.1.1 日K线数据
```sql
CREATE TABLE daily_bars (
    symbol VARCHAR(20),
    date DATE,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume BIGINT,
    PRIMARY KEY (symbol, date)
);
```

#### 6.1.2 市值数据
```sql
CREATE TABLE market_cap (
    symbol VARCHAR(20),
    date DATE,
    total_market_cap DECIMAL(20, 2),  -- 总市值（元）
    float_market_cap DECIMAL(20, 2),  -- 流通市值（元）
    PRIMARY KEY (symbol, date)
);
```

#### 6.1.3 交易记录
```sql
CREATE TABLE trades (
    trade_id VARCHAR(50),
    symbol VARCHAR(20),
    order_type VARCHAR(10),          -- BUY/SELL
    price DECIMAL(10, 2),
    quantity INT,
    timestamp DATETIME,
    strategy VARCHAR(50),
    layer INT,                        -- 加仓层数
    PRIMARY KEY (trade_id)
);
```

#### 6.1.4 持仓记录
```sql
CREATE TABLE positions (
    symbol VARCHAR(20),
    date DATE,
    quantity INT,
    avg_price DECIMAL(10, 2),
    market_value DECIMAL(20, 2),
    layer_count INT,                  -- 加仓层数
    has_risen BOOLEAN,                -- 是否上涨过
    PRIMARY KEY (symbol, date)
);
```

---

## 7. 异常处理

### 7.1 可预见的异常场景

1. **数据缺失**
   - 某些股票数据不完整
   - 处理：跳过该股票，记录日志

2. **交易异常**
   - 订单被拒绝（价格限制、流动性等）
   - 处理：重试或跳过，记录日志

3. **风险控制触发**
   - 达到单日亏损限制
   - 处理：暂停交易，发送告警

4. **计算错误**
   - 价格数据异常（如价格为0）
   - 处理：使用异常值检测，跳过该数据点

### 7.2 日志记录规范

- **INFO**: 正常交易流程
- **WARNING**: 非关键异常（数据缺失等）
- **ERROR**: 交易失败、风险触发
- **DEBUG**: 详细计算过程

---

## 8. 扩展性设计

### 8.1 策略变种支持

可以方便地扩展出以下变种策略：

1. **动态下跌阈值**
   - 根据波动率调整下跌百分比阈值
   - 实现：继承SignalGenerator，重写生成逻辑

2. **分批出场**
   - 不是一次性清仓，而是分批卖出
   - 实现：修改SignalGenerator的出场逻辑

3. **多因子选股**
   - 在市值过滤基础上增加PE、PB等因子
   - 实现：扩展StockFilter类

4. **指数对冲**
   - 对冲系统性风险
   - 实现：在PositionManager中增加对冲仓位管理

### 8.2 多策略组合

未来可以支持多策略并行：

```python
class PortfolioStrategy:
    """组合策略"""

    def __init__(self, strategies: List[BaseStrategy]):
        self.strategies = strategies

    def on_bar(self, bar: BarData):
        for strategy in self.strategies:
            strategy.on_bar(bar)
```

---

## 9. 测试策略

### 9.1 单元测试（Unit Tests）

路径：`tests/unit/`

1. **test_stock_filter.py**
   - 测试连续下跌天数计算
   - 测试市值过滤

2. **test_signal_generator.py**
   - 测试买入信号生成
   - 测试卖出信号生成
   - 测试加仓逻辑

3. **test_position_manager.py**
   - 测试仓位计算
   - 测试资金分配

### 9.2 集成测试（Integration Tests）

路径：`tests/integration/`

1. **test_strategy_flow.py**
   - 测试完整策略流程
   - 使用模拟数据

2. **test_vectorbt_integration.py**
   - 测试VectorBT回测集成

### 9.3 回归测试

- 使用历史已知结果验证策略逻辑
- 检测代码变更是否影响策略表现

---

## 10. 部署和运行

### 10.1 回测模式

```bash
# 运行回测
python scripts/run_backtest.py \
  --config configs/strategy/continuous_decline.yaml \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --symbols A_SHARE
```

### 10.2 实盘模式

```bash
# 运行实盘
python scripts/run_live.py \
  --config configs/strategy/continuous_decline.yaml \
  --gateway ctp \
  --account account.yaml
```

### 10.3 监控和告警

- 每日盈亏监控
- 风险指标监控
- 异常交易告警
- 邮件/钉钉通知

---

## 11. 待确认问题

在编码前需要确认：

1. **数据源**：使用哪个数据提供商？（Tushare/Akshare/本地CSV）
2. **股票池**：全A股还是特定板块？（沪深300/中证500/全市场）
3. **成交价格**：使用收盘价还是VWAP？
4. **加仓基准**：基于初始买入价还是最后一次加仓价？
5. **出场价格**：观察到什么价格时触发"首次下跌"？（收盘价/最低价）
6. **资金规模**：初始资金设定为多少？
7. **手续费**：券商手续费率是多少？
8. **滑点**：是否考虑滑点？滑点比例多少？

---

## 12. 风险提示

本策略属于**均值回归型抄底策略**，存在以下风险：

1. **价值陷阱**：股票持续下跌可能反映基本面恶化
2. **流动性风险**：小市值股票流动性不足
3. **尾部风险**：黑天鹅事件导致持续暴跌
4. **参数敏感**：对下跌阈值、加仓比例敏感

**建议**：
- 设置严格的止损线
- 控制单票仓位
- 分散持仓（多只股票）
- 定期评估策略有效性

---

**文档版本**：v1.0
**创建日期**：2025-01-18
**作者**：Claude Code
