"""
双均线策略实现
仅使用pandas原生功能，无外部依赖
"""

import pandas as pd
from .base import BaseStrategy
from Infrastructure.enums import Direction


class DualMAStrategy(BaseStrategy):
    """
    双均线策略
    
    当短期均线上穿长期均线时买入（金叉）
    当短期均线下穿长期均线时卖出（死叉）
    """
    
    def __init__(self, data_handler, short_window=5, long_window=20):
        """
        初始化双均线策略
        
        Args:
            data_handler: 数据处理器
            short_window: 短期均线窗口，默认5
            long_window: 长期均线窗口，默认20
        """
        super().__init__(data_handler)
        self.short_window = short_window
        self.long_window = long_window
        self.symbols = data_handler.symbol_list
        
        # 为每个股票维护一个字典，存储是否已持仓
        self.invested = {symbol: False for symbol in self.symbols}
    
    @classmethod
    def get_selection_query(cls) -> str:
        """
        定义双均线策略的选股条件

        Returns:
            str: 科技股,市值排名前十;非新股;非ST股;按照市值从大到小排序;
        """
        return "科技股,市值排名前十;非新股;非ST股;按照市值从大到小排序;"
    
    def on_market_data(self, event):
        """
        处理市场数据事件，计算均线并生成交易信号
        
        Args:
            event: 市场数据事件
        """
        for symbol in self.symbols:
            # 获取足够的历史数据用于计算均线
            bars_needed = self.long_window + 2
            bars = self.data_handler.get_latest_bars(symbol, bars_needed)
            
            # 数据不足，跳过
            if len(bars) < bars_needed:
                continue
            
            # 将BarData列表转换为DataFrame
            df = pd.DataFrame([vars(b) for b in bars])
            
            # 计算短期和长期均线
            df['short_ma'] = df['close_price'].rolling(window=self.short_window).mean()
            df['long_ma'] = df['close_price'].rolling(window=self.long_window).mean()
            
            # 获取最新和上一时刻的数据
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # 当前均线值
            current_short = current['short_ma']
            current_long = current['long_ma']
            
            # 上一时刻均线值
            prev_short = previous['short_ma']
            prev_long = previous['long_ma']
            
            # 检查是否有有效数据（避免NaN）
            if any(pd.isna([current_short, current_long, prev_short, prev_long])):
                continue
            
            # 金叉判断：上一刻短<长 且 当前短>长
            if prev_short <= prev_long and current_short > current_long:
                # 如果当前未持仓，则买入
                if not self.invested[symbol]:
                    self.send_signal(symbol, Direction.LONG)
                    self.invested[symbol] = True
            
            # 死叉判断：上一刻短>长 且 当前短<长
            elif prev_short >= prev_long and current_short < current_long:
                # 如果当前已持仓，则卖出
                if self.invested[symbol]:
                    self.send_signal(symbol, Direction.SHORT)
                    self.invested[symbol] = False