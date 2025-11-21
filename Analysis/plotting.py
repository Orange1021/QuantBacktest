"""
可视化模块
绘制专业的回测分析图表，包括资金曲线、回撤图等
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from typing import Optional
import logging
from pathlib import Path
import matplotlib.font_manager as fm


class BacktestPlotter:
    """回测图表绘制器
    
    生成专业的量化回测分析图表：
    1. 资金曲线图 (Equity Curve)
    2. 水下回撤图 (Underwater Plot)
    3. 收益分布图
    4. 滚动收益图
    """
    
    def __init__(self, analyzer, figsize: tuple = (12, 10)):
        """Initialize the plotter
        
        Args:
            analyzer: PerformanceAnalyzer instance
            figsize: Figure size, default (12, 10)
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.analyzer = analyzer
        self.figsize = figsize
        
        
    
    def show_analysis_plot(self, save_path: Optional[str] = None):
        """显示完整的分析图表
        
        包含两个子图：
        1. 上：资金曲线图
        2. 下：水下回撤图
        
        Args:
            save_path: 保存路径，如提供则保存图片
        """
        # 创建画布
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, gridspec_kw={'height_ratios': [3, 1]})
        fig.suptitle('Quantitative Backtest Analysis Report', fontsize=16, fontweight='bold')
        
        # 绘制资金曲线
        self._plot_equity_curve(ax1)
        
        # 绘制回撤图
        self._plot_drawdown(ax2)
        
        # Set main title
        fig.suptitle('Quantitative Backtest Analysis Report', fontsize=16, fontweight='bold')
        
        # 调整布局
        plt.tight_layout()
        
        # 保存或显示
        if save_path:
            self.save_plot(save_path)
        else:
            plt.show()
    
    def _plot_equity_curve(self, ax):
        """绘制资金曲线图
        
        Args:
            ax: matplotlib轴对象
        """
        df = self.analyzer.df
        
        # Set labels
        total_equity_label = 'Total Equity'
        cash_label = 'Cash'
        positions_label = 'Positions Value'
        title = 'Equity Curve'
        ylabel = 'Asset Value'
        initial_label = 'Initial Capital'
        
        # 绘制总资产曲线
        ax.plot(df.index, df['total_equity'], 
                label=total_equity_label, linewidth=2, color='#2E86AB')
        
        # 绘制现金曲线
        ax.plot(df.index, df['cash'], 
                label=cash_label, linewidth=1, color='#A23B72', alpha=0.7)
        
        # 绘制持仓市值曲线
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
        
        # 绘制回撤曲线
        ax.fill_between(drawdown_series.index, 0, drawdown_series * 100,
                       color='red', alpha=0.3, label=area_label)
        
        ax.plot(drawdown_series.index, drawdown_series * 100,
               color='red', linewidth=1, label=line_label)
        
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
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Set labels
        main_title = 'Returns Distribution Analysis'
        hist_title = 'Daily Returns Distribution'
        xlabel = 'Returns (%)'
        ylabel = 'Frequency'
        mean_label = 'Mean'
        cum_title = 'Cumulative Returns'
        cum_ylabel = 'Cumulative Returns (%)'
        
        fig.suptitle(main_title, fontsize=16, fontweight='bold')
        
        returns = self.analyzer.df['returns'].dropna()
        
        # 直方图
        ax1.hist(returns * 100, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title(hist_title)
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.axvline(returns.mean() * 100, color='red', linestyle='--', 
                   label=f'{mean_label}: {returns.mean()*100:.3f}%')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 累积收益图
        cumulative_returns = (1 + returns).cumprod() - 1
        ax2.plot(cumulative_returns.index, cumulative_returns * 100, 
                linewidth=2, color='green')
        ax2.set_title(cum_title)
        ax2.set_ylabel(cum_ylabel)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        
        if save_path:
            self.save_plot(save_path)
        else:
            plt.show()
    
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
        returns = self.analyzer.df['returns'].dropna()
        
        # 计算滚动指标
        rolling_sharpe = returns.rolling(window).apply(
            lambda x: x.mean() / x.std() * (252 ** 0.5) if x.std() != 0 else 0
        )
        rolling_volatility = returns.rolling(window).std() * (252 ** 0.5)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f'Rolling Metrics Analysis (Window: {window} days)', fontsize=16, fontweight='bold')
        
        # Rolling Sharpe ratio
        ax1.plot(rolling_sharpe.index, rolling_sharpe, linewidth=2, color='blue')
        ax1.set_title('Rolling Sharpe Ratio')
        ax1.set_ylabel('Sharpe Ratio')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # Rolling volatility
        ax2.plot(rolling_volatility.index, rolling_volatility * 100, 
                linewidth=2, color='orange')
        ax2.set_title('Rolling Annualized Volatility')
        ax2.set_ylabel('Volatility (%)')
        ax2.set_xlabel('Time')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.tight_layout()
        
        if save_path:
            self.save_plot(save_path)
        else:
            plt.show()
    
    def save_plot(self, filename: str):
        """保存图表到文件
        
        Args:
            filename: 文件名或完整路径
        """
        # 确保输出目录存在
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 构建完整路径
        if not filename.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
            filename += '.png'
        
        filepath = output_dir / filename
        
        # 保存图表
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        self.logger.info(f"Chart saved to: {filepath}")
        print(f"📊 Chart saved to: {filepath}")
    
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
        self.plot_rolling_metrics(f"{save_prefix}_rolling.png")
        
        self.logger.info("Full analysis report generation completed")
        print(f"🎉 Full analysis report generated with prefix: {save_prefix}")