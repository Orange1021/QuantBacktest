"""
QuantBacktest 回测应用程序核心模块
面向对象的回测应用程序，支持配置驱动的组件组装和动态策略加载
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Type, Optional, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from DataManager.sources.local_csv import LocalCSVLoader
from DataManager.handlers.handler import BacktestDataHandler
from DataManager.selectors.wencai_selector import WencaiSelector
from Portfolio.portfolio import BacktestPortfolio
from Execution.simulator import SimulatedExecution
from Engine.engine import BacktestEngine
from Analysis.performance import PerformanceAnalyzer
from Analysis.plotting import BacktestPlotter
from Analysis.reporting import BacktestReporter


class BacktestApplication:
    """
    量化回测应用程序
    
    职责：
    - 配置驱动的组件组装
    - 动态策略加载和实例化
    - 完整的回测流程执行
    - 自动化分析和报告生成
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化回测应用程序
        
        Args:
            config_path: 配置文件路径，默认使用项目配置
        """
        # 加载配置
        if config_path:
            settings.config_path = config_path
        
        # 创建时间戳文件夹（用于图片）
        self.output_dir = self._create_timestamp_folder()
        
        # 初始化日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 应用状态
        self.engine = None
        self.portfolio = None
        self.strategy = None
        
        self.logger.info("BacktestApplication 初始化完成")
    
    def _create_timestamp_folder(self) -> Path:
        """创建带时间戳的输出文件夹（用于图片）
        
        Returns:
            Path: 时间戳文件夹路径
        """
        # 创建output根目录
        output_root = Path(settings.data.output_path)
        output_root.mkdir(parents=True, exist_ok=True)
        
        # 生成时间戳文件夹名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = output_root / f"backtest_{timestamp}"
        
        # 创建时间戳文件夹
        timestamp_dir.mkdir(exist_ok=True)
        
        return timestamp_dir
    
    def _setup_logging(self):
        """设置日志配置"""
        log_config = settings.logging
        
        # 创建输出目录
        output_path = Path(settings.data.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 设置日志级别
        level = getattr(logging, log_config.level.upper(), logging.INFO)
        
        # 配置根日志器（日志文件保存在output根目录）
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    output_path / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    encoding='utf-8'
                )
            ]
        )
    
    def run(self, strategy_class: Type, symbol_list: Optional[List[str]] = None) -> dict:
        """
        运行回测
        
        Args:
            strategy_class: 策略类（不是实例）
            symbol_list: 股票代码列表，如果为None则尝试从问财获取或使用默认列表
            
        Returns:
            回测结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始量化回测")
        self.logger.info("=" * 60)
        
        try:
            # 1. 设置数据（传递策略类用于策略驱动选股）
            data_handler, symbols = self._setup_data(symbol_list, strategy_class)
            
            # 2. 设置策略
            strategy = self._setup_strategy(strategy_class, data_handler)
            
            # 3. 设置投资组合
            portfolio = self._setup_portfolio(data_handler)
            
            # 4. 设置执行器
            execution = self._setup_execution(data_handler)
            
            # 5. 创建并运行引擎
            engine = self._setup_engine(data_handler, strategy, portfolio, execution)
            
            # 6. 执行回测
            engine.run()
            
            # 7. 分析结果
            results = self._analyze_results(portfolio, engine)
            
            self.logger.info("=" * 60)
            self.logger.info("回测完成")
            self.logger.info("=" * 60)
            
            return results
            
        except Exception as e:
            self.logger.error(f"回测执行失败: {e}")
            raise
    
    def _setup_data(self, symbol_list: Optional[List[str]] = None, strategy_class: Type = None) -> tuple:
        """
        设置数据组件，包含数据过滤逻辑
        
        Args:
            symbol_list: 股票代码列表
            strategy_class: 策略类，用于策略驱动选股
            
        Returns:
            (data_handler, actual_symbols) 元组
        """
        self.logger.info("步骤1: 设置数据组件")
        
        # 确定股票列表
        if symbol_list is None:
            symbols = self._get_symbol_list(strategy_class)
        else:
            # 如果是外部传入的股票列表，也需要进行过滤
            symbols = self._filter_external_symbols(symbol_list)
        
        self.logger.info(f"使用股票列表: {symbols}")
        
        # 创建数据加载器
        try:
            loader = LocalCSVLoader(settings.data.csv_root_path)
            self.logger.info("CSV数据加载器创建成功")
        except Exception as e:
            self.logger.error(f"创建CSV加载器失败: {e}")
            raise
        
        # 创建数据处理器
        try:
            data_handler = BacktestDataHandler(
                loader=loader,
                symbol_list=symbols,
                start_date=datetime.strptime(settings.backtest.start_date, '%Y-%m-%d'),
                end_date=datetime.strptime(settings.backtest.end_date, '%Y-%m-%d')
            )
            self.logger.info(f"数据处理器创建成功，股票数量: {len(symbols)}")
        except Exception as e:
            self.logger.error(f"创建数据处理器失败: {e}")
            raise
        
        return data_handler, symbols
    
    def _filter_external_symbols(self, symbol_list: List[str]) -> List[str]:
        """
        过滤外部传入的股票列表，确保本地CSV文件存在
        
        Args:
            symbol_list: 外部传入的股票代码列表
            
        Returns:
            过滤后的有效股票代码列表
        """
        try:
            loader = LocalCSVLoader(settings.data.csv_root_path)
            valid_symbols = loader.filter_existing_symbols(symbol_list)
            
            if len(valid_symbols) < len(symbol_list):
                missing_count = len(symbol_list) - len(valid_symbols)
                self.logger.warning(f"过滤掉 {missing_count} 只本地没有数据的股票")
                self.logger.info(f"过滤前: {len(symbol_list)} 只，过滤后: {len(valid_symbols)} 只")
            
            return valid_symbols
            
        except Exception as e:
            self.logger.warning(f"外部股票列表过滤失败，使用原始列表: {e}")
            return symbol_list
    
    def _get_symbol_list(self, strategy_class: Type = None) -> List[str]:
        """
        获取股票列表，实现策略驱动的选股逻辑
        
        逻辑：
        1. 优先使用策略定义的选股查询
        2. 如果策略没有定义查询，回退到默认逻辑
        3. 使用 LocalCSVLoader 快速过滤掉本地没有CSV文件的股票
        4. 从剩余的有效股票中选取目标数量
        
        优先级：
        1. 策略驱动选股 + 过滤（如果策略定义了查询且配置了Cookie）
        2. 问财默认选股 + 过滤（如果配置了Cookie）
        3. 配置文件默认列表
        4. 硬编码备用列表
        """
        # 获取目标持仓数量
        target_positions = settings.get_config('strategy.parameters.max_positions', 5)
        surplus_factor = 2  # 获取目标数量的2倍，确保有足够的选择
        
        # 尝试策略驱动的问财选股
        strategy_query = None
        if strategy_class and hasattr(strategy_class, 'get_selection_query'):
            strategy_query = strategy_class.get_selection_query()
            if strategy_query:
                self.logger.info(f"使用策略定义的选股查询: {strategy_query}")
        
        # 尝试问财选股
        cookie = settings.get_env('WENCAI_COOKIE')
        if cookie:
            try:
                self.logger.info("尝试使用问财选股...")
                selector = WencaiSelector(cookie=cookie)
                
                if selector.validate_connection():
                    # 使用策略查询或默认查询
                    query = strategy_query if strategy_query else "银行"
                    
                    # 获取超过目标数量的股票
                    surplus_count = target_positions * surplus_factor
                    self.logger.info(f"目标持仓: {target_positions}, 查询: {query}, 获取 {surplus_count} 只股票进行过滤")
                    
                    symbols = selector.select_stocks(
                        date=datetime.now(),
                        query=query
                    )
                    
                    if symbols:
                        self.logger.info(f"问财选股成功，获取 {len(symbols)} 只股票")
                        
                        # 创建CSV加载器进行过滤
                        try:
                            loader = LocalCSVLoader(settings.data.csv_root_path)
                            
                            # 快速过滤掉本地没有CSV文件的股票
                            valid_symbols = loader.filter_existing_symbols(symbols)
                            self.logger.info(f"过滤后有效股票: {len(valid_symbols)} 只")
                            
                            if len(valid_symbols) >= target_positions:
                                # 从有效股票中选取目标数量
                                final_symbols = valid_symbols[:target_positions]
                                self.logger.info(f"最终选择 {len(final_symbols)} 只股票: {final_symbols}")
                                return final_symbols
                            else:
                                self.logger.warning(f"有效股票数量 {len(valid_symbols)} 少于目标 {target_positions}，使用全部有效股票")
                                return valid_symbols
                                
                        except Exception as e:
                            self.logger.warning(f"CSV过滤失败，使用原始问财结果: {e}")
                            return symbols[:target_positions]
                    else:
                        self.logger.warning("问财选股返回空列表")
                else:
                    self.logger.warning("问财连接验证失败")
                    
            except Exception as e:
                self.logger.warning(f"问财选股失败，回退到默认列表: {e}")
                # 网络问题或其他异常，回退到硬编码列表
                self.logger.warning("使用硬编码备用列表（网络异常）")
                return ["000001.SZ", "600000.SH"]
        
        # 使用配置文件默认列表
        default_symbols = settings.get_config('backtest.default_symbols')
        if default_symbols:
            self.logger.info("使用配置文件默认股票列表")
            return default_symbols
        
        # 硬编码备用列表
        self.logger.info("使用硬编码备用股票列表")
        return ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH"]
    
    def _setup_strategy(self, strategy_class: Type, data_handler) -> Any:
        """
        设置策略组件
        
        Args:
            strategy_class: 策略类
            data_handler: 数据处理器
            
        Returns:
            策略实例
        """
        self.logger.info("步骤2: 设置策略组件")
        
        try:
            # 实例化策略
            strategy = strategy_class(data_handler)
            self.logger.info(f"策略实例化成功: {strategy_class.__name__}")
            return strategy
        except Exception as e:
            self.logger.error(f"策略实例化失败: {e}")
            raise
    
    def _setup_portfolio(self, data_handler) -> BacktestPortfolio:
        """
        设置投资组合组件
        
        Args:
            data_handler: 数据处理器
            
        Returns:
            投资组合实例
        """
        self.logger.info("步骤3: 设置投资组合组件")
        
        try:
            portfolio = BacktestPortfolio(
                data_handler=data_handler,
                initial_capital=settings.backtest.initial_capital
            )
            self.logger.info(f"投资组合创建成功，初始资金: {settings.backtest.initial_capital:,.2f}")
            return portfolio
        except Exception as e:
            self.logger.error(f"投资组合创建失败: {e}")
            raise
    
    def _setup_execution(self, data_handler) -> SimulatedExecution:
        """
        设置执行器组件
        
        Args:
            data_handler: 数据处理器
            
        Returns:
            执行器实例
        """
        self.logger.info("步骤4: 设置执行器组件")
        
        try:
            execution = SimulatedExecution(
                data_handler=data_handler,
                commission_rate=settings.execution.commission_rate,
                slippage_rate=settings.execution.slippage_rate
            )
            self.logger.info("模拟执行器创建成功")
            return execution
        except Exception as e:
            self.logger.error(f"执行器创建失败: {e}")
            raise
    
    def _setup_engine(self, data_handler, strategy, portfolio, execution) -> BacktestEngine:
        """
        设置回测引擎
        
        Args:
            data_handler: 数据处理器
            strategy: 策略实例
            portfolio: 投资组合实例
            execution: 执行器实例
            
        Returns:
            回测引擎实例
        """
        self.logger.info("步骤5: 设置回测引擎")
        
        try:
            engine = BacktestEngine(
                data_handler=data_handler,
                strategy=strategy,
                portfolio=portfolio,
                execution=execution
            )
            self.logger.info("回测引擎创建成功")
            
            # 保存引用供后续使用
            self.engine = engine
            self.portfolio = portfolio
            self.strategy = strategy
            
            return engine
        except Exception as e:
            self.logger.error(f"回测引擎创建失败: {e}")
            raise
    
    def _analyze_results(self, portfolio: BacktestPortfolio, engine: BacktestEngine) -> dict:
        """
        分析回测结果
        
        Args:
            portfolio: 投资组合实例
            engine: 回测引擎实例
            
        Returns:
            分析结果字典
        """
        self.logger.info("步骤6: 分析回测结果")
        
        try:
            # 获取资金曲线
            equity_curve = portfolio.get_equity_curve()
            if len(equity_curve) < 2:
                self.logger.warning("资金曲线数据不足，无法进行详细分析")
                return self._get_basic_results(portfolio, engine)
            
            # 获取成交记录
            trades = portfolio.get_fill_history()
            self.logger.info(f"获取到 {len(trades)} 条成交记录")
            
            # 创建分析器（传递成交记录）
            analyzer = PerformanceAnalyzer(equity_curve, trades_list=trades)
            
            # 计算关键指标
            total_return = analyzer.calculate_total_return()
            annual_return = analyzer.calculate_annualized_return()
            max_drawdown = analyzer.calculate_max_drawdown()
            sharpe_ratio = analyzer.calculate_sharpe_ratio()
            volatility = analyzer.calculate_volatility()
            
            # 生成图表 - 重写画图部分
            try:
                # 创建BacktestPlotter，直接使用我们指定的时间戳文件夹
                plotter = BacktestPlotter(analyzer, output_dir=self.output_dir)
                self.logger.info("BacktestPlotter创建成功")

                # 生成完整报告（这会直接在我们指定的文件夹中创建图表）
                plotter.create_full_report("backtest_report")
                self.logger.info("完整分析报告生成成功")

            except Exception as e:
                self.logger.error(f"图表生成失败: {e}")
                # 如果图表生成失败，至少保证回测结果正常
                pass

            # 生成专业报告（CSV明细 + TXT总结）
            try:
                self.logger.info("生成专业回测报告...")
                reporter = BacktestReporter(analyzer)

                # 保存交易明细CSV（用于Excel复盘）
                trades_csv_path = self.output_dir / "trades.csv"
                reporter.save_trades_csv(trades_csv_path)
                self.logger.info(f"交易明细CSV已保存: {trades_csv_path}")

                # 保存总结报告TXT（给人看的专业报告）
                report_txt_path = self.output_dir / "report.txt"
                strategy_name = self.strategy.__class__.__name__ if self.strategy else "Unknown"
                reporter.save_summary_report(report_txt_path, strategy_name=strategy_name)
                self.logger.info(f"总结报告已保存: {report_txt_path}")

                self.logger.info("[OK] 专业报告生成完成")

            except Exception as e:
                self.logger.error(f"专业报告生成失败: {e}")
                # 报告生成失败不影响主流程
            
            # 打印关键指标
            self.logger.info("=" * 40)
            self.logger.info("回测结果摘要")
            self.logger.info("=" * 40)
            self.logger.info(f"累计收益率: {total_return*100:.2f}%")
            self.logger.info(f"年化收益率: {annual_return*100:.2f}%")
            self.logger.info(f"最大回撤: {max_drawdown*100:.2f}%")
            self.logger.info(f"夏普比率: {sharpe_ratio:.3f}")
            self.logger.info(f"年化波动率: {volatility*100:.2f}%")
            
            # 获取详细摘要
            summary = analyzer.get_summary()
            self.logger.info(f"交易天数: {summary['trading_days']}")
            self.logger.info(f"总交易次数: {summary['total_trades']}")
            self.logger.info(f"胜率: {summary['win_rate']*100:.2f}%")
            self.logger.info(f"盈亏比: {summary['profit_loss_ratio']:.3f}")
            self.logger.info(f"卡尔玛比率: {summary['calmar_ratio']:.3f}")
            
            # 返回完整结果（图表已由BacktestPlotter保存到self.output_dir）
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'volatility': volatility,
                'trading_days': summary['trading_days'],
                'win_rate': summary['win_rate'],
                'calmar_ratio': summary['calmar_ratio'],
                'equity_curve': equity_curve,
                'output_dir': str(self.output_dir)  # 提供输出目录，图表文件保存在此
            }
            
        except Exception as e:
            self.logger.error(f"结果分析失败: {e}")
            return self._get_basic_results(portfolio, engine)
    
    def _get_basic_results(self, portfolio: BacktestEngine, engine: BacktestEngine) -> dict:
        """
        获取基本结果（当详细分析失败时）
        
        Args:
            portfolio: 投资组合实例
            engine: 回测引擎实例
            
        Returns:
            基本结果字典
        """
        portfolio_info = portfolio.get_portfolio_info()
        engine_status = engine.get_status()
        
        self.logger.info("=" * 40)
        self.logger.info("基本回测结果")
        self.logger.info("=" * 40)
        self.logger.info(f"最终总资产: {portfolio_info['total_equity']:,.2f}")
        self.logger.info(f"收益率: {portfolio_info['return_rate']:.2f}%")
        self.logger.info(f"总交易次数: {portfolio_info['total_trades']}")
        self.logger.info(f"处理事件数: {engine_status['total_events']}")
        
        return {
            'total_equity': portfolio_info['total_equity'],
            'return_rate': portfolio_info['return_rate'],
            'total_trades': portfolio_info['total_trades'],
            'total_events': engine_status['total_events']
        }