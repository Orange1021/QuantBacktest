"""
配置文件读取模块
负责读取.env和config.yaml配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class BacktestConfig:
    """回测配置"""
    start_date: str
    end_date: str
    benchmark: str
    initial_capital: float


@dataclass
class DataConfig:
    """数据配置"""
    csv_root_path: str
    cache_path: str
    output_path: str


@dataclass
class SelectorConfig:
    """选股配置"""
    default_type: str
    wencai: Dict[str, Any]
    tushare: Dict[str, Any]


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    parameters: Dict[str, Any]


@dataclass
class RiskConfig:
    """风控配置"""
    max_position_ratio: float
    max_sector_ratio: float
    stop_loss: float
    take_profit: float


@dataclass
class ExecutionConfig:
    """交易配置"""
    commission_rate: float
    slippage_rate: float
    min_commission: float


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str
    file_path: str
    max_file_size: str
    backup_count: int


@dataclass
class AnalysisConfig:
    """分析配置"""
    performance_metrics: list
    charts: Dict[str, bool]


class Settings:
    """配置管理类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: config.yaml文件路径，默认为项目根目录下的config/config.yaml
        """
        if config_path is None:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = {}
        self._env_vars = {}
        
        # 加载配置
        self._load_env()
        self._load_config()
        
        # 创建配置对象
        self.backtest = self._create_backtest_config()
        self.data = self._create_data_config()
        self.selector = self._create_selector_config()
        self.strategy = self._create_strategy_config()
        self.risk = self._create_risk_config()
        self.execution = self._create_execution_config()
        self.logging = self._create_logging_config()
        self.analysis = self._create_analysis_config()
    
    def _load_env(self):
        """加载环境变量"""
        env_path = self.config_path.parent.parent / ".env"
        
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self._env_vars[key.strip()] = value.strip()
        
        # 同时也加载系统环境变量
        self._env_vars.update(os.environ)
    
    def _load_config(self):
        """加载YAML配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
    
    def get_env(self, key: str, default: str = None) -> str:
        """获取环境变量"""
        return self._env_vars.get(key, default)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _create_backtest_config(self) -> BacktestConfig:
        """创建回测配置对象"""
        data = self.get_config('backtest', {})
        return BacktestConfig(**data)
    
    def _create_data_config(self) -> DataConfig:
        """创建数据配置对象"""
        data = self.get_config('data', {})
        return DataConfig(**data)
    
    def _create_selector_config(self) -> SelectorConfig:
        """创建选股配置对象"""
        data = self.get_config('selector', {})
        return SelectorConfig(**data)
    
    def _create_strategy_config(self) -> StrategyConfig:
        """创建策略配置对象"""
        data = self.get_config('strategy', {})
        return StrategyConfig(**data)
    
    def _create_risk_config(self) -> RiskConfig:
        """创建风控配置对象"""
        data = self.get_config('risk', {})
        return RiskConfig(**data)
    
    def _create_execution_config(self) -> ExecutionConfig:
        """创建交易配置对象"""
        data = self.get_config('execution', {})
        return ExecutionConfig(**data)
    
    def _create_logging_config(self) -> LoggingConfig:
        """创建日志配置对象"""
        data = self.get_config('logging', {})
        return LoggingConfig(**data)
    
    def _create_analysis_config(self) -> AnalysisConfig:
        """创建分析配置对象"""
        data = self.get_config('analysis', {})
        return AnalysisConfig(**data)


# 全局配置实例
settings = Settings()