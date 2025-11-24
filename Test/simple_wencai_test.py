"""
简化的问财测试
直接测试pywencai库和Cookie
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

def simple_test():
    """简单测试"""
    print("开始简化测试...")
    
    # 1. 测试配置读取
    cookie = settings.get_env('WENCAI_COOKIE')
    print(f"Cookie长度: {len(cookie) if cookie else 0}")
    
    if not cookie:
        print("❌ 没有Cookie")
        return
    
    # 2. 测试pywencai导入
    try:
        import pywencai
        print("✅ pywencai导入成功")
    except Exception as e:
        print(f"❌ pywencai导入失败: {e}")
        return
    
    # 3. 测试最简单的API调用
    try:
        print("尝试API调用（股票详情）...")
        result1 = pywencai.get(query="000001", cookie=cookie)
        print(f"股票详情查询结果类型: {type(result1)}")
        
        print("\n尝试API调用（选股查询）...")
        result2 = pywencai.get(query="银行", cookie=cookie)
        print(f"选股查询结果类型: {type(result2)}")
        
        if isinstance(result2, dict):
            print("✅ 选股查询返回字典格式")
            print(f"字典键: {list(result2.keys())}")
            
            # 查找可能包含股票列表的键
            for key, value in result2.items():
                if isinstance(value, dict) and 'code' in str(value):
                    print(f"\n可能包含股票代码的键: {key}")
                    if hasattr(value, 'shape'):
                        print(f"  DataFrame形状: {value.shape}")
                        print(f"  列名: {list(value.columns)}")
                        if not value.empty:
                            print(f"  前几行数据:")
                            print(value.head())
                elif isinstance(value, list) and len(value) > 0:
                    print(f"\n列表键: {key}, 长度: {len(value)}")
                    print(f"  第一个元素: {value[0]}")
        else:
            print(f"选股查询结果类型: {type(result2)}")
            print(f"结果内容: {result2}")
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()