# 数据提供器使用指南

## 📊 概述

本项目实现了参数化数据提供器架构，支持灵活切换多种数据源（本地CSV、Tushare、Akshare），并提供自动降级和数据缓存功能。

**最新更新（2025-11-18）**：
- ✅ 已实现完整的智能降级系统（fallback_chain）
- ✅ 本地CSV提供器性能优化至~30ms/股票
- ✅ 支持多数据源混合使用
- ✅ 自动处理缺失文件和无效数据
- ✅ 测试验证：支持5346只股票全市场扫描

## 🎯 核心特性

| 特性 | 状态 | 说明 |
|------|------|------|
| 本地CSV | ✅ 生产就绪 | 超高速，~30ms/股票，支持LRU缓存 |
| Tushare | ✅ 集成完成 | 需要Token，网络依赖 |
| Akshare | ⚠️ 可选 | 免费但较慢，备用方案 |
| 自动降级 | ✅ 已测试 | 智能切换数据源 |
| 数据缓存 | ✅ LRU缓存 | 命中率50-90% |
| 全市场支持 | ✅ 已验证 | 5346只股票 |

## 📈 性能对比（基于实际测试）

| 数据源 | 单只股票(30天) | 100只股票(1年) | 缓存命中率 | 优缺点 |
|--------|---------------|----------------|-----------|--------|
| **本地CSV** | ~30ms | ~3s | 50-90% | ⭐ **推荐**：速度快、稳定、离线可用 |
| Tushare | ~1-2s | ~100s | N/A | 数据完整、官方接口，但需Token |
| Akshare | ~2-5s | ~200s | N/A | 免费、无需Token，但较慢 |

**实测数据**（2025-11-18）：
- 熊市（2024-02-05）：筛选1611只股票，耗时约2分钟
- 震荡市（2024-01-15）：筛选34只股票，耗时约2秒
- 牛市（2024-10-15）：筛选0只股票，耗时约2秒
- 自动降级功能正常：Tushare失败时自动尝试本地数据

## 🎯 核心特性

✅ **多数据源支持**：本地CSV、Tushare、Akshare
✅ **参数化配置**：一行配置切换数据源
✅ **自动降级**：主数据源失败自动尝试备用源
✅ **智能缓存**：LRU缓存减少I/O开销
✅ **数据清洗**：自动验证TS代码、过滤未来日期
✅ **性能优化**：支持并行读取、Pickle缓存

## 📁 项目结构

```
QuantBacktest/
├── src/
│   └── data/
│       ├── provider.py              # 数据提供器基类
│       ├── local_csv_provider.py    # 本地CSV提供器
│       ├── provider_factory.py      # 工厂和代理
│       └── __init__.py
├── configs/
│   └── data/
│       └── source.yaml             # 数据源配置
└── scripts/
    ├── demo_data_provider.py       # 演示脚本
    ├── validate_data.py            # 验证脚本
    └── run_backtest.py             # 回测脚本
```

## 🔧 快速开始

### 1. 配置数据源

编辑 `configs/data/source.yaml`：

```yaml
data:
  # 主数据源
  primary_provider: "local_csv"  # 可选项: local_csv, tushare, akshare

  # 降级链（主数据源失败时按顺序尝试）
  fallback_chain:
    - "local_csv"
    - "tushare"
    - "akshare"

  # 启用自动降级
  auto_fallback: true

  # 本地CSV配置
  local_csv:
    enabled: true
    data_dir: "C:/Users/123/A股数据/个股数据"  # 修改为你的数据目录
    cache:
      enabled: true
      max_size: 100  # 缓存100只股票

  # Tushare配置
  tushare:
    enabled: true
    token: "${TUSHARE_TOKEN}"  # 设置环境变量或在文件内填写
```

### 2. 基本使用

```python
from src.data import DataProviderFactory
from src.utils.config import ConfigManager

# 加载配置
config = ConfigManager.load_config('configs/data/source.yaml')

# 创建工厂
factory = DataProviderFactory(config)

# 获取主数据源（支持降级）
provider = factory.create_proxy()

# 获取K线数据
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
df = provider.get_daily_bars("000001.SZ", start_date, end_date)

print(df.head())
```

## 📈 性能对比

| 数据源 | 单只股票(30天) | 100只股票(1年) | 优点 | 缺点 |
|--------|---------------|----------------|------|------|
| 本地CSV | ~30ms | ~3s | 速度快、稳定、离线可用 | 需要本地数据 |
| Tushare | ~1-2s | ~100s | 数据完整、官方接口 | 网络依赖、需要token |
| Akshare | ~2-5s | ~200s | 免费、无需token | 不稳定、速度慢 |

## 🎭 使用场景

### 场景1：开发/调试

```yaml
# 使用本地CSV，快速验证策略
primary_provider: "local_csv"
```

```python
# 策略代码无需改变
# 只需切换配置文件即可
df = provider.get_daily_bars(symbol, start, end)
```

### 场景2：实盘交易

```yaml
# 使用Tushare实时数据
primary_provider: "tushare"
fallback_chain:
  - "tushare"
  - "local_csv"  # Tushare失败时使用本地数据
```

### 场景3：数据完整性检查

```python
# 对比多个数据源
for name in ['local_csv', 'tushare', 'akshare']:
    provider = factory.get_provider(name)
    df = provider.get_daily_bars(symbol, start, end)
    print(f"{name}: {len(df)} 条数据")
```

## 🔍 数据验证

运行验证脚本检查数据源：

```bash
# 验证所有数据源
python scripts/validate_data.py

# 验证本地CSV
python scripts/validate_data.py --provider local_csv

# 验证并生成详细报告
python scripts/validate_data.py --detailed --output report.json

# 性能测试
python scripts/validate_data.py --profile
```

## 📊 监控和统计

### 查看缓存统计

```python
# 如果提供器支持缓存
if hasattr(provider, 'get_stats'):
    stats = provider.get_stats()
    print(f"缓存命中率: {stats['hit_rate']:.2%}")
    print(f"缓存大小: {stats['cache_size']}")
```

### 查看降级日志

```python
# 如果使用代理
proxy = factory.create_proxy()
stats = proxy.get_fallback_stats()

print(f"总降级次数: {stats['total']}")
print(f"成功次数: {stats['success']}")
print(f"失败次数: {stats['fail']}")
print(f"成功率: {stats['success_rate']:.2%}")
```

降级日志保存在 `data/fallback_log.txt`。

## 🚀 进阶功能

### 缓存调优

```yaml
local_csv:
  cache:
    enabled: true
    max_size: 200  # 增加缓存大小
```

### 并行读取

```yaml
local_csv:
  parallel:
    enabled: true
    max_workers: 8  # 8线程并行
```

### 数据清洗

```yaml
local_csv:
  cleaning:
    validate_tscode: true   # 验证TS代码
    filter_future: true     # 过滤未来日期
```

## ⚠️ 注意事项

1. **本地数据路径**：确保 `data_dir` 配置正确，且文件可读
2. **Tushare Token**：需要注册并获取Token，建议设置环境变量
3. **缓存大小**：根据内存大小调整，默认100只股票约占用500MB
4. **降级链**：建议至少配置2个数据源，确保高可用
5. **日志文件**：定期清理 `logs/` 和 `data/fallback_log.txt`

## 🎯 最佳实践

### 1. 开发环境
```yaml
primary_provider: "local_csv"
auto_fallback: false  # 不降级，快速失败
```

### 2. 生产环境
```yaml
primary_provider: "tushare"
auto_fallback: true   # 启用降级
fallback_chain:
  - "tushare"
  - "local_csv"
```

### 3. 大规模回测
```yaml
local_csv:
  cache:
    max_size: 500      # 增大缓存
  parallel:
    enabled: true      # 启用并行
    max_workers: 16    # 增加线程
```

## 📚 API参考

### DataProviderFactory

- `get_primary_provider()` - 获取主数据源
- `get_provider(name)` - 获取指定数据源
- `get_fallback_chain()` - 获取降级链
- `create_proxy()` - 创建降级代理（推荐）
- `list_providers()` - 列出所有可用数据源

### DataProviderProxy

- `get_daily_bars(symbol, start, end)` - 获取K线（自动降级）
- `get_market_cap(symbols, date)` - 获取市值
- `get_stock_universe(date, market)` - 获取股票池
- `get_fallback_stats()` - 获取降级统计

### LocalCSVDataProvider

- `get_stats()` - 获取缓存统计
- `clear_cache()` - 清空缓存

## 🐛 故障排查

### 问题1：无法加载本地数据

```python
# 检查数据目录
ls C:/Users/123/A股数据/个股数据

# 验证单个文件
python -c "
import pandas as pd
df = pd.read_csv('000001.csv')
print(df.head())
"
```

### 问题2：Tushare Token错误

```bash
# 设置环境变量
export TUSHARE_TOKEN="your_token_here"

# 或修改配置文件
tushare:
  token: "your_token_here"
```

### 问题3：缓存不生效

```python
# 检查命中率
stats = provider.get_stats()
print(f"命中率过低: {stats['hit_rate']:.2%}")

# 增大缓存
provider = LocalCSVDataProvider(..., cache_size=200)
```

## 📞 支持

- 问题反馈：GitHub Issues
- 文档查看：docs/data_provider_usage.md
- 示例代码：scripts/demo_data_provider.py

## 📄 许可证

MIT License
