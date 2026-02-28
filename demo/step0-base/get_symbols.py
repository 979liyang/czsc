import os
import glob


cache_path = os.environ.get("czsc_research_cache", r"/Users/liyang/Desktop/npc-czsc/.stock_data/raw")

def get_symbols(name, **kwargs):
    """获取指定分组下的所有标的代码

    :param name: 分组名称，可选值：'A股主要指数', 'A股场内基金', '中证500成分股', '期货主力'
    :param kwargs:
    :return:
    """
    if name.upper() == "ALL":
        files = glob.glob(os.path.join(cache_path, 'CZSC投研数据', "*", "*.parquet"))
        print(files, '1files')
    else:
        files = glob.glob(os.path.join(cache_path, 'CZSC投研数据', name, "*.parquet"))
        print(files, '2files')
    return [os.path.basename(x).replace(".parquet", "") for x in files]

print(get_symbols("A股主要指数"))