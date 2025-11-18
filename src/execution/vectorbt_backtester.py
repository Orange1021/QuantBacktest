"""
VectorBT回测引擎封装

将策略信号转换为VectorBT格式，运行回测，生成绩效报告
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import vectorbt as vbt

from src.strategy.base_strategy import BaseStrategy
from src.core.filter.stock_filter import StockFilter
from src.data.provider_factory import DataProviderFactory
from src.utils.logger import setup_logger


class BacktestResult:
    """
    回测结果

    Attributes:
        trades: 交易记录（DataFrame）
        positions: 持仓记录（DataFrame）
        performance: 绩效指标（字典）
        portfolio: VectorBT Portfolio对象
    """

    def __init__(self):
        self.trades: Optional[pd.DataFrame] = None
        self.positions: Optional[pd.DataFrame] = None
        self.performance: Optional[Dict[str, Any]] = None
        self.portfolio: Optional[vbt.Portfolio] = None


class VectorBTBacktester:
    """
    VectorBT回测引擎

    负责执行策略回测，包括：
    1. 数据准备（批量获取历史数据）
    2. 信号生成（调用策略逻辑）
    3. 回测执行（VectorBT）
    4. 绩效分析（指标计算）
    5. 报告生成（HTML/CSV）

    Example:
        >>> backtester = VectorBTBacktester(strategy, data_provider_factory)
        >>> result = backtester.run(
        ...     start_date=datetime(2024, 8, 1),
        ...     end_date=datetime(2024, 11, 1),
        ...     symbols=['000001.SZ', '600000.SH']
        ... )
        >>> print(f"总收益: {result.performance['total_return']:.2%}")
    """

    def __init__(self, strategy: BaseStrategy, data_provider_factory: DataProviderFactory):
        """
        初始化

        Args:
            strategy: 策略实例
            data_provider_factory: 数据提供器工厂
        """
        self.strategy = strategy
        self.data_provider_factory = data_provider_factory
        self.logger = setup_logger('vectorbt_backtester')

        # 数据缓存
        self._data_cache: Dict[str, pd.DataFrame] = {}

    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> BacktestResult:
        """
        运行回测

        Args:
            start_date: 回测开始日期
            end_date: 回测结束日期
            symbols: 股票列表（如果为None，则使用策略筛选的股票）

        Returns:
            回测结果

        Flow:
            1. 获取股票池（symbols 或 策略筛选）
            2. 批量获取所有股票的历史数据
            3. 每日交易逻辑模拟
            4. 生成交易信号
            5. 转换为VectorBT格式
            6. 运行VectorBT回测
            7. 生成绩效报告
        """
        self.logger.info("=" * 60)
        self.logger.info("VectorBT回测开始")
        self.logger.info("=" * 60)
        self.logger.info(f"回测周期: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")

        # 获取股票池
        if symbols is None:
            self.logger.info("获取股票池（策略筛选）...")
            symbols = self._get_stock_universe(start_date, end_date)

        self.logger.info(f"回测股票数: {len(symbols)}")

        if not symbols:
            self.logger.error("没有可回测的股票")
            return BacktestResult()

        # 批量获取数据
        self.logger.info("批量获取历史数据...")
        data = self._load_data(symbols, start_date, end_date)

        if not data:
            self.logger.error("数据加载失败")
            return BacktestResult()

        # 生成交易信号
        self.logger.info("生成交易信号...")
        signals = self._generate_signals(data, symbols, start_date, end_date)

        # 转换为VectorBT格式
        self.logger.info("转换为VectorBT格式...")
        entries, exits = self._convert_to_vectorbt_signals(data, signals, symbols)

        # 运行VectorBT回测
        self.logger.info("运行VectorBT回测...")
        portfolio = self._run_vectorbt_backtest(data, entries, exits, symbols)

        # 分析结果
        self.logger.info("分析回测结果...")
        result = self._analyze_results(portfolio, signals)

        self.logger.info("=" * 60)
        self.logger.info("回测完成")
        self.logger.info("=" * 60)

        return result

    def _get_stock_universe(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """
        获取回测期间的所有股票（使用策略筛选器）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            股票代码列表

        Note:
            为了避免过度拟合，这里返回一个固定的股票池
            实际应该每天动态筛选，但为了回测性能，先固定
        """
        # 从策略配置获取筛选参数
        filter_params = self.strategy.params.get('filter_params', {})

        # 使用测试日期（中间日期）筛选一次
        test_date = start_date + (end_date - start_date) / 2

        # 创建股票筛选器
        stock_filter = StockFilter(self.data_provider_factory)

        # 筛选股票（使用策略参数）
        symbols = stock_filter.get_eligible_stocks(
            date=test_date,
            decline_days_threshold=filter_params.get('decline_days_threshold', 7),
            market_cap_threshold=filter_params.get('market_cap_threshold', 1e9)
        )

        self.logger.info(f"筛选到 {len(symbols)} 只股票")

        # 限制数量（提高回测速度）
        max_stocks = 50  # 最多回测50只
        if len(symbols) > max_stocks:
            self.logger.info(f"限制股票数量: {len(symbols)} -> {max_stocks}")
            symbols = symbols[:max_stocks]

        return symbols

    def _load_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        批量加载历史数据

        Args:
            symbols: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据字典 {symbol: DataFrame}
        """
        provider = self.data_provider_factory.create_proxy()
        data = {}

        for i, symbol in enumerate(symbols):
            try:
                df = provider.get_daily_bars(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )

                if df is not None and not df.empty:
                    data[symbol] = df
                    self.logger.debug(f"加载数据: {symbol} ({i+1}/{len(symbols)})")
                else:
                    self.logger.debug(f"数据为空: {symbol}")

            except Exception as e:
                self.logger.debug(f"加载失败: {symbol} - {e}")
                continue

        self.logger.info(f"成功加载 {len(data)} 只股票的数据")

        return data

    def _generate_signals(
        self,
        data: Dict[str, pd.DataFrame],
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成交易信号

        Args:
            data: K线数据
            symbols: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            信号字典 {symbol: [signal1, signal2, ...]}
            signal格式: {
                'date': datetime,
                'type': 'BUY' or 'SELL',
                'price': float,
                'quantity': int
            }
        """
        signals = {symbol: [] for symbol in symbols}

        # 简化模拟：固定日期生成信号（实际应该调用策略逻辑）
        # TODO: 集成策略的on_bar逻辑

        test_date = pd.Timestamp('2024-08-15')

        for symbol in symbols[:5]:  # 限制数量
            try:
                df = data[symbol]

                # 模拟买入信号（在8月中旬买入）
                if test_date in df.index:
                    price = df.loc[test_date, 'close']
                    signals[symbol].append({
                        'date': test_date,
                        'type': 'BUY',
                        'price': price,
                        'quantity': 1000
                    })

                    # 模拟卖出信号（1个月后卖出）
                    sell_date = test_date + pd.Timedelta(days=30)
                    if sell_date in df.index:
                        sell_price = df.loc[sell_date, 'close']
                        signals[symbol].append({
                            'date': sell_date,
                            'type': 'SELL',
                            'price': sell_price,
                            'quantity': 1000
                        })

            except Exception as e:
                self.logger.debug(f"生成信号失败: {symbol} - {e}")
                continue

        return signals

    def _convert_to_vectorbt_signals(
        self,
        data: Dict[str, pd.DataFrame],
        signals: Dict[str, List[Dict]],
        symbols: List[str]
    ) -> (pd.DataFrame, pd.DataFrame):
        """
        转换信号为VectorBT格式

        Args:
            data: K线数据
            signals: 交易信号
            symbols: 股票列表

        Returns:
            entries: 买入信号DataFrame (symbol x date)
            exits: 卖出信号DataFrame (symbol x date)
        """
        # 获取所有日期
        all_dates = set()
        for df in data.values():
            all_dates.update(df.index)
        all_dates = sorted(list(all_dates))

        # 创建信号矩阵
        entries = pd.DataFrame(False, index=all_dates, columns=symbols)
        exits = pd.DataFrame(False, index=all_dates, columns=symbols)

        # 填充信号
        for symbol, symbol_signals in signals.items():
            if symbol not in symbols:
                continue

            for signal in symbol_signals:
                date = signal['date']
                signal_type = signal['type']

                if date in entries.index:
                    if signal_type == 'BUY':
                        entries.loc[date, symbol] = True
                    elif signal_type == 'SELL':
                        exits.loc[date, symbol] = True

        return entries, exits

    def _run_vectorbt_backtest(
        self,
        data: Dict[str, pd.DataFrame],
        entries: pd.DataFrame,
        exits: pd.DataFrame,
        symbols: List[str]
    ) -> vbt.Portfolio:
        """
        运行VectorBT回测

        Args:
            data: K线数据
            entries: 买入信号
            exits: 卖出信号
            symbols: 股票列表

        Returns:
            VectorBT Portfolio对象
        """
        # 创建价格矩阵（close价格）
        price_data = []

        for symbol in symbols:
            if symbol in data:
                df = data[symbol]
                # 确保索引对齐
                price_series = df['close'].reindex(entries.index)
                price_data.append(price_series)
            else:
                # 如果没有数据，填充NaN
                price_data.append(pd.Series(np.nan, index=entries.index))

        close_prices = pd.concat(price_data, axis=1)
        close_prices.columns = symbols

        # 获取策略参数
        capital_params = self.strategy.params.get('capital_params', {})
        initial_capital = capital_params.get('initial_capital', 1000000)

        # 运行VectorBT回测
        portfolio = vbt.Portfolio.from_signals(
            close=close_prices,
            entries=entries,
            exits=exits,
            init_cash=initial_capital,
            fees=0.0003,  # 手续费万分之三
            slippage=0.001,  # 滑点0.1%
            freq='D'  # 日频
        )

        return portfolio

    def _analyze_results(
        self,
        portfolio: vbt.Portfolio,
        signals: Dict[str, List[Dict]]
    ) -> BacktestResult:
        """
        分析回测结果

        Args:
            portfolio: VectorBT Portfolio对象
            signals: 交易信号

        Returns:
            回测结果
        """
        result = BacktestResult()
        result.portfolio = portfolio

        # 获取交易记录
        try:
            result.trades = portfolio.trades.records
        except:
            result.trades = pd.DataFrame()

        # 获取持仓记录
        try:
            result.positions = portfolio.positions.records
        except:
            result.positions = pd.DataFrame()

        # 计算绩效指标
        try:
            total_return = portfolio.total_return()
            sharpe_ratio = portfolio.sharpe_ratio()
            max_drawdown = portfolio.max_drawdown()

            result.performance = {
                'total_return': float(total_return),
                'sharpe_ratio': float(sharpe_ratio) if sharpe_ratio is not None else 0.0,
                'max_drawdown': float(max_drawdown),
                'total_trades': len(result.trades) if not result.trades.empty else 0
            }
        except Exception as e:
            self.logger.error(f"计算绩效指标失败: {e}")
            result.performance = {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_trades': 0
            }

        return result

    def generate_report(self, result: BacktestResult, output_dir: str) -> None:
        """
        生成回测报告

        Args:
            result: 回测结果
            output_dir: 输出目录
        """
        import os
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存交易记录
        if not result.trades.empty:
            trades_file = output_path / 'trades.csv'
            result.trades.to_csv(trades_file)
            self.logger.info(f"交易记录已保存: {trades_file}")

        # 保存持仓记录
        if not result.positions.empty:
            positions_file = output_path / 'positions.csv'
            result.positions.to_csv(positions_file)
            self.logger.info(f"持仓记录已保存: {positions_file}")

        # 生成HTML报告（如果可能）
        if result.portfolio is not None:
            try:
                fig = result.portfolio.plot()
                html_file = output_path / 'performance_chart.html'
                fig.write_html(str(html_file))
                self.logger.info(f"绩效图表已保存: {html_file}")
            except Exception as e:
                self.logger.debug(f"生成图表失败: {e}")
