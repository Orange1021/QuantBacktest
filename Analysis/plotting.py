"""
可视化模块
绘制专业的回测分析图表，包括资金曲线、回撤图等
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import pandas as pd
from typing import Optional
import logging
from pathlib import Path
import matplotlib.font_manager as fm
from datetime import datetime


class BacktestPlotter:
    """回测图表绘制器
    
    生成专业的量化回测分析图表：
    1. 资金曲线图 (Equity Curve)
    2. 水下回撤图 (Underwater Plot)
    3. 收益分布图
    4. 滚动收益图
    """
    
    def __init__(self, analyzer, figsize: tuple = (12, 10), output_dir: Optional[Path] = None):
        """Initialize the plotter
        
        Args:
            analyzer: PerformanceAnalyzer instance
            figsize: Figure size, default (12, 10)
            output_dir: 输出目录，如果不提供则自动创建时间戳文件夹
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.analyzer = analyzer
        self.figsize = figsize
        
        # 使用传入的输出目录或创建时间戳文件夹
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = self._create_timestamp_folder()
        
        # 应用样式表
        try:
            plt.style.use('seaborn-v0_8-darkgrid')  # 推荐风格
        except:
            try:
                plt.style.use('ggplot')  # 备选风格
            except:
                self.logger.warning("无法应用样式表，使用默认样式")
        
        
    
    def show_analysis_plot(self, save_path: Optional[str] = None):
        """显示完整的分析图表
        
        分别生成三张独立的图片：
        1. 总资产曲线图（不包含现金和持仓）
        2. 现金和持仓市值图
        3. 水下回撤图
        
        Args:
            save_path: 保存路径，如提供则保存图片
        """
        # 确定保存路径和前缀
        if save_path is None:
            save_path = self.output_dir / "backtest_main.png"
        
        # 提取文件前缀（不带扩展名）
        save_path = Path(save_path)
        prefix = save_path.stem
        output_dir = save_path.parent
        
        # 1. 生成总资产曲线图
        fig1, ax1 = plt.subplots(figsize=self.figsize)
        self._plot_total_equity_only(ax1)
        fig1.suptitle('Total Equity Curve', fontsize=16, fontweight='bold')
        plt.tight_layout()
        equity_path = output_dir / f"{prefix}_equity.png"
        self.save_plot(equity_path)
        plt.close(fig1)
        
        # 2. 生成现金和持仓市值图
        fig2, ax2 = plt.subplots(figsize=self.figsize)
        self._plot_cash_and_positions(ax2)
        fig2.suptitle('Cash and Positions Value', fontsize=16, fontweight='bold')
        plt.tight_layout()
        cash_positions_path = output_dir / f"{prefix}_cash_positions.png"
        self.save_plot(cash_positions_path)
        plt.close(fig2)
        
        # 3. 生成水下回撤图
        fig3, ax3 = plt.subplots(figsize=self.figsize)
        self._plot_drawdown(ax3)
        fig3.suptitle('Underwater Drawdown', fontsize=16, fontweight='bold')
        plt.tight_layout()
        drawdown_path = output_dir / f"{prefix}_drawdown.png"
        self.save_plot(drawdown_path)
        plt.close(fig3)
        
        self.logger.info(f"已生成三张独立图表:")
        self.logger.info(f"  - 总资产图: {equity_path}")
        self.logger.info(f"  - 现金持仓图: {cash_positions_path}")
        self.logger.info(f"  - 回撤图: {drawdown_path}")
    
    def _plot_total_equity_only(self, ax):
        """绘制总资产曲线图（不包含现金和持仓）
        
        Args:
            ax: matplotlib轴对象
        """
        df = self.analyzer.df
        
        # Set labels
        raw_label = 'Raw'
        trend_label = 'Trend (MA5)'
        title = 'Total Equity Curve'
        ylabel = 'Asset Value'
        initial_label = 'Initial Capital'
        
        # 步骤 A (准备数据): 获取原始资金序列并创建平滑序列
        equity = df['total_equity']
        # 动态计算窗口大小，但限制在5-10之间
        window_size = min(max(len(equity) // 100, 5), 10)
        equity_smooth = equity.rolling(window=window_size, min_periods=1).mean()
        
        # 步骤 B (绘制双线):
        # 原始线: 绘制 equity，颜色为灰色，线宽 lw=1，透明度 alpha=0.3
        ax.plot(df.index, equity, 
                label=raw_label, linewidth=1, color='gray', alpha=0.3)
        
        # 平滑线: 绘制 equity_smooth，颜色为深蓝色，线宽 lw=2，透明度 alpha=1.0
        line_smooth = ax.plot(df.index, equity_smooth, 
                             label=trend_label, linewidth=2, color='#2E86AB', alpha=1.0)[0]
        
        # 步骤 C (填充区域): 在平滑线下方填充淡淡的颜色
        ax.fill_between(df.index, self.analyzer.start_equity, equity_smooth, 
                       color=line_smooth.get_color(), alpha=0.1)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(loc='upper left')
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 格式化y轴金额
        ax.yaxis.set_major_formatter(FuncFormatter(self._format_currency))
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加零线
        ax.axhline(y=self.analyzer.start_equity, color='red', linestyle='--', 
                  alpha=0.5, label=f'{initial_label}: {self.analyzer.start_equity:,.0f}')

    def _plot_cash_and_positions(self, ax):
        """绘制现金和持仓市值图
        
        Args:
            ax: matplotlib轴对象
        """
        df = self.analyzer.df
        
        # Set labels
        cash_label = 'Cash'
        positions_label = 'Positions Value'
        title = 'Cash and Positions Value'
        ylabel = 'Asset Value'
        
        # 绘制现金曲线
        ax.plot(df.index, df['cash'], 
                label=cash_label, linewidth=2, color='#A23B72', alpha=0.8)
        
        # 绘制持仓市值曲线
        ax.plot(df.index, df['positions_value'], 
                label=positions_label, linewidth=2, color='#F18F01', alpha=0.8)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(loc='upper left')
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 格式化y轴金额
        ax.yaxis.set_major_formatter(FuncFormatter(self._format_currency))
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加零线
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

    def _plot_equity_curve(self, ax):
        """绘制资金曲线图（保留原方法以兼容其他调用）
        
        Args:
            ax: matplotlib轴对象
        """
        # 调用新的分离方法
        self._plot_total_equity_only(ax)
        
        # 添加现金和持仓曲线（保持原有行为）
        df = self.analyzer.df
        cash_label = 'Cash'
        positions_label = 'Positions Value'
        
        ax.plot(df.index, df['cash'], 
                label=cash_label, linewidth=1, color='#A23B72', alpha=0.7)
        
        ax.plot(df.index, df['positions_value'], 
                label=positions_label, linewidth=1, color='#F18F01', alpha=0.7)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(loc='upper left')
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 格式化y轴金额
        ax.yaxis.set_major_formatter(FuncFormatter(self._format_currency))
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加零线
        ax.axhline(y=self.analyzer.start_equity, color='red', linestyle='--', 
                  alpha=0.5, label=f'{initial_label}: {self.analyzer.start_equity:,.0f}')
    
    def _plot_drawdown(self, ax):
        """绘制水下回撤图
        
        Args:
            ax: matplotlib轴对象
        """
        drawdown_series = self.analyzer.get_drawdown_series()
        
        # Set labels
        area_label = 'Drawdown Area'
        line_label = 'Drawdown Curve'
        title = 'Underwater Drawdown'
        ylabel = 'Drawdown (%)'
        xlabel = 'Time'
        max_dd_label = 'Max Drawdown'
        
        # 优化回撤图: 使用 fill_between 填充红色区域，增加视觉冲击力
        ax.fill_between(drawdown_series.index, 0, drawdown_series * 100,
                       color='red', alpha=0.3, label=area_label)
        
        # 回撤曲线不需要平滑（我们需要看到最尖锐的风险）
        ax.plot(drawdown_series.index, drawdown_series * 100,
               color='darkred', linewidth=1.5, label=line_label)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.legend(loc='lower right')
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加零线
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 标记最大回撤
        max_dd_idx = drawdown_series.idxmin()
        max_dd_value = drawdown_series.min()
        ax.annotate(f'{max_dd_label}: {max_dd_value*100:.2f}%',
                   xy=(max_dd_idx, max_dd_value * 100),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    def plot_returns_distribution(self, save_path: Optional[str] = None):
        """绘制收益分布图
        
        Args:
            save_path: 保存路径
        """
        # 确定保存路径和前缀
        if save_path is None:
            save_path = self.output_dir / "returns_distribution.png"
        
        save_path = Path(save_path)
        prefix = save_path.stem
        output_dir = save_path.parent
        
        returns = self.analyzer.df['returns'].dropna()
        
        # 1. 生成直方图
        fig1, ax1 = plt.subplots(figsize=self.figsize)
        
        # Set labels
        hist_title = 'Daily Returns Distribution'
        xlabel = 'Returns (%)'
        ylabel = 'Frequency'
        mean_label = 'Mean'
        
        # 直方图
        ax1.hist(returns * 100, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title(hist_title, fontsize=14, fontweight='bold')
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.axvline(returns.mean() * 100, color='red', linestyle='--', 
                   label=f'{mean_label}: {returns.mean()*100:.3f}%')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        plt.tight_layout()
        hist_path = output_dir / f"{prefix}_histogram.png"
        self.save_plot(hist_path)
        plt.close(fig1)
        
        # 2. 生成累积收益图
        fig2, ax2 = plt.subplots(figsize=self.figsize)
        
        # Set labels
        cum_title = 'Cumulative Returns'
        cum_ylabel = 'Cumulative Returns (%)'
        
        cumulative_returns = (1 + returns).cumprod() - 1
        ax2.plot(cumulative_returns.index, cumulative_returns * 100, 
                linewidth=2, color='green')
        ax2.set_title(cum_title, fontsize=14, fontweight='bold')
        ax2.set_ylabel(cum_ylabel)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        cum_path = output_dir / f"{prefix}_cumulative.png"
        self.save_plot(cum_path)
        plt.close(fig2)
        
        self.logger.info(f"已生成收益分布图:")
        self.logger.info(f"  - 直方图: {hist_path}")
        self.logger.info(f"  - 累积收益图: {cum_path}")
    
    def plot_monthly_returns(self, save_path: Optional[str] = None):
        """绘制月度收益热力图
        
        Args:
            save_path: 保存路径
        """
        # 计算月度收益
        monthly_returns = self.analyzer.df['returns'].resample('M').apply(
            lambda x: (1 + x).prod() - 1
        ).to_frame('monthly_return')
        
        # 创建年-月的透视表
        monthly_returns['year'] = monthly_returns.index.year
        monthly_returns['month'] = monthly_returns.index.month
        heatmap_data = monthly_returns.pivot(index='year', columns='month', values='monthly_return')
        
        # Set month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        heatmap_data.columns = [month_names[i-1] for i in heatmap_data.columns]
        
        # Draw heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data * 100, annot=True, fmt='.2f', cmap='RdYlGn', 
                   center=0, cbar_kws={'label': 'Returns (%)'})
        plt.title('Monthly Returns Heatmap', fontsize=16, fontweight='bold')
        plt.ylabel('Year')
        plt.xlabel('Month')
        
        if save_path:
            self.save_plot(save_path)
        else:
            plt.show()
    
    def plot_rolling_metrics(self, window: int = 30, save_path: Optional[str] = None):
        """绘制滚动指标图
        
        Args:
            window: 滚动窗口天数
            save_path: 保存路径
        """
        # 确定保存路径和前缀
        if save_path is None:
            save_path = self.output_dir / "rolling_metrics.png"
        
        save_path = Path(save_path)
        prefix = save_path.stem
        output_dir = save_path.parent
        
        returns = self.analyzer.df['returns'].dropna()
        
        # 计算滚动指标
        rolling_sharpe = returns.rolling(window=window).apply(
            lambda x: x.mean() / x.std() * (252 ** 0.5) if x.std() != 0 else 0
        )
        rolling_volatility = returns.rolling(window=window).std() * (252 ** 0.5)
        
        # 1. 生成滚动夏普比率图
        fig1, ax1 = plt.subplots(figsize=self.figsize)
        
        ax1.plot(rolling_sharpe.index, rolling_sharpe, linewidth=2, color='blue')
        ax1.set_title(f'Rolling Sharpe Ratio (Window: {window} days)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Sharpe Ratio')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        sharpe_path = output_dir / f"{prefix}_sharpe.png"
        self.save_plot(sharpe_path)
        plt.close(fig1)
        
        # 2. 生成滚动波动率图
        fig2, ax2 = plt.subplots(figsize=self.figsize)
        
        ax2.plot(rolling_volatility.index, rolling_volatility * 100, 
                linewidth=2, color='orange')
        ax2.set_title(f'Rolling Annualized Volatility (Window: {window} days)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Volatility (%)')
        ax2.set_xlabel('Time')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        volatility_path = output_dir / f"{prefix}_volatility.png"
        self.save_plot(volatility_path)
        plt.close(fig2)
        
        self.logger.info(f"已生成滚动指标图:")
        self.logger.info(f"  - 夏普比率图: {sharpe_path}")
        self.logger.info(f"  - 波动率图: {volatility_path}")
    
    def save_plot(self, filename: str):
        """保存图表到文件
        
        Args:
            filename: 文件名或完整路径
        """
        filepath = Path(filename)
        
        # 如果只是文件名，则保存到时间戳文件夹
        if not filepath.parent or str(filepath.parent) == '.':
            filepath = self.output_dir / filepath.name
        
        # 确保输出目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建完整路径
        if not str(filepath).endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
            filepath = filepath.with_suffix('.png')
        
        # 保存图表
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        self.logger.info(f"Chart saved to: {filepath}")
        print(f"[CHART] Chart saved to: {filepath}")
    
    def create_full_report(self, save_prefix: str = "backtest_report"):
        """创建完整的分析报告
        
        Args:
            save_prefix: 保存文件前缀
        """
        self.logger.info("Starting to generate full analysis report...")
        
        # 1. 主分析图
        self.show_analysis_plot(f"{save_prefix}_main.png")
        
        # 2. 收益分布图
        self.plot_returns_distribution(f"{save_prefix}_returns.png")
        
        # 3. 月度收益热力图
        try:
            self.plot_monthly_returns(f"{save_prefix}_monthly.png")
        except Exception as e:
            self.logger.warning(f"Monthly returns heatmap generation failed: {e}")
        
        # 4. 滚动指标图
        self.plot_rolling_metrics(save_path=f"{save_prefix}_rolling.png")
        
        self.logger.info("Full analysis report generation completed")
        print(f"[REPORT] Full analysis report generated in folder: {self.output_dir}")
        print(f"[FILES] Report files with prefix: {save_prefix}")
    
    def _create_timestamp_folder(self) -> Path:
        """创建带时间戳的输出文件夹
        
        Returns:
            Path: 时间戳文件夹路径
        """
        # 创建output根目录
        output_root = Path("output")
        output_root.mkdir(exist_ok=True)
        
        # 生成时间戳文件夹名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = output_root / f"backtest_{timestamp}"
        
        # 创建时间戳文件夹
        timestamp_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"创建输出文件夹: {timestamp_dir}")
        return timestamp_dir
    
    def _format_currency(self, x, pos):
        """格式化金额为易读形式
        
        Args:
            x: 数值
            pos: 位置
            
        Returns:
            格式化后的字符串
        """
        if x >= 1e6:
            return f'{x/1e6:.1f}M'
        elif x >= 1e3:
            return f'{x/1e3:.0f}k'
        else:
            return f'{x:.0f}'