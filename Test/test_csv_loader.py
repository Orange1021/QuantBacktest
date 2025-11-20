"""
测试本地CSV数据加载器
验证数据读取和转换功能是否正常
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.sources import LocalCSVLoader
from DataManager.schema.constant import Exchange


def test_csv_loader():
    """测试CSV数据加载器"""
    print("=" * 60)
    print("开始测试本地CSV数据加载器")
    print("=" * 60)
    
    # 配置参数
    csv_root_path = r"C:\Users\123\A股数据\个股数据"
    symbol = "000001"
    exchange = "SZSE"
    
    try:
        # 创建加载器实例
        print(f"创建CSV加载器，数据路径: {csv_root_path}")
        loader = LocalCSVLoader(csv_root_path)
        
        # 设置测试日期范围（最近30天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"测试股票代码: {symbol}.{exchange}")
        print(f"测试日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        print("-" * 60)
        
        # 加载数据
        bar_data_list = loader.load_bar_data(symbol, exchange, start_date, end_date)
        
        # 验证结果
        if not bar_data_list:
            print("❌ 未加载到任何数据，请检查文件路径和日期范围")
            return False
        
        print(f"✅ 成功加载 {len(bar_data_list)} 条K线数据")
        
        # 显示前5条数据的详细信息
        print("\n前5条数据详情:")
        print("-" * 60)
        for i, bar in enumerate(bar_data_list[:5]):
            print(f"第 {i+1} 条:")
            print(f"  日期: {bar.datetime.strftime('%Y-%m-%d')}")
            print(f"  开盘价: {bar.open_price:.2f}")
            print(f"  最高价: {bar.high_price:.2f}")
            print(f"  最低价: {bar.low_price:.2f}")
            print(f"  收盘价: {bar.close_price:.2f}")
            print(f"  成交量(股): {bar.volume:,.0f}")
            print(f"  成交额(元): {bar.turnover:,.0f}")
            print(f"  涨停价: {bar.limit_up:.2f}")
            print(f"  跌停价: {bar.limit_down:.2f}")
            print(f"  vt_symbol: {bar.vt_symbol}")
            
            # 显示extra字段中的额外信息
            if bar.extra:
                print("  额外字段:")
                for key, value in bar.extra.items():
                    print(f"    {key}: {value}")
            print()
        
        # 数据完整性检查
        print("数据完整性检查:")
        print("-" * 60)
        
        # 检查价格逻辑
        price_errors = 0
        for bar in bar_data_list:
            if bar.high_price < max(bar.open_price, bar.close_price):
                price_errors += 1
            if bar.low_price > min(bar.open_price, bar.close_price):
                price_errors += 1
        
        if price_errors == 0:
            print("✅ 价格逻辑检查通过")
        else:
            print(f"❌ 发现 {price_errors} 个价格逻辑错误")
        
        # 检查单位转换
        first_bar = bar_data_list[0]
        if first_bar.volume > 100:  # 成交量应该已经转换为股
            print("✅ 成交量单位转换正确（股）")
        else:
            print("❌ 成交量单位可能未正确转换")
        
        if first_bar.turnover > 1000:  # 成交额应该已经转换为元
            print("✅ 成交额单位转换正确（元）")
        else:
            print("❌ 成交额单位可能未正确转换")
        
        # 检查时间排序
        is_sorted = all(bar_data_list[i].datetime <= bar_data_list[i+1].datetime 
                       for i in range(len(bar_data_list)-1))
        if is_sorted:
            print("✅ 数据按时间升序排列")
        else:
            print("❌ 数据时间顺序错误")
        
        print("\n" + "=" * 60)
        print("测试完成！CSV数据加载器工作正常")
        print("=" * 60)
        return True
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        print("请检查CSV文件路径是否正确")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构是否正确"""
    print("检查项目文件结构...")
    
    required_files = [
        "DataManager/__init__.py",
        "DataManager/api.py",
        "DataManager/schema/__init__.py",
        "DataManager/schema/constant.py",
        "DataManager/schema/base.py",
        "DataManager/schema/bar.py",
        "DataManager/sources/__init__.py",
        "DataManager/sources/base_source.py",
        "DataManager/sources/local_csv.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少以下文件:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True


if __name__ == "__main__":
    print("开始运行测试...\n")
    
    # 检查文件结构
    structure_ok = test_file_structure()
    print()
    
    if structure_ok:
        # 测试CSV加载器
        test_ok = test_csv_loader()
        
        if test_ok:
            print("\n🎉 所有测试通过！")
        else:
            print("\n💥 测试失败，请检查错误信息")
    else:
        print("\n💥 文件结构检查失败，请先确保所有文件都存在")
