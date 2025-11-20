# QuantBacktest - 量化交易回测系统

一个完整的量化交易回测框架，采用事件驱动架构设计，支持多种数据源、策略类型和分析工具。

## 🚀 特性

- **事件驱动架构** - 模块间松耦合，易于扩展
- **多数据源支持** - 本地CSV、Tushare、Yahoo Finance、问财选股等
- **完整数据管道** - 从数据获取到策略执行的完整流程
- **灵活策略框架** - 支持多种策略类型和自定义策略
- **详细分析工具** - 性能分析、图表生成、风险指标计算
- **配置化管理** - YAML配置文件和环境变量支持

## 📁 项目结构

```
QuantBacktest/
├── DataManager/          # 数据管理层
│   ├── handlers/         # 数据驱动层
│   ├── sources/          # 数据源适配器
│   ├── schema/           # 数据结构定义
│   ├── selectors/        # 选股器
│   └── ...
├── Infrastructure/       # 基础设施
│   └── events.py         # 事件系统
├── Engine/              # 回测引擎
├── Execution/           # 撮合执行
├── Portfolio/           # 投资组合管理
├── Strategies/          # 策略实现
├── Analysis/            # 分析工具
├── config/              # 配置管理
└── Test/                # 测试用例
```

## 🛠️ 安装

### 环境要求

- Python 3.8+
- pandas
- pywencai (问财选股)
- pyyaml

### 安装依赖

```bash
pip install pandas pywencai pyyaml
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

### 1. 测试本地数据加载

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

### 3. 事件系统测试

```python
from Infrastructure.events import MarketEvent, SignalEvent
from DataManager.schema.bar import BarData
from datetime import datetime

# 创建行情事件
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

market_event = MarketEvent(bar=bar)
print(f"行情事件: {market_event}")
```

### 4. 数据驱动层使用

```python
from DataManager.handlers import BacktestDataHandler
from DataManager.sources import LocalCSVLoader
from datetime import datetime

# 创建数据处理器
data_source = LocalCSVLoader("C:/path/to/csv/data")
handler = BacktestDataHandler(
    data_source=data_source,
    symbol_list=["000001.SZSE", "000002.SZSE"],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# 生成事件流
for event in handler.update_bars():
    print(f"事件: {event.bar.symbol} @ {event.bar.datetime}")
```

## 📊 示例用法

### 完整的选股+回测流程

```python
from DataManager.selectors import WencaiSelector
from DataManager.handlers import BacktestDataHandler
from DataManager.sources import LocalCSVLoader
from datetime import datetime

# 1. 选股
selector = WencaiSelector()
stocks = selector.select_stocks(datetime.now(), query="科技股")

# 2. 数据准备
data_source = LocalCSVLoader("C:/path/to/csv/data")
handler = BacktestDataHandler(
    data_source=data_source,
    symbol_list=stocks[:10],  # 取前10只
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# 3. 运行回测
for event in handler.update_bars():
    # 在这里添加策略逻辑
    # 处理MarketEvent、SignalEvent、OrderEvent、FillEvent
    pass
```

## 🧪 测试

运行测试用例验证系统功能：

```bash
# 测试CSV数据加载
python Test/test_csv_loader.py

# 测试事件系统
python Test/test_event_system.py

# 测试问财选股
python Test/test_wencai_selector.py

# 测试集成功能
python Test/test_wencai_csv_integration.py
```

## 📈 支持的数据源

| 数据源 | 状态 | 说明 |
|--------|------|------|
| 本地CSV | ✅ | 支持标准格式的股票数据文件 |
| 问财选股 | ✅ | 自然语言选股，需要Cookie |
| Tushare | 🚧 | 计划支持，需要Token |
| Yahoo Finance | 🚧 | 计划支持，国际市场数据 |
| Binance | 🚧 | 计划支持，加密货币数据 |

## 🎨 策略开发

### 创建自定义策略

```python
from Infrastructure.events import MarketEvent, SignalEvent, OrderEvent

class MyStrategy:
    def __init__(self):
        self.position = {}
        
    def on_market_data(self, event: MarketEvent):
        """处理行情数据"""
        bar = event.bar
        # 策略逻辑
        if self.should_buy(bar):
            self.send_buy_signal(bar)
            
    def should_buy(self, bar) -> bool:
        """买入条件"""
        return bar.close_price > bar.open_price * 1.02
        
    def send_buy_signal(self, bar):
        """发送买入信号"""
        signal = SignalEvent(
            symbol=bar.symbol,
            direction="LONG",
            strength=0.5,
            datetime=bar.datetime
        )
        # 发送信号到Portfolio
```

## 📋 开发计划

- [x] 数据结构和事件系统
- [x] 本地CSV数据加载
- [x] 问财选股器
- [x] 数据驱动层
- [ ] 回测引擎核心
- [ ] 投资组合管理
- [ ] 撮合执行系统
- [ ] 策略框架
- [ ] 性能分析工具
- [ ] 图表生成模块

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发规范

1. 遵循单一职责原则
2. 添加适当的异常处理
3. 编写单元测试
4. 更新相关文档

## 📄 许可证

MIT License

## 📞 联系

如有问题或建议，请提交Issue或联系项目维护者。

---

**注意**: 本项目仅用于学习和研究目的，不构成投资建议。使用本系统进行实际交易的风险由用户自行承担。