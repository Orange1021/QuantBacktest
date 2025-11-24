"""
回测报告生成模块
生成结构化的文本报告和CSV明细文件
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .performance import PerformanceAnalyzer


class BacktestReporter:
    """
    回测报告生成器

    职责：
    1. 生成CSV格式的交易明细（方便Excel复盘）
    2. 生成TXT格式的总结报告（给人看的专业报告）

    这是计算与展示的分离，符合单一职责原则。
    PerformanceAnalyzer 只负责'算数'，BacktestReporter 负责'写作文'。
    """

    def __init__(self, analyzer: 'PerformanceAnalyzer'):
        """
        初始化报告生成器

        Args:
            analyzer: 绩效分析器实例，提供所有计算好的数据
        """
        self.analyzer = analyzer

    def save_trades_csv(self, output_path: Path) -> None:
        """
        保存交易明细到CSV文件

        将已匹配的完整交易记录保存为CSV格式，方便用Excel进行复盘分析。
        包含每笔交易的完整信息：开仓、平仓、盈亏等。

        Args:
            output_path: CSV文件输出路径
        """
        if not self.analyzer.closed_trades:
            print(f"警告：没有交易记录可保存到 {output_path}")
            return

        # 准备CSV数据
        csv_data = []
        for trade in self.analyzer.closed_trades:
            csv_data.append({
                '股票代码': trade['symbol'],
                '开仓时间': trade['open_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                '平仓时间': trade['close_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                '持仓天数': (trade['close_datetime'] - trade['open_datetime']).days,
                '数量': trade['volume'],
                '开仓价': f"{trade['open_price']:.2f}",
                '平仓价': f"{trade['close_price']:.2f}",
                '盈亏金额': f"{trade['net_pnl']:,.2f}",
                '收益率': f"{trade['return_pct']:.2f}%",
                '开仓手续费': f"{trade['open_commission']:,.2f}",
                '平仓手续费': f"{trade['close_commission']:,.2f}"
            })

        # 写入CSV文件
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)

        print(f"[OK] 交易明细已保存到: {output_path}")
        print(f"     共 {len(csv_data)} 笔交易")

    def save_summary_report(self, output_path: Path, strategy_name: str = "Unknown") -> None:
        """
        生成回测总结报告（TXT格式）

        生成一份专业的、给人阅读的回测报告，包含所有核心指标和交易统计。
        格式清晰，易于理解和分享。

        Args:
            output_path: TXT报告输出路径
            strategy_name: 策略名称
        """
        summary = self.analyzer.get_summary()

        # 构建报告内容
        report_lines = []

        # 标题和基本信息
        report_lines.append("=" * 80)
        report_lines.append("量化回测绩效报告")
        report_lines.append("=" * 80)
        report_lines.append("")

        # 基础信息
        report_lines.append("📊 基础信息")
        report_lines.append("-" * 80)
        report_lines.append(f"策略名称: {strategy_name}")
        report_lines.append(f"回测期间: {summary['start_date'].strftime('%Y-%m-%d')} 至 {summary['end_date'].strftime('%Y-%m-%d')}")
        report_lines.append(f"交易天数: {summary['trading_days']} 天")
        report_lines.append(f"初始资金: {summary['start_equity']:,.2f} 元")
        report_lines.append(f"最终权益: {summary['end_equity']:,.2f} 元")
        report_lines.append("")

        # 收益指标
        report_lines.append("📈 收益指标")
        report_lines.append("-" * 80)
        report_lines.append(f"累计收益率: {summary['total_return_pct']:>10.2f}%")
        report_lines.append(f"年化收益率: {summary['annualized_return_pct']:>10.2f}%")
        report_lines.append("")

        # 风险指标
        report_lines.append("⚠️  风险指标")
        report_lines.append("-" * 80)
        report_lines.append(f"最大回撤:   {summary['max_drawdown_pct']:>10.2f}%")
        report_lines.append(f"年化波动率: {summary['volatility_pct']:>10.2f}%")
        report_lines.append("")

        # 风险调整收益
        report_lines.append("🎯 风险调整收益")
        report_lines.append("-" * 80)
        report_lines.append(f"夏普比率:   {summary['sharpe_ratio']:>10.3f}")
        report_lines.append(f"卡尔玛比率: {summary['calmar_ratio']:>10.3f}")
        report_lines.append("")

        # 交易统计
        report_lines.append("💰 交易统计")
        report_lines.append("-" * 80)
        report_lines.append(f"总交易次数: {summary['total_trades']:>10} 次")
        report_lines.append(f"盈利交易:   {summary['winning_trades']:>10} 次")
        report_lines.append(f"亏损交易:   {summary['losing_trades']:>10} 次")
        report_lines.append(f"胜率:       {summary['win_rate_pct']:>10.2f}%")
        report_lines.append(f"盈亏比:     {summary['profit_loss_ratio']:>10.3f}")
        report_lines.append("")

        # 盈亏详情
        report_lines.append("📊 盈亏详情")
        report_lines.append("-" * 80)
        report_lines.append(f"平均每笔盈亏: {summary['avg_trade_pnl']:>10,.2f} 元")
        report_lines.append(f"平均盈利:     {summary['avg_winning_trade']:>10,.2f} 元")
        report_lines.append(f"平均亏损:     {summary['avg_losing_trade']:>10,.2f} 元")
        report_lines.append(f"最大盈利:     {summary['largest_win']:>10,.2f} 元")
        report_lines.append(f"最大亏损:     {summary['largest_loss']:>10,.2f} 元")
        report_lines.append(f"总手续费:     {summary['total_commission']:>10,.2f} 元")
        report_lines.append("")

        # 交易明细
        if self.analyzer.closed_trades:
            report_lines.append("📝 最近5笔交易明细")
            report_lines.append("-" * 80)

            # 取最近5笔交易
            recent_trades = self.analyzer.closed_trades[-5:]

            for i, trade in enumerate(recent_trades, 1):
                report_lines.append(f"\n交易 {i}: {trade['symbol']}")
                report_lines.append(f"  开仓: {trade['open_datetime'].strftime('%Y-%m-%d')} @ {trade['open_price']:.2f}")
                report_lines.append(f"  平仓: {trade['close_datetime'].strftime('%Y-%m-%d')} @ {trade['close_price']:.2f}")
                report_lines.append(f"  盈亏: {trade['net_pnl']:,.2f} 元 ({trade['return_pct']:.2f}%)")

            report_lines.append("")

        # 页脚
        report_lines.append("=" * 80)
        report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print(f"✓ 总结报告已保存到: {output_path}")
