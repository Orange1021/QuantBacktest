"""
分析模块
提供回测结果的绩效分析和可视化功能
"""

from .performance import PerformanceAnalyzer
from .plotting import BacktestPlotter

__all__ = ['PerformanceAnalyzer', 'BacktestPlotter']