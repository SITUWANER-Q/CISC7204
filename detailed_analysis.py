import pandas as pd
import json
import re
from collections import Counter

# 读取Excel文件
df = pd.read_excel('SC_UTI_FR_2024_Y.xls')

print("=== 完整数据集 ===")
for idx, row in df.iterrows():
    print(f"{int(row['1.'])}. {row['住户使用资讯科技情况']}")

print("\n=== 文本分析 ===")

# 分析文本模式
texts = df['住户使用资讯科技情况'].tolist()

# 提取关键词和模式
keywords = []
categories = []

for text in texts:
    # 提取统计类型
    if '统计' in text:
        categories.append('统计数据')
    if '使用' in text:
        categories.append('使用情况')
    if '住户' in text:
        categories.append('住户相关')
    if '活动' in text:
        categories.append('活动状态')
    if '职业' in text:
        categories.append('职业相关')
    if '产品' in text:
        categories.append('产品相关')
    if '电话' in text:
        categories.append('通信相关')
    if '互联网' in text:
        categories.append('互联网相关')

# 统计各类别的出现频率
category_counts = Counter(categories)

print("内容类别分布:")
for category, count in category_counts.items():
    print(f"  {category}: {count}")

# 分析数据结构模式
patterns = {
    '按年龄统计': 0,
    '按活动状态统计': 0,
    '按职业统计': 0,
    '按教育程度统计': 0,
    '产品和服务统计': 0,
    '通信工具统计': 0
}

for text in texts:
    if '年龄' in text or '学' in text:
        patterns['按年龄统计'] += 1
    if '活动状态' in text:
        patterns['按活动状态统计'] += 1
    if '职业' in text:
        patterns['按职业统计'] += 1
    if '教育' in text:
        patterns['按教育程度统计'] += 1
    if '产品' in text:
        patterns['产品和服务统计'] += 1
    if '电话' in text or '通信' in text:
        patterns['通信工具统计'] += 1

print("\n数据结构模式:")
for pattern, count in patterns.items():
    if count > 0:
        print(f"  {pattern}: {count}")

# 创建故事线分析
story_elements = {
    "title": "澳门住户资讯科技使用状况分析",
    "overview": "这份数据描述了澳门住户在不同维度上的资讯科技使用情况，包括年龄、教育程度、活动状态、职业等人口统计学特征，以及各类科技产品的使用情况。",
    "key_themes": [
        "人口统计学特征分析（年龄、教育、职业、活动状态）",
        "科技产品使用情况（电话、互联网等）",
        "住户科技素养评估"
    ],
    "data_scope": "涵盖10个主要统计维度的数据收集和分析",
    "insights": [
        "数据按年龄和教育程度进行分层分析",
        "包含活动状态和职业维度的统计",
        "覆盖通信工具和互联网使用情况"
    ]
}

# 保存详细分析结果
analysis_result = {
    "dataset_info": {
        "total_records": len(df),
        "columns": df.columns.tolist(),
        "data_range": f"{df['1.'].min()}-{df['1.'].max()}"
    },
    "content_analysis": {
        "categories": dict(category_counts),
        "patterns": {k: v for k, v in patterns.items() if v > 0}
    },
    "story_elements": story_elements
}

with open('detailed_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, indent=2, ensure_ascii=False)

print("\n详细分析结果已保存到 detailed_analysis.json")

# 为可视化准备数据
viz_data = {
    "categories": list(category_counts.keys()),
    "category_counts": list(category_counts.values()),
    "patterns": list(patterns.keys()),
    "pattern_counts": list(patterns.values()),
    "texts": texts,
    "story_title": story_elements["title"],
    "story_overview": story_elements["overview"],
    "key_themes": story_elements["key_themes"]
}

with open('viz_data.json', 'w', encoding='utf-8') as f:
    json.dump(viz_data, f, indent=2, ensure_ascii=False)

print("可视化数据已保存到 viz_data.json")
