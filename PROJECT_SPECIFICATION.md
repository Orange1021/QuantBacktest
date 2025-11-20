# QuantBacktest 量化回测系统项目说明书

## 项目概述

QuantBacktest是一个完整的量化交易回测系统，采用事件驱动架构设计，支持多种数据源、策略类型和分析工具。

## 项目结构

```
QuantBacktest/
├── .env                         # 环境变量配置文件
├── config/                       # 配置管理模块
│   ├── config.yaml               # 业务配置文件
│   ├── settings.py               # 配置读取类
│   └── __init__.py
├── DataManager/                  # 数据管理模块
│   ├── api.py                    # 数据管理对外接口
│   ├── handlers/                 # 数据驱动层
│   │   ├── handler.py            # 数据处理器实现
│   │   └── __init__.py
│   ├── feeds/                    # 数据供应层
│   │   ├── base_feed.py          # 供应器基类
│   │   ├── lazy_feed.py          # 懒加载供应器
│   │   ├── mem_feed.py           # 内存供应器
│   │   └── __init__.py
│   ├── processors/               # 数据处理层
│   │   ├── adjuster.py           # 复权处理器
│   │   ├── cleaner.py            # 数据清洗器
│   │   ├── merger.py             # 数据合并器
│   │   └── resampler.py          # 重采样器
│   ├── schema/                   # 数据结构定义
│   │   ├── base.py               # 基础数据类
│   │   ├── bar.py                # K线数据类
│   │   ├── constant.py           # 常量定义
│   │   ├── fundamental.py       # 财务数据类
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
│   │   └── yfinance.py           # Yahoo Finance数据源
│   ├── storage/                  # 存储引擎
│   │   ├── base_store.py         # 存储基类
│   │   ├── csv_store.py          # CSV存储
│   │   ├── hdf5_store.py         # HDF5存储
│   │   ├── influx_store.py       # InfluxDB存储
│   │   └── mysql_store.py        # MySQL存储
│   └── __init__.py
├── Infrastructure/               # 基础设施模块
│   ├── events.py                 # 事件系统定义
│   └── __init__.py
├── Engine/                       # 回测引擎模块（待实现）
├── Execution/                    # 撮合执行模块（待实现）
├── Portfolio/                    # 投资组合模块（待实现）
├── Strategies/                   # 策略模块（待实现）
├── Analysis/                     # 分析模块（待实现）
├── Test/                         # 测试模块
│   ├── test_csv_loader.py        # CSV加载器测试
│   ├── test_event_system.py      # 事件系统测试
│   ├── test_wencai_csv_integration.py  # 集成测试
│   └── ...
└── txt/                          # 文档文件夹
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

#### Infrastructure/events.py
```python
class EventType(Enum):
    """事件类型枚举"""
    枚举值:
        - MARKET = "MARKET"      # 行情推送
        - SIGNAL = "SIGNAL"      # 策略发出信号
        - ORDER = "ORDER"        # 账户发出订单
        - FILL = "FILL"          # 交易所回报成交

@dataclass
class MarketEvent:
    """行情事件"""
    属性:
        - bar: BarData                              # 携带具体的K线数据
        - type: EventType = EventType.MARKET       # 事件类型
        - timestamp: Optional[datetime] = None     # 时间戳
    
    方法:
        - __post_init__()                          # 设置时间戳

@dataclass
class SignalEvent:
    """信号事件"""
    属性:
        - symbol: str                              # 股票代码
        - direction: str                           # 交易方向 "LONG"/"SHORT"
        - strength: float                          # 信号强度
        - datetime: datetime                        # 信号产生时间
        - type: EventType = EventType.SIGNAL       # 事件类型
        - timestamp: Optional[datetime] = None     # 时间戳
        - price: Optional[float] = None            # 参考价格
    
    方法:
        - __post_init__()                          # 设置时间戳
        - __str__() -> str                         # 字符串表示

@dataclass
class OrderEvent:
    """订单事件"""
    属性:
        - symbol: str                              # 股票代码
        - order_type: str                          # 订单类型 "MARKET"/"LIMIT"
        - direction: str                           # 交易方向 "BUY"/"SELL"
        - volume: int                              # 下单数量（股数）
        - price: float = 0.0                       # 限价单价格
        - type: EventType = EventType.ORDER       # 事件类型
        - datetime: Optional[datetime] = None     # 订单时间
        - timestamp: Optional[datetime] = None     # 时间戳
    
    方法:
        - __post_init__()                          # 设置时间戳
        - __str__() -> str                         # 字符串表示

@dataclass
class FillEvent:
    """成交事件"""
    属性:
        - symbol: str                              # 股票代码
        - datetime: datetime                        # 成交时间
        - direction: str                           # 交易方向 "BUY"/"SELL"
        - volume: int                              # 实际成交数量
        - price: float                             # 实际成交价格（含滑点）
        - commission: float                        # 手续费成本
        - type: EventType = EventType.FILL         # 事件类型
        - timestamp: Optional[datetime] = None     # 时间戳
    
    方法:
        - __post_init__()                          # 设置时间戳
        - trade_value (property) -> float          # 成交金额
        - net_value (property) -> float            # 净成交金额（扣除手续费）
        - __str__() -> str                         # 字符串表示
```

## 依赖关系

```
Strategies → Infrastructure.events
Portfolio → Infrastructure.events
Execution → Infrastructure.events
Engine → DataManager.handlers + Infrastructure.events
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

## 注意事项

1. 所有价格相关字段使用 `float` 类型
2. 日期时间统一使用 `datetime` 类型并包含时区信息
3. 股票代码统一格式为 "symbol.exchange"
4. 所有异常处理都要记录日志
5. 数据验证在 `__post_init__` 方法中进行
6. 扩展字段统一使用 `extra` 字典存储