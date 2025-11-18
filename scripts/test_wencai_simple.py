#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版pywencai测试脚本
不依赖配置文件，直接测试wencai连接
"""

import sys
from datetime import datetime

# Cookie常量（从配置文件复制）
WENCAI_COOKIE = "Ths_iwencai_Xuangu_mt4zcu73qjh83vi4y5pr2nybkxnoenud; ta_random_userid=wx7wznncgr; cid=baf1622e8eea6272fc9d2ce794097ea61746875841; u_ukey=A10702B8689642C6BE607730E11E6E4A; u_uver=1.0.0; u_dpass=vGdGzLxENUG6ZwHZ8OGxTLDmIKF5Rmb8llOwW2ykQE%2BOjjddJ4Q3jJx2t9d7r%2FnWHi80LrSsTFH9a%2B6rtRvqGg%3D%3D; u_did=3C009AF7CFB64A2EB8000AEAFC84637E; u_ttype=WEB; ttype=WEB; user=MDpteF9qOWIxb3JjZjQ6Ok5vbmU6NTAwOjc0MzYyNjc0MDo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoxNjo6OjczMzYyNjc0MDoxNzYzNDU2NjQ5Ojo6MTcyNzQxMzM4MDo2MDQ4MDA6MDoxNGIzMGE3OWJlZTVjNTFhNTY3MTdmYzJkODI2NDZlNWI6ZGVmYXVsdF81OjA%3D; userid=733626740; u_name=mx_j9b1orcf4; escapename=mx_j9b1orcf4; ticket=196b8d3516872396b9d61a7861207165; user_status=0; utk=e46397c25629b3cfcd6e1bfa34125d4a; sess_tk=eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6InNlc3NfdGtfMSIsImJ0eSI6InNlc3NfdGsifQ.eyJqdGkiOiI1YjZlNjQ4MjJkZmMxNzY3YTU1MTVjZWU5YmE3MzA0YjEiLCJpYXQiOjE3NjM0NTY2NDksImV4cCI6MTc2NDA2MTQ0OSwic3ViIjoiNzMzNjI2NzQwIiwiaXNzIjoidXBhc3MuaXdlbmNhaS5jb20iLCJhdWQiOiIyMDIwMTExODUyODg5MDcyIiwiYWN0Ijoib2ZjIiwiY3VocyI6ImY0MDc5ZjJmNWU4MWZiNTgxYzdkM2YwNmRmZDgxOGQ0NjAwMTZiZTUwOWNkYjUzZmM2NmYxNTcyNzMyYWU5NDIifQ.UkFAerw8xEr2LfqqGeam3Rb4rLLihUcex-GXwoGFbbiyZsv3LnPn7j7ZzdQJn8aUERlDZLuCOowpGnxZoFUhbw; cuc=80pgkax6oqk0; THSSESSID=167576bfd4ec1b26c44679b2a4; v=A5ZHNl7v431o69fZCVulVBKh50edN9a7LHUO_QDsgu8V_zj5aMcqgfwLXsXT"

def test_connection():
    """测试pywencai连接"""
    print("=" * 60)
    print("测试pywencai连接")
    print("=" * 60)

    try:
        import pywencai
        print("[OK] pywencai库已安装")
    except ImportError:
        print("[ERROR] 未安装pywencai，请先运行: pip install pywencai")
        return False

    print("\n使用Cookie进行连接测试...")
    try:
        # 使用简单的查询测试
        test_query = "非st"
        df = pywencai.get(query=test_query, cookie=WENCAI_COOKIE)

        if df is not None and not df.empty:
            print("[OK] 连接成功！")
            print(f"\n测试查询返回了 {len(df)} 条数据")
            print(f"\n数据列: {list(df.columns)}")
            return True
        else:
            print("[ERROR] 连接失败（返回空数据）")
            print("可能原因：")
            print("  1. Cookie已过期")
            print("  2. 网络连接问题")
            print("  3. 问财服务器异常")
            return False

    except Exception as e:
        print(f"[ERROR] 连接失败：{str(e)[:200]}")
        print("\n可能原因：")
        print("  1. Cookie已过期")
        print("  2. 网络连接问题")
        print("  3. pywencai版本不兼容")
        return False

def test_query():
    """测试查询功能"""
    print("\n" + "=" * 60)
    print("测试查询功能")
    print("=" * 60)

    import pywencai

    # 查询今天（或最近交易日）连续下跌8天的股票
    query_date = datetime.now()
    formatted_date = f"{query_date.year}年{query_date.month}月{query_date.day}日"

    query = f"{formatted_date}连续下跌天数>=8;非st;非退市;非新股"
    print(f"\n查询语句: {query}")

    try:
        df = pywencai.get(query=query, cookie=WENCAI_COOKIE)

        if df is None or df.empty:
            print("\n[WARN] 未找到符合条件的股票")
            return

        print(f"\n[OK] 查询成功！找到 {len(df)} 只股票")
        print(f"\n数据列: {list(df.columns)}")
        print("\n前5条数据：")
        print(df.head())

        # 转换股票代码格式
        stocks = []
        for _, row in df.iterrows():
            code = str(row.get('code', ''))
            if not code:
                continue
            if code.startswith('6'):
                suffix = 'SH'
            else:
                suffix = 'SZ'
            stocks.append(f"{code}.{suffix}")

        print(f"\n转换后的股票代码列表（共{len(stocks)}只）：")
        for i, symbol in enumerate(stocks[:20], 1):  # 显示前20个
            print(f"  {i}. {symbol}")

        if len(stocks) > 20:
            print(f"  ... 还有 {len(stocks) - 20} 只")

        # 保存到文件
        with open('wencai_test_results.txt', 'w', encoding='utf-8') as f:
            f.write(f"问财查询结果 - {query_date.strftime('%Y-%m-%d')}\n")
            f.write(f"查询条件: {query}\n")
            f.write(f"股票数量: {len(stocks)}\n\n")
            for symbol in stocks:
                f.write(f"{symbol}\n")

        print("\n[OK] 结果已保存到: wencai_test_results.txt")

    except Exception as e:
        print(f"\n[ERROR] 查询失败：{str(e)[:200]}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("pywencai集成测试脚本（简化版）")
    print("=" * 60)

    # 测试连接
    success = test_connection()

    if success:
        # 如果连接成功，执行查询测试
        test_query()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
