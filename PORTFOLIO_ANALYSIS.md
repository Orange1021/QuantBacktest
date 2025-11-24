# 投资组合仓位管理分析

## 当前仓位管理逻辑（硬编码）

### 1. 单只股票资金分配
**逻辑位置**: `Portfolio/portfolio.py:271-276`

```python
# 计算最大可买入数量（使用90%现金，预留10%作为缓冲）
available_cash = self.current_cash * 0.9
max_shares = int(available_cash / current_price)

# 应用A股规则：向下取整到100的倍数
target_volume = (max_shares // 100) * 100
```

**特点**:
- 每次买入使用 **90%的当前可用现金**
- 每只股票都是"全仓买入"策略
- 预留10%现金作为缓冲（防止价格波动导致现金为负）

### 2. 持仓数量限制
**逻辑位置**: `Portfolio/portfolio.py:263-269`

```python
# 风控检查2：检查是否已有该股票持仓（避免重复建仓）
if symbol in self.positions and self.positions[symbol] > 0:
    self.logger.info(f"已有持仓，忽略买入信号 {symbol}")
    return None
```

**特点**:
- ❌ **没有最大持仓数量限制**
- ✅ 不允许重复买入同一股票（必须清仓后才能再次买入）
- 理论上可以无限持有不同股票（直到现金耗尽）

### 3. 满仓判断
**逻辑位置**: `Portfolio/portfolio.py:254-261`

```python
# 风控检查1：是否已满仓（现金比例过低）
cash_ratio = self.current_cash / self.total_equity if self.total_equity > 0 else 1.0
if cash_ratio < 0.05:  # 现金比例低于5%认为满仓
    return None
```

**特点**:
- 现金比例低于5%时停止买入新股票
- 这是一个**软限制**，不是硬性的股票数量限制

### 4. 卖出策略
**逻辑位置**: `Portfolio/portfolio.py:338-381`

```python
# 检查持仓
current_position = self.positions.get(symbol, 0)

if current_position <= 0:
    return None

# 生成卖出订单（卖出全部持仓）
order = OrderEvent(
    ...
    volume=current_position,  # 清仓
    ...
)
```

**特点**:
- **全部卖出**（清仓），不支持部分卖出
- 估值低于1000元时忽略卖出信号（避免手续费占比过高）

---

## 存在的问题

### ❌ 问题1：不能同时持有多只股票
**场景示例**:
```
初始资金: 1,000,000元
买入股票A: 使用900,000元 → 剩余现金100,000元

此时股票B发出买入信号:
- available_cash = 100,000 * 0.9 = 90,000元
- 如果股票B价格 > 90,000元，则无法买入
- 或者只能买入很少数量（不足以买100股）

结论: 先买入的股票会占用大部分资金，导致后续股票无法买入
```

### ❌ 问题2：没有单只股票仓位上限
**风险**:
- 如果将所有资金投入一只股票，风险过于集中
- 没有分散投资的机制
- 不符合"不要把所有鸡蛋放在一个篮子里"的原则

### ❌ 问题3：硬编码参数无法配置
**硬编码的参数**:
- `0.9` (90%资金使用比例) - 写死在代码中
- `0.05` (5%现金比例作为满仓线) - 写死在代码中
- `1000.0` (最低卖出金额) - 写死在代码中
- `100` (100股倍数) - 这是A股规则，可以保留

**问题**:
- 无法通过配置文件调整策略
- 不同策略需要不同的仓位管理方式
- 缺乏灵活性

### ❌ 问题4：资金分配过于激进
**分析**:
- 使用90%现金买入意味着杠杆率很高
- 如果同时持有5只股票，理论上会使用 `5 × 90% = 450%` 的资金
- 实际上会被"现金比例<5%"的满仓检查阻止

**实际表现**:
- 回测显示最多持有26只股票（实际是22笔交易，有些是重复买卖）
- 但从不会同时持有多只，因为第一只股票就用完了大部分资金

---

## 对比业内标准实践

### 量化策略常见仓位管理方式

#### 方式A：等权重分配
```python
# 假设目标持仓10只股票
target_stock_count = 10
cash_per_stock = total_cash / target_stock_count

# 每只股票分配总资金的10%
volume = (cash_per_stock / price) // 100 * 100
```

#### 方式B：风险平价
```python
# 根据股票波动率分配资金
# 波动率高的股票分配较少资金
# 波动率低的股票分配较多资金
```

#### 方式C：信号强度加权
```python
# 买入信号强度高的股票分配更多资金
# 信号强度低的股票分配较少资金
```

#### 方式D：固定比例（单只股票上限）
```python
# 单只股票不超过总资金的20%
max_per_stock = total_cash * 0.20
volume = min(desired_volume, max_per_stock // price // 100 * 100)
```

---

## 建议优化方案

### 方案1：引入配置文件参数（快速改进）

**config.yaml 新增配置**:
```yaml
portfolio:
  # 仓位管理参数
  max_positions: 10              # 最大同时持仓数量
  cash_reserve_ratio: 0.10       # 现金预留比例 (10%)
  max_position_ratio: 0.15       # 单只股票最大仓位 (15%)
  min_sell_value: 1000.0         # 最低卖出金额
```

**代码修改**:
```python
# Portfolio/portfolio.py

# 从配置读取参数（带默认值）
self.max_positions = settings.get_config('portfolio.max_positions', 10)
self.cash_reserve_ratio = settings.get_config('portfolio.cash_reserve_ratio', 0.10)
self.max_position_ratio = settings.get_config('portfolio.max_position_ratio', 0.15)
self.min_sell_value = settings.get_config('portfolio.min_sell_value', 1000.0)

# 在买入逻辑中使用配置参数
def _process_buy_signal(self, event: SignalEvent):
    # 检查持仓数量限制
    if len(self.positions) >= self.max_positions:
        return None

    # 计算单只股票最大可买金额
    max_per_stock = self.total_equity * self.max_position_ratio
    available_cash = min(self.current_cash * (1 - self.cash_reserve_ratio), max_per_stock)

    # 后续计算...
```

### 方案2：分层架构（推荐）

```
Portfolio (基类)
├── BacktestPortfolio (回测专用)
│   └── DynamicPositionSizer (动态仓位计算器)
        ├── EqualWeightSizer (等权重)
        ├── RiskParitySizer (风险平价)
        └── FixedRatioSizer (固定比例)
```

### 方案3：策略驱动仓位管理（最灵活）

```python
class MACDKDJStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent):
        # 策略自己计算仓位大小
        if signal_is_strong:
            position_size = 0.20  # 20%仓位
        else:
            position_size = 0.05  # 5%仓位

        self.send_signal(symbol, Direction.LONG, position_size)

# Portfolio接收信号强度作为仓位参数
order.volume = total_equity * signal.strength / price
```

---

## 当前系统的适用场景

**适合**:
- ✅ 低频策略（每月交易几次）
- ✅ 趋势跟踪策略（持仓周期长）
- ✅ 单一股票策略（每次只持有1-2只）
- ✅ 回测验证（快速验证策略逻辑）

**不适合**:
- ❌ 高频策略（需要快速切换持仓）
- ❌ 多因子策略（同时持有20+只股票）
- ❌ 对冲策略（需要精细的仓位控制）
- ❌ 实盘交易（风险过于集中）

---

## 建议的下一步行动

**优先级排序**:

1. **P0 (紧急)**: 添加配置文件参数化
   - 让硬编码的值可配置
   - 不改变现有逻辑

2. **P1 (重要)**: 实现等权重分配
   - 支持同时持有多只股票
   - 提高资金利用率

3. **P2 (优化)**: 引入仓位管理器(Position Sizer)
   - 支持多种仓位策略
   - 提高架构灵活性

4. **P3 (高级)**: 策略驱动仓位
   - 信号强度决定仓位大小
   - 实现精细化资金管理
