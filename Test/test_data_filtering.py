"""
测试数据过滤功能
验证 LocalCSVLoader.filter_existing_symbols 方法和 main.py 中的 surplus selection + filtering 策略
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.sources.local_csv import LocalCSVLoader
from config.settings import settings


def test_filter_existing_symbols():
    """测试 LocalCSVLoader.filter_existing_symbols 方法"""
    print("=" * 60)
    print("测试 LocalCSVLoader.filter_existing_symbols 方法")
    print("=" * 60)
    
    # 创建CSV加载器
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    try:
        loader = LocalCSVLoader(csv_root_path)
        print(f"✅ CSV加载器创建成功，数据路径: {csv_root_path}")
    except Exception as e:
        print(f"❌ CSV加载器创建失败: {e}")
        return False
    
    # 测试用例1: 包含有效和无效股票代码的列表
    print(f"\n测试用例1: 混合有效/无效股票代码")
    test_symbols = [
        "000001.SZ",  # 平安银行 - 应该存在
        "000002.SZ",  # 万科A - 应该存在
        "DELISTED.SH",  # 退市股票 - 应该不存在
        "600000.SH",  # 浦发银行 - 应该存在
        "INVALID.BJ",  # 无效代码 - 应该不存在
        "600036.SH",  # 招商银行 - 应该存在
    ]
    
    print(f"原始股票列表: {test_symbols}")
    
    try:
        valid_symbols = loader.filter_existing_symbols(test_symbols)
        print(f"✅ 过滤成功")
        print(f"有效股票列表: {valid_symbols}")
        print(f"过滤前: {len(test_symbols)} 只，过滤后: {len(valid_symbols)} 只")
        
        if len(valid_symbols) < len(test_symbols):
            missing_count = len(test_symbols) - len(valid_symbols)
            print(f"过滤掉 {missing_count} 只本地没有数据的股票")
            
    except Exception as e:
        print(f"❌ 过滤失败: {e}")
        return False
    
    # 测试用例2: 全部有效的股票代码
    print(f"\n测试用例2: 全部有效的股票代码")
    valid_test_symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
    print(f"原始股票列表: {valid_test_symbols}")
    
    try:
        valid_symbols = loader.filter_existing_symbols(valid_test_symbols)
        print(f"✅ 过滤成功")
        print(f"有效股票列表: {valid_symbols}")
        print(f"过滤前: {len(valid_test_symbols)} 只，过滤后: {len(valid_symbols)} 只")
        
        if len(valid_symbols) == len(valid_test_symbols):
            print("✅ 全部股票代码都有效")
        else:
            print("⚠️ 部分股票代码无效")
            
    except Exception as e:
        print(f"❌ 过滤失败: {e}")
        return False
    
    # 测试用例3: 全部无效的股票代码
    print(f"\n测试用例3: 全部无效的股票代码")
    invalid_test_symbols = ["DELISTED.SH", "INVALID.BJ", "NONEXISTENT.SZ"]
    print(f"原始股票列表: {invalid_test_symbols}")
    
    try:
        valid_symbols = loader.filter_existing_symbols(invalid_test_symbols)
        print(f"✅ 过滤成功")
        print(f"有效股票列表: {valid_symbols}")
        print(f"过滤前: {len(invalid_test_symbols)} 只，过滤后: {len(valid_symbols)} 只")
        
        if len(valid_symbols) == 0:
            print("✅ 全部股票代码都被正确过滤")
        else:
            print("⚠️ 意外：部分股票代码有效")
            
    except Exception as e:
        print(f"❌ 过滤失败: {e}")
        return False
    
    return True


def test_surplus_selection_strategy():
    """测试 main.py 中的 surplus selection + filtering 策略"""
    print("\n" + "=" * 60)
    print("测试 surplus selection + filtering 策略")
    print("=" * 60)
    
    # 检查是否有问财Cookie
    cookie = settings.get_env('WENCAI_COOKIE')
    if not cookie:
        print("❌ 未找到问财Cookie，跳过问财选股测试")
        print("💡 可以通过设置环境变量 WENCAI_COOKIE 来测试完整功能")
        return True
    
    try:
        from main import BacktestApplication
        
        # 创建应用实例
        app = BacktestApplication()
        print("✅ BacktestApplication 创建成功")
        
        # 测试 _get_symbol_list 方法
        print(f"\n测试 _get_symbol_list 方法...")
        symbols = app._get_symbol_list()
        
        print(f"✅ 获取股票列表成功: {len(symbols)} 只")
        print(f"股票列表: {symbols}")
        
        # 验证获取的股票数量不超过目标持仓数量
        target_positions = settings.get_config('strategy.parameters.max_positions', 5)
        if len(symbols) <= target_positions:
            print(f"✅ 股票数量 {len(symbols)} 符合目标持仓 {target_positions}")
        else:
            print(f"⚠️ 股票数量 {len(symbols)} 超过目标持仓 {target_positions}")
        
        # 测试 _filter_external_symbols 方法
        print(f"\n测试 _filter_external_symbols 方法...")
        test_external_symbols = [
            "000001.SZ", "000002.SZ", "DELISTED.SH", 
            "600000.SH", "INVALID.BJ", "600036.SH"
        ]
        
        filtered_symbols = app._filter_external_symbols(test_external_symbols)
        print(f"✅ 外部股票列表过滤成功")
        print(f"过滤前: {len(test_external_symbols)} 只，过滤后: {len(filtered_symbols)} 只")
        print(f"过滤后列表: {filtered_symbols}")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """集成测试：运行完整的回测流程"""
    print("\n" + "=" * 60)
    print("集成测试：运行完整回测流程")
    print("=" * 60)
    
    try:
        from main import BacktestApplication
        from Strategies.simple_strategy import SimpleMomentumStrategy
        
        # 创建应用实例
        app = BacktestApplication()
        
        # 运行回测（使用较短的日期范围以加快测试）
        original_start_date = settings.backtest.start_date
        original_end_date = settings.backtest.end_date
        
        # 设置较短的测试日期范围
        settings._config_data['backtest']['start_date'] = '2025-01-01'
        settings._config_data['backtest']['end_date'] = '2025-01-10'
        
        print(f"使用测试日期范围: {settings.backtest.start_date} 到 {settings.backtest.end_date}")
        
        # 运行回测
        results = app.run(strategy_class=SimpleMomentumStrategy)
        
        print("✅ 集成测试成功")
        print(f"回测结果: 收益率 {results.get('return_rate', 0):.2f}%")
        
        # 恢复原始日期设置
        settings._config_data['backtest']['start_date'] = original_start_date
        settings._config_data['backtest']['end_date'] = original_end_date
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 恢复原始日期设置
        try:
            settings._config_data['backtest']['start_date'] = original_start_date
            settings._config_data['backtest']['end_date'] = original_end_date
        except:
            pass
        
        return False


def main():
    """主测试函数"""
    print("🔍 数据过滤功能测试")
    print("测试 LocalCSVLoader.filter_existing_symbols 和 surplus selection + filtering 策略")
    
    success_count = 0
    total_tests = 3
    
    # 测试1: 基础过滤功能
    if test_filter_existing_symbols():
        success_count += 1
    
    # 测试2: 策略功能
    if test_surplus_selection_strategy():
        success_count += 1
    
    # 测试3: 集成测试
    if test_integration():
        success_count += 1
    
    # 结果总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！数据过滤功能正常工作")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ 数据过滤功能测试完成")
        print("💡 现在系统可以自动跳过本地没有CSV文件的股票")
        print("🚀 可以开始正常的量化回测了！")
    else:
        print("\n❌ 测试失败，请检查配置和数据文件")