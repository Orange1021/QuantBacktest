"""
测试问财选股器
验证pywencai库和Cookie是否正常工作
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.selectors.wencai_selector import WencaiSelector
from config.settings import settings


def test_wencai_connection():
    """测试问财连接"""
    print("=" * 60)
    print("测试问财连接")
    print("=" * 60)
    
    try:
        # 从配置中获取Cookie
        cookie = settings.get_env('WENCAI_COOKIE')
        if not cookie:
            print("❌ 未找到问财Cookie，请在.env文件中设置WENCAI_COOKIE")
            return False
        
        print(f"Cookie长度: {len(cookie)} 字符")
        print("Cookie前10位:", cookie[:10] + "...")
        
        # 创建选股器
        selector = WencaiSelector(cookie=cookie)
        
        # 测试连接
        is_connected = selector.validate_connection()
        
        if is_connected:
            print("✅ 问财连接验证成功")
            return True
        else:
            print("❌ 问财连接验证失败")
            print("可能原因:")
            print("  - Cookie已过期")
            print("  - Cookie格式不正确")
            print("  - 网络连接问题")
            return False
            
    except ImportError as e:
        print(f"❌ 导入pywencai失败: {e}")
        print("请安装pywencai: pip install pywencai")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


def test_wencai_selection():
    """测试问财选股功能"""
    print("\n" + "=" * 60)
    print("测试问财选股功能")
    print("=" * 60)
    
    try:
        # 从配置中获取Cookie
        cookie = settings.get_env('WENCAI_COOKIE')
        if not cookie:
            print("❌ 未找到问财Cookie")
            return False
        
        # 创建选股器
        selector = WencaiSelector(cookie=cookie)
        
        # 测试查询1：简单股票查询
        print("测试1: 查询平安银行")
        result1 = selector.select_stocks(
            date=datetime.now(),
            query="000001.SZ"
        )
        
        if result1:
            print(f"✅ 查询成功，返回 {len(result1)} 只股票")
            print(f"   结果: {result1[:3]}")  # 显示前3个
        else:
            print("❌ 查询1失败")
            return False
        
        # 测试查询2：自然语言查询
        print("\n测试2: 自然语言查询（涨幅大于5%）")
        yesterday = datetime.now() - timedelta(days=1)
        result2 = selector.select_stocks(
            date=yesterday,
            query="{date}涨幅大于5%"
        )
        
        if result2:
            print(f"✅ 查询成功，返回 {len(result2)} 只股票")
            print(f"   前5只股票: {result2[:5]}")
        else:
            print("⚠️ 查询2返回空结果（可能是当天没有符合条件的股票）")
        
        # 测试查询3：行业查询
        print("\n测试3: 银行股查询")
        result3 = selector.select_stocks(
            date=datetime.now(),
            query="银行"
        )
        
        if result3:
            print(f"✅ 查询成功，返回 {len(result3)} 只股票")
            print(f"   前5只股票: {result3[:5]}")
        else:
            print("❌ 查询3失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 选股测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_parsing():
    """测试股票代码解析功能"""
    print("\n" + "=" * 60)
    print("测试股票代码解析功能")
    print("=" * 60)
    
    try:
        # 创建模拟DataFrame测试解析功能
        import pandas as pd
        
        # 测试数据1：标准代码列
        df1 = pd.DataFrame({
            '代码': ['000001', '000002', '600000', '300001', '430001']
        })
        
        cookie = settings.get_env('WENCAI_COOKIE')
        selector = WencaiSelector(cookie=cookie) if cookie else None
        
        if selector:
            result1 = selector._parse_codes(df1)
            expected1 = ['000001.SZ', '000002.SZ', '600000.SH', '300001.SZ', '430001.BJ']
            
            print(f"输入代码: {df1['代码'].tolist()}")
            print(f"解析结果: {result1}")
            print(f"期望结果: {expected1}")
            
            if set(result1) == set(expected1):
                print("✅ 代码解析测试1通过")
            else:
                print("❌ 代码解析测试1失败")
                return False
        
        # 测试数据2：已有后缀的代码
        df2 = pd.DataFrame({
            'stock_code': ['000001.SZ', '600000.SH', '300001.SZ']
        })
        
        if selector:
            result2 = selector._parse_codes(df2)
            expected2 = ['000001.SZ', '600000.SH', '300001.SZ']
            
            print(f"\n输入代码: {df2['stock_code'].tolist()}")
            print(f"解析结果: {result2}")
            
            if set(result2) == set(expected2):
                print("✅ 代码解析测试2通过")
            else:
                print("❌ 代码解析测试2失败")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 代码解析测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试问财选股器...\n")
    
    # 测试连接
    connection_ok = test_wencai_connection()
    
    if not connection_ok:
        print("\n💥 连接测试失败，跳过后续测试")
        return
    
    # 测试选股功能
    selection_ok = test_wencai_selection()
    
    # 测试代码解析
    parsing_ok = test_code_parsing()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if connection_ok and selection_ok and parsing_ok:
        print("🎉 所有测试通过！问财选股器工作正常")
    else:
        print("💥 部分测试失败")
        print(f"   连接测试: {'✅' if connection_ok else '❌'}")
        print(f"   选股测试: {'✅' if selection_ok else '❌'}")
        print(f"   解析测试: {'✅' if parsing_ok else '❌'}")


if __name__ == "__main__":
    main()