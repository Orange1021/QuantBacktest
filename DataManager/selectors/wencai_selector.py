"""
基于 pywencai 的自然语言选股器
使用问财的自然语言查询功能进行选股
"""

import logging
import time
import pandas as pd
from typing import List, Optional
from datetime import datetime

from .base import BaseStockSelector


class WencaiSelector(BaseStockSelector):
    """
    [具体实现类] 基于 pywencai 的自然语言选股器
    """

    def __init__(self, cookie: str = None, retry_count: int = 3, sleep_time: int = 2):
        """
        初始化选股器，尝试动态 import pywencai
        """
        self.cookie = cookie
        self.retry_count = retry_count
        self.sleep_time = sleep_time
        self._wencai = None
        self.logger = logging.getLogger(__name__)
        
        # 验证Cookie格式
        if cookie and len(cookie) < 100:
            self.logger.warning("Cookie长度异常，可能无效")
        
        # 动态加载 pywencai 库
        try:
            import pywencai
            self._wencai = pywencai
            
            # 测试导入是否成功
            if self.cookie:
                test_result = self._wencai.get(query="银行", cookie=self.cookie)
                if test_result is None:
                    raise ImportError("pywencai导入后测试失败")
            
            self.logger.info("成功加载 pywencai 库")
            
        except ImportError as e:
            self.logger.error(f"无法加载 pywencai 库: {e}")
            self.logger.error("请安装 pywencai: pip install pywencai")
            self._wencai = None
        except Exception as e:
            self.logger.error(f"pywencai 初始化失败: {e}")
            self._wencai = None

    def select_stocks(self, date: datetime, **kwargs) -> List[str]:
        """
        [实现方法]
        逻辑步骤:
        1. 从 kwargs 中获取 'query' 参数 (str)。如果不存在，记录 Error 并返回空列表。
        2. 日期处理: 
           - 生成 'YYYYMMDD' 格式字符串 (例如 '20240105')
           - 将 query 字符串中的占位符 "{date}" 替换为上述日期。
        3. 调用 pywencai.get(query=..., cookie=...)。
        4. 包含重试机制 (try-except loop)。
        5. 调用 _parse_codes 清洗数据。
        """
        # 检查pywencai是否正确初始化
        if self._wencai is None:
            self.logger.error("pywencai未正确初始化，无法执行选股")
            return []
        
        # 获取查询参数
        query = kwargs.get('query')
        if not query:
            self.logger.error("缺少必需的 'query' 参数")
            return []
        
        # 日期处理
        date_str = date.strftime('%Y%m%d')
        formatted_query = query.replace('{date}', date_str)
        
        self.logger.info(f"执行问财选股查询: {formatted_query}")
        
        # 重试机制
        for attempt in range(self.retry_count):
            try:
                # 调用问财API
                result = self._wencai.get(
                    query=formatted_query,
                    cookie=self.cookie
                )
                
                # 处理不同类型的返回值
                if result is None:
                    self.logger.warning(f"问财查询返回None，尝试 {attempt + 1}/{self.retry_count}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.sleep_time)
                        continue
                    return []
                
                if isinstance(result, dict):
                    # 字典返回值通常是单股查询，不是选股结果
                    self.logger.warning("收到字典返回值，可能是单股查询而非选股查询")
                    return []
                elif isinstance(result, pd.DataFrame):
                    if result.empty:
                        self.logger.warning(f"问财查询返回空DataFrame，尝试 {attempt + 1}/{self.retry_count}")
                        if attempt < self.retry_count - 1:
                            time.sleep(self.sleep_time)
                            continue
                        return []
                    
                    # 解析股票代码
                    stock_codes = self._parse_codes(result)
                    self.logger.info(f"问财选股成功，返回 {len(stock_codes)} 只股票")
                    return stock_codes
                else:
                    self.logger.error(f"未知返回类型: {type(result)}")
                    return []
                
            except Exception as e:
                self.logger.error(f"问财查询失败，尝试 {attempt + 1}/{self.retry_count}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.sleep_time)
                    continue
                else:
                    self.logger.error("所有重试均失败，返回空列表")
                    return []
        
        return []

    def validate_connection(self) -> bool:
        """
        [实现方法]
        发送一个简单查询测试 Cookie 是否有效。
        """
        if not self.cookie:
            self.logger.warning("未提供 Cookie，无法验证连接")
            return False
        
        if self._wencai is None:
            self.logger.error("pywencai未正确初始化")
            return False
        
        try:
            # 发送选股查询测试连接（返回DataFrame）
            df = self._wencai.get(
                query="银行",
                cookie=self.cookie
            )
            
            if df is not None and hasattr(df, 'empty') and not df.empty:
                self.logger.info("问财连接验证成功")
                return True
            else:
                self.logger.warning("问财连接验证失败：返回空结果")
                return False
                
        except Exception as e:
            self.logger.error(f"问财连接验证失败: {e}")
            return False

    def _parse_codes(self, df) -> List[str]:
        """
        [私有辅助方法]
        职责: 从混乱的 DataFrame 中提取代码列并标准化。
        逻辑:
        1. 遍历列名寻找包含 'code' 或 '代码' 的列。
        2. 遍历该列数据，补充后缀:
           - 6开头 -> .SH
           - 0/3开头 -> .SZ
           - 4/8开头 -> .BJ (如果代码本身已有后缀则不处理)
        3. 去重并返回列表。
        """
        # 添加输入类型检查
        if not isinstance(df, pd.DataFrame):
            self.logger.error(f"_parse_codes期望DataFrame，收到: {type(df)}")
            return []
        
        if df is None or df.empty:
            return []
        
        # 查找代码列
        code_column = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'code' in col_lower or '代码' in col:
                code_column = col
                break
        
        if code_column is None:
            self.logger.error("未找到代码列，可用列名: " + str(list(df.columns)))
            return []
        
        # 提取并标准化股票代码
        stock_codes = []
        for code in df[code_column]:
            if pd.isna(code):
                continue
                
            code_str = str(code).strip()
            
            # 如果代码已经有后缀，直接使用
            if '.' in code_str:
                stock_codes.append(code_str.upper())
                continue
            
            # 根据代码开头添加后缀
            if len(code_str) == 6:
                if code_str.startswith('6'):
                    stock_codes.append(f"{code_str}.SH")
                elif code_str.startswith('0') or code_str.startswith('3'):
                    stock_codes.append(f"{code_str}.SZ")
                elif code_str.startswith('4') or code_str.startswith('8'):
                    stock_codes.append(f"{code_str}.BJ")
                else:
                    # 未知代码，默认添加.SH
                    stock_codes.append(f"{code_str}.SH")
                    self.logger.warning(f"未知代码格式: {code_str}，默认添加.SH后缀")
            else:
                # 非标准长度代码，直接使用
                stock_codes.append(code_str)
                self.logger.warning(f"非标准长度代码: {code_str}")
        
        # 去重并返回
        unique_codes = list(set(stock_codes))
        self.logger.debug(f"解析得到 {len(unique_codes)} 只股票代码")
        
        return unique_codes