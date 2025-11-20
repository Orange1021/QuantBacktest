import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').parent))

from config.settings import settings

try:
    from DataManager.selectors.wencai_selector import WencaiSelector
    cookie = settings.get_env('WENCAI_COOKIE')
    selector = WencaiSelector(cookie=cookie)
    print("WencaiSelector创建成功")
    print("_wencai:", selector._wencai)
    
    # 测试连接
    result = selector.validate_connection()
    print("连接结果:", result)
    
except Exception as e:
    print("错误:", e)
    import traceback
    traceback.print_exc()