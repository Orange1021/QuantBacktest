"""
测试问财选股器与本地CSV数据的配合使用
流程: 问财选股 -> 获取股票列表 -> 本地CSV读取历史数据
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataManager.selectors.wencai_selector import WencaiSelector
from DataManager.sources.local_csv import LocalCSVLoader
from DataManager.schema.constant import Exchange
from config.settings import settings


def extract_symbol_from_vt_symbol(vt_symbol: str) -> str:
    """从vt_symbol中提取股票代码"""
    if '.' in vt_symbol:
        return vt_symbol.split('.')[0]
    return vt_symbol


def get_exchange_from_vt_symbol(vt_symbol: str) -> str:
    """从vt_symbol中提取交易所代码"""
    if '.' in vt_symbol:
        suffix = vt_symbol.split('.')[1]
        if suffix == 'SH':
            return 'SSE'
        elif suffix == 'SZ':
            return 'SZSE'
        elif suffix == 'BJ':
            return 'BSE'
    return 'SZSE'  # 默认


def test_wencai_csv_integration():
    """测试问财选股与本地CSV的集成"""
    print("=" * 60)
    print("问财选股器与本地CSV数据集成测试")
    print("=" * 60)
    
    # 1. 使用问财选股器获取银行股列表
    print("步骤1: 使用问财选股器获取银行股列表")
    cookie = settings.get_env('WENCAI_COOKIE')
    if not cookie:
        print("❌ 未找到问财Cookie")
        return False
    
    wencai_selector = WencaiSelector(cookie=cookie)
    
    # 获取银行股列表
    bank_stocks = wencai_selector.select_stocks(
        date=datetime.now(),
        query="银行"
    )
    
    if not bank_stocks:
        print("❌ 问财选股失败")
        return False
    
    print(f"✅ 问财选股成功，获取到 {len(bank_stocks)} 只银行股")
    print(f"   前10只: {bank_stocks[:10]}")
    
    # 2. 创建本地CSV加载器
    print(f"\n步骤2: 创建本地CSV数据加载器")
    csv_root_path = settings.get_config('data.csv_root_path')
    if not csv_root_path:
        print("❌ 未配置CSV数据路径")
        return False
    
    csv_loader = LocalCSVLoader(csv_root_path)
    print(f"✅ CSV加载器创建成功，数据路径: {csv_root_path}")
    
    # 3. 为每只银行股加载2025年1月数据
    print(f"\n步骤3: 加载银行股2025年1月的历史数据")
    
    # 设置时间范围：2025年1月
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)
    
    successful_loads = 0
    failed_loads = 0
    total_data_points = 0
    stock_data_summary = {}
    
    for vt_symbol in bank_stocks[:10]:  # 只测试前10只股票
        symbol = extract_symbol_from_vt_symbol(vt_symbol)
        exchange = get_exchange_from_vt_symbol(vt_symbol)
        
        print(f"\n  处理股票: {vt_symbol} ({symbol}.{exchange})")
        
        try:
            # 加载该股票的历史数据
            bar_data_list = csv_loader.load_bar_data(
                symbol=symbol,
                exchange=exchange,
                start_date=start_date,
                end_date=end_date
            )
            
            if bar_data_list:
                successful_loads += 1
                total_data_points += len(bar_data_list)
                
                # 统计数据概要
                first_bar = bar_data_list[0]
                last_bar = bar_data_list[-1]
                
                stock_data_summary[vt_symbol] = {
                    'data_count': len(bar_data_list),
                    'first_date': first_bar.datetime.strftime('%Y-%m-%d'),
                    'last_date': last_bar.datetime.strftime('%Y-%m-%d'),
                    'first_price': first_bar.close_price,
                    'last_price': last_bar.close_price,
                    'price_change': last_bar.close_price - first_bar.close_price,
                    'price_change_pct': ((last_bar.close_price - first_bar.close_price) / first_bar.close_price) * 100
                }
                
                print(f"    ✅ 成功加载 {len(bar_data_list)} 条数据")
                print(f"    📊 时间范围: {stock_data_summary[vt_symbol]['first_date']} 到 {stock_data_summary[vt_symbol]['last_date']}")
                print(f"    💰 价格变化: {first_bar.close_price:.2f} -> {last_bar.close_price:.2f} ({stock_data_summary[vt_symbol]['price_change_pct']:+.2f}%)")
                
            else:
                failed_loads += 1
                print(f"    ❌ 未找到数据")
                
        except Exception as e:
            failed_loads += 1
            print(f"    ❌ 加载失败: {e}")
    
    # 4. 生成汇总报告
    print(f"\n" + "=" * 60)
    print("数据加载汇总报告")
    print("=" * 60)
    
    print(f"问财选股总数: {len(bank_stocks)}")
    print(f"测试股票数量: {min(10, len(bank_stocks))}")
    print(f"成功加载数据: {successful_loads} 只")
    print(f"加载失败: {failed_loads} 只")
    print(f"总数据点数: {total_data_points}")
    
    if stock_data_summary:
        print(f"\n股票表现统计:")
        print("-" * 40)
        
        # 按涨跌幅排序
        sorted_stocks = sorted(stock_data_summary.items(), 
                             key=lambda x: x[1]['price_change_pct'], 
                             reverse=True)
        
        for vt_symbol, summary in sorted_stocks:
            change_str = f"{summary['price_change_pct']:+.2f}%"
            if summary['price_change_pct'] > 0:
                change_str = "📈" + change_str
            elif summary['price_change_pct'] < 0:
                change_str = "📉" + change_str
            else:
                change_str = "➡️" + change_str
                
            print(f"{vt_symbol:12} | {summary['data_count']:3}天 | {summary['first_price']:6.2f} -> {summary['last_price']:6.2f} | {change_str}")
        
        # 计算平均表现
        avg_change = sum(s['price_change_pct'] for s in stock_data_summary.values()) / len(stock_data_summary)
        positive_count = sum(1 for s in stock_data_summary.values() if s['price_change_pct'] > 0)
        negative_count = sum(1 for s in stock_data_summary.values() if s['price_change_pct'] < 0)
        
        print(f"\n📊 2025年1月银行股表现:")
        print(f"   平均涨跌幅: {avg_change:+.2f}%")
        print(f"   上涨股票: {positive_count} 只")
        print(f"   下跌股票: {negative_count} 只")
        print(f"   上涨比例: {positive_count/len(stock_data_summary)*100:.1f}%")
    
    # 5. 验证集成效果
    print(f"\n步骤4: 集成效果验证")
    
    if successful_loads > 0:
        print("✅ 问财选股器与本地CSV数据成功集成")
        print("✅ 可以实现: 选股 -> 获取股票列表 -> 本地历史数据分析")
        print("✅ 支持完整的量化回测数据流程")
        return True
    else:
        print("❌ 集成失败，无法加载任何股票数据")
        print("💡 建议: 检查CSV数据路径和文件是否存在")
        return False


if __name__ == "__main__":
    success = test_wencai_csv_integration()
    
    if success:
        print("\n🎉 集成测试成功！可以进行量化回测了！")
    else:
        print("\n💥 集成测试失败，请检查配置和数据文件")
