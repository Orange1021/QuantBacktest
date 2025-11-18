# QuantBacktest - 量化回测与交易框架

## 📊 项目简介

**QuantBacktest** 是一个基于 **vn.py (实盘交易)** 和 **VectorBT (回测)** 的专业量化交易框架，支持多策略开发、回测和实盘交易。

### 核心特性

✅ **多策略支持**：插件化架构，轻松添加新策略
✅ **双引擎**：VectorBT（高速回测） + vn.py（实盘交易）
✅ **模块化设计**：数据层、策略层、执行层分离
✅ **配置驱动**：所有参数通过YAML配置文件管理
✅ **工业级代码**：类型提示、文档字符串、错误处理

### 技术架构

```
vn.py (实盘交易)  +  VectorBT (回测)
    ↓                    ↓
    └──────────────────┬─┘
                       ↓
                策略核心层
                       ↓
          ┌────────────┼────────────┐
          ↓            ↓            ↓
    持续下跌策略   均线交叉策略   你的策略...
```

---

## 📁 项目结构

```
QuantBacktest/
├── src/                          # 源代码
│   ├── core/                     # 核心模块
│   │   ├── __init__.py
│   │   ├── filter/               # 股票筛选
│   │   ├── position/             # 仓位管理
│   │   └── risk/                 # 风险控制
│   ├── data/                     # 数据层
│   │   ├── __init__.py
│   │   ├── models.py             # 数据模型（BarData, PositionData等）
│   │   └── provider.py           # 数据提供器接口
│   ├── strategy/                 # 策略层
│   │   ├── __init__.py
│   │   ├── base_strategy.py      # 策略基类
│   │   ├── factory.py            # 策略工厂
│   │   ├── continuous_decline.py # 持续下跌策略（示例）
│   │   └── ma_crossover.py       # 均线交叉策略（示例）
│   ├── execution/                # 执行层
│   │   ├── __init__.py
│   │   ├── vectorbt_backtester.py# VectorBT回测引擎
│   │   └── vnpy_executor.py      # vn.py实盘执行
│   └── utils/                    # 工具类
│       ├── __init__.py
│       ├── config.py             # 配置管理
│       └── logger.py             # 日志管理
├── configs/                      # 配置文件
│   ├── strategy/
│   │   ├── continuous_decline.yaml   # 持续下跌策略配置
│   │   └── ma_crossover.yaml         # 均线交叉策略配置
│   ├── market/
│   │   └── market.yaml               # 市场规则配置
│   └── live/
│       └── account.example.yaml      # 账户配置示例
├── data/                         # 数据存储
│   ├── raw/                      # 原始数据
│   ├── processed/                # 处理后数据
│   └── backtest_results/         # 回测结果
├── docs/                         # 文档
│   ├── design/
│   │   ├── architecture.md           # 系统架构设计
│   │   └── extensibility_analysis.md # 可扩展性分析
│   ├── api/
│   │   └── vnpy_vs_vectorbt.md       # API对比
│   └── DESIGN_SUMMARY.md         # 项目总结
├── scripts/                      # 运行脚本
│   ├── run_backtest.py          # 回测脚本v1
│   ├── run_backtest_v2.py       # 回测脚本v2（多策略）
│   └── run_live.py              # 实盘脚本
├── tests/                        # 测试
│   ├── unit/                     # 单元测试
│   └── integration/              # 集成测试
├── requirements.txt             # Python依赖
├── .gitignore                   # Git忽略配置
└── README.md                    # 本文档
```

---

## 🚀 快速开始

### 1. 环境准备（重要）

**⚠️ 注意**：**Termux无法运行此项目**（缺少CUDA，且vn.py难以编译）。请上传至GitHub后在电脑上运行。

**支持的运行环境：**
- **Windows 10/11**（推荐）
- **Ubuntu 20.04/22.04**（Linux）
- **macOS 11+**（Apple Silicon支持有限）

### 2. 安装步骤（Ubuntu/Windows）

**克隆项目：**

```bash
# 方式1：通过GitHub（推荐）
git clone https://github.com/your_username/QuantBacktest.git
cd QuantBacktest

# 方式2：直接解压上传的文件
cd QuantBacktest
```

**创建虚拟环境：**

```bash
# 1. 创建虚拟环境（推荐）
python -m venv venv

# 2. 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. 升级pip
pip install --upgrade pip setuptools wheel
```

**安装依赖：**

```bash
# 推荐：分步安装（可处理兼容性问题）

# 步骤1：安装基础科学计算库
pip install numpy pandas scipy matplotlib seaborn

# 步骤2：安装VectorBT（回测引擎）
pip install vectorbt

# 步骤3：安装Akshare（数据获取，不需要Token）
pip install akshare

# 步骤4：安装vn.py（实盘交易框架）
pip install vnpy

# 或者一键安装：
pip install -r requirements.txt

# 如果遇到安装错误，请查看FAQ
```

**验证安装：**

```python
# 测试VectorBT
python -c "import vectorbt; print(f'VectorBT version: {vectorbt.__version__}')"

# 测试Akshare
python -c "import akshare; print(f'Akshare version: {akshare.__version__}')"

# 测试vn.py
python -c "from vnpy.trader.engine import MainEngine; print('vn.py installed successfully!')"
```

### 3. 数据准备

**方式1：使用Akshare（无需Token，推荐新手）**

Akshare已经内置在项目配置中，可以直接使用。

**方式2：使用Tushare（需要Token，数据质量更高）**

1. 注册Tushare账号：https://tushare.pro/register
2. 获取Token：https://tushare.pro/user/token
3. 修改配置文件：

```bash
# 编辑配置文件
configs/strategy/continuous_decline.yaml
```

找到 `data.provider` 和 `data.tushare_token`：

```yaml
data:
  provider: "tushare"                  # 改为 tushare
  tushare_token: "你的Token"           # 填写你的Token
  local_data_dir: "data/raw"
  adjust_type: "qfq"
  price_field: "close"
```

### 4. 配置文件说明

**策略配置文件**：`configs/strategy/continuous_decline.yaml`

关键参数：

```yaml
strategy:
  filter_params:
    decline_days_threshold: 8          # 连续下跌天数
    market_cap_threshold: 1000000000   # 最小市值（10亿）

  entry_params:
    decline_percent_per_layer: 0.10    # 每层下跌10%
    position_percent_per_layer: 0.10   # 每层加仓10%
    max_layers: 10                     # 最大加仓层数

  risk_params:
    single_position_limit: 0.30        # 单票最大30%
    total_position_limit: 0.80         # 总仓位最大80%
    stop_loss_percent: 0.15            # 止损线15%

  capital_params:
    initial_capital: 10000000          # 初始资金1000万
    commission_rate: 0.0003            # 手续费万分之三
```

**市场配置文件**：`configs/market/market.yaml`

包含A股交易规则、时间、涨跌停等配置。通常无需修改。

### 5. 运行回测

**基础回测：**

```bash
# 使用默认配置（回测2020-2023年全市场股票）
python scripts/run_backtest.py

# 输出结果：
# - 回测报告（绩效指标）
# - 资金曲线图
# - 交易记录（CSV）
# - 持仓记录（CSV）
# 结果保存在：data/backtest_results/
```

**指定股票回测：**

```bash
# 回测特定股票（多个股票用逗号分隔）
python scripts/run_backtest.py \
  --symbols "000001.SZ,600000.SH,000002.SZ" \
  --start 2020-01-01 \
  --end 2023-12-31

# 使用自定义配置文件
python scripts/run_backtest.py \
  --config configs/strategy/continuous_decline.yaml \
  --start 2022-01-01 \
  --end 2022-12-31
```

**查看结果：**

回测完成后，在 `data/backtest_results/` 目录下会生成：
- `performance_report.html`: 绩效报告（网页版）
- `trades.csv`: 交易明细
- `positions.csv`: 持仓明细
- `equity_curve.png`: 资金曲线图

**关键指标：**
- **总收益率**：策略总盈利
- **年化收益率**：年化后的收益率
- **最大回撤**：最大亏损比例
- **夏普比率**：风险调整后的收益
- **胜率**：盈利交易占比
- **盈亏比**：平均每笔盈利 / 平均每笔亏损

### 6. 运行实盘（vn.py）

**⚠️ 警告**：实盘交易有风险，请先充分测试并理解策略逻辑！

```bash
# 编辑实盘账户配置
cp configs/live/account.example.yaml configs/live/account.yaml
```

修改 `account.yaml`：

```yaml
account:
  investor_id: "你的期货账户"
  password: "你的密码"
  broker_id: "你的经纪商代码"
  td_address: "交易服务器地址"
  md_address: "行情服务器地址"
```

启动实盘：

```bash
python scripts/run_live.py \
  --config configs/strategy/continuous_decline.yaml \
  --symbols "600000.SH,000001.SZ"
```

---

## 📖 功能说明

### VectorBT：回测引擎

VectorBT是一个高性能的回测库，特色：
- ✅ **向量化计算**：利用NumPy/Pandas，回测速度极快（比事件驱动快1000倍）
- ✅ **并行处理**：支持多参数优化
- ✅ **丰富的统计指标**：内置50+种绩效指标
- ✅ **可视化**：一键生成专业图表

在本项目中：
- 快速验证策略想法
- 批量回测多只股票
- 参数优化

**核心类**：`src/execution/vectorbt_backtester.py`

---

### vn.py：实盘交易框架

vn.py是国内最流行的量化交易框架，特色：
- ✅ **多市场支持**：期货(CTP)、股票(XTP)、港股美股(富途等)
- ✅ **事件驱动**：精确模拟实盘交易
- ✅ **模块化设计**：易于扩展

在本项目中：
- 对接实盘交易接口
- 订单管理
- 风险管理

**核心类**：`src/execution/vnpy_executor.py`

---

### 策略核心模块

#### 1. 股票筛选器：`StockFilter`

职责：筛选符合"连续下跌8天 + 市值≥10亿"的股票

```python
from src.core.filter.stock_filter import StockFilter

# 使用示例（在回测中）
filter = StockFilter(data_provider)
eligible_stocks = filter.get_eligible_stocks(date='2023-01-01')
# 返回：['000001.SZ', '600000.SH', ...]
```

**筛选逻辑：**
```python
# 伪代码
def is_continuous_decline(prices, days=8):
    """连续下跌N天"""
    for i in range(1, days):
        if prices[-i] >= prices[-i-1]:  # 某天未下跌
            return False
    return True

def has_enough_market_cap(symbol, min_cap=1e9):
    """市值是否充足"""
    market_cap = get_market_cap(symbol)
    return market_cap >= min_cap
```

#### 2. 信号生成器：`SignalGenerator`

职责：生成买入/卖出信号

**买入信号**（加仓）：
```python
# 当前价格 vs 持仓成本
current_price = 9.0        # 当前价
entry_price = 10.0         # 成本价

# 跌幅计算
decline = (entry_price - current_price) / entry_price
# decline = (10 - 9) / 10 = 0.10 = 10%

# 判断是否触发加仓
if decline >= 0.10 * (layer + 1):
    generate_buy_signal()
```

**卖出信号**（清仓）：
```python
# 关键状态：has_risen（是否上涨过）
if position.has_risen == False:
    # 还没上涨过
    if current_price > entry_price:
        position.has_risen = True  # 标记已上涨
else:
    # 已经上涨过，检查是否下跌
    if current_price < last_price:
        generate_sell_signal()  # 清仓
```

#### 3. 仓位管理器：`PositionManager`

职责：管理资金和持仓

**首次建仓：**
```python
initial_capital = 10_000_000  # 1000万
initial_percent = 0.05        # 首仓5%
position_size = 10_000_000 * 0.05 = 500_000  # 50万
```

**分层加仓：**
```python
# 每次下跌10%，加仓初始仓位的10%
initial_position = 500_000

layer_0: 500_000                           # 首次建仓
layer_1: 500_000 + 500_000 * 0.10 = 550_000   # 下跌10%
layer_2: 550_000 + 500_000 * 0.10 = 600_000   # 下跌20%
layer_3: 600_000 + 500_000 * 0.10 = 650_000   # 下跌30%
# ...
```

**风险控制：**
- 单票仓位 ≤ 30%
- 总仓位 ≤ 80%
- 最大加仓层数 ≤ 10层

---

## 🔧 修改策略参数

在 `configs/strategy/continuous_decline.yaml` 中可以调整所有参数：

### 选股参数

```yaml
filter_params:
  decline_days_threshold: 8           # 调整下跌天数（例如改为5天更激进）
  market_cap_threshold: 1000000000   # 调整市值门槛（例如改为50亿更保守）
```

### 入场参数

```yaml
entry_params:
  decline_percent_per_layer: 0.10     # 调整每层的下跌阈值（例如改为5%加仓更频繁）
  position_percent_per_layer: 0.10    # 调整每层的加仓比例
  max_layers: 10                      # 调整最大加仓层数（防止无限加仓）
```

### 风控参数

```yaml
risk_params:
  single_position_limit: 0.30         # 单票最大仓位
  total_position_limit: 0.80          # 总仓位限制
  stop_loss_percent: 0.15            # 止损线（强制止损）
  daily_loss_limit: 0.05             # 单日亏损限制（5%）
```

---

## 🎯 多策略支持（新增）

框架支持在同一系统中运行多个策略，实现多策略组合。

### 查看可用策略

```bash
python scripts/run_backtest_v2.py --list

# 输出示例：
# 已注册的策略
# ============================================================
#   continuous_decline       -> ContinuousDeclineStrategy
#   ma_crossover             -> MACrossoverStrategy
# ============================================================
```

### 运行不同策略

**持续下跌策略（默认）**:
```bash
python scripts/run_backtest_v2.py --strategy continuous_decline
```

**均线交叉策略**:
```bash
python scripts/run_backtest_v2.py --strategy ma_crossover
```

**使用自定义配置**:
```bash
python scripts/run_backtest_v2.py --strategy ma_crossover --config configs/strategy/ma_crossover.yaml
```

### 添加新策略（3步骤）

#### 步骤1：创建策略类

```python
# src/strategy/my_strategy.py
from src.strategy.base_strategy import BaseStrategy
from src.strategy.factory import StrategyRegistry

@StrategyRegistry.register('my_strategy')
class MyStrategy(BaseStrategy):
    """你的策略"""

    def initialize(self, context):
        """初始化"""
        pass

    def on_bar(self, bar, context):
        """K线处理"""
        # 你的交易逻辑
        if should_buy(bar):
            return {'signals': [buy_signal]}

        if should_sell(bar):
            return {'signals': [sell_signal]}

        return None
```

#### 步骤2：创建配置文件

```yaml
# configs/strategy/my_strategy.yaml
strategy:
  name: "my_strategy"
  params:
    param1: value1
    param2: value2
```

#### 步骤3：运行新策略

```bash
python scripts/run_backtest_v2.py --strategy my_strategy
```

详细指南请查看：`docs/design/extensibility_analysis.md`

### 策略复用度分析

| 组件 | 复用度 | 说明 |
|------|--------|------|
| **数据层** | 100% | 完全可复用，无需修改 |
| **执行层** | 100% | VectorBT/vn.py支持任意策略 |
| **风控层** | 90% | 可配置，微调即可 |
| **仓位管理** | 80% | 可选复用 |
| **策略逻辑** | 40% | 需要重写核心逻辑 |

**开发新策略时间**：熟悉框架后，**2-3天**可完成一个策略。



## 📊 回测结果分析

### 典型报告结构

回测完成后，会生成HTML报告，包含：

1. **资金曲线图**
   - 蓝线：策略收益
   - 红线：基准收益（上证指数）
   - 绿线：最大回撤

2. **月度收益热力图**
   - 不同月份的表现
   - 识别季节性规律

3. **绩效指标汇总**
   - 总收益、年化收益
   - 夏普比率、索提诺比率
   - 最大回撤、最长回撤期
   - 胜率、盈亏比
   - 平均持仓天数

4. **交易明细**
   - 每笔交易的买卖点
   - 盈亏分析

5. **持仓分析**
   - 行业分布
   - 市值分布

### 如何解读结果

**优秀策略的特征：**
- 夏普比率 > 1.0
- 年化收益 / 最大回撤 > 1.0
- 盈亏比 > 1.5
- 胜率 > 40%（趋势策略）

**需要警惕的信号：**
- 最大回撤过大（> 30%）
- 单次亏损过大（> 5%）
- 过度集中（单票>30%）

---

## ⚠️ 风险提示

### 策略固有风险

1. **价值陷阱**：持续下跌可能反映基本面恶化
2. **流动性风险**：小市值股票成交困难
3. **尾部风险**：黑天鹅事件导致持续暴跌
4. **政策风险**：监管政策变化影响市场

### 使用建议

- **分散持仓**：至少持仓10-20只股票
- **分批建仓**：不要一次性满仓
- **严格止损**：设置15-20%的止损线
- **定期复盘**：每月评估策略有效性
- **小资金测试**：实盘先用小资金验证

**重要声明**：本策略仅供学习和研究使用，实盘交易盈亏自负！

---

## 📚 进一步学习

### 相关资源

- **VectorBT文档**：https://vectorbt.dev
- **vn.py文档**：https://www.vnpy.com
- **Tushare数据**：https://tushare.pro (需要注册获取Token)
- **Akshare数据**：https://akshare.readthedocs.io

### 推荐书籍

- 《量化投资：以Python为工具》
- 《海龟交易法则》
- 《主动投资组合管理》

---

## 🤝 贡献与反馈

欢迎提交Issue和PR！

**项目地址**：
```bash
git clone https://github.com/your_username/QuantBacktest.git
```

**意见反馈**：
- GitHub Issues：https://github.com/your_username/QuantBacktest/issues
- 邮箱：your_email@example.com

---

## 📄 许可证

MIT License

---

## ❓ FAQ（常见问题）

### Q1: Termux上能运行吗？
**A:** 不能。本项目的依赖（vn.py、VectorBT等）需要编译C++扩展，且需要CUDA支持复杂计算。请在Windows/Linux/macOS电脑上运行。

### Q2: vn.py安装失败怎么办？
**A:**
1. 确保安装Python 3.8-3.10（vn.py对3.11+支持不完善）
2. 安装编译工具：
   - Ubuntu: `sudo apt-get install build-essential python3-dev`
   - Windows: 安装Visual Studio Build Tools
3. 使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple vnpy`
4. 如果仍失败，可先跳过vn.py，只使用VectorBT进行回测

### Q3: 数据获取失败/速度慢？
**A:**
1. 使用Tushare（需Token），稳定性更高
2. 使用Akshare（无需Token）适合简单测试
3. 首次运行后，将数据保存到本地，后续从本地加载（速度快）

### Q4: 回测内存不足/崩溃？
**A:**
1. 减少回测股票数量（--symbols参数指定少数几只）
2. 缩短回测时间（--start和--end参数）
3. 在配置文件中减少max_workers（并发线程数）
4. 在64位系统上运行，并确保有足够的内存（8GB+）

### Q5: 参数如何优化？
**A:**
1. 使用VectorBT的参数优化功能：
```python
import vectorbt as vbt

# 定义参数范围
param_product = vbt.utils.params.create_param_product(
    (range(5, 30), range(10, 50), range(20, 100)),
    names=['fast_window', 'slow_window', 'exit_window']
)

# 批量回测
pf = vbt.Portfolio.from_signals(
    close,
    entries=entries,
    exits=exits,
    param_product=param_product
)

# 找到最优参数
best_idx = pf.sharpe_ratio().idxmax()
best_params = param_product.loc[best_idx]
```

### Q6: 如何接入实盘交易？
**A:**
1. 开通量化交易账户（期货：CTP；股票：XTP）
2. 修改配置文件：`configs/live/account.yaml`
3. 使用少量资金测试
4. 联系vn.py社区获取技术支持

### Q7: 策略在回测中表现很好，但实盘亏损？
**A:**
这是常见现象，原因可能包括：
1. **过拟合**：参数过度优化，不适应新数据
2. **幸存者偏差**：回测数据没有包含退市股票
3. **未来函数**：使用了未来信息（确保shift数据）
4. **滑点和冲击成本**：实盘成交价格劣于回测
5. **市场变化**：策略失效

**解决方案**:
- 使用交叉验证
- 留出样本外数据测试
- 降低杠杆
- 添加更多约束条件

### Q8: 如何添加新策略？
**A:**
1. 继承 `src/strategy/base_strategy.py`
2. 实现 `on_bar()` 方法
3. 编写信号生成逻辑
4. 参考 `src/strategy/continuous_decline.py` 示例

---

## 📌 版本历史

- **v1.0.0** (2025-01-18): 初始版本
  - 完成策略逻辑设计
  - 实现核心模块框架
  - 添加详细文档

---

**最后更新**：2025-01-18
**作者**：Claude Code
# QuantBacktest
