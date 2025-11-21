"""
绩效分析模块
计算回测结果的核心指标，包括收益率、夏普比率、最大回撤等
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime
import logging


class PerformanceAnalyzer:
    """绩效分析器
    
    将Portfolio记录的流水账变成专业的报表和指标
    
    核心功能：
    1. 将equity_curve数据转换为pandas DataFrame
    2. 计算每日收益率
    3. 计算各种绩效指标
    4. 生成分析报告
    """
    
    def __init__(self, equity_curve: List[Dict[str, Any]]):
        """初始化绩效分析器
        
        Args:
            equity_curve: 来自Portfolio的资金曲线数据，List[Dict]格式
                         每个字典包含: datetime, total_equity, cash, positions_value
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if not equity_curve:
            raise ValueError("资金曲线数据为空")
        
        # 转换为DataFrame
        self.df = self._prepare_dataframe(equity_curve)
        
        # 计算每日收益率
        self.df['returns'] = self.df['total_equity'].pct_change()
        
        # 基础统计信息
        self.start_date = self.df.index[0]
        self.end_date = self.df.index[-1]
        self.trading_days = len(self.df)
        self.start_equity = self.df['total_equity'].iloc[0]
        self.end_equity = self.df['total_equity'].iloc[-1]
        
        self.logger.info(f"PerformanceAnalyzer 初始化完成")
        self.logger.info(f"分析期间: {self.start_date} 至 {self.end_date}")
        self.logger.info(f"交易天数: {self.trading_days}")
        self.logger.info(f"初始资金: {self.start_equity:,.2f}")
        self.logger.info(f"最终资金: {self.end_equity:,.2f}")
    
    def _prepare_dataframe(self, equity_curve: List[Dict[str, Any]]) -> pd.DataFrame:
        """准备DataFrame数据
        
        Args:
            equity_curve: 原始资金曲线数据
            
        Returns:
            pd.DataFrame: 处理后的DataFrame，datetime为索引
        """
        # 转换为DataFrame
        df = pd.DataFrame(equity_curve)
        
        # 确保datetime列存在且为datetime类型
        if 'datetime' not in df.columns:
            raise ValueError("equity_curve数据中缺少datetime字段")
        
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 设置datetime为索引
        df.set_index('datetime', inplace=True)
        
        # 按时间排序
        df.sort_index(inplace=True)
        
        # 检查必要的列
        required_columns = ['total_equity', 'cash', 'positions_value']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"equity_curve数据中缺少{col}字段")
        
        return df
    
    def calculate_total_return(self) -> float:
        """计算累计收益率
        
        Returns:
            float: 累计收益率（小数形式，如0.15表示15%）
        """
        total_return = (self.end_equity / self.start_equity) - 1.0
        return total_return
    
    def calculate_annualized_return(self) -> float:
        """计算年化收益率 (CAGR)
        
        使用复利年化收益率公式：(end/start)^(252/days) - 1
        
        Returns:
            float: 年化收益率（小数形式）
        """
        if self.trading_days <= 1:
            return 0.0
        
        # 假设一年252个交易日
        trading_days_per_year = 252
        
        cagr = (self.end_equity / self.start_equity) ** (trading_days_per_year / self.trading_days) - 1.0
        return cagr
    
    def calculate_max_drawdown(self) -> float:
        """计算历史最大回撤
        
        算法：
        1. 计算累计最大值: roll_max = df['total_equity'].cummax()
        2. 计算每日回撤: daily_dd = df['total_equity'] / roll_max - 1.0
        3. 取最小值: max_dd = daily_dd.min()
        
        Returns:
            float: 最大回撤（负数，如-0.15表示回撤15%）
        """
        # 计算累计最大值（历史高点）
        roll_max = self.df['total_equity'].cummax()
        
        # 计算每日回撤
        daily_drawdown = self.df['total_equity'] / roll_max - 1.0
        
        # 最大回撤
        max_drawdown = daily_drawdown.min()
        
        return max_drawdown
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率
        
        公式：(mean_returns - risk_free_daily) / std_returns * sqrt(252)
        
        Args:
            risk_free_rate: 年化无风险利率，默认2%
            
        Returns:
            float: 夏普比率
        """
        if len(self.df['returns'].dropna()) < 2:
            return 0.0
        
        # 计算日化无风险利率
        risk_free_daily = risk_free_rate / 252
        
        # 计算超额收益率的均值和标准差
        excess_returns = self.df['returns'] - risk_free_daily
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()
        
        if std_excess == 0:
            return 0.0
        
        # 年化夏普比率
        sharpe_ratio = mean_excess / std_excess * np.sqrt(252)
        
        return sharpe_ratio
    
    def calculate_volatility(self) -> float:
        """计算年化波动率
        
        Returns:
            float: 年化波动率
        """
        if len(self.df['returns'].dropna()) < 2:
            return 0.0
        
        daily_vol = self.df['returns'].std()
        annualized_vol = daily_vol * np.sqrt(252)
        
        return annualized_vol
    
    def calculate_calmar_ratio(self) -> float:
        """计算卡尔玛比率
        
        公式：年化收益率 / abs(最大回撤)
        
        Returns:
            float: 卡尔玛比率
        """
        max_dd = self.calculate_max_drawdown()
        if max_dd == 0:
            return 0.0
        
        annual_return = self.calculate_annualized_return()
        calmar_ratio = annual_return / abs(max_dd)
        
        return calmar_ratio
    
    def calculate_win_rate(self) -> float:
        """计算胜率
        
        Returns:
            float: 胜率（正收益交易日占比）
        """
        positive_days = (self.df['returns'] > 0).sum()
        total_days = len(self.df['returns'].dropna())
        
        if total_days == 0:
            return 0.0
        
        win_rate = positive_days / total_days
        return win_rate
    
    def calculate_profit_loss_ratio(self) -> float:
        """计算盈亏比
        
        Returns:
            float: 平均盈利 / 平均亏损
        """
        positive_returns = self.df['returns'][self.df['returns'] > 0]
        negative_returns = self.df['returns'][self.df['returns'] < 0]
        
        if len(negative_returns) == 0:
            return float('inf') if len(positive_returns) > 0 else 0.0
        
        avg_profit = positive_returns.mean() if len(positive_returns) > 0 else 0.0
        avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0.0
        
        if avg_loss == 0:
            return float('inf') if avg_profit > 0 else 0.0
        
        return avg_profit / avg_loss
    
    def get_drawdown_series(self) -> pd.Series:
        """获取回撤序列
        
        Returns:
            pd.Series: 回撤时间序列
        """
        roll_max = self.df['total_equity'].cummax()
        drawdown_series = self.df['total_equity'] / roll_max - 1.0
        
        return drawdown_series
    
    def get_summary(self) -> Dict[str, Any]:
        """获取完整的绩效分析摘要
        
        Returns:
            Dict[str, Any]: 包含所有绩效指标的字典
        """
        summary = {
            # 基础信息
            'start_date': self.start_date,
            'end_date': self.end_date,
            'trading_days': self.trading_days,
            'start_equity': self.start_equity,
            'end_equity': self.end_equity,
            
            # 收益指标
            'total_return': self.calculate_total_return(),
            'total_return_pct': self.calculate_total_return() * 100,
            'annualized_return': self.calculate_annualized_return(),
            'annualized_return_pct': self.calculate_annualized_return() * 100,
            
            # 风险指标
            'max_drawdown': self.calculate_max_drawdown(),
            'max_drawdown_pct': self.calculate_max_drawdown() * 100,
            'volatility': self.calculate_volatility(),
            'volatility_pct': self.calculate_volatility() * 100,
            
            # 风险调整收益指标
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'calmar_ratio': self.calculate_calmar_ratio(),
            
            # 交易统计
            'win_rate': self.calculate_win_rate(),
            'win_rate_pct': self.calculate_win_rate() * 100,
            'profit_loss_ratio': self.calculate_profit_loss_ratio(),
        }
        
        return summary
    
    def print_summary(self):
        """打印格式化的绩效摘要"""
        summary = self.get_summary()
        
        print("\n" + "=" * 80)
        print("回测绩效分析报告")
        print("=" * 80)
        
        # 基础信息
        print(f"\n📅 基础信息:")
        print(f"   回测期间: {summary['start_date'].strftime('%Y-%m-%d')} 至 {summary['end_date'].strftime('%Y-%m-%d')}")
        print(f"   交易天数: {summary['trading_days']} 天")
        print(f"   初始资金: {summary['start_equity']:,.2f}")
        print(f"   最终资金: {summary['end_equity']:,.2f}")
        
        # 收益指标
        print(f"\n📈 收益指标:")
        print(f"   累计收益: {summary['total_return_pct']:.2f}%")
        print(f"   年化收益: {summary['annualized_return_pct']:.2f}%")
        
        # 风险指标
        print(f"\n⚠️ 风险指标:")
        print(f"   最大回撤: {summary['max_drawdown_pct']:.2f}%")
        print(f"   年化波动: {summary['volatility_pct']:.2f}%")
        
        # 风险调整收益
        print(f"\n🎯 风险调整收益:")
        print(f"   夏普比率: {summary['sharpe_ratio']:.3f}")
        print(f"   卡尔玛比率: {summary['calmar_ratio']:.3f}")
        
        # 交易统计
        print(f"\n📊 交易统计:")
        print(f"   胜率: {summary['win_rate_pct']:.2f}%")
        print(f"   盈亏比: {summary['profit_loss_ratio']:.3f}")
        
        print("\n" + "=" * 80)
