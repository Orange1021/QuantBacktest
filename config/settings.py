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
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            try:
                                key, value = line.split('=', 1)
                                self._env_vars[key.strip()] = value.strip()
                            except ValueError as e:
                                raise ValueError(
                                    f".env文件第{line_num}行格式错误: {line}\n"
                                    f"正确格式: KEY=VALUE\n"
                                    f"请检查.env文件格式"
                                ) from e
            except UnicodeDecodeError as e:
                raise ValueError(
                    f".env文件编码错误，请使用UTF-8编码\n"
                    f"文件路径: {env_path}\n"
                    f"建议: 用记事本打开.env文件，另存为UTF-8格式"
                ) from e
            except Exception as e:
                raise IOError(
                    f"读取.env文件失败\n"
                    f"文件路径: {env_path}\n"
                    f"错误信息: {str(e)}\n"
                    f"请检查文件是否存在且可读"
                ) from e
        
        # 同时也加载系统环境变量
        self._env_vars.update(os.environ)
    
    def _load_config(self):
        """加载YAML配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                f"请检查:\n"
                f"1. 文件路径是否正确\n"
                f"2. 项目根目录下是否存在config/config.yaml文件\n"
                f"3. 文件是否被误删除或移动"
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
                
            # 验证关键配置项
            self._validate_required_configs()
                
        except yaml.YAMLError as e:
            raise ValueError(
                f"YAML配置文件格式错误\n"
                f"文件路径: {self.config_path}\n"
                f"错误信息: {str(e)}\n"
                f"请检查:\n"
                f"1. YAML语法是否正确（缩进、冒号等）\n"
                f"2. 是否有特殊字符未正确转义\n"
                f"3. 使用在线YAML验证器检查格式"
            ) from e
        except UnicodeDecodeError as e:
            raise ValueError(
                f"配置文件编码错误，请使用UTF-8编码\n"
                f"文件路径: {self.config_path}\n"
                f"建议: 用记事本打开config.yaml文件，另存为UTF-8格式"
            ) from e
        except Exception as e:
            raise IOError(
                f"读取配置文件失败\n"
                f"文件路径: {self.config_path}\n"
                f"错误信息: {str(e)}\n"
                f"请检查文件是否存在且可读"
            ) from e
    
    def get_env(self, key: str, default: str = None) -> str:
        """获取环境变量"""
        value = self._env_vars.get(key, default)
        
        # 特殊关键配置项的验证
        if key in ['WENCAI_COOKIE'] and value:
            if len(value) < 100:
                raise ValueError(
                    f"环境变量 {key} 长度异常，可能无效\n"
                    f"当前长度: {len(value)}\n"
                    f"请检查:\n"
                    f"1. Cookie是否完整复制\n"
                    f"2. Cookie是否已过期\n"
                    f"3. 是否包含特殊字符被截断"
                )
        
        return value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                if default is None and self._is_required_config(key):
                    raise ValueError(
                        f"配置文件缺少必需的配置项: {key}\n"
                        f"配置文件路径: {self.config_path}\n"
                        f"请检查config.yaml文件并添加相应配置"
                    )
                return default
        
        # 验证配置值的有效性
        self._validate_config_value(key, value)
        
        return value
    
    def _is_required_config(self, key: str) -> bool:
        """判断是否为必需的配置项"""
        required_configs = [
            'backtest.initial_capital',
            'backtest.start_date',
            'backtest.end_date',
            'data.csv_root_path',
            'data.output_path'
        ]
        return key in required_configs
    
    def _validate_config_value(self, key: str, value: Any) -> None:
        """验证配置值的有效性"""
        if key == 'backtest.initial_capital':
            try:
                capital = float(value)
                if capital <= 0:
                    raise ValueError(f"初始资金必须大于0，当前值: {capital}")
                if capital < 1000:
                    raise ValueError(f"初始资金过小，建议至少1000元，当前值: {capital}")
            except (ValueError, TypeError) as e:
                raise ValueError(f"初始资金配置错误: {value}，必须是正数") from e
                
        elif key == 'data.csv_root_path':
            if not value:
                raise ValueError("CSV数据根路径不能为空")
            csv_path = Path(value)
            if not csv_path.exists():
                raise ValueError(
                    f"CSV数据根路径不存在: {value}\n"
                    f"请检查:\n"
                    f"1. 路径是否正确\n"
                    f"2. 目录是否存在\n"
                    f"3. 是否有访问权限"
                )
                
        elif key in ['backtest.start_date', 'backtest.end_date']:
            try:
                from datetime import datetime
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError as e:
                raise ValueError(
                    f"日期格式错误: {value}\n"
                    f"正确格式: YYYY-MM-DD (如: 2024-01-01)\n"
                    f"请检查config.yaml中的日期配置"
                ) from e
    
    def _validate_required_configs(self) -> None:
        """验证必需的配置项是否存在"""
        required_configs = {
            'backtest.initial_capital': '初始资金',
            'backtest.start_date': '回测开始日期',
            'backtest.end_date': '回测结束日期',
            'data.csv_root_path': 'CSV数据根路径',
            'data.output_path': '输出路径'
        }
        
        missing_configs = []
        for config_key, description in required_configs.items():
            if self.get_config(config_key, None) is None:
                missing_configs.append(f"  - {config_key}: {description}")
        
        if missing_configs:
            raise ValueError(
                f"配置文件缺少必需的配置项:\n" + "\n".join(missing_configs) + "\n\n"
                f"请在config.yaml文件中添加这些配置项\n"
                f"配置文件路径: {self.config_path}"
            )
    
    def _create_backtest_config(self) -> BacktestConfig:
        """创建回测配置对象"""
        try:
            data = self.get_config('backtest', {})
            return BacktestConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"回测配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中backtest配置项是否完整\n"
                f"必需字段: start_date, end_date, benchmark, initial_capital"
            ) from e
    
    def _create_data_config(self) -> DataConfig:
        """创建数据配置对象"""
        try:
            data = self.get_config('data', {})
            return DataConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"数据配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中data配置项是否完整\n"
                f"必需字段: csv_root_path, cache_path, output_path"
            ) from e
    
    def _create_selector_config(self) -> SelectorConfig:
        """创建选股配置对象"""
        try:
            data = self.get_config('selector', {})
            return SelectorConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"选股配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中selector配置项是否完整"
            ) from e
    
    def _create_strategy_config(self) -> StrategyConfig:
        """创建策略配置对象"""
        try:
            data = self.get_config('strategy', {})
            return StrategyConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"策略配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中strategy配置项是否完整"
            ) from e
    
    def _create_risk_config(self) -> RiskConfig:
        """创建风控配置对象"""
        try:
            data = self.get_config('risk', {})
            return RiskConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"风控配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中risk配置项是否完整"
            ) from e
    
    def _create_execution_config(self) -> ExecutionConfig:
        """创建交易配置对象"""
        try:
            data = self.get_config('execution', {})
            return ExecutionConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"交易配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中execution配置项是否完整"
            ) from e
    
    def _create_logging_config(self) -> LoggingConfig:
        """创建日志配置对象"""
        try:
            data = self.get_config('logging', {})
            return LoggingConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"日志配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中logging配置项是否完整"
            ) from e
    
    def _create_analysis_config(self) -> AnalysisConfig:
        """创建分析配置对象"""
        try:
            data = self.get_config('analysis', {})
            return AnalysisConfig(**data)
        except TypeError as e:
            raise ValueError(
                f"分析配置创建失败\n"
                f"错误信息: {str(e)}\n"
                f"请检查config.yaml中analysis配置项是否完整"
            ) from e


# 全局配置实例
settings = Settings()