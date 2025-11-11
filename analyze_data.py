import pandas as pd
import numpy as np

# 读取Excel文件
df = pd.read_excel('SC_UTI_FR_2024_Y.xls')

print("=== 数据基本信息 ===")
print(f"数据形状: {df.shape}")
print(f"\n列名: {df.columns.tolist()}")

print("\n=== 数据类型 ===")
print(df.dtypes)

print("\n=== 前5行数据 ===")
print(df.head())

print("\n=== 数值列统计信息 ===")
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 0:
    print(df[numeric_cols].describe())

print("\n=== 非数值列信息 ===")
non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
for col in non_numeric_cols:
    print(f"\n{col} 列:")
    print(f"唯一值数量: {df[col].nunique()}")
    print(f"前10个唯一值: {df[col].unique()[:10]}")
    print(f"缺失值数量: {df[col].isnull().sum()}")

print("\n=== 缺失值统计 ===")
print(df.isnull().sum())

# 保存数据摘要到JSON文件
import json

summary = {
    "shape": df.shape,
    "columns": df.columns.tolist(),
    "dtypes": df.dtypes.astype(str).to_dict(),
    "numeric_summary": df[numeric_cols].describe().to_dict() if len(numeric_cols) > 0 else {},
    "null_counts": df.isnull().sum().to_dict()
}

with open('data_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("\n数据摘要已保存到 data_summary.json")
