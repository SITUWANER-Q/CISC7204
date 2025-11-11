import pandas as pd
import json

# 读取模拟数据
df = pd.read_excel('simulated_samples.xlsx')

print("原始列名:")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

# 创建正确的列名映射
column_mapping = {
    'age_group': 'age_group',
    'gender': 'gender',
    'internet_access': 'internet_access',
    'internet_type': 'internet_type',
    '手机': 'mobile_phone',
    '手提电脑': 'laptop_computer',
    '桌面电脑': 'desktop_computer',
    '平板电脑': 'tablet',
    '没有个人电脑设备': 'no_personal_computer',
    '通讯/浏览社交平台': 'communication_social_platforms',
    '娱乐': 'entertainment',
    '资讯搜寻': 'information_search',
    '银行服务/移动支付': 'banking_mobile_payment',
    '网上政府服务': 'online_government_services',
    '购买商品及服务': 'purchase_goods_services',
    '分享个人创作': 'share_personal_content',
    '阅读报章、杂志及电子书': 'reading_news_magazines',
    '培训及会议': 'training_meetings',
    'education_level': 'education_level',
    'economic_status': 'economic_status',
    'occupation': 'occupation'
}

# 重命名列
df = df.rename(columns=column_mapping)

print("\n映射后的列名:")
for col in df.columns:
    print(col)

# 保存处理后的数据
df.to_csv('simulated_samples_clean.csv', index=False, encoding='utf-8')

print("\n数据已保存到 simulated_samples_clean.csv")
print(f"数据形状: {df.shape}")
print(f"数据类型:\n{df.dtypes}")