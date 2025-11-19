"""
仓位管理器

管理资金和持仓，支持：
- 初始建仓
- 分层加仓
- 成本价计算（加权平均）
- 持仓状态追踪
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.utils.logger import setup_logger


@dataclass
class Position:
    """
    持仓数据

    Attributes:
        symbol: 股票代码
        quantity: 持仓数量（股）
        avg_price: 持仓均价（成本价）
        current_price: 当前价格
        entry_date: 首次建仓日期
        layer_count: 加仓层数（从0开始）
        has_risen: 是否上涨过（关键字段，用于卖出判断）
        initial_position_size: 初始仓位大小（占单票配额比例）
        total_cost: 总成本
        last_update: 最后更新时间
    """
    symbol: str
    quantity: int = 0
    avg_price: float = 0.0
    current_price: float = 0.0
    entry_date: Optional[datetime] = None
    layer_count: int = 0
    has_risen: bool = False
    initial_position_size: float = 0.0
    total_cost: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.entry_date is None:
            self.entry_date = datetime.now()

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.quantity * self.current_price

    @property
    def cost_value(self) -> float:
        """持仓成本"""
        return self.total_cost

    @property
    def pnl(self) -> float:
        """盈亏金额"""
        return self.market_value - self.cost_value

    @property
    def pnl_percent(self) -> float:
        """盈亏百分比"""
        if self.cost_value == 0:
            return 0.0
        return self.pnl / self.cost_value

    def update_price(self, price: float) -> None:
        """更新当前价格"""
        self.current_price = price
        self.last_update = datetime.now()

        # 检查是否上涨过
        if price > self.avg_price and not self.has_risen:
            self.has_risen = True

    def add_shares(self, quantity: int, price: float) -> None:
        """
        添加股票（加仓）

        Args:
            quantity: 增持数量
            price: 增持价格
        """
        # 计算新的总成本
        old_cost = self.total_cost
        add_cost = quantity * price

        new_quantity = self.quantity + quantity
        new_cost = old_cost + add_cost

        # 更新持仓
        self.quantity = new_quantity
        self.total_cost = new_cost

        # 重新计算平均成本（加权平均）
        if new_quantity > 0:
            self.avg_price = new_cost / new_quantity

        self.last_update = datetime.now()

    def remove_shares(self, quantity: int) -> float:
        """
        减少股票（减仓）

        Args:
            quantity: 减持数量

        Returns:
            减持部分的成本（用于计算盈亏）
        """
        if quantity > self.quantity:
            raise ValueError(f"减持数量 {quantity} 超过持仓 {self.quantity}")

        # 计算减持比例
        ratio = quantity / self.quantity
        removed_cost = self.total_cost * ratio

        # 更新持仓
        self.quantity -= quantity
        self.total_cost -= removed_cost

        if self.quantity == 0:
            self.avg_price = 0.0
            self.total_cost = 0.0
            self.has_risen = False

        self.last_update = datetime.now()

        return removed_cost

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'cost_value': self.cost_value,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent * 100,
            'layer_count': self.layer_count,
            'has_risen': self.has_risen,
            'entry_date': self.entry_date.strftime('%Y-%m-%d') if self.entry_date else None
        }


class PositionManager:
    """
    仓位管理器

    管理资金和持仓，支持：
    - 初始建仓（20%）
    - 分层加仓（每跌1%补仓10%，基于总资金）
    - 成本价计算（加权平均）
    - 持仓状态追踪

    Attributes:
        total_capital: 总资金
        available_capital: 可用资金
        positions: 持仓字典 {symbol: Position}
        params: 策略参数
    """

    def __init__(self, total_capital: float, params: Optional[Dict[str, Any]] = None):
        """
        初始化

        Args:
            total_capital: 总资金（初始资金）
            params: 策略参数，包含：
                - initial_position_size: 初始仓位比例（默认0.20）
                - decline_percent_per_layer: 每层下跌比例（默认0.01）
                - position_percent_per_layer: 每层加仓比例（默认0.10）
                - max_layers: 最大加仓层数（默认8）

        Example:
            >>> params = {
            ...     'initial_position_size': 0.20,  # 初始20%
            ...     'position_percent_per_layer': 0.10,  # 每次补仓10%
            ...     'max_layers': 8
            ... }
            >>> pm = PositionManager(total_capital=1000000, params=params)
        """
        self.total_capital = total_capital
        self.available_capital = total_capital
        self.positions: Dict[str, Position] = {}
        self.params = params or {}

        # 新增：最大持仓数量（用于资金分配）
        self.max_position_count = self.params.get('max_position_count', 10)
        if self.max_position_count <= 0:
            raise ValueError(f"max_position_count必须大于0, 当前: {self.max_position_count}")

        # 新增：单票配额 = 总资金 / 最大持仓数
        self.per_stock_allocation = self.total_capital / self.max_position_count

        self.logger = setup_logger('position_manager')
        self.logger.info(f"仓位管理器初始化: 总资金={total_capital:,.0f}元")
        self.logger.info(f"  最大持仓数: {self.max_position_count}")
        self.logger.info(f"  单票配额: {self.per_stock_allocation:,.0f}")

    def calculate_initial_position_size(self, price: float) -> int:
        """
        计算初始建仓数量

        公式：
        - 初始资金 = 总资金 * 20%
        - 建仓数量 = 初始资金 / 价格

        Args:
            price: 股票价格

        Returns:
            建仓数量（股）

        Example:
            >>> pm = PositionManager(1000000)
            >>> quantity = pm.calculate_initial_position_size(10.0)
            >>> print(f"初始建仓数量: {quantity}股")  # 20000股 (20万/10元)
        """
        initial_percent = self.params.get('initial_position_size', 0.20)
        # 关键修改：基于单票配额，而不是总资金
        position_value = self.per_stock_allocation * initial_percent

        # 检查可用资金
        if position_value > self.available_capital:
            self.logger.warning(f"可用资金不足，调整建仓金额: {position_value:.0f} > {self.available_capital:.0f}")
            position_value = self.available_capital

        quantity = int(position_value / price)

        self.logger.info(f"初始建仓计算: 价格={price:.2f}, 金额={position_value:.0f}, 数量={quantity}")

        return quantity

    def calculate_add_position_size(
        self,
        symbol: str,
        current_price: float,
        layer: int
    ) -> int:
        """
        计算加仓数量（第N层）

        规则：
        - 基于**总资金**的百分比（不是初始仓位）
        - 每跌1%补仓10%
        - 第0层：初始建仓20%
        - 第1-8层：每次补仓10%

        Args:
            symbol: 股票代码（用于验证持仓状态）
            current_price: 当前价格
            layer: 加仓层数（0=初始建仓，1=第一次补仓，...）

        Returns:
            加仓数量（股）

        Calculation:
            总资金 = 100万
            初始仓位(0层) = 100万 * 20% = 20万
            第1层补仓 = 100万 * 10% = 10万 (跌1%时)
            第2层补仓 = 100万 * 10% = 10万 (跌2%时)
            ...
            第8层补仓 = 100万 * 10% = 10万 (跌8%时)
            最终仓位 = 20万 + 8*10万 = 100万 (满仓)

        Example:
            >>> pm = PositionManager(1000000)
            >>> # 当前价格10元，第1层补仓
            >>> quantity = pm.calculate_add_position_size('000001.SZ', 10.0, 1)
            >>> print(f"加仓数量: {quantity}股")  # 10000股 (10万/10元)
        """
        max_layers = self.params.get('max_layers', 8)
        position_percent_per_layer = self.params.get('position_percent_per_layer', 0.10)

        if layer > max_layers:
            self.logger.warning(f"超过最大加仓层数: {layer} > {max_layers}")
            return 0

        # 关键修改：基于单票配额，而不是总资金
        # 加仓金额 = 单票配额 * 10%
        add_value = self.per_stock_allocation * position_percent_per_layer

        # 检查可用资金
        if add_value > self.available_capital:
            self.logger.warning(f"可用资金不足，调整加仓金额: {add_value:.0f} > {self.available_capital:.0f}")
            add_value = self.available_capital

        quantity = int(add_value / current_price)

        self.logger.info(f"加仓计算: 层数={layer}, 价格={current_price:.2f}, 金额={add_value:.0f}, 数量={quantity}")

        return quantity

    def open_position(
        self,
        symbol: str,
        price: float,
        quantity: Optional[int] = None,
        percent: Optional[float] = None,
        entry_date: Optional[datetime] = None
    ) -> bool:
        """
        开仓（首次建仓）

        Args:
            symbol: 股票代码
            price: 价格
            quantity: 数量（可选）
            percent: 仓位比例（可选，如0.20表示20%）

        Returns:
            是否成功

        Example:
            >>> pm = PositionManager(1000000)
            >>> success = pm.open_position('000001.SZ', price=10.0, percent=0.20)
            >>> print(f"建仓成功: {success}")
        """
        if symbol in self.positions:
            self.logger.error(f"股票已持仓，不能重复开仓: {symbol}")
            return False

        # 计算数量
        if quantity is None and percent is not None:
            quantity = int((self.total_capital * percent) / price)
        elif quantity is None:
            quantity = self.calculate_initial_position_size(price)

        if quantity == 0:
            self.logger.warning(f"计算出的数量为0，无法开仓: {symbol}")
            return False

        # 计算成本
        cost = quantity * price

        # 检查可用资金
        if cost > self.available_capital:
            self.logger.error(f"可用资金不足: 需要{cost:.0f}, 可用{self.available_capital:.0f}")
            return False

        # 创建持仓
        position = Position(
            symbol=symbol,
            quantity=quantity,
            avg_price=price,
            current_price=price,
            entry_date=entry_date,
            layer_count=0,
            has_risen=False,
            initial_position_size=percent or self.params.get('initial_position_size', 0.20),
            total_cost=cost
        )

        self.positions[symbol] = position
        self.available_capital -= cost

        self.logger.info(f"开仓成功: {symbol}, 价格={price:.2f}, 数量={quantity}, 金额={cost:.0f}")
        self.logger.info(f"剩余可用资金: {self.available_capital:.0f}")

        return True

    def add_position(
        self,
        symbol: str,
        price: float,
        layer: int
    ) -> bool:
        """
        加仓（第N层）

        Args:
            symbol: 股票代码
            price: 当前价格
            layer: 加仓层数

        Returns:
            是否成功

        Example:
            >>> pm = PositionManager(1000000)
            >>> pm.open_position('000001.SZ', price=10.0)
            >>> # 价格下跌，触发补仓
            >>> success = pm.add_position('000001.SZ', price=9.9, layer=1)
            >>> print(f"加仓成功: {success}")
        """
        if symbol not in self.positions:
            self.logger.error(f"股票未持仓，无法加仓: {symbol}")
            return False

        position = self.positions[symbol]

        # 计算加仓数量
        quantity = self.calculate_add_position_size(symbol, price, layer)

        if quantity == 0:
            return False

        # 计算成本
        cost = quantity * price

        # 检查可用资金
        if cost > self.available_capital:
            self.logger.error(f"可用资金不足: 需要{cost:.0f}, 可用{self.available_capital:.0f}")
            return False

        # 加仓
        position.add_shares(quantity, price)
        position.layer_count = layer
        self.available_capital -= cost

        self.logger.info(f"加仓成功: {symbol}, 层数={layer}, 价格={price:.2f}, 数量={quantity}, 金额={cost:.0f}")
        self.logger.info(f"新持仓: 数量={position.quantity}, 成本={position.avg_price:.2f}, 层数={position.layer_count}")
        self.logger.info(f"剩余可用资金: {self.available_capital:.0f}")

        return True

    def close_position(self, symbol: str, price: float) -> Optional[float]:
        """
        平仓（清仓）

        Args:
            symbol: 股票代码
            price: 平仓价格

        Returns:
            盈亏金额（正数=盈利，负数=亏损），如果失败返回None

        Example:
            >>> pm = PositionManager(1000000)
            >>> pm.open_position('000001.SZ', price=10.0)
            >>> # 价格上涨后卖出
            >>> pnl = pm.close_position('000001.SZ', price=11.0)
            >>> print(f"平仓盈亏: {pnl:.0f}")
        """
        if symbol not in self.positions:
            self.logger.error(f"股票未持仓，无法平仓: {symbol}")
            return None

        position = self.positions[symbol]

        # 计算市值
        market_value = position.quantity * price
        cost = position.total_cost
        pnl = market_value - cost

        # 释放资金
        self.available_capital += market_value

        # 移除持仓
        del self.positions[symbol]

        self.logger.info(f"平仓成功: {symbol}")
        self.logger.info(f"  成本: {cost:.0f}")
        self.logger.info(f"  市值: {market_value:.0f}")
        self.logger.info(f"  盈亏: {pnl:+.0f} ({pnl/cost*100:+.2f}%)")
        self.logger.info(f"  可用资金: {self.available_capital:.0f}")

        return pnl

    def update_position_price(self, symbol: str, price: float) -> None:
        """
        更新持仓价格（每日调用）

        Args:
            symbol: 股票代码
            price: 最新价格
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        position.update_price(price)

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            symbol: 股票代码

        Returns:
            Position对象，如果没有持仓返回None
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        """
        获取所有持仓

        Returns:
            Position对象列表
        """
        return list(self.positions.values())

    def get_position_stats(self) -> Dict[str, Any]:
        """
        获取持仓统计

        Returns:
            统计信息字典
        """
        if not self.positions:
            return {
                'position_count': 0,
                'total_value': 0.0,
                'total_cost': 0.0,
                'total_pnl': 0.0,
                'available_capital': self.available_capital,
                'used_capital_percent': 0.0
            }

        total_value = sum(p.market_value for p in self.positions.values())
        total_cost = sum(p.total_cost for p in self.positions.values())
        total_pnl = sum(p.pnl for p in self.positions.values())
        used_capital = self.total_capital - self.available_capital

        return {
            'position_count': len(self.positions),
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'pnl_percent': (total_pnl / total_cost * 100) if total_cost > 0 else 0.0,
            'available_capital': self.available_capital,
            'exposure': total_value / self.total_capital if self.total_capital > 0 else 0.0,
            'used_capital_percent': used_capital / self.total_capital if self.total_capital > 0 else 0.0
        }

    def check_position_limit(self, symbol: str, max_percent: float = 0.30) -> bool:
        """
        检查单票持仓限制

        Args:
            symbol: 股票代码
            max_percent: 最大持仓比例（默认30%）

        Returns:
            是否在限制内
        """
        if symbol not in self.positions:
            return True

        position = self.positions[symbol]
        position_percent = position.market_value / self.total_capital

        if position_percent > max_percent:
            self.logger.warning(f"股票 {symbol} 持仓超限: {position_percent:.1%} > {max_percent:.1%}")
            return False

        return True

    def check_total_exposure(self, max_exposure: float = 0.80) -> bool:
        """
        检查总仓位暴露

        Args:
            max_exposure: 最大暴露（默认80%）

        Returns:
            是否在限制内
        """
        total_value = sum(p.market_value for p in self.positions.values())
        exposure = total_value / self.total_capital if self.total_capital > 0 else 0.0

        if exposure > max_exposure:
            self.logger.warning(f"总仓位超限: {exposure:.1%} > {max_exposure:.1%}")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于日志和调试）

        Returns:
            字典格式
        """
        stats = self.get_position_stats()

        return {
            'total_capital': self.total_capital,
            'available_capital': self.available_capital,
            'position_count': stats['position_count'],
            'total_value': stats['total_value'],
            'total_pnl': stats['total_pnl'],
            'exposure': stats['exposure'],
            'positions': [p.to_dict() for p in self.get_all_positions()]
        }
