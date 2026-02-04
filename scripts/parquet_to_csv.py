import pandas as pd
import os

# 1. 定义文件路径（当前目录下的文件）
parquet_file = "/Users/liyang/Desktop/npc-czsc/.stock_data/raw/minute_by_stock/stock_code=600000.SH/year=2023/600000.SH_2023-08.parquet"
csv_file = "/Users/liyang/Desktop/000001.SH.parquet.csv" 

# 2. 检查文件是否存在
if not os.path.exists(parquet_file):
    print(f"错误：文件 {parquet_file} 不存在！请检查当前目录：{os.getcwd()}")
    exit()

# 3. 读取 Parquet 并转换为 CSV
try:
    df = pd.read_parquet(parquet_file)
    df.to_csv(csv_file, index=False)
    print(f"✅ 转换成功：{parquet_file} → {csv_file}")
    print("\n📊 前 5 行数据预览：")
    print(df.head())
except Exception as e:
    print(f"❌ 转换失败：{e}")