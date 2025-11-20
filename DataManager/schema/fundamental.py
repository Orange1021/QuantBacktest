"""
财务数据模型定义
继承自BaseData，包含PE、PB、EPS等基本面指标
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import BaseData
from .constant import Exchange


@dataclass
class FundamentalData(BaseData):
    """
    财务数据类，包含基本面分析所需的核心指标
    用于价值投资策略和基本面因子分析
    """
    # 基础估值指标
    pe_ratio: float = 0.0           # 市盈率 (Price-to-Earnings Ratio)
    pb_ratio: float = 0.0           # 市净率 (Price-to-Book Ratio)
    ps_ratio: float = 0.0           # 市销率 (Price-to-Sales Ratio)
    
    # 盈利能力指标
    eps: float = 0.0                # 每股收益 (Earnings Per Share)
    roe: float = 0.0                # 净资产收益率 (Return on Equity)
    roa: float = 0.0                # 总资产收益率 (Return on Assets)
    roic: float = 0.0               # 投入资本回报率 (Return on Invested Capital)
    gross_margin: float = 0.0       # 毛利率 (%)
    net_margin: float = 0.0         # 净利率 (%)
    
    # 成长性指标
    revenue_growth: float = 0.0     # 营收增长率 (%)
    profit_growth: float = 0.0      # 净利润增长率 (%)
    eps_growth: float = 0.0         # 每股收益增长率 (%)
    
    # 偿债能力指标
    current_ratio: float = 0.0      # 流动比率
    quick_ratio: float = 0.0        # 速动比率
    debt_to_equity: float = 0.0     # 资产负债率
    interest_coverage: float = 0.0  # 利息保障倍数
    
    # 运营效率指标
    inventory_turnover: float = 0.0 # 存货周转率
    receivable_turnover: float = 0.0 # 应收账款周转率
    asset_turnover: float = 0.0     # 总资产周转率
    
    # 现金流指标
    operating_cash_flow: float = 0.0    # 经营活动现金流
    free_cash_flow: float = 0.0         # 自由现金流
    cash_per_share: float = 0.0         # 每股现金流
    
    # 股本相关
    total_shares: float = 0.0           # 总股本
    float_shares: float = 0.0           # 流通股本
    market_cap: float = 0.0             # 总市值
    circulating_cap: float = 0.0        # 流通市值
    
    # 分红相关
    dividend_per_share: float = 0.0     # 每股分红
    dividend_yield: float = 0.0         # 股息率 (%)
    payout_ratio: float = 0.0           # 分红率 (%)
    
    # 报告期信息
    report_date: Optional[datetime] = None  # 财报发布日期
    report_type: str = ""                # 报告类型: 年报/半年报/季报
    
    def __post_init__(self):
        """数据类初始化后处理"""
        super().__post_init__()
        
        # 数据合理性验证
        if self.total_shares <= 0:
            raise ValueError("总股本必须大于0")
        
        if self.pe_ratio < 0:
            raise ValueError("市盈率不能为负数")
        
        if self.pb_ratio < 0:
            raise ValueError("市净率不能为负数")

    @property
    def book_value_per_share(self) -> float:
        """每股净资产"""
        if self.total_shares == 0:
            return 0.0
        return self.market_cap / (self.pb_ratio * self.total_shares)

    @property
    def earnings_yield(self) -> float:
        """盈利收益率 = 1 / PE"""
        if self.pe_ratio == 0:
            return 0.0
        return 1.0 / self.pe_ratio

    @property
    def price_to_cash_flow(self) -> float:
        """市现率"""
        if self.operating_cash_flow == 0 or self.total_shares == 0:
            return 0.0
        return (self.market_cap / self.total_shares) / (self.operating_cash_flow / self.total_shares)

    @property
    def enterprise_value(self) -> float:
        """企业价值 (简化计算)"""
        # EV = 市值 + 总负债 - 现金
        return self.market_cap * (1 + self.debt_to_equity) - self.cash_per_share * self.total_shares

    @property
    def ev_to_ebitda(self) -> float:
        """EV/EBITDA 比率"""
        # 简化计算，使用净利润近似EBITDA
        if self.eps == 0 or self.total_shares == 0:
            return 0.0
        ebitda = self.eps * self.total_shares
        return self.enterprise_value / ebitda if ebitda != 0 else 0.0

    @property
    def is_value_stock(self) -> bool:
        """判断是否为价值股 (低PE, 低PB)"""
        return self.pe_ratio < 15 and self.pb_ratio < 2.0

    @property
    def is_growth_stock(self) -> bool:
        """判断是否为成长股 (高增长)"""
        return self.revenue_growth > 20 and self.profit_growth > 20

    @property
    def is_quality_stock(self) -> bool:
        """判断是否为优质股 (高ROE, 低负债)"""
        return self.roe > 15 and self.debt_to_equity < 0.5

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"FundamentalData: {self.vt_symbol}, {self.report_date}, "
            f"PE:{self.pe_ratio:.2f}, PB:{self.pb_ratio:.2f}, "
            f"ROE:{self.roe:.2f}%, EPS:{self.eps:.2f}"
        )