import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import json

# 读取模拟数据
df = pd.read_excel('simulated_samples.xlsx')

print("=== 模拟数据分析 ===")
print(f"数据形状: {df.shape}")
print(f"列名: {list(df.columns)}")

# 数值列统计
print("\n=== 数值列统计 ===")
numeric_cols = df.select_dtypes(include=['int64']).columns
for col in numeric_cols:
    stats = df[col].describe()
    print(f"\n{col}:")
    print(f"  均值: {stats['mean']:.2f}")
    print(f"  标准差: {stats['std']:.2f}")
    print(f"  最小值: {stats['min']}")
    print(f"  最大值: {stats['max']}")
    print(f"  中位数: {stats['50%']:.2f}")

# 分类变量分布
print("\n=== 分类变量分布 ===")
categorical_cols = ['age_group', 'gender', 'internet_access', 'education_level', 'economic_status']
for col in categorical_cols:
    print(f"\n{col} 分布:")
    value_counts = df[col].value_counts()
    for val, count in value_counts.items():
        print(f"  {val}: {count} ({count/len(df)*100:.1f}%)")

# 检查数据质量
print("\n=== 数据质量检查 ===")
print(f"缺失值统计:")
print(df.isnull().sum())

# 相关性分析
print("\n=== 数值变量相关性 ===")
correlation_matrix = df[numeric_cols].corr()
print("相关性最高的变量对:")
correlations = []
for i in range(len(numeric_cols)):
    for j in range(i+1, len(numeric_cols)):
        corr = correlation_matrix.iloc[i, j]
        correlations.append((numeric_cols[i], numeric_cols[j], abs(corr)))

correlations.sort(key=lambda x: x[2], reverse=True)
for var1, var2, corr in correlations[:10]:
    print(f"  {var1} vs {var2}: {corr:.3f}")

print("\n=== 可视化建议 ===")
print("1. 密集数据点点阵:")
print("   - 适合变量: age_group, gender, internet_access")
print("   - 可以用颜色编码不同的群体特征")
print("   - 支持条件筛选和区域高亮")

print("\n2. 箱线图与点图结合:")
print(f"   - 数值变量数量: {len(numeric_cols)}")
print("   - 适合按分类变量分组显示分布")
print("   - 可以展示中位数、异常值等统计信息")

print("\n3. 数据质量:")
if df.isnull().sum().sum() == 0:
    print("   ✓ 无缺失值，数据完整")
else:
    print(f"   ⚠ 存在缺失值，需要处理")

print(f"\n4. 样本量: {len(df)} - 适合统计分析")

# 保存分析结果
analysis_result = {
    'data_shape': df.shape,
    'numeric_columns': list(numeric_cols),
    'categorical_columns': categorical_cols,
    'correlations': correlations[:10],
    'recommendations': [
        '密集数据点点阵 - 支持条件筛选',
        '箱线图+点图 - 展示分布特征',
        '交互式仪表板 - 多维度探索'
    ]
}

with open('simulated_data_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print("\n分析结果已保存到 simulated_data_analysis.json")
