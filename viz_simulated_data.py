import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import dash
from dash import html, dcc, Input, Output
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64

# 读取模拟数据
df = pd.read_excel('simulated_samples.xlsx')

# 清理列名（正确映射中文列名）
clean_columns = {}
for col in df.columns:
    if col in ['age_group', 'gender', 'internet_access', 'internet_type', 'education_level', 'economic_status', 'occupation']:
        clean_columns[col] = col
    else:
        # 映射中文列名为英文简写
        chinese_to_english = {
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
            '培训及会议': 'training_meetings'
        }
        clean_columns[col] = chinese_to_english.get(col, f'col_{len(clean_columns)}')

df = df.rename(columns=clean_columns)

# 读取分析数据（用于词云等功能）
try:
    with open('viz_data.json', 'r', encoding='utf-8') as f:
        viz_data = json.load(f)
except FileNotFoundError:
    viz_data = {'texts': ['澳门', 'ICT', '技术', '使用', '分析', '数据', '可视化']}

# 创建Dash应用
app = dash.Dash(__name__, title="Macau ICT Simulated Data Visualization")

app.layout = html.Div([
    html.H1("Macau ICT Usage - Simulated Data Analysis", style={'textAlign': 'center'}),

    # 控制面板
    html.Div([
        html.Div([
            html.Label("选择年龄组:"),
            dcc.Dropdown(
                id='age-filter',
                options=[{'label': age, 'value': age} for age in df['age_group'].unique()],
                value=None,
                multi=True,
                placeholder="选择年龄组..."
            )
        ], style={'width': '30%', 'display': 'inline-block', 'margin': '10px'}),

        html.Div([
            html.Label("选择性别:"),
            dcc.Dropdown(
                id='gender-filter',
                options=[{'label': gen, 'value': gen} for gen in df['gender'].unique()],
                value=None,
                multi=True,
                placeholder="选择性别..."
            )
        ], style={'width': '30%', 'display': 'inline-block', 'margin': '10px'}),

        html.Div([
            html.Label("选择互联网接入:"),
            dcc.Dropdown(
                id='internet-filter',
                options=[{'label': inet, 'value': inet} for inet in df['internet_access'].unique()],
                value=None,
                multi=True,
                placeholder="选择互联网接入..."
            )
        ], style={'width': '30%', 'display': 'inline-block', 'margin': '10px'})
    ]),

    # 图表容器
    html.Div([
        html.H2("1. 密集数据点点阵 - ICT设备使用情况"),
        dcc.Graph(id='scatter-plot', style={'height': '600px'})
    ]),

    html.Div([
        html.H2("2. 箱线图与点图结合 - 按年龄组和性别分析"),
        html.Div([
            html.Label("选择分析变量:"),
            dcc.Dropdown(
                id='boxplot-variable',
                options=[
                    {'label': '移动电话使用', 'value': 'mobile_phone'},
                    {'label': '电脑使用', 'value': 'computer'},
                    {'label': '平板电脑使用', 'value': 'tablet'},
                    {'label': '智能电视使用', 'value': 'smart_tv'},
                    {'label': '社交媒体使用', 'value': 'social_media'},
                    {'label': '在线购物', 'value': 'online_shopping'}
                ],
                value='mobile_phone'
            )
        ], style={'width': '50%', 'margin': '20px auto'}),
        dcc.Graph(id='box-dot-plot', style={'height': '600px'})
    ]),

    html.Div([
        html.H2("3. 相关性热力图 - ICT使用模式"),
        dcc.Graph(id='correlation-heatmap', style={'height': '600px'})
    ]),

    html.Div([
        html.H2("4. 词云分析 - 数据关键词"),
        html.Img(id='wordcloud-image', style={'width': '100%', 'height': '350px', 'objectFit': 'contain'}),
        html.P("数据关键词词云", style={'textAlign': 'center', 'marginTop': '10px', 'color': '#666'})
    ]),

    html.Div([
        html.H2("5. 雷达图分析 - 年龄组技术使用能力"),
        dcc.Graph(id='radar-chart', style={'height': '400px'})
    ]),

    html.Div([
        html.H2("6. 树状图分析 - 统计分类系统"),
        dcc.Graph(id='treemap-chart', style={'height': '500px'})
    ])
])

@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('age-filter', 'value'),
     Input('gender-filter', 'value'),
     Input('internet-filter', 'value')]
)
def update_scatter_plot(selected_ages, selected_genders, selected_internet):
    # 筛选数据
    filtered_df = df.copy()

    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]
    if selected_internet:
        filtered_df = filtered_df[filtered_df['internet_access'].isin(selected_internet)]

    if len(filtered_df) == 0:
        return go.Figure()

    # 创建密集点点阵
    fig = go.Figure()

    # 使用移动电话和电脑使用作为坐标
    color_map = {
        '3-14': 'red',
        '15-24': 'orange',
        '25-34': 'yellow',
        '35-44': 'green',
        '45-54': 'blue',
        '55-64': 'indigo',
        '65-74': 'violet',
        '>=75': 'purple'
    }

    for age_group in filtered_df['age_group'].unique():
        age_data = filtered_df[filtered_df['age_group'] == age_group]
        fig.add_trace(go.Scatter(
            x=age_data['mobile_phone'] + np.random.normal(0, 0.1, len(age_data)),  # 添加随机噪声
            y=age_data['computer'] + np.random.normal(0, 0.1, len(age_data)),
            mode='markers',
            name=f'年龄: {age_group}',
            marker=dict(
                size=8,
                color=color_map.get(age_group, 'gray'),
                opacity=0.7,
                symbol='circle' if (age_data['gender'] == 'male').any() else 'square'
            ),
            text=[f'性别: {g}, 互联网: {i}' for g, i in zip(age_data['gender'], age_data['internet_access'])],
            hovertemplate='<b>年龄组: %{fullData.name}</b><br>' +
                         '移动电话使用: %{x:.2f}<br>' +
                         '电脑使用: %{y:.2f}<br>' +
                         '%{text}<extra></extra>'
        ))

    fig.update_layout(
        title="ICT设备使用密集点阵图 (支持条件筛选)",
        xaxis_title="移动电话使用强度",
        yaxis_title="电脑使用强度",
        showlegend=True,
        hovermode='closest'
    )

    return fig

@app.callback(
    Output('box-dot-plot', 'figure'),
    [Input('boxplot-variable', 'value'),
     Input('age-filter', 'value'),
     Input('gender-filter', 'value')]
)
def update_box_dot_plot(selected_variable, selected_ages, selected_genders):
    # 筛选数据
    filtered_df = df.copy()

    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    if len(filtered_df) == 0:
        return go.Figure()

    # 创建箱线图与点图结合
    fig = make_subplots(rows=1, cols=2, subplot_titles=('按年龄组', '按性别'))

    # 按年龄组的箱线图
    age_order = ['3-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '>=75']
    age_filtered = filtered_df[filtered_df['age_group'].isin(age_order)]

    fig.add_trace(
        go.Box(
            x=age_filtered['age_group'],
            y=age_filtered[selected_variable],
            name='年龄组分布',
            marker_color='lightblue',
            boxmean=True
        ),
        row=1, col=1
    )

    # 添加散点
    for age in age_order:
        if age in age_filtered['age_group'].values:
            age_data = age_filtered[age_filtered['age_group'] == age]
            fig.add_trace(
                go.Scatter(
                    x=[age] * len(age_data),
                    y=age_data[selected_variable] + np.random.normal(0, 0.05, len(age_data)),
                    mode='markers',
                    marker=dict(size=4, color='rgba(255, 0, 0, 0.6)'),
                    showlegend=False,
                    hovertemplate=f'{age}<br>值: %{{y:.2f}}<extra></extra>'
                ),
                row=1, col=1
            )

    # 按性别的箱线图
    fig.add_trace(
        go.Box(
            x=filtered_df['gender'],
            y=filtered_df[selected_variable],
            name='性别分布',
            marker_color='lightgreen',
            boxmean=True
        ),
        row=1, col=2
    )

    # 添加散点
    for gender in filtered_df['gender'].unique():
        gender_data = filtered_df[filtered_df['gender'] == gender]
        fig.add_trace(
            go.Scatter(
                x=[gender] * len(gender_data),
                y=gender_data[selected_variable] + np.random.normal(0, 0.05, len(gender_data)),
                mode='markers',
                marker=dict(size=4, color='rgba(255, 0, 0, 0.6)'),
                showlegend=False,
                hovertemplate=f'{gender}<br>值: %{{y:.2f}}<extra></extra>'
            ),
            row=1, col=2
        )

    variable_names = {
        'mobile_phone': '移动电话使用',
        'computer': '电脑使用',
        'tablet': '平板电脑使用',
        'smart_tv': '智能电视使用',
        'social_media': '社交媒体使用',
        'online_shopping': '在线购物'
    }

    fig.update_layout(
        title=f"{variable_names.get(selected_variable, selected_variable)} - 箱线图与点图结合分析",
        showlegend=False,
        height=600
    )

    fig.update_xaxes(title_text="年龄组", row=1, col=1)
    fig.update_xaxes(title_text="性别", row=1, col=2)
    fig.update_yaxes(title_text="使用强度", row=1, col=1)
    fig.update_yaxes(title_text="使用强度", row=1, col=2)

    return fig

@app.callback(
    Output('correlation-heatmap', 'figure'),
    [Input('age-filter', 'value'),
     Input('gender-filter', 'value')]
)
def update_correlation_heatmap(selected_ages, selected_genders):
    # 筛选数据
    filtered_df = df.copy()

    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    if len(filtered_df) < 10:  # 需要足够的数据点计算相关性
        return go.Figure()

    # 选择数值列进行相关性分析
    numeric_cols = [col for col in filtered_df.columns if filtered_df[col].dtype in ['int64', 'float64']]

    # 计算相关性矩阵
    corr_matrix = filtered_df[numeric_cols].corr()

    # 创建热力图
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))

    fig.update_layout(
        title="ICT使用变量相关性热力图",
        xaxis_title="变量",
        yaxis_title="变量",
        height=600
    )

    return fig

@app.callback(
    Output('wordcloud-image', 'src'),
    [Input('age-filter', 'value'),
     Input('gender-filter', 'value')]
)
def update_wordcloud(selected_ages, selected_genders):
    # 筛选数据用于词云
    filtered_df = df.copy()

    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    # 从筛选数据中提取关键词
    keywords = []

    # 添加年龄组关键词
    for age in filtered_df['age_group'].unique():
        count = len(filtered_df[filtered_df['age_group'] == age])
        keywords.extend([age] * count)

    # 添加性别关键词
    for gender in filtered_df['gender'].unique():
        count = len(filtered_df[filtered_df['gender'] == gender])
        keywords.extend([gender] * count)

    # 添加互联网访问关键词
    for access in filtered_df['internet_access'].unique():
        count = len(filtered_df[filtered_df['internet_access'] == access])
        keywords.extend([access] * count)

    # 如果没有足够数据，使用默认文本
    if not keywords and 'texts' in viz_data:
        for text in viz_data['texts']:
            words = text.replace('按', '').replace('统计', '').replace('的', '').replace('和', '').split()
            keywords.extend(words)

    # 过滤关键词
    keyword_counts = {}
    for word in keywords:
        if len(word) >= 2:
            keyword_counts[word] = keyword_counts.get(word, 0) + 1

    # 生成词云文本
    text = ' '.join([word * count for word, count in keyword_counts.items()])

    if not text.strip():
        text = '澳门 ICT 技术 使用 分析 数据 可视化'

    # 生成词云
    try:
        wordcloud = WordCloud(
            width=400,
            height=250,
            background_color='white',
            font_path='C:/Windows/Fonts/simhei.ttf',  # 使用中文字体
            max_words=30,
            colormap='Blues',
            contour_width=0,
            contour_color='steelblue',
            prefer_horizontal=0.8
        ).generate(text)
    except:
        # 如果中文字体不可用，使用默认字体
        wordcloud = WordCloud(
            width=400,
            height=250,
            background_color='white',
            max_words=30,
            colormap='Blues',
            contour_width=0,
            contour_color='steelblue',
            prefer_horizontal=0.8
        ).generate(text)

    # 转换为base64图片
    plt.figure(figsize=(4, 2.5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return f'data:image/png;base64,{image_base64}'

@app.callback(
    Output('radar-chart', 'figure'),
    [Input('age-filter', 'value')]
)
def update_radar_chart(selected_ages):
    # 筛选数据
    filtered_df = df.copy()
    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]

    # 计算每个年龄组的ICT使用平均值
    age_groups = ['3-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '>=75']
    tech_categories = ['mobile_phone', 'laptop_computer', 'desktop_computer', 'tablet',
                      'communication_social_platforms', 'entertainment', 'information_search']

    # 计算每个年龄组的平均使用率
    radar_data = []
    for age_group in age_groups:
        if age_group in filtered_df['age_group'].values:
            age_data = filtered_df[filtered_df['age_group'] == age_group]
            values = []
            for tech in tech_categories:
                if tech in age_data.columns:
                    values.append(age_data[tech].mean())
                else:
                    values.append(0)

            # 归一化到0-1范围
            max_val = max(values) if values else 1
            if max_val > 0:
                values = [v/max_val for v in values]

            radar_data.append({
                'age_group': age_group,
                'values': values,
                'categories': ['手机', '手提电脑', '桌面电脑', '平板', '社交平台', '娱乐', '资讯搜索']
            })

    if not radar_data:
        return go.Figure()

    # 创建雷达图
    fig = go.Figure()

    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet', 'purple']
    for i, data in enumerate(radar_data):
        fig.add_trace(go.Scatterpolar(
            r=data['values'] + [data['values'][0]],  # 闭合图形
            theta=data['categories'] + [data['categories'][0]],
            fill='toself',
            name=data['age_group'],
            line_color=colors[i % len(colors)],
            fillcolor=colors[i % len(colors)],
            opacity=0.3
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="年龄组ICT技术使用能力雷达图"
    )

    return fig

@app.callback(
    Output('treemap-chart', 'figure'),
    [Input('age-filter', 'value'),
     Input('gender-filter', 'value')]
)
def update_treemap_chart(selected_ages, selected_genders):
    # 筛选数据
    filtered_df = df.copy()

    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    if len(filtered_df) == 0:
        return go.Figure()

    # 按年龄组、性别和经济状况统计
    grouped_data = filtered_df.groupby(['age_group', 'gender', 'economic_status']).size().reset_index(name='count')

    # 创建树状图
    fig = px.treemap(
        grouped_data,
        path=['age_group', 'gender', 'economic_status'],
        values='count',
        color='count',
        color_continuous_scale='Blues',
        title='人口统计分类树状图'
    )

    fig.update_layout(
        font=dict(size=12),
        margin=dict(t=50, l=25, r=25, b=25)
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
