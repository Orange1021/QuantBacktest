# QuantBacktest 量化回测系统项目说明书

## 项目概述

QuantBacktest是一个完整的量化交易回测系统，采用事件驱动架构设计，支持多种数据源、策略类型和分析工具。

## 项目结构

```
QuantBacktest/
├── .gitignore                   # Git忽略文件配置
├── CODE_ISSUES.md               # 代码问题记录
├── PROJECT_SPECIFICATION.md     # 项目说明书
├── README.md                    # 项目说明文档
├── requirements.txt             # 项目依赖文件
├── app.py                       # 应用程序主入口
├── main.py                      # 命令行入口
├── .claude/                     # Claude配置目录
│   └── settings.local.json      # 本地配置
├── config/                       # 配置管理模块
│   ├── config.yaml               # 业务配置文件
│   ├── sizer_config.yaml         # 仓位管理配置
│   ├── settings.py               # 配置读取类
│   └── __init__.py
├── DataManager/                  # 数据管理模块
│   ├── __init__.py
│   ├── feeds/                    # 数据流处理
│   │   ├── __init__.py
│   │   ├── base_feed.py          # 基础数据流类
│   │   ├── lazy_feed.py          # 懒加载数据流
│   │   └── mem_feed.py           # 内存数据流
│   ├── handlers/                 # 数据驱动层
│   │   ├── __init__.py
│   │   └── handler.py            # 数据处理器实现
│   ├── processors/               # 数据处理器
│   │   ├── __init__.py
│   │   ├── adjuster.py           # 数据调整器
│   │   ├── cleaner.py            # 数据清洗器
│   │   ├── merger.py             # 数据合并器
│   │   └── resampler.py          # 数据重采样器
│   ├── schema/                   # 数据结构定义
│   │   ├── __init__.py
│   │   ├── base.py               # 基础数据类
│   │   ├── bar.py                # K线数据类
│   │   ├── constant.py           # 常量定义
│   │   ├── fundamental.py        # 财务数据类
│   │   └── tick.py               # Tick数据类
│   ├── selectors/                # 选股器模块
│   │   ├── __init__.py
│   │   ├── base.py               # 选股器基类
│   │   ├── tushare_selector.py   # Tushare选股器
│   │   └── wencai_selector.py    # 问财选股器
│   ├── sources/                  # 数据源适配器
│   │   ├── __init__.py
│   │   ├── base_source.py        # 数据源基类
│   │   ├── binance.py            # 币安数据源
│   │   ├── local_csv.py          # 本地CSV数据源
│   │   ├── tushare.py            # Tushare数据源
│   │   └── yfinance.py           # Yahoo Finance数据源
│   └── storage/                  # 数据存储模块
│       ├── __init__.py
│       ├── base_store.py         # 存储基类
│       ├── csv_store.py          # CSV存储
│       ├── hdf5_store.py         # HDF5存储
│       ├── influx_store.py       # InfluxDB存储
│       └── mysql_store.py        # MySQL存储
├── Engine/                       # 回测引擎模块
│   ├── __init__.py
│   └── engine.py                 # 回测引擎核心
├── Execution/                    # 撮合执行模块
│   ├── __init__.py
│   ├── base.py                   # 执行器基类
│   └── simulator.py              # 模拟执行器
├── Infrastructure/               # 基础设施模块
│   ├── __init__.py
│   ├── enums.py                  # 枚举定义
│   └── events.py                 # 事件系统定义
├── Portfolio/                    # 投资组合模块
│   ├── __init__.py
│   ├── base.py                   # 投资组合基类
│   ├── portfolio.py              # 投资组合实现
│   └── sizers.py                 # 仓位管理策略
├── Strategies/                   # 策略模块
│   ├── __init__.py
│   ├── base.py                   # 策略基类
│   ├── simple_strategy.py        # 简单策略示例
│   ├── ma_strategy.py            # 移动平均策略
│   └── macd_kdj_strategy.py      # MACD+KDJ策略
├── Analysis/                     # 分析模块
│   ├── __init__.py
│   ├── performance.py            # 绩效分析器
│   ├── plotting.py               # 图表绘制器
│   └── reporting.py              # 报告生成器
├── Test/                         # 测试模块
│   ├── debug_data.py             # 数据调试脚本
│   ├── debug_plotting.py         # 图表调试脚本
│   ├── debug_strategy.py         # 策略调试脚本
│   ├── debug_strategy_signals.py # 策略信号调试脚本
│   ├── simple_wencai_test.py     # 问财简单测试
│   ├── test_complete_analysis.py # 完整分析测试
│   ├── test_comprehensive_integration.py  # 综合集成测试
│   ├── test_engine.py            # 引擎测试
│   ├── test_execution_module.py  # 执行模块测试
│   ├── test_fixes.py             # 修复测试
│   ├── test_main_plotting.py     # 主绘图测试
│   ├── test_new_event_system.py  # 新事件系统测试
│   ├── test_optimized_smoothing.py # 优化平滑测试
│   ├── test_portfolio.py         # 投资组合测试
│   ├── test_refactor.py          # 重构测试
│   ├── test_sawtooth_issue.py    # 锯齿问题测试
│   ├── test_strategy_base.py     # 策略基类测试
│   ├── test_wencai_connection.py # 问财连接测试
│   ├── test_wencai_csv_integration.py  # 问财CSV集成测试
│   └── test_wencai_final.py      # 问财最终测试
└── output/                       # 输出目录（图表、报告）
    └── backtest_20251124_204820/ # 回测结果示例
        ├── backtest_report_*.png # 各类分析图表
        └── report.txt             # 回测报告
```

## 详细模块说明

### 1. 配置管理模块 (config/)

#### config/settings.py
```python
class BacktestConfig:
    """回测配置类"""
    属性:
        - start_date: str        # 回测开始日期
        - end_date: str          # 回测结束日期
        - benchmark: str         # 基准指数
        - initial_capital: float # 初始资金

class DataConfig:
    """数据配置类"""
    属性:
        - csv_root_path: str     # CSV数据根路径
        - cache_path: str        # 缓存路径
        - output_path: str       # 输出路径

class Settings:
    """配置管理主类"""
    方法:
        - __init__(config_path: str = None)
        - get_env(key: str, default: str = None) -> str
        - get_config(key: str, default: Any = None) -> Any
```

### 2. 回测引擎模块 (Engine/)

#### Engine/engine.py
```python
class BacktestEngine:
    """回测引擎核心"""
    
    核心属性：
        - data_handler: BaseDataHandler  # 数据处理器
        - strategy: Any  # 策略实例，实现 IStrategy 接口
        - portfolio: Any  # 投资组合实例
        - execution: Any  # 执行器实例
        - event_queue: Deque[Any]  # 统一事件队列
        - is_running: bool  # 回测运行状态
        - current_time: Optional[datetime]  # 当前回测时间
        - total_events: int  # 总事件数
        - market_events: int  # 行情事件数
        - signal_events: int  # 信号事件数
        - order_events: int  # 订单事件数
        - fill_events: int  # 成交事件数
    
    职责：
    - 维护事件队列和事件循环
    - 协调数据处理器、策略、投资组合和执行器之间的交互
    - 严格按时间顺序处理事件，防止未来函数
    - 提供统一的回测启动和管理接口
    
    核心方法：
        - __init__(data_handler, strategy, portfolio, execution)  # 初始化依赖
        - run()  # 主入口，启动回测
        - _process_queue()  # 处理事件队列
        - _handle_event(event)  # 事件分发处理器
        - _handle_market_event(event)  # 处理行情事件
        - _handle_signal_event(event)  # 处理信号事件
        - _handle_order_event(event)  # 处理订单事件
        - _handle_fill_event(event)  # 处理成交事件
        - _show_progress()  # 显示回测进度
        - _show_statistics()  # 显示统计信息
        - get_status() -> dict  # 获取引擎状态
    
    事件处理流程：
        - MarketEvent → 投资组合更新市值 + 策略处理行情
        - SignalEvent → 投资组合风控 + 订单生成
        - OrderEvent → 执行器撮合 + 成交生成
        - FillEvent → 投资组合更新持仓和资金
```

### 3. 策略抽象层 (Strategies/)

#### Strategies/base.py
```python
class IStrategy(ABC):
    """策略接口，强制实现关键方法"""
    
    @abstractmethod
    def on_market_data(self, event: MarketEvent) -> None:
        """处理行情数据的抽象方法"""
        pass
    
    @abstractmethod  
    def set_event_queue(self, event_queue: deque) -> None:
        """设置事件队列的抽象方法"""
        pass
    
    @classmethod
    def get_selection_query(cls) -> str:
        """定义策略的静态选股条件，返回问财查询语句"""
        return None

class BaseStrategy(IStrategy, ABC):
    """策略抽象基类"""
    
    职责：
    - 标准化输入：所有策略都以相同方式接收行情数据
    - 标准化输出：所有策略都通过统一接口发出信号
    - 数据访问权限：策略通过 DataHandler 访问历史数据，严禁访问未来数据
    - 模板方法模式：确保状态更新和策略逻辑的正确执行顺序
    
    核心属性：
        - data_handler: BaseDataHandler  # 数据处理器
        - event_queue: Optional[deque]   # 事件队列（延迟注入）
        - portfolio: Optional[Any]       # 投资组合引用（延迟注入）
        - is_initialized: bool           # 策略初始化状态
        - current_time: Optional[datetime] # 当前回测时间
        - signals_generated: int         # 生成信号数量
        - market_data_processed: int     # 处理行情数据数量
    
    核心方法：
        - __init__(data_handler)  # 初始化依赖
        - set_event_queue(event_queue)  # 设置事件队列引用
        - set_portfolio(portfolio)  # 设置投资组合引用
        - on_market_data(event) [抽象]  # 处理行情数据
        - send_signal(symbol, direction, strength)  # 发送信号到引擎队列
        - get_latest_bars(symbol, n)  # 获取历史数据
        - get_latest_bar(symbol)  # 获取最新K线
        - get_current_price(symbol)  # 获取当前价格
        - calculate_sma(symbol, period)  # 计算SMA
        - calculate_ema(symbol, period)  # 计算EMA
        - is_price_above_sma(symbol, period)  # 判断价格是否在SMA之上
        - get_price_change_pct(symbol)  # 获取价格变动百分比
        - _update_strategy_state(event)  # 更新策略状态
        - _process_market_data(event)  # 模板方法（引擎应调用此方法）
        - get_strategy_info() -> dict  # 获取策略信息
```

#### Strategies/simple_strategy.py
```python
class SimpleMomentumStrategy(BaseStrategy):
    """简单动量策略示例"""
    
    策略逻辑：
    - 涨幅超过0.3%时买入
    - 跌幅超过0.3%时卖出（如果有持仓）
    
    统计方法：
        - buy_signals: 买入信号数量
        - sell_signals: 卖出信号数量
```

#### Strategies/ma_strategy.py
```python
class MAStrategy(BaseStrategy):
    """移动平均策略"""
    
    策略逻辑：
    - 基于双均线交叉信号
    - 支持自定义短期和长期均线周期
```

#### Strategies/macd_kdj_strategy.py
```python
class MACDKDJStrategy(BaseStrategy):
    """MACD+KDJ组合策略"""
    
    策略逻辑：
    - MACD指标判断趋势方向
    - KDJ指标判断超买超卖
    - 组合信号提高准确性
```

### 4. 投资组合模块 (Portfolio/)

#### Portfolio/base.py
```python
class BasePortfolio(ABC):
    """投资组合抽象基类"""
    
    职责：
    - 资金管理 (Capital Management)
    - 信号转化 (Signal -> Order)
    - 成交处理 (Fill Processing)
    - 盯市 (Mark-to-Market)
    
    核心属性（所有子类必须实现）：
        - current_cash: float  # 当前可用现金
        - positions: dict  # 持仓字典 {symbol: volume}
        - total_equity: float  # 总资产 = 现金 + 持仓市值
    
    抽象方法：
        - __init__(data_handler, initial_capital)  # 初始化
        - update_on_market(event) [抽象]  # 更新持仓市值
        - update_on_fill(event) [抽象]  # 处理成交
        - process_signal(event) [抽象]  # 处理信号
```

#### Portfolio/portfolio.py
```python
class BacktestPortfolio(BasePortfolio):
    """现货回测投资组合实现"""
    
    核心属性：
        - current_cash: float  # 当前可用现金
        - positions: Dict[str, int]  # 持仓字典
        - total_equity: float  # 总资产
        - total_trades: int  # 总交易次数
        - total_commission: float  # 总手续费
        - equity_curve: List[Dict]  # 资金曲线记录
        - fill_history: List[Dict]  # 成交历史记录
        - max_positions: int  # 最大同时持仓数量
        - cash_reserve_ratio: float  # 现金预留比例
        - sizer: BaseSizer  # 仓位管理器
    
    核心功能：
    - 资金管理：维护现金和持仓
    - 信号转化：将策略建议转化为具体订单
    - 成交处理：实际扣款、记账（工业级精度）
    - 盯市：更新总资产
    - 风控：多层保护机制
    
    关键逻辑：
        - 买入：使用Sizer计算目标资金，预留10%缓冲
        - 卖出：清仓卖出，小额交易过滤
        - 风控：满仓检查、重复持仓检查、手续费预估
        - 手续费：0.03%费率，最低5元
        - 资金验证：每笔交易后验证计算正确性
    
    核心方法：
        - update_on_market(event)  # 盯市更新
        - update_on_fill(event)  # 成交处理
        - process_signal(event)  # 信号转订单
        - _process_buy_signal(event)  # 处理买入信号
        - _process_sell_signal(event)  # 处理卖出信号
        - get_position(symbol)  # 获取持仓
        - get_positions()  # 获取所有持仓
        - get_cash()  # 获取现金
        - get_equity()  # 获取总资产
        - get_portfolio_info()  # 获取详细信息
        - _record_equity_curve()  # 记录资金曲线
        - _update_total_equity()  # 更新总资产
        - _record_fill(event)  # 记录成交
        - get_fill_history()  # 获取成交历史
        - get_equity_curve()  # 获取资金曲线
```

#### Portfolio/sizers.py
```python
class BaseSizer(ABC):
    """仓位管理策略基类"""
    
    核心方法：
        - calculate_target_value(portfolio, signal, data_handler) -> float  # 计算目标金额
        - get_param(key, default)  # 获取参数
        - set_logger(logger)  # 设置日志记录器

class EqualWeightSizer(BaseSizer):
    """等权重分配策略"""
    
    逻辑：目标金额 = 总资金 / 最大持仓数量

class FixedRatioSizer(BaseSizer):
    """固定比例分配策略"""
    
    逻辑：目标金额 = 总资金 * 固定比例

class SignalWeightedSizer(BaseSizer):
    """信号强度加权分配策略"""
    
    逻辑：根据信号强度分配不同比例的仓位

class ATRSizer(BaseSizer):
    """ATR波动率仓位管理策略"""
    
    逻辑：根据股票历史波动率动态调整仓位

def create_sizer(sizer_type: str, **kwargs) -> BaseSizer:
    """工厂函数：根据类型创建仓位管理器"""
```

### 5. 数据处理器模块 (DataManager/handlers/)

#### DataManager/handlers/handler.py
```python
class BacktestDataHandler(BaseDataHandler):
    """回测数据处理器"""
    
    核心功能：
    - 时间对齐：多股票统一时间轴处理
    - 防未来函数：策略只能访问当前视图数据
    - 事件生成：通过生成器模式高效推送事件
    
    关键方法：
        - update_bars() - 生成市场事件流
        - get_latest_bar() - 获取最新K线
        - get_latest_bars() - 获取历史K线
        - get_current_time() - 获取当前回测时间
```

### 2. 数据管理模块 (DataManager/)

#### DataManager/schema/constant.py
```python
class Exchange(Enum):
    """交易所枚举"""
    枚举值:
        - SSE = "SSE"          # 上海证券交易所
        - SZSE = "SZSE"        # 深圳证券交易所
        - BSE = "BSE"          # 北京证券交易所
        - CFFEX = "CFFEX"      # 中金所
        - SHFE = "SHFE"        # 上期所
        - DCE = "DCE"          # 大商所
        - CZCE = "CZCE"        # 郑商所
        - HKEX = "HKEX"        # 香港交易所
        - NASDAQ = "NASDAQ"    # 纳斯达克
        - NYSE = "NYSE"        # 纽约证券交易所
        - BINANCE = "BINANCE"  # 币安
        - OKEX = "OKEX"        # OKX
        - LOCAL = "LOCAL"      # 本地数据源

class Interval(Enum):
    """K线周期枚举"""
    枚举值:
        - TICK = "tick"
        - MINUTE = "1m"
        - MINUTE_5 = "5m"
        - MINUTE_15 = "15m"
        - MINUTE_30 = "30m"
        - HOUR = "1h"
        - HOUR_4 = "4h"
        - DAILY = "d"
        - WEEKLY = "w"
        - MONTHLY = "M"

class Direction(Enum):
    """交易方向枚举"""
    枚举值:
        - LONG = "LONG"        # 多头/买入
        - SHORT = "SHORT"      # 空头/卖出
        - NET = "NET"          # 净值

class Offset(Enum):
    """开平方向枚举"""
    枚举值:
        - OPEN = "OPEN"              # 开仓
        - CLOSE = "CLOSE"            # 平仓
        - CLOSETODAY = "CLOSETODAY"    # 平今
        - CLOSEYESTERDAY = "CLOSEYESTERDAY"  # 平昨

class Status(Enum):
    """状态枚举"""
    枚举值:
        - NOTTRADED = "NOTTRADED"    # 未交易
        - ALLTRADED = "ALLTRADED"    # 全部成交
        - PARTTRADED = "PARTTRADED"  # 部分成交
        - CANCELLED = "CANCELLED"    # 已撤销
        - REJECTED = "REJECTED"      # 已拒绝
```

#### DataManager/schema/base.py
```python
@dataclass
class BaseData:
    """基础数据类"""
    属性:
        - gateway_name: str                    # 数据来源接口名称
        - symbol: str                          # 标的代码
        - exchange: Exchange                    # 交易所枚举值
        - datetime: datetime                   # 带时区信息的时间戳
        - extra: Dict[str, Any]                # 扩展字段，默认空字典
    
    方法:
        - __post_init__()                       # 初始化后处理
        - vt_symbol (property) -> str          # 虚拟标的代码 (symbol.exchange)
        - __str__() -> str                      # 字符串表示
        - __repr__() -> str                     # 调试用字符串表示
        - update_extra(key: str, value: Any)    # 更新扩展字段
        - get_extra(key: str, default: Any) -> Any  # 获取扩展字段
```

#### DataManager/schema/bar.py
```python
@dataclass
class BarData(BaseData):
    """K线数据类"""
    继承: BaseData
    
    属性:
        - interval: Interval                    # K线周期
        - open_price: float                     # 开盘价
        - high_price: float                     # 最高价
        - low_price: float                      # 最低价
        - close_price: float                    # 收盘价
        - volume: float                         # 成交量（股数）
        - turnover: float                       # 成交额（金额）
        - open_interest: float                  # 持仓量（期货专用）
        - limit_up: float                       # 涨停价
        - limit_down: float                     # 跌停价
        - pre_close: float                      # 昨收价
        - settlement: float                     # 结算价（期货用）
    
    方法:
        - __post_init__()                       # 数据验证
        - price_change (property) -> float      # 价格变动 = 当前收盘价 - 昨收价
        - price_change_pct (property) -> float  # 价格变动百分比
        - amplitude (property) -> float         # 振幅百分比
        - is_limit_up (property) -> bool        # 是否涨停
        - is_limit_down (property) -> bool      # 是否跌停
        - average_price (property) -> float     # 成交均价
        - __str__() -> str                      # 字符串表示
```

#### DataManager/schema/tick.py
```python
@dataclass
class TickData(BaseData):
    """Tick数据类"""
    继承: BaseData
    
    属性:
        - name: str                             # 中文名称
        - last_price: float                      # 最新成交价
        - last_volume: float                     # 最新成交量
        # 卖盘五档
        - ask_price_1 到 ask_price_5: float      # 卖一价到卖五价
        - ask_volume_1 到 ask_volume_5: float     # 卖一量到卖五量
        # 买盘五档
        - bid_price_1 到 bid_price_5: float      # 买一价到买五价
        - bid_volume_1 到 bid_volume_5: float     # 买一量到买五量
        # 其他字段
        - limit_up: float                        # 涨停价
        - limit_down: float                      # 跌停价
        - open_interest: float                   # 持仓量
        - pre_close: float                       # 昨收价
        - turnover: float                        # 累计成交额
        - volume: float                          # 累计成交量
        - avg_price: float                       # 当日均价
    
    方法:
        - spread (property) -> float            # 买卖价差 = 卖一价 - 买一价
        - spread_pct (property) -> float        # 买卖价差百分比
        - total_ask_volume (property) -> float   # 卖盘总挂单量
        - total_bid_volume (property) -> float   # 买盘总挂单量
        - volume_ratio (property) -> float       # 买卖量比
        - weighted_bid_price (property) -> float # 买盘加权价格
        - weighted_ask_price (property) -> float # 卖盘加权价格
        - mid_price (property) -> float         # 中间价
        - __str__() -> str                      # 字符串表示
```

#### DataManager/schema/fundamental.py
```python
@dataclass
class FundamentalData(BaseData):
    """财务数据类"""
    继承: BaseData
    
    属性:
        # 基础估值指标
        - pe_ratio: float                        # 市盈率
        - pb_ratio: float                        # 市净率
        - ps_ratio: float                        # 市销率
        # 盈利能力指标
        - eps: float                             # 每股收益
        - roe: float                              # 净资产收益率
        - roa: float                              # 总资产收益率
        - roic: float                             # 投入资本回报率
        - gross_margin: float                     # 毛利率
        - net_margin: float                       # 净利率
        # 成长性指标
        - revenue_growth: float                   # 营收增长率
        - profit_growth: float                    # 净利润增长率
        - eps_growth: float                       # 每股收益增长率
        # 偿债能力指标
        - current_ratio: float                    # 流动比率
        - quick_ratio: float                      # 速动比率
        - debt_to_equity: float                   # 资产负债率
        - interest_coverage: float                # 利息保障倍数
        # 运营效率指标
        - inventory_turnover: float               # 存货周转率
        - receivable_turnover: float              # 应收账款周转率
        - asset_turnover: float                   # 总资产周转率
        # 现金流指标
        - operating_cash_flow: float              # 经营活动现金流
        - free_cash_flow: float                   # 自由现金流
        - cash_per_share: float                   # 每股现金流
        # 股本相关
        - total_shares: float                     # 总股本
        - float_shares: float                     # 流通股本
        - market_cap: float                       # 总市值
        - circulating_cap: float                  # 流通市值
        # 分红相关
        - dividend_per_share: float               # 每股分红
        - dividend_yield: float                   # 股息率
        - payout_ratio: float                     # 分红率
        # 报告期信息
        - report_date: Optional[datetime]         # 财报发布日期
        - report_type: str                        # 报告类型: 年报/半年报/季报
    
    方法:
        - book_value_per_share (property) -> float     # 每股净资产
        - earnings_yield (property) -> float           # 盈利收益率 = 1 / PE
        - price_to_cash_flow (property) -> float       # 市现率
        - enterprise_value (property) -> float         # 企业价值
        - ev_to_ebitda (property) -> float             # EV/EBITDA 比率
        - is_value_stock (property) -> bool           # 判断是否为价值股
        - is_growth_stock (property) -> bool          # 判断是否为成长股
        - is_quality_stock (property) -> bool         # 判断是否为优质股
        - __str__() -> str                              # 字符串表示
```

#### DataManager/sources/base_source.py
```python
class BaseDataSource(ABC):
    """数据源抽象基类"""
    
    抽象方法:
        - load_bar_data(symbol: str, exchange: str, start_date: datetime, end_date: datetime) -> List[BarData]
        - load_tick_data(symbol: str, exchange: str, start_date: datetime, end_date: datetime) -> List[TickData]
        - load_fundamental_data(symbol: str, exchange: str, start_date: datetime, end_date: datetime) -> List[FundamentalData]
    
    方法:
        - stream_bar_data(symbol: str, exchange: str, start_date: datetime, end_date: datetime) -> Generator[BarData, None, None]
```

#### DataManager/sources/local_csv.py
```python
class LocalCSVLoader(BaseDataSource):
    """本地CSV文件加载器"""
    继承: BaseDataSource
    
    属性:
        - root_path: Path                        # CSV文件根目录
        - logger: Logger                          # 日志记录器
        - column_mapping: Dict[str, str]          # 列名映射表
    
    方法:
        - __init__(root_path: str)               # 构造函数
        - _get_file_path(symbol: str) -> Path     # 获取文件路径
        - _parse_datetime(date_str) -> datetime    # 解析日期
        - _map_row_to_bar_data(row: pd.Series, symbol: str, exchange: Exchange) -> BarData  # 映射行数据
        - load_bar_data(...) -> List[BarData]      # 实现加载K线数据
        - load_tick_data(...) -> List[TickData]    # 未实现，抛出NotImplementedError
        - load_fundamental_data(...) -> List[FundamentalData]  # 未实现，抛出NotImplementedError
```

#### DataManager/selectors/base.py
```python
class BaseStockSelector(ABC):
    """选股器抽象基类"""
    
    抽象方法:
        - select_stocks(date: datetime, **kwargs) -> List[str]  # 执行选股
        - validate_connection() -> bool                           # 连接健康检查
```

#### DataManager/selectors/wencai_selector.py
```python
class WencaiSelector(BaseStockSelector):
    """基于 pywencai 的自然语言选股器"""
    继承: BaseStockSelector
    
    属性:
        - cookie: str                              # 问财鉴权Cookie
        - retry_count: int                         # 失败重试次数
        - sleep_time: int                          # 防封号休眠秒数
        - _wencai: module                          # pywencai库对象
        - logger: Logger                            # 日志记录器
    
    方法:
        - __init__(cookie: str = None, retry_count: int = 3, sleep_time: int = 2)  # 构造函数
        - select_stocks(date: datetime, **kwargs) -> List[str]                           # 实现选股方法
        - validate_connection() -> bool                                                    # 实现连接验证
        - _parse_codes(df) -> List[str]                                                   # 解析股票代码
```

#### DataManager/handlers/handler.py
```python
class BaseDataHandler(ABC):
    """数据处理器抽象基类"""
    
    属性:
        - data_source: BaseDataSource              # 数据加载器
        - symbol_data: Dict[str, List[BarData]]   # 存储历史数据
        - current_index: Dict[str, int]           # 当前回测游标
        - continue_backtest: bool                  # 回测继续标志
        - logger: Logger                           # 日志记录器
    
    抽象方法:
        - update_bars() -> Generator[MarketEvent, None, None]  # 核心生成器
        - get_latest_bar(symbol: str) -> Optional[BarData]       # 获取最新K线
        - get_latest_bars(symbol: str, n: int = 1) -> List[BarData]  # 获取最近N根K线

class BacktestDataHandler(BaseDataHandler):
    """回测数据处理器"""
    继承: BaseDataHandler
    
    属性:
        - symbol_list: List[str]                  # 股票代码列表
        - start_date: datetime                    # 回测开始日期
        - end_date: datetime                      # 回测结束日期
        - timeline: List[datetime]                 # 时间轴
        - time_indexed_data: Dict[datetime, Dict[str, BarData]]  # 时间索引数据
        - current_time_index: int                 # 当前时间指针
    
    方法:
        - __init__(data_source, symbol_list, start_date, end_date)  # 构造函数
        - _load_data()                            # 加载数据
        - _build_timeline()                       # 构建时间轴
        - _align_data_by_time()                   # 按时间对齐数据
        - update_bars() -> Generator[MarketEvent, None, None]        # 实现事件生成
        - get_latest_bar(symbol: str) -> Optional[BarData]           # 实现获取最新K线
        - get_latest_bars(symbol: str, n: int = 1) -> List[BarData]    # 实现获取最近N根K线
        - get_current_time() -> Optional[datetime]                     # 获取当前回测时间
        - reset()                                 # 重置数据处理器
```

### 3. 基础设施模块 (Infrastructure/)

#### Infrastructure/enums.py
```python
class EventType(Enum):
    """事件类型枚举"""
    枚举值:
        - MARKET = "MARKET"      # 行情来了（由 DataManager 发出）
        - SIGNAL = "SIGNAL"      # 策略产生想法了（由 Strategies 发出）
        - ORDER = "ORDER"        # 风控通过，准备下单了（由 Portfolio 发出）
        - FILL = "FILL"          # 交易所成交了（由 Execution 发出）
        - ERROR = "ERROR"        # 系统报错（可选，用于异常处理）

class Direction(Enum):
    """交易方向枚举"""
    枚举值:
        - LONG = "LONG"          # 做多/买入
        - BUY = "BUY"            # 买入（与LONG同义）
        - SHORT = "SHORT"        # 做空/卖出
        - SELL = "SELL"          # 卖出（与SHORT同义）

class OrderType(Enum):
    """订单类型枚举"""
    枚举值:
        - MARKET = "MARKET"      # 市价单（回测最常用）
        - LIMIT = "LIMIT"        # 限价单（需要指定价格）
```

#### Infrastructure/events.py
```python
@dataclass
class MarketEvent:
    """行情事件"""
    描述: 承载一根 K 线或一个 Tick，驱动系统向前推进一步
    
    属性:
        - bar: BarData                              # 携带具体的K线数据
        - type: EventType = EventType.MARKET       # 事件类型

@dataclass
class SignalEvent:
    """信号事件"""
    描述: 策略层发出的"建议"，注意：这里不包含具体的买卖股数，只包含意图
    
    属性:
        - symbol: str                              # 股票代码，如 "000001.SZ"
        - datetime: datetime                       # 信号产生的时间
        - direction: Direction                     # 买还是卖
        - strength: float                          # 信号强度，1.0 表示强烈买入，0.5 观望
        - type: EventType = EventType.SIGNAL       # 事件类型
    
    方法:
        - __str__() -> str                         # 字符串表示

@dataclass
class OrderEvent:
    """订单事件"""
    描述: Portfolio 经过资金计算和风控检查后，发出的"确切指令"
    
    属性:
        - symbol: str                              # 股票代码
        - datetime: datetime                       # 订单时间
        - order_type: OrderType                    # 市价还是限价
        - direction: Direction                     # 交易方向
        - volume: int                              # 关键：具体的股数，例如 1000 股，不能是金额
        - limit_price: float = 0.0                 # 如果是限价单，必填；市价单为 0
        - type: EventType = EventType.ORDER       # 事件类型
    
    方法:
        - __str__() -> str                         # 字符串表示
        - type: EventType = EventType.ORDER       # 事件类型
        - datetime: Optional[datetime] = None     # 订单时间
        - timestamp: Optional[datetime] = None     # 时间戳
    
    方法:
        - __post_init__()                          # 设置时间戳
        - __str__() -> str                         # 字符串表示

@dataclass
class FillEvent:
    """成交事件"""
    描述: 模拟交易所（Execution）撮合成功后返回的凭证，Portfolio 收到这个才能扣钱
    
    属性:
        - symbol: str                              # 股票代码
        - datetime: datetime                       # 实际成交时间，可能滞后于订单时间
        - direction: Direction                     # 交易方向
        - volume: int                              # 实际成交数量，可能因为滑点或资金不足只成交了一半
        - price: float                             # 实际成交价，包含滑点影响
        - commission: float                        # 产生的手续费金额
        - type: EventType = EventType.FILL         # 事件类型
    
    方法:
        - trade_value (property) -> float          # 成交金额 = price × volume
        - net_value (property) -> float            # 净成交金额（已修复手续费计算逻辑）
            # 买入时：成交金额 + 手续费（现金净流出）
            # 卖出时：成交金额 - 手续费（现金净流入）
        - __str__() -> str                         # 字符串表示
```

### 4. 数据处理器模块 (DataManager/handlers/)

#### DataManager/handlers/handler.py
```python
class BaseDataHandler(ABC):
    """数据处理器抽象基类"""
    职责: 定义数据处理器对外的标准接口，确保策略层调用数据的方式统一
    
    抽象方法:
        - get_latest_bar(self, symbol: str) -> Optional[BarData]
            # 获取指定股票在"当前回测时间点"的最新一根 K 线
            # 用途：策略判断当前价格（如 bar.close_price）时使用
        
        - get_latest_bars(self, symbol: str, n: int = 1) -> List[BarData]
            # 获取指定股票截止到"当前回测时间点"的最近 N 根 K 线
            # 用途：策略计算技术指标（如计算 MA5 需要最近 5 根 Bar）
        
        - update_bars(self) -> Generator
            # 驱动系统时间流动的生成器
            # 行为：每次调用 next()，时间前进一步，并返回一个新的 MarketEvent

class BacktestDataHandler(BaseDataHandler):
    """专用于历史回测，处理多只股票的时间对齐，维护"最新数据视图"以防止未来函数"""
    
    属性:
        - loader: BaseDataSource                   # 数据加载器实例（如 LocalCSVLoader）
        - symbol_list: List[str]                   # 需要回测的股票代码列表
        - start_date, end_date: datetime           # 回测起止时间
        - _data_cache: Dict[str, List[BarData]]    # 全量数据缓存：在初始化时一次性把所有 CSV 数据读入这里
        - _timeline: List[datetime]                # 统一时间轴：所有股票时间戳的并集，并按升序排列
        - _latest_data: Dict[str, List[BarData]]   # 当前视图缓存：随着时间推进，把 _data_cache 里的数据一根根搬运到这里
    
    方法:
        - __init__(loader, symbol_list, start_date, end_date)
            # 初始化数据处理器，调用 _load_all_data()
        
        - _load_all_data() (私有方法)
            # 1. 遍历 symbol_list，调用 loader.load_bar_data()
            # 2. 将加载结果存入 _data_cache
            # 3. 同时收集所有 BarData 的时间戳，去重、排序，生成 _timeline
        
        - update_bars() -> Generator (核心逻辑)
            # 外层循环：遍历 _timeline 中的每一个 timestamp
            # 内层循环：检查每个 symbol 在 _data_cache 中是否存在该 timestamp 的数据
            #     如果有：
            #         1. 将该 BarData 追加到 _latest_data[symbol] 列表末尾
            #         2. yield MarketEvent(bar) (向外抛出事件)
            #     如果没有（停牌）：跳过，不产生事件
        
        - get_latest_bar(symbol: str) -> Optional[BarData]
            # 读取 self._latest_data[symbol] 的最后一个元素，如果列表为空，返回 None
        
        - get_latest_bars(symbol: str, n: int = 1) -> List[BarData]
            # 读取 self._latest_data[symbol] 的最后 n 个元素，返回列表切片
```

### 5. 撮合执行模块 (Execution/)

#### Execution/base.py
```python
class BaseExecutor(ABC):
    """执行器抽象基类"""
    
    职责：
    - 接收订单事件 (OrderEvent)
    - 模拟交易所撮合过程
    - 返回成交事件 (FillEvent)
    - 实现交易成本（手续费、滑点）计算
    - 处理订单状态管理
    
    抽象方法：
        - execute_order(order_event: OrderEvent) -> Optional[FillEvent]  # 执行订单
        - validate_order(order_event: OrderEvent) -> bool                # 订单验证
        - get_execution_stats() -> Dict[str, Any]                       # 获取执行统计
```

#### Execution/simulator.py
```python
class SimulatedExecution(BaseExecutor):
    """回测模拟执行器"""
    
    核心属性：
        - data_handler: BaseDataHandler  # 数据处理器
        - orders_received: int  # 接收订单数
        - orders_executed: int  # 执行订单数
        - orders_rejected: int  # 拒绝订单数
        - total_commission: float  # 总手续费
    
    职责：
    - 模拟真实的交易执行环境
    - 实现手续费、滑点等交易成本
    - 处理市价单和限价单
    - 维护订单状态和执行统计
    
    特点：
    - 假设无限流动性，订单总是能全额成交
    - 支持市价单和限价单
    - 考虑手续费和滑点成本
    
    核心方法：
        - __init__(data_handler, **kwargs)  # 初始化
        - execute_order(order_event) -> Optional[FillEvent]  # 执行订单
        - _get_fill_price(order_event) -> Optional[float]  # 获取成交价格
        - _get_current_time() -> Optional[datetime]  # 获取当前回测时间
        - get_execution_stats() -> dict  # 获取执行统计
        - reset_stats()  # 重置统计信息
```

### 6. 分析模块 (Analysis/)

#### Analysis/performance.py
```python
class PerformanceAnalyzer:
    """绩效分析器"""
    
    职责：
    - 将Portfolio记录的流水账变成专业的报表和指标
    - 计算核心绩效指标：收益率、夏普比率、最大回撤等
    - 生成分析报告和统计摘要
    
    属性：
        - df: pd.DataFrame              # 资金曲线DataFrame，datetime为索引
        - start_date: datetime          # 回测开始日期
        - end_date: datetime            # 回测结束日期
        - trading_days: int             # 交易天数
        - start_equity: float           # 初始资金
        - end_equity: float             # 最终资金
    
    构造方法：
        - __init__(equity_curve: List[Dict[str, Any]])
            # equity_curve: 来自Portfolio的资金曲线数据
            # 每个字典包含: datetime, total_equity, cash, positions_value
    
    核心方法：
        - _prepare_dataframe(equity_curve: List[Dict[str, Any]]) -> pd.DataFrame
            # 准备DataFrame数据：转换格式、设置索引、按时间排序
        
        - calculate_total_return() -> float
            # 计算累计收益率：(end/start) - 1
        
        - calculate_annualized_return() -> float
            # 计算年化收益率：使用复利公式 (end/start)^(252/trading_days) - 1
        
        - calculate_max_drawdown() -> float
            # 计算历史最大回撤：基于资金曲线计算最大跌幅
        
        - calculate_sharpe_ratio(risk_free_rate: float = 0.02) -> float
            # 计算夏普比率：(超额收益率均值 / 超额收益率标准差) * sqrt(252)
        
        - calculate_volatility() -> float
            # 计算年化波动率：日收益率标准差 * sqrt(252)
        
        - calculate_calmar_ratio() -> float
            # 计算卡尔玛比率：年化收益率 / abs(最大回撤)
        
        - calculate_win_rate() -> float
            # 计算胜率：正收益交易日占比
        
        - calculate_profit_loss_ratio() -> float
            # 计算盈亏比：平均盈利 / 平均亏损
        
        - get_drawdown_series() -> pd.Series
            # 获取回撤时间序列
        
        - get_summary() -> Dict[str, Any]
            # 获取完整绩效分析摘要：包含所有关键指标
        
        - print_summary()
            # 打印格式化的绩效摘要
```

#### Analysis/plotting.py
```python
class BacktestPlotter:
    """回测图表绘制器"""
    
    职责：
    - 绘制专业的量化回测分析图表
    - 生成资金曲线图、回撤图、收益分布图等
    - 支持多种可视化图表和完整报告生成
    
    属性：
        - analyzer: PerformanceAnalyzer  # 绩效分析器实例
        - figsize: tuple                # 图表尺寸，默认 (12, 10)
        - logger: Logger                # 日志记录器
    
    构造方法：
        - __init__(analyzer, figsize: tuple = (12, 10))
    
    核心方法：
```

#### Analysis/reporting.py
```python
class BacktestReporter:
    """回测报告生成器"""
    
    职责：
    - 生成详细的回测报告
    - 分析交易明细和绩效指标
    - 输出格式化的报告文件
    
    核心方法：
        - generate_report(portfolio, analyzer, output_path)  # 生成报告
        - analyze_trades(fill_history)  # 分析交易明细
        - format_performance_metrics(summary)  # 格式化绩效指标
```
        - show_analysis_plot(save_path: Optional[str] = None)
            # 显示完整的分析图表，包含：
            # - 上图：资金曲线图（总资产、现金、持仓市值）
            # - 下图：水下回撤图（回撤曲线及面积）
        
        - _plot_equity_curve(ax)
            # 绘制资金曲线图：总资产、现金、持仓市值三条线
        
        - _plot_drawdown(ax)
            # 绘制回撤图：回撤曲线及面积，标记最大回撤点
        
        - plot_returns_distribution(save_path: Optional[str] = None)
            # 绘制收益分布图：日收益率直方图和累积收益图
        
        - plot_monthly_returns(save_path: Optional[str] = None)
            # 绘制月度收益热力图：年-月收益矩阵
        
        - plot_rolling_metrics(window: int = 30, save_path: Optional[str] = None)
            # 绘制滚动指标图：滚动夏普比率和波动率
        
        - save_plot(filename: str)
            # 保存图表到文件
        
        - create_full_report(save_prefix: str = "backtest_report")
            # 创建完整的分析报告：生成所有类型的图表
```
```

## 依赖关系

```
Strategies → Infrastructure.events
Portfolio → Infrastructure.events
Execution → Infrastructure.events
Analysis → Infrastructure.events
Engine → DataManager.handlers + Infrastructure.events + Strategies + Portfolio + Execution
DataManager.handlers → DataManager.sources + Infrastructure.events
DataManager.sources → DataManager.schema
DataManager.selectors → Infrastructure.events
```

## 设计原则

1. **单一职责原则**：每个类只负责一个特定的功能
2. **开闭原则**：对扩展开放，对修改封闭
3. **依赖倒置原则**：高层模块不依赖低层模块，都依赖于抽象
4. **接口隔离原则**：客户端不应该依赖它不需要的接口
5. **事件驱动架构**：通过事件系统实现模块间的松耦合

## 扩展指南

### 添加新的数据源
1. 继承 `BaseDataSource` 类
2. 实现必要的数据加载方法
3. 在 `DataManager/sources/__init__.py` 中导出

### 添加新的选股器
1. 继承 `BaseStockSelector` 类
2. 实现选股和连接验证方法
3. 在 `DataManager/selectors/__init__.py` 中导出

### 添加新的事件类型
1. 在 `EventType` 枚举中添加新类型
2. 创建对应的事件类
3. 更新相关模块以处理新事件

### 添加新的数据处理器
1. 继承 `BaseDataHandler` 类
2. 实现数据处理逻辑
3. 在相应位置注册使用

## 📋 开发计划

### 已完成模块 ✅

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
- [x] **系统主入口 main.py**
- [x] **边界异常处理增强**
- [x] **配置驱动架构**

### V1.0 新增功能 🆕

#### 系统主入口 (main.py)
- **BacktestApplication 类**：面向对象的应用程序入口
- **配置驱动组件组装**：支持命令行参数覆盖配置文件
- **动态策略加载**：支持传入策略类进行回测
- **完整回测流程**：自动化数据→策略→投资组合→引擎→分析流程
- **专业报告生成**：自动生成时间戳命名的图表和日志文件

#### 边界异常处理增强
- **LocalCSVLoader**：
  - 文件不存在友好提示
  - 文件被占用检测（Excel等程序）
  - 编码错误处理
  - 列名缺失验证
  - 空文件检测
- **WencaiSelector**：
  - 网络连接检查和重试机制
  - Cookie有效性验证
  - 频率限制自动处理
  - 分层异常处理（网络、认证、业务逻辑）
- **配置读取**：
  - YAML格式错误验证
  - 必需配置项检查
  - 配置值有效性验证
  - 环境变量格式验证

#### 命令行接口
```bash
# 基本用法
python main.py

# 自定义参数
python main.py --start-date 2024-01-01 --end-date 2024-03-31 --capital 100000 --symbols 000001.SZ 600036.SH

# 查看帮助
python main.py --help
```

### V1.1 规划功能 📋

- [ ] 策略注册机制 (Strategy Registry)
- [ ] 多策略批量回测
- [ ] 实时交易支持扩展
- [ ] 更多数据源适配器 (Tushare、Yahoo Finance等)
- [ ] Web界面和API服务
- [ ] 分布式回测支持

## 测试验证

### 测试模块
- `test_csv_loader.py` - CSV数据加载测试
- `test_wencai_csv_integration.py` - 问财选股与CSV集成测试
- `test_new_event_system.py` - 新事件系统测试
- `test_comprehensive_integration.py` - 综合集成测试

### 测试覆盖范围
- ✅ 枚举定义和事件类创建
- ✅ 问财选股功能
- ✅ CSV数据加载和解析
- ✅ 数据处理器事件生成
- ✅ 防未来函数机制
- ✅ 时间对齐和多股票处理
- ✅ 完整流程模拟（选股→数据加载→事件生成→策略信号）
- ✅ 执行器订单处理和成交模拟
- ✅ 绩效分析和图表生成

### 测试结果
- 问财选股：成功获取42只银行股
- 数据加载：单股7条数据，多股时间对齐正常
- 事件系统：20个MarketEvent生成，6只股票分布均匀
- 策略模拟：检测到2个上涨信号（涨幅超过2%）
- 订单执行：成功处理1个交易订单，执行率100%
- 绩效统计：收益率-1.36%，夏普比率-3.897，最大回撤-1.83%
- 图表生成：成功生成资金曲线图和收益分布图

## 🎯 当前系统状态 (V1.0)

### 核心架构模块

1. **数据结构层** - 完整的BarData、TickData、FundamentalData模型，支持标准化交易所格式
2. **数据源层** - LocalCSVLoader，支持中文列名和单位转换，增强异常处理
3. **选股器层** - WencaiSelector，自然语言选股，增强网络异常处理和重试机制
4. **事件系统** - EventType枚举和MarketEvent、SignalEvent、OrderEvent、FillEvent，修复了FillEvent.net_value计算逻辑
5. **数据处理器** - BacktestDataHandler，时间对齐和防未来函数
6. **配置管理** - YAML配置文件和环境变量支持，增强配置验证和错误提示
7. **回测引擎** - BacktestEngine，事件驱动架构核心，重构策略信号机制
8. **策略框架** - BaseStrategy抽象基类和SimpleMomentumStrategy示例，采用模板方法模式
9. **投资组合管理** - BacktestPortfolio，A股规则的资金和持仓管理，工业级精度计算
10. **执行系统** - SimulatedExecution，订单处理、手续费、滑点模拟
11. **分析系统** - PerformanceAnalyzer和BacktestPlotter，绩效分析和图表生成，修复路径保存问题
12. **系统入口** - BacktestApplication，配置驱动的应用程序入口，支持命令行参数

### V1.0 关键特性

#### 🏗️ 生产级架构
- **事件驱动设计** - 通过事件实现模块解耦，统一的事件队列管理
- **面向对象入口** - BacktestApplication类，职责清晰分离
- **配置驱动组装** - 支持命令行参数覆盖配置文件，灵活的组件组装
- **动态策略加载** - 支持传入策略类进行回测，便于扩展

#### 🛡️ 健壮性增强
- **三大边界异常处理**：
  - 数据IO异常：文件不存在、被占用、编码错误等友好提示
  - 网络API异常：Cookie过期、频率限制、连接问题等重试机制
  - 配置读取异常：YAML格式错误、必需配置缺失等验证
- **友好的错误提示** - 每种异常都提供具体的解决建议
- **完整的日志记录** - 详细的操作日志和错误追踪

#### 📊 专业分析能力
- **自动图表生成** - 时间戳命名的专业分析图表
- **完整绩效指标** - 收益率、夏普比率、最大回撤、胜率等
- **批量回测支持** - 命令行接口便于服务器批量运行
- **工业级精度** - 精确的资金计算和多层风控机制

#### 🚀 易用性提升
- **一键启动** - `python main.py` 即可运行完整回测
- **灵活配置** - 命令行参数可覆盖配置文件设置
- **智能股票管理** - 问财选股→配置默认→硬编码备用的三层降级
- **自动化输出** - 自动创建目录、生成报告、保存图表

### 已实现核心功能
1. **智能选股** - 问财自然语言选股，支持网络异常重试
2. **数据加载** - 本地CSV数据加载，支持多种文件状态检测
3. **事件驱动** - 完整的事件流转机制和防未来函数保护
4. **策略执行** - 信号生成和订单转化，支持动态策略加载
5. **交易模拟** - A股规则、手续费、滑点的精确模拟
6. **绩效分析** - 专业的量化指标计算和分析
7. **报告生成** - 自动生成时间戳命名的专业图表和日志
8. **命令行操作** - 支持参数化配置和批量回测

## 📋 使用指南

### 快速开始

```bash
# 基本用法（使用默认配置）
python main.py

# 自定义参数
python main.py --start-date 2024-01-01 --end-date 2024-03-31 --capital 100000 --symbols 000001.SZ 600036.SH

# 查看帮助信息
python main.py --help
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--config` | 配置文件路径 | `--config custom.yaml` |
| `--start-date` | 回测开始日期 | `--start-date 2024-01-01` |
| `--end-date` | 回测结束日期 | `--end-date 2024-12-31` |
| `--capital` | 初始资金 | `--capital 1000000` |
| `--symbols` | 股票代码列表 | `--symbols 000001.SZ 600036.SH` |

### 输出文件

运行完成后，系统会在 `output/` 目录生成：
- `backtest_main_TIMESTAMP.png` - 主分析图（资金曲线+回撤图）
- `backtest_returns_TIMESTAMP.png` - 收益分布图
- `backtest_TIMESTAMP.log` - 详细运行日志

## 🔧 开发指南

### 自定义策略

```python
from Strategies.base import BaseStrategy
from Infrastructure.events import MarketEvent, Direction

class MyStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> None:
        # 实现策略逻辑
        bar = event.bar
        
        # 示例：简单动量策略
        if bar.close_price > bar.open_price * 1.02:
            self.send_signal(bar.symbol, Direction.LONG, strength=0.8)
```

### 运行自定义策略

```python
from main import BacktestApplication
from Strategies.my_strategy import MyStrategy

app = BacktestApplication()
results = app.run(strategy_class=MyStrategy)
```

## ⚠️ 注意事项

1. **数据安全**：策略只能通过DataHandler接口访问数据，严禁访问未来数据
2. **资金精度**：所有资金计算使用float类型，注意手续费和滑点影响
3. **时间格式**：统一使用datetime类型，股票代码格式为"symbol.exchange"
4. **异常处理**：所有模块都要有完整的异常处理和日志记录
5. **配置管理**：关键配置项缺失会有明确的错误提示
6. **文件路径**：确保CSV数据路径正确，文件没有被其他程序占用
7. **网络依赖**：问财选股需要稳定的网络连接和有效的Cookie