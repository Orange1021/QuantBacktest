#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理模块

提供统一的日志记录功能，支持控制台和文件输出
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "continuous_decline_strategy",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        log_file: 日志文件路径（None表示只输出到控制台）
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 备份文件数量

    Returns:
        配置好的日志记录器

    Example:
        logger = setup_logger(
            name="backtest",
            level="INFO",
            log_file="logs/backtest.log"
        )
        logger.info("开始回测...")
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 创建格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 使用RotatingFileHandler实现日志轮转
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建文件日志处理器: {e}")

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取已配置的日志记录器

    Args:
        name: 日志记录器名称（None表示获取根记录器）

    Returns:
        日志记录器

    Example:
        logger = get_logger("backtest")
        logger.info("日志消息")
    """
    return logging.getLogger(name)


class LogMixin:
    """
    日志混入类

    为类提供快捷的日志记录方法

    Example:
        class MyClass(LogMixin):
            def do_something(self):
                self.info("开始执行任务...")
                self.debug(f"参数: {params}")
                self.warning("注意了！")
                self.error("出错了！")
    """

    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        name = self.__class__.__name__
        return logging.getLogger(name)

    def debug(self, msg: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)


# 默认日志记录器
default_logger = setup_logger(
    name="continuous_decline_strategy",
    level="INFO",
    log_file="logs/strategy.log"
)
