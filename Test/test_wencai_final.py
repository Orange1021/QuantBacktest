"""
最终的问财选股器测试
重点测试选股功能而不是单股查询
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.selectors.wencai_selector import WencaiSelector
from config.settings import settings


def test_wencai_selector():
    """测试问财选股器的核心功能"""
    print("=" * 60)
    print("问财选股器最终测试")
    print("=" * 60)
    
    # 获取Cookie并创建选股器
    cookie = settings.get_env('WENCAI_COOKIE')
    if not cookie:
        print("❌ 未找到Cookie")
        return False
    
    selector = WencaiSelector(cookie=cookie)
    
    # 验证连接
    if not selector.validate_connection():
        print("❌ 连接验证失败")
        return False
    
    print("✅ 连接验证成功")
    
    # 测试真实的选股查询
    test_cases = [
        {
            "name": "银行股选股",
            "query": "银行",
            "expected_min": 10  # 至少返回10只股票
        },
        {
            "name": "科技股选股", 
            "query": "科技",
            "expected_min": 5
        },
        {
            "name": "市值大于100亿",
            "query": "市值大于100亿",
            "expected_min": 5
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试{i}: {test_case['name']}")
        print(f"查询条件: {test_case['query']}")
        
        try:
            result = selector.select_stocks(
                date=datetime.now(),
                query=test_case['query']
            )
            
            if len(result) >= test_case['expected_min']:
                print(f"✅ 成功，返回 {len(result)} 只股票")
                print(f"   前5只: {result[:5]}")
                success_count += 1
            else:
                print(f"⚠️ 返回股票数量不足: {len(result)} < {test_case['expected_min']}")
                print(f"   实际结果: {result}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    # 测试日期占位符功能
    print(f"\n测试{len(test_cases)+1}: 日期占位符功能")
    yesterday = datetime.now() - timedelta(days=1)
    try:
        result = selector.select_stocks(
            date=yesterday,
            query="{date}涨幅大于0"
        )
        print(f"✅ 日期占位符测试成功，返回 {len(result)} 只股票")
        if len(result) > 0:
            print(f"   示例: {result[:3]}")
        success_count += 1
    except Exception as e:
        print(f"❌ 日期占位符测试失败: {e}")
    
    # 总结
    total_tests = len(test_cases) + 1
    print(f"\n" + "=" * 60)
    print(f"测试总结: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！问财选股器工作正常")
        return True
    else:
        print("💥 部分测试失败")
        return False


if __name__ == "__main__":
    test_wencai_selector()