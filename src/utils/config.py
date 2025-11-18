#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块

提供统一的配置文件加载和管理功能
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Union


def load_yaml_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载YAML配置文件

    Args:
        file_path: 配置文件路径

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 文件不存在
        yaml.YAMLError: YAML解析错误

    Example:
        config = load_yaml_config("configs/strategy.yaml")
        print(config['strategy']['name'])
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"YAML解析错误 ({file_path}): {e}")


def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载JSON配置文件

    Args:
        file_path: 配置文件路径

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON解析错误

    Example:
        config = load_json_config("configs/market.json")
        print(config['market']['name'])
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"JSON解析错误 ({file_path}): {e}", None, 0)


def save_yaml_config(config: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    保存配置到YAML文件

    Args:
        config: 配置字典
        file_path: 输出文件路径

    Example:
        config = {'strategy': {'name': 'MyStrategy'}}
        save_yaml_config(config, "output.yaml")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            config,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )


def save_json_config(config: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    保存配置到JSON文件

    Args:
        config: 配置字典
        file_path: 输出文件路径

    Example:
        config = {'strategy': {'name': 'MyStrategy'}}
        save_json_config(config, "output.json")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(
            config,
            f,
            ensure_ascii=False,
            indent=2
        )


class ConfigManager:
    """
    配置管理器类

    提供配置加载、缓存、验证等功能
    """

    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_config(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        加载配置文件（带缓存）

        Args:
            file_path: 配置文件路径

        Returns:
            配置字典

        Example:
            config = ConfigManager.load_config("configs/strategy.yaml")
        """
        file_path = str(file_path)

        # 如果已在缓存中，直接返回
        if file_path in cls._cache:
            return cls._cache[file_path]

        # 根据文件扩展名选择加载器
        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            config = load_yaml_config(file_path)
        elif file_path.endswith('.json'):
            config = load_json_config(file_path)
        else:
            raise ValueError(f"不支持的配置文件格式: {file_path}")

        # 添加到缓存
        cls._cache[file_path] = config
        return config

    @classmethod
    def clear_cache(cls) -> None:
        """清除配置缓存"""
        cls._cache.clear()

    @classmethod
    def get(cls, file_path: Union[str, Path], key: str, default: Any = None) -> Any:
        """
        获取配置中的特定值

        Args:
            file_path: 配置文件路径
            key: 键（支持点分式，如 'strategy.filter_params'）
            default: 默认值（如果不存在）

        Returns:
            配置值

        Example:
            # 获取单层值
            name = ConfigManager.get("config.yaml", "strategy.name")

            # 获取嵌套值
            threshold = ConfigManager.get("config.yaml", "strategy.filter_params.decline_days_threshold")
        """
        config = cls.load_config(file_path)

        # 支持点分式键
        keys = key.split('.')
        value = config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default


def confirm_user(message: str, choices: list) -> str:
    """
    向用户确认操作

    Args:
        message: 提示消息
        choices: 可选列表

    Returns:
        用户选择

    Example:
        choice = confirm_user("确认开始实盘？", ["是", "否"])
    """
    print(f"\n{message}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")

    while True:
        try:
            selection = int(input("\n请输入选项（数字）："))
            if 1 <= selection <= len(choices):
                return choices[selection - 1]
            else:
                print("无效选项，请重新输入")
        except ValueError:
            print("请输入数字")


# 快捷函数
load_yaml = load_yaml_config
load_json = load_json_config
save_yaml = save_yaml_config
save_json = save_json_config
