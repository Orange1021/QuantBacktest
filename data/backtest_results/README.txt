# 回测结果文件说明

## 文件位置
data/backtest_results/

## 文件说明

### 1. trades.csv (交易记录)
- 包含所有买卖交易的详细信息
- 列包括：id, 股票代码, 数量, 入场价格, 出场价格, 盈亏, 收益率等
- 大小：约9KB
- 用途：查看每笔交易的明细

### 2. positions.csv (持仓记录)
- 包含持仓的详细信息
- 大小：约9KB
- 用途：分析持仓分布和变化

### 3. performance_summary.json (绩效汇总 - JSON)
- 包含20+项绩效指标
- 包括：总收益率、年化收益率、夏普比率、最大回撤、胜率等
- 大小：约350字节
- 用途：程序读取和自动化分析

### 4. performance_summary.csv (绩效汇总 - CSV)
- 与JSON相同的数据，CSV格式
- 大小：约244字节
- 用途：Excel直接打开查看

### 5. performance_summary.txt (绩效摘要)
- 文本格式的绩效摘要
- 大小：约18字节
- 用途：快速查看

### 6. performance_chart.html (绩效图表)
- 交互式资金曲线图
- 用途：可视化分析回测结果

## 绩效指标说明

- **总收益率**：回测期间的总收益百分比
- **年化收益率**：年化后的收益率
- **夏普比率**：风险调整后的收益指标
- **最大回撤**：最大亏损幅度
- **总交易次数**：总交易笔数
- **胜率**：盈利交易的比例

## 使用方式

1. **查看交易明细**：
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('data/backtest_results/trades.csv'); print(df.head())"
   ```

2. **查看绩效指标**：
   ```bash
   python -c "import json; import pprint; data = json.load(open('data/backtest_results/performance_summary.json')); pprint.pprint(data)"
   ```

3. **Excel打开**：直接双击performance_summary.csv

4. **查看图表**：用浏览器打开performance_chart.html
