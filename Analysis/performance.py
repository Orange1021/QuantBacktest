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
    
    def __init__(self, equity_curve: List[Dict[str, Any]], trades_list: List[Dict[str, Any]] = None):
        """初始化绩效分析器
        
        Args:
            equity_curve: 来自Portfolio的资金曲线数据，List[Dict]格式
                         每个字典包含: datetime, total_equity, cash, positions_value
            trades_list: 来自Portfolio的成交记录，List[Dict]格式
                        每个字典包含: datetime, symbol, direction, volume, price, commission
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
        # 计算实际交易天数（去重后的日期数量）
        self.trading_days = len(self.df.index.normalize().unique())
        self.start_equity = self.df['total_equity'].iloc[0]
        self.end_equity = self.df['total_equity'].iloc[-1]
        
        # 成交记录
        self.trades_list = trades_list or []
        self.closed_trades = []  # 已平仓交易列表（在__init__时计算）

        # 在初始化时完成交易配对
        if self.trades_list:
            self.logger.info(f"开始配对交易记录（共 {len(self.trades_list)} 条成交）...")
            self.closed_trades = self._match_trades()
            self.logger.info(f"交易配对完成，共 {len(self.closed_trades)} 笔完整交易")

        self.logger.info(f"PerformanceAnalyzer 初始化完成")
        self.logger.info(f"分析期间: {self.start_date} 至 {self.end_date}")
        self.logger.info(f"交易天数: {self.trading_days}")
        self.logger.info(f"初始资金: {self.start_equity:,.2f}")
        self.logger.info(f"最终资金: {self.end_equity:,.2f}")
        self.logger.info(f"成交记录数: {len(self.trades_list)}")
        self.logger.info(f"完整交易数: {len(self.closed_trades)}")
    
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
        # 按日期分组，取每日最后一个净值计算收益率
        daily_equity = self.df.groupby(self.df.index.normalize())['total_equity'].last()
        daily_returns = daily_equity.pct_change().dropna()
        
        if len(daily_returns) < 2:
            return 0.0
        
        # 计算日化无风险利率
        risk_free_daily = risk_free_rate / 252
        
        # 计算超额收益率的均值和标准差
        excess_returns = daily_returns - risk_free_daily
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
        # 按日期分组，取每日最后一个净值计算收益率
        daily_equity = self.df.groupby(self.df.index.normalize())['total_equity'].last()
        daily_returns = daily_equity.pct_change().dropna()
        
        if len(daily_returns) < 2:
            return 0.0
        
        daily_vol = daily_returns.std()
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
    
    def _match_trades(self) -> List[Dict[str, Any]]:
        """
        配对交易记录 - 使用FIFO（先进先出）算法将买卖订单配对成完整交易

        每笔交易包含：
        - symbol: 股票代码
        - open_datetime: 开仓时间
        - close_datetime: 平仓时间
        - direction: 交易方向（LONG/SHORT）
        - volume: 交易数量
        - entry_price: 开仓价格
        - exit_price: 平仓价格
        - pnl: 净盈亏（扣除手续费）
        - return_pct: 收益率

        Returns:
            List[Dict[str, Any]]: 已平仓交易列表
        """
        if not self.trades_list:
            return []
        
        # 按股票分组
        symbol_positions = {}
        closed_trades = []
        
        # 按时间排序成交记录
        sorted_trades = sorted(self.trades_list, key=lambda x: x['datetime'])
        
        for trade in sorted_trades:
            symbol = trade['symbol']
            direction = trade['direction']
            volume = trade['volume']
            price = trade['price']
            commission = trade['commission']
            
            if symbol not in symbol_positions:
                symbol_positions[symbol] = []
            
            if direction == 'LONG':  # 买入开仓
                # 记录开仓位置
                symbol_positions[symbol].append({
                    'datetime': trade['datetime'],
                    'volume': volume,
                    'price': price,
                    'commission': commission
                })
            
            elif direction == 'SHORT':  # 卖出平仓
                # 使用FIFO匹配开仓位置
                remaining_volume = volume
                
                while remaining_volume > 0 and symbol_positions[symbol]:
                    # 取出最早的开仓记录
                    open_pos = symbol_positions[symbol][0]
                    
                    if open_pos['volume'] <= remaining_volume:
                        # 完全平仓
                        trade_volume = open_pos['volume']
                        
                        # 计算盈亏
                        open_value = trade_volume * open_pos['price']
                        close_value = trade_volume * price
                        gross_pnl = close_value - open_value
                        net_pnl = gross_pnl - open_pos['commission'] - commission * (trade_volume / volume)
                        
                        closed_trade = {
                            'symbol': symbol,
                            'open_datetime': open_pos['datetime'],
                            'close_datetime': trade['datetime'],
                            'open_price': open_pos['price'],
                            'close_price': price,
                            'volume': trade_volume,
                            'open_commission': open_pos['commission'],
                            'close_commission': commission * (trade_volume / volume),
                            'gross_pnl': gross_pnl,
                            'net_pnl': net_pnl,
                            'return_pct': (gross_pnl / open_value) * 100 if open_value > 0 else 0
                        }
                        
                        closed_trades.append(closed_trade)
                        remaining_volume -= trade_volume
                        symbol_positions[symbol].pop(0)  # 移除已用完的开仓记录
                        
                    else:
                        # 部分平仓
                        trade_volume = remaining_volume

                        # 计算盈亏
                        open_value = trade_volume * open_pos['price']
                        close_value = trade_volume * price
                        gross_pnl = close_value - open_value

                        # 按比例分配开仓手续费
                        allocated_open_commission = open_pos['commission'] * (trade_volume / open_pos['volume'])

                        # 净盈亏 = 毛盈亏 - 分摊的开仓手续费 - 本次平仓手续费
                        net_pnl = gross_pnl - allocated_open_commission - commission * (trade_volume / volume)
                        
                        closed_trade = {
                            'symbol': symbol,
                            'open_datetime': open_pos['datetime'],
                            'close_datetime': trade['datetime'],
                            'open_price': open_pos['price'],
                            'close_price': price,
                            'volume': trade_volume,
                            'open_commission': allocated_open_commission,
                            'close_commission': commission * (trade_volume / volume),
                            'gross_pnl': gross_pnl,
                            'net_pnl': net_pnl,
                            'return_pct': (gross_pnl / open_value) * 100 if open_value > 0 else 0
                        }
                        
                        closed_trades.append(closed_trade)
                        
                        # 更新剩余开仓数量和手续费
                        open_pos['volume'] -= trade_volume
                        open_pos['commission'] -= allocated_open_commission
                        remaining_volume = 0

        return closed_trades
    
    def calculate_win_rate(self) -> float:
        """计算胜率

        基于已匹配的完整交易计算

        Returns:
            float: 胜率（盈利交易次数占比）
        """
        if not self.closed_trades:
            return 0.0

        profitable_trades = sum(1 for trade in self.closed_trades if trade['net_pnl'] > 0)
        win_rate = profitable_trades / len(self.closed_trades)

        return win_rate
    
    def calculate_profit_loss_ratio(self) -> float:
        """计算盈亏比

        基于已匹配的完整交易计算

        Returns:
            float: 平均盈利交易金额 / 平均亏损交易金额
        """
        if not self.closed_trades:
            return 0.0

        profitable_trades = [trade['net_pnl'] for trade in self.closed_trades if trade['net_pnl'] > 0]
        losing_trades = [abs(trade['net_pnl']) for trade in self.closed_trades if trade['net_pnl'] < 0]

        if not losing_trades:
            return float('inf') if profitable_trades else 0.0

        if not profitable_trades:
            return 0.0

        avg_profit = sum(profitable_trades) / len(profitable_trades)
        avg_loss = sum(losing_trades) / len(losing_trades)

        if avg_loss == 0.0:
            return float('inf')

        return avg_profit / avg_loss
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """
        获取详细的交易统计信息

        基于已匹配的完整交易计算

        Returns:
            包含详细交易统计的字典
        """
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_loss_ratio': 0.0,
                'avg_trade_pnl': 0.0,
                'avg_winning_trade': 0.0,
                'avg_losing_trade': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'total_commission': 0.0
            }

        profitable_trades = [trade for trade in self.closed_trades if trade['net_pnl'] > 0]
        losing_trades = [trade for trade in self.closed_trades if trade['net_pnl'] < 0]

        total_pnl = sum(trade['net_pnl'] for trade in self.closed_trades)
        total_commission = sum(trade['open_commission'] + trade['close_commission'] for trade in self.closed_trades)

        stats = {
            'total_trades': len(self.closed_trades),
            'winning_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(profitable_trades) / len(self.closed_trades),
            'profit_loss_ratio': self.calculate_profit_loss_ratio(),
            'avg_trade_pnl': total_pnl / len(self.closed_trades),
            'avg_winning_trade': sum(trade['net_pnl'] for trade in profitable_trades) / len(profitable_trades) if profitable_trades else 0.0,
            'avg_losing_trade': abs(sum(trade['net_pnl'] for trade in losing_trades) / len(losing_trades)) if losing_trades else 0.0,
            'largest_win': max(trade['net_pnl'] for trade in profitable_trades) if profitable_trades else 0.0,
            'largest_loss': abs(min(trade['net_pnl'] for trade in losing_trades)) if losing_trades else 0.0,
            'total_commission': total_commission
        }

        return stats
    
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
        # 获取详细交易统计
        trade_stats = self.get_trade_statistics()
        
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
            
            # 交易统计（基于真实成交记录）
            'total_trades': trade_stats['total_trades'],
            'winning_trades': trade_stats['winning_trades'],
            'losing_trades': trade_stats['losing_trades'],
            'win_rate': trade_stats['win_rate'],
            'win_rate_pct': trade_stats['win_rate'] * 100,
            'profit_loss_ratio': trade_stats['profit_loss_ratio'],
            'avg_trade_pnl': trade_stats['avg_trade_pnl'],
            'avg_winning_trade': trade_stats['avg_winning_trade'],
            'avg_losing_trade': trade_stats['avg_losing_trade'],
            'largest_win': trade_stats['largest_win'],
            'largest_loss': trade_stats['largest_loss'],
            'total_commission': trade_stats['total_commission'],
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
        
        # 交易统计（基于真实成交记录）
        print(f"\n📊 交易统计:")
        print(f"   总交易次数: {summary['total_trades']}")
        print(f"   盈利交易: {summary['winning_trades']}")
        print(f"   亏损交易: {summary['losing_trades']}")
        print(f"   胜率: {summary['win_rate_pct']:.2f}%")
        print(f"   盈亏比: {summary['profit_loss_ratio']:.3f}")
        print(f"   平均每笔盈亏: {summary['avg_trade_pnl']:.2f}")
        print(f"   平均盈利: {summary['avg_winning_trade']:.2f}")
        print(f"   平均亏损: {summary['avg_losing_trade']:.2f}")
        print(f"   最大盈利: {summary['largest_win']:.2f}")
        print(f"   最大亏损: {summary['largest_loss']:.2f}")
        print(f"   总手续费: {summary['total_commission']:.2f}")
        
        print("\n" + "=" * 80)
