"""
MACD + KDJ 融合策略实现
趋势+波段组合策略，纯Pandas计算无外部依赖
"""

import pandas as pd
import numpy as np
from .base import BaseStrategy
from Infrastructure.enums import Direction


class MACDKDJStrategy(BaseStrategy):
    """
    MACD + KDJ 融合策略
    
    趋势过滤器 + 进场触发器组合：
    - MACD作为趋势过滤器，只在多头状态时考虑进场
    - KDJ作为进场触发器，捕捉短期回调后的上车机会
    
    买入条件：
    - MACD处于多头状态（DIFF > DEA）
    - KDJ金叉（K上穿D）
    - D值小于60（避免高位追涨）
    
    卖出条件：
    - KDJ死叉（K下穿D）或者MACD转弱（DIFF < DEA）
    """
    
    def __init__(self, data_handler, 
                 fast_period=12, slow_period=26, signal_period=9, 
                 kdj_n=9, kdj_m1=3, kdj_m2=3):
        """
        初始化MACD + KDJ策略
        
        Args:
            data_handler: 数据处理器
            fast_period: MACD快线周期，默认12
            slow_period: MACD慢线周期，默认26
            signal_period: MACD信号线周期，默认9
            kdj_n: KDJ计算周期，默认9
            kdj_m1: K值平滑系数，默认3
            kdj_m2: D值平滑系数，默认3
        """
        super().__init__(data_handler)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.kdj_n = kdj_n
        self.kdj_m1 = kdj_m1
        self.kdj_m2 = kdj_m2
        self.symbols = data_handler.symbol_list

        # 记录上次信号状态，避免重复信号
        self.last_signal = {symbol: None for symbol in self.symbols}
    
    @classmethod
    def get_selection_query(cls) -> str:
        """
        定义MACD + KDJ策略的选股条件
        
        Returns:
            str: 中证500成分股，剔除ST，上市时间大于1年
        """
        return "中证500成分股，剔除ST，上市时间大于1年"
    
    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD指标（纯Pandas实现）
        
        Args:
            df: 包含close_price的DataFrame
            
        Returns:
            添加了MACD指标的DataFrame
        """
        # 计算EMA
        ema_fast = df['close_price'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df['close_price'].ewm(span=self.slow_period, adjust=False).mean()
        
        # 计算DIFF和DEA
        df['MACD_DIFF'] = ema_fast - ema_slow
        df['MACD_DEA'] = df['MACD_DIFF'].ewm(span=self.signal_period, adjust=False).mean()
        df['MACD_HIST'] = df['MACD_DIFF'] - df['MACD_DEA']
        
        return df
    
    def _calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算KDJ指标（纯Pandas实现，重点处理递归平滑）
        
        Args:
            df: 包含high_price, low_price, close_price的DataFrame
            
        Returns:
            添加了KDJ指标的DataFrame
        """
        # 计算RSV (Raw Stochastic Value)
        low_min = df['low_price'].rolling(window=self.kdj_n).min()
        high_max = df['high_price'].rolling(window=self.kdj_n).max()
        
        # 避免除零错误
        denominator = high_max - low_min
        denominator = denominator.replace(0, np.nan)  # 避免除零
        
        rsv = (df['close_price'] - low_min) / denominator * 100
        
        # 处理NaN值：用50填充（中性位置）
        rsv = rsv.fillna(50)
        
        # 计算K值 (使用ewm模拟SMA，alpha=1/3对应com=2)
        # K = (2/3) * 前一日K + (1/3) * 当日RSV
        df['KDJ_K'] = rsv.ewm(com=2, adjust=False).mean()
        
        # 计算D值 (同样使用ewm模拟SMA)
        # D = (2/3) * 前一日D + (1/3) * 当日K
        df['KDJ_D'] = df['KDJ_K'].ewm(com=2, adjust=False).mean()
        
        # 计算J值
        df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']
        
        return df
    
    def on_market_data(self, event):
        """
        处理市场数据事件，计算MACD和KDJ并生成交易信号
        
        Args:
            event: 市场数据事件
        """
        for symbol in self.symbols:
            try:
                # 获取足够的历史数据用于计算指标
                # 需要至少 slow_period + signal_period + kdj_n 根K线
                bars_needed = max(self.slow_period + self.signal_period + 10, self.kdj_n + 10)
                bars = self.data_handler.get_latest_bars(symbol, bars_needed)
                
                # 数据不足，跳过
                if len(bars) < bars_needed:
                    continue
                
                # 将BarData列表转换为DataFrame
                df = pd.DataFrame([vars(b) for b in bars])
                
                # 计算MACD指标
                df = self._calculate_macd(df)
                
                # 计算KDJ指标
                df = self._calculate_kdj(df)
                
                # 获取最新和上一时刻的数据
                current = df.iloc[-1]
                previous = df.iloc[-2]
                
                # 检查指标数据是否有效
                macd_cols = ['MACD_DIFF', 'MACD_DEA']
                kdj_cols = ['KDJ_K', 'KDJ_D']
                
                # 修复pandas数组判断错误
                has_nan = False
                for col in macd_cols + kdj_cols:
                    if pd.isna(current[col]) or pd.isna(previous[col]):
                        has_nan = True
                        break
                
                if has_nan:
                    continue
                
                # 提取当前和上一时刻的指标值
                # MACD指标
                macd_diff_curr = current['MACD_DIFF']
                macd_dea_curr = current['MACD_DEA']
                
                # KDJ指标
                k_curr = current['KDJ_K']
                d_curr = current['KDJ_D']
                k_prev = previous['KDJ_K']
                d_prev = previous['KDJ_D']
                
                # 交易逻辑
                current_signal = None

                # 获取当前持仓数量（单一数据源原则：从Portfolio查询）
                current_pos = 0
                if self.portfolio:
                    current_pos = self.portfolio.get_position(symbol)

                # 买入信号条件：没有持仓 且 触发买入信号
                if (current_pos == 0 and  # 当前未持仓
                    macd_diff_curr > macd_dea_curr and  # MACD多头状态
                    k_prev < d_prev and k_curr > d_curr and  # KDJ金叉
                    d_curr < 60):  # D值不高，避免追涨

                    current_signal = Direction.LONG

                # 卖出信号条件：有持仓 且 触发卖出信号
                elif (current_pos > 0 and  # 当前已持仓
                      ((k_prev > d_prev and k_curr < d_curr) or  # KDJ死叉
                       (macd_diff_curr < macd_dea_curr))):  # MACD转弱

                    current_signal = Direction.SHORT
                
                # 发送信号（避免重复发送相同信号）
                if current_signal and current_signal != self.last_signal.get(symbol):
                    self.send_signal(symbol, current_signal)
                    self.last_signal[symbol] = current_signal
                    
                    # 记录信号详情（用于调试）
                    if current_signal == Direction.LONG:
                        self.logger.info(
                            f"MACD+KDJ买入信号: {symbol} @ {event.bar.datetime.strftime('%Y-%m-%d')}, "
                            f"MACD_DIFF={macd_diff_curr:.4f}, MACD_DEA={macd_dea_curr:.4f}, "
                            f"K={k_curr:.2f}, D={d_curr:.2f}"
                        )
                    else:
                        self.logger.info(
                            f"MACD+KDJ卖出信号: {symbol} @ {event.bar.datetime.strftime('%Y-%m-%d')}, "
                            f"MACD_DIFF={macd_diff_curr:.4f}, MACD_DEA={macd_dea_curr:.4f}, "
                            f"K={k_curr:.2f}, D={d_curr:.2f}"
                        )
                
            except Exception as e:
                self.logger.error(f"处理{symbol}时发生错误: {e}")
                continue