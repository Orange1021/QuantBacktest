#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财连接测试脚本
用于验证问财选股功能是否正常工作
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.selectors.wencai_selector import WencaiSelector
from config.settings import settings

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_wencai_connection():
    """测试问财连接和选股功能"""
    print("=" * 60)
    print("问财连接测试开始")
    print("=" * 60)
    
    # 1. 获取Cookie
    cookie = settings.get_env('WENCAI_COOKIE')
    if not cookie:
        print("❌ 错误：未找到问财Cookie")
        print("请在 .env 文件中配置 WENCAI_COOKIE")
        return False
    
    print(f"✅ Cookie长度: {len(cookie)} 字符")
    
    # 2. 创建选股器
    try:
        selector = WencaiSelector(cookie=cookie)
        print("✅ WencaiSelector 创建成功")
    except Exception as e:
        print(f"❌ WencaiSelector 创建失败: {e}")
        return False
    
    # 3. 测试连接验证
    print("\n步骤1: 测试连接验证...")
    try:
        is_valid = selector.validate_connection()
        if is_valid:
            print("✅ 问财连接验证成功")
        else:
            print("❌ 问财连接验证失败")
            return False
    except Exception as e:
        print(f"❌ 连接验证异常: {e}")
        return False
    
    # 4. 测试简单选股查询
    print("\n步骤2: 测试简单选股查询...")
    try:
        bank_stocks = selector.select_stocks(
            date=datetime.now(),
            query="银行"
        )
        
        if bank_stocks:
            print(f"✅ 银行股查询成功，返回 {len(bank_stocks)} 只股票")
            print(f"前5只股票: {bank_stocks[:5]}")
        else:
            print("❌ 银行股查询返回空结果")
            return False
            
    except Exception as e:
        print(f"❌ 银行股查询异常: {e}")
        return False
    
    # 5. 测试策略查询（沪深300成分股）
    print("\n步骤3: 测试策略查询...")
    try:
        hs300_stocks = selector.select_stocks(
            date=datetime.now(),
            query="沪深300成分股，按市值排名取前10"
        )
        
        if hs300_stocks:
            print(f"✅ 沪深300查询成功，返回 {len(hs300_stocks)} 只股票")
            print(f"前10只股票: {hs300_stocks[:10]}")
        else:
            print("❌ 沪深300查询返回空结果")
            return False
            
    except Exception as e:
        print(f"❌ 沪深300查询异常: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！问财功能正常")
    print("=" * 60)
    return True

def test_direct_connection():
    """测试直接网络连接"""
    print("\n补充测试: 直接网络连接")
    print("-" * 40)
    
    import requests
    
    try:
        # 测试1: 百度（应该能访问）
        print("测试1: 访问百度...")
        response = requests.get('https://www.baidu.com', timeout=5)
        print(f"✅ 百度访问成功，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 百度访问失败: {e}")
    
    try:
        # 测试2: 问财首页
        print("测试2: 访问问财首页...")
        response = requests.get('https://www.iwencai.com', timeout=5)
        print(f"✅ 问财首页访问成功，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 问财首页访问失败: {e}")
    
    try:
        # 测试3: 禁用代理访问问财
        print("测试3: 禁用代理访问问财...")
        response = requests.get(
            'https://www.iwencai.com', 
            timeout=5,
            proxies={'http': None, 'https': None}
        )
        print(f"✅ 禁用代理访问问财成功，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 禁用代理访问问财失败: {e}")

if __name__ == "__main__":
    print("开始问财连接测试...")
    
    # 先测试直接网络连接
    test_direct_connection()
    
    # 再测试问财功能
    success = test_wencai_connection()
    
    if success:
        print("\n🎯 结论: 问财功能正常，可以正常进行策略驱动选股")
        sys.exit(0)
    else:
        print("\n⚠️ 结论: 问财功能异常，需要检查网络或代理设置")
        sys.exit(1)