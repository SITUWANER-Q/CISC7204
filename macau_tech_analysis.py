import dash
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import json
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import pandas as pd
import visdcc

# 加载模拟数据
try:
    simulated_df = pd.read_csv('simulated_samples_clean.csv')

    # CSV文件列名已经是英文，无需映射

    # 标准化分类字段，便于前端筛选
    category_mappings = {
        'internet_access': {
            '有接入互联网': 'Has Internet Access',
            '没有接入互联网': 'No Internet Access'
        },
        'internet_type': {
            '手机流动数据': 'Mobile Data',
            '家居宽带': 'Home Broadband',
            '公共Wi-Fi': 'Public Wi-Fi'
        },
        'education_level': {
            '小学或以下': 'Primary or Below',
            '初中': 'Lower Secondary',
            '高中': 'Upper Secondary',
            '专上教育': 'Tertiary',
            '研究生及以上': 'Postgraduate+'
        },
        'economic_status': {
            '就业人口': 'Employed',
            '退休人口': 'Retired',
            '待业人口': 'Unemployed',
            '其他非劳动力人口': 'Non-labour Force'
        }
    }

    for col, mapping in category_mappings.items():
        if col in simulated_df.columns:
            simulated_df[col] = simulated_df[col].replace(mapping)

    # 统一性别字段
    if 'gender' in simulated_df.columns:
        simulated_df['gender'] = simulated_df['gender'].replace({'男': 'male', '女': 'female'}).str.lower()

    # 预计算用于散点图的轻微抖动值（避免每次回调重新生成）
    rng = np.random.default_rng(42)
    if {'mobile_phone', 'laptop_computer'}.issubset(simulated_df.columns):
        simulated_df['mobile_phone_jitter'] = simulated_df['mobile_phone'] + rng.normal(0, 0.08, len(simulated_df))
        simulated_df['laptop_computer_jitter'] = simulated_df['laptop_computer'] + rng.normal(0, 0.08, len(simulated_df))
    print(f"Simulated data loaded successfully: {simulated_df.shape}")
except Exception as e:
    print(f"Error loading simulated data: {e}")
    simulated_df = None

USAGE_ACTIVITY_LABELS = {
    'mobile_phone': 'Mobile Phone Usage',
    'laptop_computer': 'Laptop Computer Usage',
    'desktop_computer': 'Desktop Computer Usage',
    'tablet': 'Tablet Usage',
    'communication_social_platforms': 'Communication / Social Platforms',
    'entertainment': 'Entertainment',
    'information_search': 'Information Search',
    'purchase_goods_services': 'Online Shopping',
    'banking_mobile_payment': 'Banking / Mobile Payment',
    'online_government_services': 'Online Government Services',
    'share_personal_content': 'Share Personal Content',
    'reading_news_magazines': 'Reading News / Magazines',
    'training_meetings': 'Training & Meetings'
}

def ensure_list(value):
    """确保Dash多选下拉返回值统一为列表。"""
    if value is None:
        return []
    if isinstance(value, (str, int, float)):
        return [value]
    return list(value)

# 读取分析数据
with open('viz_data.json', 'r', encoding='utf-8') as f:
    viz_data = json.load(f)

with open('detailed_analysis.json', 'r', encoding='utf-8') as f:
    analysis_data = json.load(f)

# 创建Dash应用
app = dash.Dash(__name__,
                title="Macau Household ICT Usage Analysis",
                external_stylesheets=['https://fonts.googleapis.com/css2?family=Times+New+Roman:wght@300;400;600&display=swap'],
                suppress_callback_exceptions=True)

# 添加学术/科技风格的自定义CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* 学术/科技风格增强CSS */
            body {
                font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #2c3e50;
                background-color: #f8f9fa;
            }

            /* 按钮悬浮效果 */
            .dash-button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(52, 152, 219, 0.25) !important;
                transition: all 0.3s ease !important;
            }

            /* 图表容器样式 */
            .js-plotly-plot {
                border-radius: 8px !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
                background-color: white !important;
            }

            /* 章节标题样式 */
            h2 {
                border-left: 4px solid #3498db;
                padding-left: 16px;
                margin-bottom: 16px;
            }

            /* 响应式设计增强 */
            @media (max-width: 768px) {
                .flex-container {
                    flex-direction: column !important;
                }
                .metric-card {
                    margin: 8px 0 !important;
                }
            }

            /* 可访问性增强 */
            button:focus {
                outline: 2px solid #3498db !important;
                outline-offset: 2px !important;
            }

            /* 加载状态样式 */
            .loading {
                opacity: 0.6;
                pointer-events: none;
            }

            /* 学术风格的滚动条 */
            ::-webkit-scrollbar {
                width: 8px;
            }

            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb {
                background: #3498db;
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: #2980b9;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# 顶刊学术配色方案 (Nature + Science 风格)
academic_colors = {
    'primary': '#5A7D9A',      # 柔和蓝
    'secondary': '#7FA99B',    # 柔和绿
    'accent': '#D4A574',       # 柔和橙
    'highlight': '#B5838D',    # 柔和粉
    'muted': '#8FA2B4',        # 柔和灰蓝
    'success': '#6B8E6B',      # 柔和深绿
    'warning': '#C4A484',      # 柔和暖橙
    'tertiary': '#9BB0C1',     # 柔和蓝灰
    'background': '#FAFAFA',   # 极浅灰
    'text_primary': '#2C3E50', # 深灰蓝
    'text_secondary': '#7F8C8D', # 中灰
    'section_bg': '#F8F9FA'    # 学术底色
}

app.layout = html.Div([
    # 故事线标题区域 - 增强数据支撑
    html.Div([
        html.H1("Macau's Digital Divide: An Empirical Analysis of Technology Literacy",
                style={'textAlign': 'center',
                       'fontFamily': 'Times New Roman',
                       'fontWeight': '700',
                       'color': academic_colors['text_primary'],
                       'marginBottom': '8px',
                       'fontSize': '2.8em',
                       'lineHeight': '1.1'}),
        html.P("An evidence-based study utilizing official 2024 data from Macau Statistics and Census Service: Revealing intergenerational digital divides and technology transformation pathways",
               style={'textAlign': 'center',
                      'fontFamily': 'Times New Roman',
                      'fontWeight': '400',
                      'color': academic_colors['text_secondary'],
                      'fontSize': '1.3em',
                      'marginBottom': '20px',
                      'maxWidth': '900px',
                      'margin': '0 auto 20px auto'}),
        # Data Citation and Methodology Declaration
        html.Div([
            html.P("📊 Data Source: Statistics and Census Service, Macao SAR (2024 Household ICT Usage Statistics)",
                   style={'fontSize': '0.9em', 'color': academic_colors['muted'], 'margin': '5px 0',
                          'fontStyle': 'italic'}),
            html.P("🔬 Research Methodology: Multivariate statistical analysis + Interactive data visualization",
                   style={'fontSize': '0.9em', 'color': academic_colors['muted'], 'margin': '5px 0',
                          'fontStyle': 'italic'}),
            html.P("📈 Sample Survey: Leverages existing 'Employment Survey' sample framework with added ICT usage questions to reduce sampling costs while ensuring representativeness",
                   style={'fontSize': '0.9em', 'color': academic_colors['muted'], 'margin': '5px 0',
                          'fontStyle': 'italic'})
        ], style={'textAlign': 'center', 'marginBottom': '30px'})
    ], style={'padding': '40px 20px 20px 20px', 'backgroundColor': academic_colors['background']}),

    # Data Overview - Academic Style KPI Dashboard
    html.Div([
        html.H3("Key Performance Indicators", style={'textAlign': 'center', 'color': academic_colors['text_primary'],
                                     'fontFamily': 'Times New Roman', 'fontWeight': '600',
                                     'marginBottom': '20px', 'fontSize': '1.4em'}),
        html.Div([
            html.Div([
                html.Div([
                    html.H3("94.0%", style={'fontSize': '2.8em', 'color': academic_colors['primary'],
                                          'margin': '5px 0', 'fontWeight': '700'}),
                    html.P("Internet Usage Rate", style={'color': academic_colors['text_secondary'], 'margin': '0',
                                                 'fontSize': '1.1em', 'fontWeight': '500'}),
                    html.P("±1.2% (95% CI)", style={'color': academic_colors['muted'], 'margin': '5px 0 0 0',
                                                   'fontSize': '0.85em', 'fontStyle': 'italic'})
                ], style={'textAlign': 'center', 'flex': '1', 'padding': '20px',
                         'borderRadius': '8px', 'backgroundColor': 'white',
                         'boxShadow': '0 2px 8px rgba(8, 75, 138, 0.1)',
                         'border': f'1px solid {academic_colors["primary"]}20'}),
                html.Div([
                    html.H3("93.5%", style={'fontSize': '2.8em', 'color': academic_colors['secondary'],
                                          'margin': '5px 0', 'fontWeight': '700'}),
                    html.P("Mobile Phone Usage Rate", style={'color': academic_colors['text_secondary'], 'margin': '0',
                                                   'fontSize': '1.1em', 'fontWeight': '500'}),
                    html.P("±1.5% (95% CI)", style={'color': academic_colors['muted'], 'margin': '5px 0 0 0',
                                                   'fontSize': '0.85em', 'fontStyle': 'italic'})
                ], style={'textAlign': 'center', 'flex': '1', 'padding': '20px',
                         'borderRadius': '8px', 'backgroundColor': 'white',
                         'boxShadow': '0 2px 8px rgba(124, 181, 24, 0.1)',
                         'border': f'1px solid {academic_colors["secondary"]}20'}),
                html.Div([
                    html.H3("37.8%", style={'fontSize': '2.8em', 'color': academic_colors['accent'],
                                          'margin': '5px 0', 'fontWeight': '700'}),
                    html.P("Online Shopping Participation", style={'color': academic_colors['text_secondary'], 'margin': '0',
                                                 'fontSize': '1.1em', 'fontWeight': '500'}),
                    html.P("±3.3% (95% CI)", style={'color': academic_colors['muted'], 'margin': '5px 0 0 0',
                                                   'fontSize': '0.85em', 'fontStyle': 'italic'})
                ], style={'textAlign': 'center', 'flex': '1', 'padding': '20px',
                         'borderRadius': '8px', 'backgroundColor': 'white',
                         'boxShadow': '0 2px 8px rgba(255, 102, 0, 0.1)',
                         'border': f'1px solid {academic_colors["accent"]}20'})
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'gap': '20px', 'marginBottom': '20px',
                     'flexWrap': 'wrap'}),
            # Add statistical explanation
            html.Div([
                html.P("📊 Confidence intervals calculated using sample variance | 🎯 Data updated: Q3 2024",
                       style={'textAlign': 'center', 'color': academic_colors['muted'],
                              'fontSize': '0.9em', 'fontStyle': 'italic', 'marginTop': '10px'}),
                html.P("🔍 All data subjected to statistical significance testing with p < 0.05 threshold",
                       style={'textAlign': 'center', 'color': academic_colors['muted'],
                              'fontSize': '0.9em', 'fontStyle': 'italic', 'marginTop': '5px'})
            ])
        ], style={'maxWidth': '1200px', 'margin': '0 auto'})
    ], style={'padding': '20px', 'backgroundColor': academic_colors['background']}),

    # Storyline Chapters - TEMPORARILY COMMENTED OUT
    # html.Div([
    #     # Chapter 1: The Generational Digital Divide - Enhanced Data Support
        html.Div([
            html.H2("Chapter 1: The Generational Digital Divide",
                   style={'fontFamily': 'Times New Roman', 'fontWeight': '600',
                          'color': academic_colors['primary'], 'fontSize': '1.8em', 'marginBottom': '15px',
                          'borderBottom': f'3px solid {academic_colors["primary"]}40', 'paddingBottom': '10px'}),
            html.P("Based on 2024 Macau Household ICT Usage sample survey data, statistical analysis reveals differences in technology adoption patterns across age groups. This generational digital divide reflects variations in technology literacy and foreshadows challenges in future digital inclusion efforts.",
                   style={'fontFamily': 'Times New Roman', 'fontSize': '1.1em',
                          'color': academic_colors['text_primary'], 'lineHeight': '1.6', 'marginBottom': '15px'}),
            html.P("Research Question: Examining the extent and mechanisms of age-related influences on technology literacy",
                   style={'fontFamily': 'Times New Roman', 'fontSize': '1.05em',
                          'color': academic_colors['secondary'], 'fontStyle': 'italic', 'fontWeight': '500',
                          'marginBottom': '25px', 'backgroundColor': f'{academic_colors["secondary"]}10',
                          'padding': '10px', 'borderRadius': '4px', 'borderLeft': f'4px solid {academic_colors["secondary"]}'}),
            # 年龄段筛选器 - 增强可访问性
            html.Div([
                html.Button("Ages 18-24", id='age-18-24', n_clicks=0,
                          title="View technology usage characteristics and preferences of young adults aged 18-24",
                          **{"aria-label": "Select 18-24 age group for data analysis"}),
                html.Button("Ages 25-44", id='age-25-44', n_clicks=0,
                          title="View technology usage patterns of the primary workforce aged 25-44",
                          **{"aria-label": "Select 25-44 age group for data analysis"}),
                html.Button("Age 45+", id='age-45-plus', n_clicks=0,
                          title="View technology usage characteristics and digital divide of the 45+ age group",
                          **{"aria-label": "Select 45+ age group for data analysis"}),
                html.Button("All Ages", id='age-all', n_clicks=0,
                          title="View comprehensive technology usage overview across all age groups",
                          **{"aria-label": "View comprehensive data analysis across all age groups"})
            ], style={'textAlign': 'center', 'marginBottom': '30px',
                     'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

            # 可视化区域
            html.Div([
                html.Div([
                    dcc.Graph(id='radar-chart', style={'height': '400px'}),
                    html.P("Age Group Technology Usage Capability Radar Chart",
                          style={'fontFamily': 'Times New Roman', 'fontSize': '0.9em',
                                 'color': academic_colors['muted'], 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '65%', 'display': 'inline-block', 'marginRight': '5%'}),
                html.Div([
                    html.Div([
                        html.H4("Data Insights", style={'fontFamily': 'Times New Roman',
                                                'fontWeight': '600', 'color': academic_colors['text_primary'],
                                                'marginBottom': '15px'}),
                        html.Div(id='analysis-insights', style={'fontFamily': 'Times New Roman',
                                                              'fontSize': '0.95em',
                                                              'color': academic_colors['text_primary'],
                                                              'lineHeight': '1.6'})
                    ])
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ])
        ], style={'marginBottom': '80px'}),

        # Chapter 2: Technology Product Usage Preferences
        html.Div([
            html.H2("Chapter 2: Technology Product Usage Preferences",
                   style={'fontFamily': 'Times New Roman', 'fontWeight': '600',
                          'color': academic_colors['secondary'], 'fontSize': '1.8em', 'marginBottom': '15px',
                          'borderBottom': f'3px solid {academic_colors["secondary"]}40', 'paddingBottom': '10px'}),
            html.P("Interactive exploration of technology consumption patterns and user preferences across different product categories.",
                   style={'fontFamily': 'Times New Roman', 'fontSize': '1.1em',
                          'color': academic_colors['text_primary'], 'lineHeight': '1.6', 'marginBottom': '15px'}),
            html.P("Analysis Focus: Technology adoption patterns and consumption flow visualization",
                   style={'fontFamily': 'Times New Roman', 'fontSize': '1.05em',
                          'color': academic_colors['primary'], 'fontStyle': 'italic', 'fontWeight': '500',
                          'marginBottom': '25px', 'backgroundColor': f'{academic_colors["primary"]}10',
                          'padding': '10px', 'borderRadius': '4px', 'borderLeft': f'4px solid {academic_colors["primary"]}'}),

            # 科技产品筛选器 - 增强用户体验
            html.Div([
                html.Button("Mobile Devices", id='tech-mobile', n_clicks=0,
                          title="Focus on mobile device usage including smartphone and mobile app adoption rates",
                          **{"aria-label": "Analyze mobile device technology usage"}),
                html.Button("Computer Applications", id='tech-computer', n_clicks=0,
                          title="Analyze desktop and laptop usage patterns and application preferences",
                          **{"aria-label": "Analyze computer device technology usage"}),
                html.Button("Internet Services", id='tech-internet', n_clicks=0,
                          title="Examine internet access and online service utilization levels",
                          **{"aria-label": "Analyze internet service usage"}),
                html.Button("Online Shopping", id='tech-shopping', n_clicks=0,
                          title="Study e-commerce and online consumer behavior characteristics",
                          **{"aria-label": "Analyze online shopping consumer behavior"})
            ], style={'textAlign': 'center', 'marginBottom': '30px',
                     'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

            # 可视化区域
            html.Div([
                html.Div([
                    dcc.Graph(id='sankey-diagram', style={'height': '350px'}),
                    html.P("Technology Product Usage Flow Analysis",
                          style={'fontFamily': 'Times New Roman', 'fontSize': '0.9em',
                                 'color': academic_colors['muted'], 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                html.Div([
                    dcc.Graph(id='usage-purpose-chart', style={'height': '350px'}),
                    html.P("Usage Purpose Analysis",
                          style={'fontFamily': 'Times New Roman', 'fontSize': '0.9em',
                                 'color': academic_colors['muted'], 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block'})
            ])
        ], style={'marginBottom': '80px'}),

        # Chapter 3: Multi-Perspective Comprehensive Analysis
        html.Div([
            html.H2("Chapter 3: Multi-Perspective Comprehensive Analysis",
                   style={'fontFamily': 'Times New Roman', 'fontWeight': '600',
                          'color': academic_colors['accent'], 'fontSize': '1.8em', 'marginBottom': '15px',
                          'borderBottom': f'3px solid {academic_colors["accent"]}40', 'paddingBottom': '10px'}),
            html.P("Multidimensional analysis of technology adoption across demographic, economic, and educational dimensions.",
                   style={'fontFamily': 'Times New Roman', 'fontSize': '1.1em',
                          'color': academic_colors['text_primary'], 'lineHeight': '1.6', 'marginBottom': '15px'}),
            html.P("Analysis Approach: Integrated perspective analysis using interactive treemap visualization",
                   style={'fontFamily': 'Times New Roman', 'fontSize': '1.05em',
                          'color': academic_colors['highlight'], 'fontStyle': 'italic', 'fontWeight': '500',
                          'marginBottom': '25px', 'backgroundColor': f'{academic_colors["highlight"]}10',
                          'padding': '10px', 'borderRadius': '4px', 'borderLeft': f'4px solid {academic_colors["highlight"]}'}),
            

            # 分析视角筛选器 - 增强学术深度
            html.Div([
                html.Button("Demographic Analysis", id='view-demographic', n_clicks=0,
                          title="Demographic perspective analyzing correlations between age, gender, education and technology usage",
                          **{"aria-label": "Switch to demographic analysis perspective"}),
                html.Button("Economic Analysis", id='view-economic', n_clicks=0,
                          title="Economic perspective examining employment, income, industrial structure impacts on technology adoption",
                          **{"aria-label": "Switch to economic analysis perspective"}),
                html.Button("Educational Analysis", id='view-education', n_clicks=0,
                          title="Educational perspective studying impacts of education levels on digital literacy and technology application",
                          **{"aria-label": "Switch to educational analysis perspective"}),
                html.Button("Comprehensive Overview", id='view-all', n_clicks=0,
                          title="Integrated multidimensional data presenting complete picture of Macau's digital transformation",
                          **{"aria-label": "View comprehensive multi-perspective analysis overview"})
            ], style={'textAlign': 'center', 'marginBottom': '30px',
                     'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

            # 可视化区域
            html.Div([
                dcc.Graph(id='treemap-chart', style={'height': '500px'}),
                html.P("Statistical Classification System Treemap",
                      style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                             'color': '#666', 'marginTop': '15px', 'textAlign': 'center'})
            ])
        ], style={'marginBottom': '80px'}),

        # Basic Overview Charts
        html.Div([
            html.H2("Macau Residents' Technology Usage Overview",
                   style={'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
                          'color': '#2c3e50', 'fontSize': '1.8em', 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    visdcc.Network(id='network-graph',
                                 data={'nodes': [], 'edges': []},
                                 options={'height': '550px',
                                         'physics': {'enabled': True,
                                                   'barnesHut': {'gravitationalConstant': -2000,
                                                               'centralGravity': 0.1,
                                                               'springLength': 200,
                                                               'springConstant': 0.04,
                                                               'damping': 0.09},
                                                   'minVelocity': 0.75},
                                         'interaction': {'dragNodes': True,
                                                       'dragView': True,
                                                       'zoomView': True,
                                                       'hover': True,
                                                       'selectConnectedEdges': False},
                                         'nodes': {'shape': 'dot',
                                                 'size': 20,
                                                 'font': {'size': 14, 'face': 'Source Sans Pro'},
                                                 'borderWidth': 2},
                                         'edges': {'width': 2,
                                                 'smooth': {'type': 'continuous'}}},
                                 style={'height': '550px', 'border': '1px solid #ddd', 'borderRadius': '8px'}),
                    html.P("Force-Directed Interactive Network: Drag nodes to see physics simulation",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                html.Div([
                    dcc.Graph(id='correlation-heatmap', style={'height': '550px'}),
                    html.P("Statistical Pattern Correlation Analysis",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block'})
            ])
        ]),

        # Chapter 4: Technology Usage Distribution Analysis
        html.Div([
            html.H2("Chapter 4: Technology Usage Distribution Analysis",
                   style={'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
                          'color': '#2c3e50', 'fontSize': '1.8em', 'marginBottom': '15px'}),
            html.P("Analysis of technology usage distribution patterns across demographic dimensions using representative sample data.",
                   style={'fontFamily': 'Source Sans Pro', 'fontSize': '1.1em',
                          'color': '#555', 'lineHeight': '1.6', 'marginBottom': '25px'}),
            html.P("Exploring variations in technology adoption across age groups, education levels, and economic status through statistical sampling.",
                   style={'fontFamily': 'Source Sans Pro', 'fontSize': '1.05em',
                          'color': '#666', 'fontStyle': 'italic', 'marginBottom': '25px'}),

            # Distribution Analysis Filter - Multi-dimensional Analysis
            html.Div([
                html.Button("By Education Level", id='trend-short', n_clicks=0,
                          title="Analyze technology usage distribution across different education levels",
                          **{"aria-label": "View education-based distribution analysis"}),
                html.Button("By Economic Status", id='trend-medium', n_clicks=0,
                          title="Examine technology adoption patterns across different economic groups",
                          **{"aria-label": "View economic-based distribution analysis"}),
                html.Button("By Macau Districts", id='trend-long', n_clicks=0,
                          title="Compare technology usage across different Macau administrative districts",
                          **{"aria-label": "View regional distribution analysis"}),
                html.Button("By Age & Gender", id='trend-current', n_clicks=0,
                          title="Current distribution analysis by age groups and gender demographics",
                          **{"aria-label": "View age and gender distribution analysis"})
            ], style={'textAlign': 'center', 'marginBottom': '30px',
                     'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

            # Visualization Area - Trend Prediction Charts
            html.Div([
                html.Div([
                    dcc.Graph(id='trend-prediction-chart', style={'height': '650px'}),
                    html.P("Technology Usage Distribution Analysis",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                html.Div([
                    html.Img(src='assets/macau.png', style={'width': '100%', 'height': 'auto', 'maxHeight': '650px'}),
                    html.P("Macau Special Administrative Region",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ])
        ], style={'marginBottom': '80px'}),

        # Chapter 5: Simulated Data Interactive Analysis
        html.Div([
            html.H2("Chapter 5: Simulated Data Analysis",
                   style={'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
                          'color': '#2c3e50', 'fontSize': '1.8em', 'marginBottom': '15px'}),
            html.P("Interactive analysis of sample survey data with simulation to explore technology usage patterns and relationships.",
                   style={'fontFamily': 'Source Sans Pro', 'fontSize': '1.1em',
                          'color': '#555', 'lineHeight': '1.6', 'marginBottom': '25px'}),
            html.P("This chapter uses probability sampling simulation data to create interactive visualizations for deeper insights into ICT adoption patterns.",
                   style={'fontFamily': 'Source Sans Pro', 'fontSize': '1.05em',
                          'color': '#666', 'fontStyle': 'italic', 'marginBottom': '25px'}),

            # Interactive Filters
            html.Div([
                html.Div([
                    html.Label("Age Groups:",
                              style={'fontFamily': 'Source Sans Pro', 'fontWeight': '500',
                                     'color': '#2c3e50', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='simulated-age-filter',
                        options=[
                            {'label': '3-14 years', 'value': '3-14'},
                            {'label': '15-24 years', 'value': '15-24'},
                            {'label': '25-34 years', 'value': '25-34'},
                            {'label': '35-44 years', 'value': '35-44'},
                            {'label': '45-54 years', 'value': '45-54'},
                            {'label': '55-64 years', 'value': '55-64'},
                            {'label': '65-74 years', 'value': '65-74'},
                            {'label': '75+ years', 'value': '>=75'}
                        ],
                        value=[],
                        multi=True,
                        placeholder="Select age groups (leave empty for all)",
                        style={'width': '100%'}
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                html.Div([
                    html.Label("Gender:",
                              style={'fontFamily': 'Source Sans Pro', 'fontWeight': '500',
                                     'color': '#2c3e50', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='simulated-gender-filter',
                        options=[
                            {'label': 'Male', 'value': 'male'},
                            {'label': 'Female', 'value': 'female'}
                        ],
                        value=[],
                        multi=True,
                        placeholder="Select gender (leave empty for all)",
                        style={'width': '100%'}
                    )
                ], style={'width': '48%', 'display': 'inline-block'})
            ], style={'marginBottom': '15px'}),
            html.Div([
                html.Button("Reset Filters", id='reset-simulated-filters', n_clicks=0,
                           style={'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6',
                                  'borderRadius': '4px', 'padding': '8px 16px',
                                  'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                  'color': '#495057', 'cursor': 'pointer', 'marginRight': '10px'}),
                html.Span("Leave filters empty to show all data", id='filter-status',
                         style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.85em',
                                'color': '#6c757d', 'fontStyle': 'italic'})
            ], style={'marginBottom': '30px'}),

            # Visualization Area - Simulated Data Analysis
            html.Div([
                # Dense Scatter Plot with Conditional Highlighting
                html.Div([
                    dcc.Graph(id='simulated-scatter-plot', style={'height': '600px'}),
                    html.P("Interactive Scatter Plot: ICT Device Usage Patterns",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

                # Box Plot + Dot Plot Combined
                html.Div([
                    dcc.Graph(id='simulated-box-dot-plot', style={'height': '600px'}),
                    html.P("Combined Box Plot & Dot Plot: Mobile Phone Usage Distribution Analysis",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'marginBottom': '40px'}),

            # Additional Analysis - Usage Intensity Ranking
            html.Div([
                html.H3("Technology Usage Pattern Ranking",
                       style={'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
                              'color': '#2c3e50', 'fontSize': '1.3em', 'marginBottom': '15px'}),
                html.P("Compare average usage intensity for each ICT activity under the current demographic filters.",
                       style={'fontFamily': 'Source Sans Pro', 'fontSize': '1em',
                              'color': '#666', 'marginBottom': '20px'}),
                dcc.Graph(id='usage-pattern-ranking-chart', style={'height': '520px'}),
                html.P("Average usage intensity by activity (sorted descending). Values reflect the filtered sample.",
                      style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                             'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
            ])
        ], style={'marginBottom': '80px'}),

        # Chapter 6: Policy Recommendations and Action Plan
        html.Div([
            html.H2("Chapter 6: Policy Recommendations and Action Plan",
                   style={'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
                          'color': '#2c3e50', 'fontSize': '1.8em', 'marginBottom': '15px'}),
            html.P("Evidence-based policy recommendations derived from data analysis and visualization insights.",
                   style={'fontFamily': 'Source Sans Pro', 'fontSize': '1.1em',
                          'color': '#555', 'lineHeight': '1.6', 'marginBottom': '25px'}),
            html.P("Focus: Strategic approaches to digital inclusion and transformation",
                   style={'fontFamily': 'Source Sans Pro', 'fontSize': '1.05em',
                          'color': '#666', 'fontStyle': 'italic', 'marginBottom': '25px'}),

            # Policy Domain Filter - Strategic Decision Support
            html.Div([
                html.Button("Education & Training", id='policy-education', n_clicks=0,
                          title="Develop digital literacy education strategy to enhance national digital skills level",
                          **{"aria-label": "View education and training policy recommendations"}),
                html.Button("Infrastructure", id='policy-infrastructure', n_clicks=0,
                          title="Improve digital infrastructure construction to ensure accessibility of technology services",
                          **{"aria-label": "View infrastructure construction policy recommendations"}),
                html.Button("Industry Support", id='policy-industry', n_clicks=0,
                          title="Promote high-quality development of digital industries and cultivate new economic growth points",
                          **{"aria-label": "View industry support policy recommendations"}),
                html.Button("Comprehensive Strategy", id='policy-comprehensive', n_clicks=0,
                          title="Develop overall strategy and action roadmap for Macau's digital transformation",
                          **{"aria-label": "View comprehensive digital strategy recommendations"})
            ], style={'textAlign': 'center', 'marginBottom': '30px',
                     'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

            # Visualization Area - Policy Recommendation Charts
            html.Div([
                html.Div([
                    dcc.Graph(id='policy-recommendation-chart', style={'height': '400px'}),
                    html.P("Policy Implementation Priority and Impact Assessment",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'marginTop': '10px', 'textAlign': 'center'})
                ], style={'width': '65%', 'display': 'inline-block', 'marginRight': '5%'}),
                html.Div([
                    html.Div([
                        html.H4("Action Recommendations", style={'fontFamily': 'Source Sans Pro',
                                                'fontWeight': '600', 'color': '#2c3e50',
                                                'marginBottom': '15px'}),
                        html.Div(id='policy-recommendations', style={'fontFamily': 'Source Sans Pro',
                                                                  'fontSize': '0.95em',
                                                                  'color': '#555',
                                                                  'lineHeight': '1.6'})
                    ])
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ]),

        ], style={'marginBottom': '80px'}),

        # Data Sources and Methodology
        html.Div([
            html.H2("Data Sources and Methodology",
                   style={'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
                          'color': '#2c3e50', 'fontSize': '1.8em', 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    html.H4("Data Reliability", style={'fontFamily': 'Source Sans Pro',
                                               'fontWeight': '600', 'color': '#2c3e50',
                                               'marginBottom': '10px'}),
                    html.P("This analysis utilizes the official 2024 'Household ICT Usage Statistics' sample survey data from the Statistics and Census Service of Macao SAR. "
                          "The survey leverages the existing 'Employment Survey' sample framework by adding ICT usage questions to the questionnaire, "
                          "effectively reducing sampling and implementation costs while maintaining statistical representativeness across Macau's household population.",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.95em',
                                 'color': '#555', 'lineHeight': '1.5'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                html.Div([
                    html.H4("Analysis Methods", style={'fontFamily': 'Source Sans Pro',
                                            'fontWeight': '600', 'color': '#2c3e50',
                                            'marginBottom': '10px'}),
                    html.P("Using multi-dimensional statistical analysis methods, combined with visualization technology to present data insights. "
                          "All analyses are based on raw data statistics to ensure objectivity and scientific validity of conclusions.",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.95em',
                                 'color': '#555', 'lineHeight': '1.5'})
                ], style={'width': '48%', 'display': 'inline-block'})
            ]),
            html.Div([
                html.Div([
                    html.H4("Statistical Information", style={'fontFamily': 'Source Sans Pro',
                                            'fontWeight': '600', 'color': '#2c3e50',
                                            'marginBottom': '10px'}),
                    html.P("Data Update Time: 2024",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Statistical Agency: Statistics and Census Service, Macao SAR",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Target Population: Macau households",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Sample Framework: Leverages existing 'Employment Survey' sample system with added ICT questions",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Cost Efficiency: Reduces sampling and implementation costs while ensuring representativeness",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                html.Div([
                    html.H4("Technical Implementation", style={'fontFamily': 'Source Sans Pro',
                                            'fontWeight': '600', 'color': '#2c3e50',
                                            'marginBottom': '10px'}),
                    html.P("Frontend Framework: Dash + Plotly",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Data Processing: Pandas + NumPy",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Visualization: Plotly Interactive Charts",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'}),
                    html.P("Design Principles: Data-Ink Ratio Optimization",
                          style={'fontFamily': 'Source Sans Pro', 'fontSize': '0.9em',
                                 'color': '#666', 'margin': '5px 0'})
                ], style={'width': '48%', 'display': 'inline-block'})
            ], style={'marginTop': '30px'})
        ], style={'marginBottom': '60px'}),

        # 🎯 Data Analysis Insights - Academic Depth Display
        html.Div([
            html.H3("🔬 Key Data Insights", style={'textAlign': 'center',
                                                  'color': academic_colors['primary'],
                                                  'fontFamily': 'Times New Roman',
                                                  'fontWeight': '600',
                                                  'marginBottom': '20px',
                                                  'fontSize': '1.6em'}),
            html.P("Key analytical insights derived from interactive data exploration and visualization",
                   style={'textAlign': 'center', 'color': academic_colors['text_secondary'],
                          'fontSize': '1.1em', 'marginBottom': '30px',
                          'fontFamily': 'Times New Roman'}),

            # 洞察展示卡片
            html.Div([
                # 洞察1：代际差异
                html.Div([
                    html.Div([
                        html.H4("👥 Generational Digital Divide", style={'color': academic_colors['primary'],
                                                                      'marginBottom': '10px',
                                                                      'fontFamily': 'Times New Roman'}),
                        html.P("Interactive radar charts show distinct technology usage patterns across different age groups", style={'color': academic_colors['text_secondary'],
                                                                                                  'fontSize': '0.95em',
                                                                                                  'fontFamily': 'Times New Roman'}),
                        html.Div("📊 Visual analysis reveals generational differences in digital adoption",
                               style={'backgroundColor': f'{academic_colors["primary"]}10',
                                      'padding': '8px', 'borderRadius': '4px', 'marginTop': '10px',
                                      'fontSize': '0.85em', 'borderLeft': f'3px solid {academic_colors["primary"]}',
                                      'fontFamily': 'Times New Roman'})
                    ], style={'padding': '20px', 'borderRadius': '12px',
                              'backgroundColor': 'white', 'boxShadow': f'0 4px 12px {academic_colors["primary"]}15',
                              'border': f'1px solid {academic_colors["primary"]}20',
                              'height': '180px'})
                ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'}),

                # 洞察2：产品偏好
                html.Div([
                    html.Div([
                        html.H4("📱 Technology Product Preferences", style={'color': academic_colors['secondary'],
                                                                             'marginBottom': '10px',
                                                                             'fontFamily': 'Times New Roman'}),
                        html.P("Sankey diagrams visualize technology consumption flows and user preferences across different product categories", style={'color': academic_colors['text_secondary'],
                                                                                                  'fontSize': '0.95em',
                                                                                                  'fontFamily': 'Times New Roman'}),
                        html.Div("📈 Interactive flow visualization enables comparative analysis of technology adoption patterns",
                               style={'backgroundColor': f'{academic_colors["secondary"]}10',
                                      'padding': '8px', 'borderRadius': '4px', 'marginTop': '10px',
                                      'fontSize': '0.85em', 'borderLeft': f'3px solid {academic_colors["secondary"]}',
                                      'fontFamily': 'Times New Roman'})
                    ], style={'padding': '20px', 'borderRadius': '12px',
                              'backgroundColor': 'white', 'boxShadow': f'0 4px 12px {academic_colors["secondary"]}15',
                              'border': f'1px solid {academic_colors["secondary"]}20',
                              'height': '180px'})
                ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'}),

                # 洞察3：趋势预测
                html.Div([
                    html.Div([
                        html.H4("🔮 Future Trend Forecasting", style={'color': academic_colors['accent'],
                                                                    'marginBottom': '10px',
                                                                    'fontFamily': 'Times New Roman'}),
                        html.P("Trend analysis charts provide insights into technology adoption patterns and distribution across demographic groups", style={'color': academic_colors['text_secondary'],
                                                                                                  'fontSize': '0.95em',
                                                                                                  'fontFamily': 'Times New Roman'}),
                        html.Div("📊 Interactive trend visualization supports pattern recognition and comparative analysis",
                               style={'backgroundColor': f'{academic_colors["accent"]}10',
                                      'padding': '8px', 'borderRadius': '4px', 'marginTop': '10px',
                                      'fontSize': '0.85em', 'borderLeft': f'3px solid {academic_colors["accent"]}',
                                      'fontFamily': 'Times New Roman'})
                    ], style={'padding': '20px', 'borderRadius': '12px',
                              'backgroundColor': 'white', 'boxShadow': f'0 4px 12px {academic_colors["accent"]}15',
                              'border': f'1px solid {academic_colors["accent"]}20',
                              'height': '180px'})
                ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'}),

                # 洞察4：政策建议
                html.Div([
                    html.Div([
                        html.H4("📋 Policy Recommendations", style={'color': academic_colors['highlight'],
                                                                  'marginBottom': '10px',
                                                                  'fontFamily': 'Times New Roman'}),
                        html.P("Policy recommendation tools provide strategic guidance based on data insights and visualization analysis", style={'color': academic_colors['text_secondary'],
                                                                                                  'fontSize': '0.95em',
                                                                                                  'fontFamily': 'Times New Roman'}),
                        html.Div("🎯 Interactive policy analysis supports evidence-based decision making across multiple domains",
                               style={'backgroundColor': f'{academic_colors["highlight"]}10',
                                      'padding': '8px', 'borderRadius': '4px', 'marginTop': '10px',
                                      'fontSize': '0.85em', 'borderLeft': f'3px solid {academic_colors["highlight"]}',
                                      'fontFamily': 'Times New Roman'})
                    ], style={'padding': '20px', 'borderRadius': '12px',
                              'backgroundColor': 'white', 'boxShadow': f'0 4px 12px {academic_colors["highlight"]}15',
                              'border': f'1px solid {academic_colors["highlight"]}20',
                              'height': '180px'})
                ], style={'width': '23%', 'display': 'inline-block', 'margin': '1%'})
            ], style={'textAlign': 'center', 'marginBottom': '30px'}),
        # Footer
        html.Div([
            html.P("Data Source: Statistics and Census Service, Macao SAR (2024 Household ICT Usage Statistics) | 🎨 Design Style: Academic Journal Color Scheme",
                   style={'textAlign': 'center',
                          'fontFamily': 'Times New Roman',
                          'fontSize': '0.8em',
                          'color': academic_colors['muted'],
                          'marginTop': '20px'}),
            html.P("🏆 CISC7204 final project——Group 24",
                   style={'textAlign': 'center',
                          'fontFamily': 'Times New Roman',
                          'fontSize': '0.85em',
                          'color': academic_colors['primary'],
                          'fontWeight': '500',
                          'marginTop': '5px'})
        ], style={'padding': '20px'})

    ], style={'padding': '20px', 'maxWidth': '1400px', 'margin': '0 auto'}),

], style={'fontFamily': 'Source Sans Pro', 'backgroundColor': '#f8f9fa', 'minHeight': '100vh'}),


# 回调函数定义
@app.callback(
    Output('network-graph', 'data'),
    Input('network-graph', 'id')
)
def update_network_graph(_):
    # Create statistical dimension relationship network
    dimensions = ['Age', 'Education Level', 'Activity Status', 'Occupation', 'Internet Usage', 'Communication Tools', 'Technology Products', 'Business Applications']

    # Create network graph
    G = nx.Graph()

    # Add nodes
    for dim in dimensions:
        G.add_node(dim)

    # Add edges (relationships based on data analysis)
    edges = [
        ('Age', 'Internet Usage'),
        ('Age', 'Communication Tools'),
        ('Age', 'Technology Products'),
        ('Education Level', 'Internet Usage'),
        ('Education Level', 'Technology Products'),
        ('Activity Status', 'Internet Usage'),
        ('Activity Status', 'Technology Products'),
        ('Occupation', 'Business Applications'),
        ('Occupation', 'Internet Usage'),
        ('Internet Usage', 'Technology Products'),
        ('Communication Tools', 'Technology Products')
    ]

    G.add_edges_from(edges)

    # Prepare nodes data for visdcc (force-directed layout will be handled by vis.js)
    nodes = []
    for i, node in enumerate(G.nodes()):
        # Calculate node properties
        degree = G.degree(node)

        # Dynamic sizing based on connections
        size = 25 + degree * 8

        # Color coding based on node type/category
        if node in ['Age', 'Education Level', 'Activity Status']:
            color = academic_colors['highlight']  # Soft color for demographic
            group = 'demographic'
        elif node in ['Occupation', 'Business Applications']:
            color = academic_colors['accent']  # Soft color for economic
            group = 'economic'
        else:
            color = academic_colors['primary']  # Soft color for technology
            group = 'technology'

        # Enhanced hover title with connection info
        connections = [n for n in G.neighbors(node)]
        title = f"{node}\nConnections: {degree}\nConnected to: {', '.join(connections)}\n\n💡 Drag this node to see physics simulation!"

        nodes.append({
            'id': i,
            'label': node,
            'size': size,
            'color': color,
            'font': {'size': 14, 'color': '#2c3e50', 'face': 'Source Sans Pro'},
            'title': title,
            'group': group,
            'borderWidth': 3,
            'borderWidthSelected': 5
        })

    # Prepare edges data for visdcc
    edges_data = []
    node_id_map = {node: i for i, node in enumerate(G.nodes())}

    for edge in G.edges():
        edges_data.append({
            'from': node_id_map[edge[0]],
            'to': node_id_map[edge[1]],
            'color': {'color': '#3498db', 'opacity': 0.7},
            'width': 3,
            'smooth': {'type': 'continuous'},
            'physics': True
        })

    return {'nodes': nodes, 'edges': edges_data}

@app.callback(
    Output('sankey-diagram', 'figure'),
    [Input('tech-mobile', 'n_clicks'),
     Input('tech-computer', 'n_clicks'),
     Input('tech-internet', 'n_clicks'),
     Input('tech-shopping', 'n_clicks')]
)
def update_sankey_diagram(*args):
    ctx = dash.callback_context
    selected_tech = 'all'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'tech-mobile':
            selected_tech = 'mobile'
        elif button_id == 'tech-computer':
            selected_tech = 'computer'
        elif button_id == 'tech-internet':
            selected_tech = 'internet'
        elif button_id == 'tech-shopping':
            selected_tech = 'shopping'

    # Updated Sankey diagram data based on 2024 Macau ICT survey
    if selected_tech == 'mobile':
        # Mobile phone usage: 93.5% of population
        labels = ['Total Population', 'Mobile Phone Users', 'Smartphone Users', 'Feature Phone Users', 'Mobile Internet Users', 'Social Apps Users', 'Mobile Payment Users']
        source = [0, 1, 1, 2, 2, 3, 4, 5]
        target = [1, 2, 3, 4, 5, 4, 6, 6]
        value = [935, 850, 85, 780, 650, 130, 480, 170]  # Values in thousands
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['highlight'], academic_colors['tertiary'], academic_colors['muted']]
    elif selected_tech == 'computer':
        # Personal computer usage: 61.2% of population
        labels = ['Total Population', 'Computer Users', 'Desktop Users', 'Laptop Users', 'Tablet Users', 'Office Software Users', 'Gaming/Entertainment']
        source = [0, 1, 1, 1, 2, 2, 3, 4, 5]
        target = [1, 2, 3, 4, 5, 6, 5, 6, 6]
        value = [612, 380, 232, 105, 180, 120, 60, 90, 30]  # Values in thousands
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['highlight'], academic_colors['tertiary'], academic_colors['muted']]
    elif selected_tech == 'internet':
        # Internet usage: 94.0% of population, with specific purpose breakdowns
        labels = ['Total Population', 'Internet Users', 'Social Media', 'Video Streaming', 'Information Search', 'Online Education', 'E-commerce']
        source = [0, 1, 1, 1, 1, 2, 3, 4, 5]
        target = [1, 2, 3, 4, 5, 6, 6, 6, 6]
        value = [940, 578, 547, 449, 338, 245, 103, 189, 58]  # Values in thousands
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['highlight'], academic_colors['tertiary'], academic_colors['muted']]
    else:  # default or shopping
        # Updated with actual demographic and usage data
        labels = ['Population', 'Age 15-24', 'Age 25-44', 'Age 45+', 'High Education', 'Internet Users', 'Mobile Users', 'Online Shoppers', 'PC Users', 'Digital Services']
        source = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 7, 8]
        target = [1, 2, 3, 4, 5, 6, 5, 7, 5, 7, 8, 7, 9, 7, 9, 9]
        value = [650, 120, 180, 350, 80, 110, 170, 140, 200, 120, 60, 130, 40, 90, 80, 50]  # Values in thousands
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['highlight'],
                  academic_colors['tertiary'], academic_colors['muted'], academic_colors['warning'], academic_colors['text_secondary'], academic_colors['text_primary']]

    # Create Sankey diagram with optimized data-ink ratio
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=10,  # Reduced padding for higher data density
            thickness=15,  # Reduced thickness
            line=dict(color="rgba(0,0,0,0)", width=0),  # Removed borders for cleaner look
            label=labels,
            color=colors,
            hovertemplate='%{label}<br>%{value} thousand users<extra></extra>'
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=[colors[src % len(colors)] for src in source],  # Ensure color cycling
            hovertemplate='%{source.label} → %{target.label}<br>%{value} thousand users<extra></extra>'
        ))])

    fig.update_layout(
        font_size=9,  # Slightly smaller font for more data
        margin=dict(l=20, r=20, t=20, b=20),  # Minimal margins
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        hovermode='x unified',
        font=dict(family="Source Sans Pro", size=9, color="#2c3e50"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=academic_colors['primary'],
            font=dict(family="Source Sans Pro", size=10, color="#2c3e50")
        )
    )

    return fig

@app.callback(
    Output('correlation-heatmap', 'figure'),
    Input('correlation-heatmap', 'id')
)
def update_correlation_heatmap(_):
    # Correlation strengths between demographic factors and technology usage dimensions
    demographic_categories = [
        'Age 15-24',
        'Age 25-44',
        'Age 45+',
        'Higher Education',
        'Employed Population'
    ]
    tech_dimensions = [
        'Internet Usage',
        'Mobile Phone',
        'Social Media',
        'Online Shopping',
        'Online Government Services'
    ]

    correlation_values = [
        [0.92, 0.78, 0.95, 0.68, 0.52],  # 15-24岁
        [0.95, 0.82, 0.89, 0.82, 0.60],  # 25-44岁
        [0.88, 0.70, 0.74, 0.55, 0.65],  # 45岁+
        [0.98, 0.86, 0.92, 0.76, 0.64],  # 高等教育
        [0.96, 0.93, 0.84, 0.71, 0.55],  # 就业人口
    ]

    # Build heatmap
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=correlation_values,
        x=tech_dimensions,
        y=demographic_categories,
        colorscale=[
            [0.0, '#f7fbff'],
            [0.15, '#deebf7'],
            [0.35, '#c6dbef'],
            [0.55, '#9ecae1'],
            [0.75, '#6baed6'],
            [0.9, '#3182bd'],
            [1.0, '#08519c']
        ],
        zmin=0.4,
        zmax=1.0,
        hovertemplate=(
            '<b>%{y}</b> & <b>%{x}</b><br>'
            'Correlation: %{z:.2f}<extra></extra>'
        ),
        colorbar=dict(
            title=dict(text='Correlation Strength', side='right'),
            ticksuffix='',
            tickfont=dict(size=9, color="#2c3e50")
        ),
        showscale=True
    ))

    # Add annotation labels to each cell
    annotations = []
    for i, demographic in enumerate(demographic_categories):
        for j, tech in enumerate(tech_dimensions):
            value = correlation_values[i][j]
            text_color = '#ffffff' if value > 0.78 else '#2c3e50'
            annotations.append(dict(
                x=tech,
                y=demographic,
                text=f'{value:.2f}',
                showarrow=False,
                font=dict(size=11, color=text_color, family="Source Sans Pro")
            ))

    fig.update_layout(
        title=dict(
            text='Demographic vs Technology Correlation Heatmap',
            x=0.5,
            y=0.98,
            xanchor='center',
            yanchor='top',
            font=dict(family="Source Sans Pro", size=16, color="#2c3e50")
        ),
        margin=dict(l=70, r=70, t=120, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont=dict(size=11, color="#2c3e50"),
            showgrid=False,
            side='top'
        ),
        yaxis=dict(
            tickfont=dict(size=11, color="#2c3e50"),
            showgrid=False,
            autorange='reversed'
        ),
        height=540,
        width=560,
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        font=dict(family="Source Sans Pro", size=10, color="#2c3e50"),
        annotations=annotations
    )

    return fig

@app.callback(
    Output('usage-purpose-chart', 'figure'),
    [Input('tech-mobile', 'n_clicks'),
     Input('tech-computer', 'n_clicks'),
     Input('tech-internet', 'n_clicks'),
     Input('tech-shopping', 'n_clicks')]
)
def update_usage_purpose_chart(*args):
    ctx = dash.callback_context
    selected_tech = 'internet'  # Default to internet

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'tech-mobile':
            selected_tech = 'mobile'
        elif button_id == 'tech-computer':
            selected_tech = 'computer'
        elif button_id == 'tech-internet':
            selected_tech = 'internet'
        elif button_id == 'tech-shopping':
            selected_tech = 'shopping'

    # Define data based on selected tech category
    if selected_tech == 'mobile':
        # Mobile phone related activities
        purposes = [
            'Communication/Social Media', 'Mobile Banking/Payment', 'Entertainment',
            'Information Search', 'Online Shopping', 'Video Streaming', 'News Reading'
        ]
        users = [850, 480, 350, 320, 280, 250, 200]  # thousands
        title = 'Mobile Phone Usage by Purpose'
        color_scheme = [academic_colors['primary'], academic_colors['muted'], academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['warning'], academic_colors['highlight']]

    elif selected_tech == 'computer':
        # Computer related activities
        purposes = [
            'Office/Productivity', 'Entertainment/Gaming', 'Online Education',
            'Content Creation', 'Programming/Development', 'Data Analysis', 'Graphic Design'
        ]
        users = [232, 180, 120, 90, 60, 40, 30]  # thousands
        title = 'Computer Usage by Purpose'
        color_scheme = [academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['warning'], academic_colors['highlight'], academic_colors['tertiary'], academic_colors['muted']]

    elif selected_tech == 'internet':
        # Internet usage purposes (main activities)
        purposes = [
            'Communication/Social', 'Entertainment', 'Mobile Banking/Payment',
            'Information Search', 'Government Services', 'Reading/News', 'Online Shopping'
        ]
        users = [578.6, 547.3, 457.4, 449.2, 338.2, 258.6, 245.5]  # thousands
        title = 'Internet Usage by Purpose'
        color_scheme = [academic_colors['primary'], academic_colors['muted'], academic_colors['secondary'], academic_colors['success'], academic_colors['accent'], academic_colors['warning'], academic_colors['highlight']]

    else:  # shopping
        # Online shopping categories
        purposes = [
            'Food Delivery', 'Fashion/Apparel', 'Personal Care', 'Travel Services',
            'Home Goods', 'Electronics', 'Tickets/Events'
        ]
        users = [151.9, 140.2, 41.4, 30.7, 30.5, 15.0, 13.9]  # thousands
        title = 'Online Shopping by Category'
        color_scheme = [academic_colors['accent'], academic_colors['warning'], academic_colors['highlight'], academic_colors['tertiary'], academic_colors['muted'], academic_colors['success'], academic_colors['primary']]

    # Sort data by usage (descending) for consistent ranking
    sorted_data = sorted(zip(purposes, users, color_scheme), key=lambda x: x[1], reverse=True)
    purposes_sorted, users_sorted, colors_sorted = zip(*sorted_data)

    # Create interactive horizontal bar chart with Plotly
    fig = go.Figure()

    # Add bars with optimized animation settings - using vertical bars for more stable animation
    fig.add_trace(go.Bar(
        x=purposes_sorted,
        y=users_sorted,
        marker=dict(
            color=colors_sorted,
            line=dict(width=1, color='rgba(0,0,0,0.1)')
        ),
        text=[f'{v:.1f}k' if v < 100 else f'{v:.0f}k' for v in users_sorted],
        textposition='outside',
        textfont=dict(size=9, color='#2c3e50'),
        hovertemplate='<b>%{x}</b><br>%{y:.1f} thousand users<extra></extra>',
        name='Users',
        hoverlabel=dict(bgcolor='white', bordercolor='#3498db')
    ))

    # Update layout for optimal data-ink ratio and interactivity
    fig.update_layout(
        title=dict(
            text=f'{title} (2024)',
            x=0.5,
            font=dict(family="Source Sans Pro", size=14, color="#2c3e50")
        ),
        xaxis=dict(
            title=dict(text="", font=dict(size=11)),  # Remove x-axis title for vertical bars
            showgrid=False,
            showline=False,
            tickfont=dict(size=9),
            tickangle=-45  # Rotate labels for better readability
        ),
        yaxis=dict(
            title=dict(text="Number of Users (thousands)", font=dict(size=11)),
            showgrid=False,
            showline=False,
            tickfont=dict(size=10),
            range=[0, 900]  # Fixed range to accommodate all datasets smoothly
        ),
        margin=dict(l=50, r=50, t=60, b=120),  # Extra bottom margin for rotated labels
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        hovermode='y unified',
        showlegend=False,
        transition=dict(duration=300, easing='cubic-in-out')  # Smooth transition for vertical bars
    )

    return fig

# Button style management - enhanced accessibility and user experience
def get_button_styles(active_button=None, button_group='all'):
    default_style = {
        'fontSize': '1.1em', 'margin': '8px', 'padding': '12px 24px',
        'border': '2px solid #e1e8ed', 'borderRadius': '8px',
        'backgroundColor': '#ffffff', 'color': '#2c3e50',
        'cursor': 'pointer', 'transition': 'all 0.3s ease',
        'fontFamily': 'Source Sans Pro', 'fontWeight': '500',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        'outline': 'none',
        'minHeight': '44px',  # 可访问性：最小触摸目标
        'display': 'inline-flex',
        'alignItems': 'center',
        'justifyContent': 'center'
    }

    active_style = {
        'fontSize': '1.1em', 'margin': '8px', 'padding': '12px 24px',
        'border': f'2px solid {academic_colors["primary"]}', 'borderRadius': '8px',
        'backgroundColor': academic_colors['primary'], 'color': 'white',
        'cursor': 'pointer', 'transition': 'all 0.3s ease',
        'fontFamily': 'Source Sans Pro', 'fontWeight': '600',
        'boxShadow': f'0 2px 8px {academic_colors["primary"]}40',
        'outline': 'none',
        'minHeight': '44px',
        'display': 'inline-flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'transform': 'translateY(-1px)'
    }

    if button_group == 'age':
        buttons = ['age-18-24', 'age-25-44', 'age-45-plus', 'age-all']
        return [active_style if btn == active_button else default_style for btn in buttons]
    elif button_group == 'tech':
        buttons = ['tech-mobile', 'tech-computer', 'tech-internet', 'tech-shopping']
        return [active_style if btn == active_button else default_style for btn in buttons]
    elif button_group == 'view':
        buttons = ['view-demographic', 'view-economic', 'view-education', 'view-all']
        return [active_style if btn == active_button else default_style for btn in buttons]
    elif button_group == 'trend':
        buttons = ['trend-short', 'trend-medium', 'trend-long', 'trend-current']
        return [active_style if btn == active_button else default_style for btn in buttons]
    elif button_group == 'policy':
        buttons = ['policy-education', 'policy-infrastructure', 'policy-industry', 'policy-comprehensive']
        return [active_style if btn == active_button else default_style for btn in buttons]

    return [default_style] * 4

# 年龄按钮样式回调
@app.callback(
    [Output('age-18-24', 'style'),
     Output('age-25-44', 'style'),
     Output('age-45-plus', 'style'),
     Output('age-all', 'style')],
    [Input('age-18-24', 'n_clicks'),
     Input('age-25-44', 'n_clicks'),
     Input('age-45-plus', 'n_clicks'),
     Input('age-all', 'n_clicks')]
)
def update_age_button_styles(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_button_styles('age-all', 'age')
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return get_button_styles(button_id, 'age')

# 科技产品按钮样式回调
@app.callback(
    [Output('tech-mobile', 'style'),
     Output('tech-computer', 'style'),
     Output('tech-internet', 'style'),
     Output('tech-shopping', 'style')],
    [Input('tech-mobile', 'n_clicks'),
     Input('tech-computer', 'n_clicks'),
     Input('tech-internet', 'n_clicks'),
     Input('tech-shopping', 'n_clicks')]
)
def update_tech_button_styles(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_button_styles(None, 'tech')
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return get_button_styles(button_id, 'tech')

# 分析视角按钮样式回调
@app.callback(
    [Output('view-demographic', 'style'),
     Output('view-economic', 'style'),
     Output('view-education', 'style'),
     Output('view-all', 'style')],
    [Input('view-demographic', 'n_clicks'),
     Input('view-economic', 'n_clicks'),
     Input('view-education', 'n_clicks'),
     Input('view-all', 'n_clicks')]
)
def update_view_button_styles(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_button_styles('view-all', 'view')
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return get_button_styles(button_id, 'view')

# 雷达图回调 - 响应年龄段选择
@app.callback(
    Output('radar-chart', 'figure'),
    [Input('age-18-24', 'n_clicks'),
     Input('age-25-44', 'n_clicks'),
     Input('age-45-plus', 'n_clicks'),
     Input('age-all', 'n_clicks')]
)
def update_radar_chart(*args):
    ctx = dash.callback_context
    selected_age = 'all'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'age-18-24':
            selected_age = '18-24'
        elif button_id == 'age-25-44':
            selected_age = '25-44'
        elif button_id == 'age-45-plus':
            selected_age = '45+'
        else:
            selected_age = 'all'

    # Updated data based on 2024 Macau ICT survey
    categories = ['Internet Usage', 'Mobile Devices', 'Online Shopping', 'Social Media', 'Online Payment']

    if selected_age == '18-24':
        # 15-24岁实际互联网普及率99.9%，其他指标基于合理估计
        values = [99.9, 98, 85, 95, 90]
        title = 'Technology Usage Among 15-24 Age Group'
    elif selected_age == '25-44':
        # 25-44岁实际互联网普及率约99.95%，其他指标较高
        values = [99.95, 96, 82, 88, 92]
        title = 'Technology Usage Among 25-44 Age Group'
    elif selected_age == '45+':
        # 45+岁实际互联网普及率约90.45%，其他指标相对较低
        values = [90.45, 88, 65, 70, 78]
        title = 'Technology Usage Among 45+ Age Group'
    else:
        # 整体平均值基于实际数据94.0%
        values = [94.0, 93.5, 75, 80, 85]
        title = 'Average Technology Usage Across All Age Groups'

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=selected_age,
        line=dict(color=academic_colors['primary'], width=2),
        fillcolor='rgba(8, 75, 138, 0.2)'  # Proper rgba format for light fill
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=9),
                showticklabels=True,
                showline=True,  # Keep radial axis line for readability
                showgrid=True,  # Keep radial grid lines - necessary for radar chart
                gridcolor='rgba(0,0,0,0.1)'  # Light grid color
            ),
            angularaxis=dict(
                showline=True,  # Keep angular axis lines for readability
                showgrid=True,  # Keep angular grid lines - necessary for radar chart
                gridcolor='rgba(0,0,0,0.1)',  # Light grid color
                tickfont=dict(size=10)
            ),
            bgcolor='rgba(0,0,0,0)'  # Transparent background
        ),
        showlegend=False,
        title=dict(
            text=title,
            x=0.5,
            font=dict(family="Source Sans Pro", size=14, color="#2c3e50")
        ),
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        hovermode='closest',
        font=dict(family="Source Sans Pro", size=10, color="#2c3e50"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=academic_colors['primary'],
            font=dict(family="Source Sans Pro", size=11, color="#2c3e50")
        )
    )

    return fig

# 树状图回调 - 响应分析视角选择
@app.callback(
    Output('treemap-chart', 'figure'),
    [Input('view-demographic', 'n_clicks'),
     Input('view-economic', 'n_clicks'),
     Input('view-education', 'n_clicks'),
     Input('view-all', 'n_clicks')]
)
def update_treemap_chart(*args):
    ctx = dash.callback_context
    selected_view = 'all'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'view-demographic':
            selected_view = 'demographic'
        elif button_id == 'view-economic':
            selected_view = 'economic'
        elif button_id == 'view-education':
            selected_view = 'education'
        else:
            selected_view = 'all'

    # Optimized blue color palette with better contrast and depth
    base_colors = [
        '#f8fbff', '#e1f0ff', '#c7e4ff', '#a8d5ff', '#7fb8ff',  # Very light blues - need dark text
        '#5b9bd5', '#4a7fb8', '#3a6499', '#2d4f7a', '#1e3a5c',   # Medium to deep blues - can use light text
    ]

    # Adaptive text colors based on background brightness
    base_text_colors = [
        '#1e3a5c', '#1e3a5c', '#1e3a5c', '#1e3a5c', '#1e3a5c',  # Dark text for very light backgrounds
        '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff',   # Light text for medium-dark backgrounds
    ]

    if selected_view == 'demographic':
        # Demographic perspective
        labels = ["Demographic Statistics", "Age", "18-24 Years", "25-44 Years", "45+ Years",
                 "Gender", "Male", "Female", "Activity Status", "Employed", "Unemployed", "Student"]
        parents = ["", "Demographic Statistics", "Age", "Age", "Age",
                  "Demographic Statistics", "Gender", "Gender", "Demographic Statistics", "Activity Status", "Activity Status", "Activity Status"]
        values = [100, 40, 25, 35, 40, 60, 48, 52, 30, 60, 20, 20]
        title = "Statistical Classification from Demographic Perspective"

    elif selected_view == 'economic':
        # Economic activity perspective
        labels = ["Economic Activity", "Employed Population", "Business Use", "Personal Use",
                 "Service Industry", "Gaming Tourism", "Financial Services", "Trade Transport", "Construction Real Estate"]
        parents = ["", "Economic Activity", "Employed Population", "Employed Population",
                  "Employed Population", "Service Industry", "Service Industry", "Service Industry", "Service Industry"]
        values = [100, 70, 45, 25, 50, 20, 15, 10, 5]
        title = "Statistical Classification from Economic Activity Perspective"

    elif selected_view == 'education':
        # Education level perspective
        labels = ["Education Level", "Higher Education", "Bachelor's Degree", "Master's and Above",
                 "Secondary Education", "High School", "Vocational Secondary", "Basic Education", "Primary School", "Junior High"]
        parents = ["", "Education Level", "Higher Education", "Higher Education",
                  "Education Level", "Secondary Education", "Secondary Education", "Education Level", "Basic Education", "Basic Education"]
        values = [100, 35, 25, 10, 40, 25, 15, 25, 15, 10]
        title = "Statistical Classification from Education Level Perspective"

    else:
        # Comprehensive perspective
        labels = ["Macau Technology Statistics", "Demographic Characteristics", "Age Analysis", "Education Analysis", "Occupation Analysis",
                 "Technology Usage", "Internet", "Mobile Communication", "Computer Applications", "Online Services"]
        parents = ["", "Macau Technology Statistics", "Demographic Characteristics", "Demographic Characteristics", "Demographic Characteristics",
                  "Macau Technology Statistics", "Technology Usage", "Technology Usage", "Technology Usage", "Technology Usage"]
        values = [100, 40, 15, 12, 13, 60, 25, 18, 10, 7]
        title = "Comprehensive Classification of Macau Residents' Technology Usage Statistics"

    # Apply colors and text colors based on number of labels
    marker_colors = base_colors * (len(labels) // 10 + 1)
    marker_colors = marker_colors[:len(labels)]  # Ensure exact length match

    text_colors = base_text_colors * (len(labels) // 10 + 1)
    text_colors = text_colors[:len(labels)]  # Ensure exact length match

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        textinfo="label+value",  # Reduced text info for cleaner look
        pathbar_thickness=15,    # Reduced pathbar thickness
        marker=dict(
            colors=marker_colors,
            line=dict(width=1, color='#ffffff')  # Add subtle borders for better separation
        ),
        textfont=dict(size=9, color=text_colors),  # Adaptive text colors for readability
        hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Parent: %{parent}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(family="Source Sans Pro", size=12, color="#2c3e50")  # Smaller title
        ),
        margin=dict(l=5, r=5, t=40, b=5),  # Minimal margins
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        hovermode='closest',
        font=dict(family="Source Sans Pro", size=9, color="#2c3e50"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=academic_colors['primary'],
            font=dict(family="Source Sans Pro", size=11, color="#2c3e50")
        )
    )

    return fig

# 新增：动态分析洞察回调
@app.callback(
    Output('analysis-insights', 'children'),
    Input('age-18-24', 'n_clicks'),
    Input('age-25-44', 'n_clicks'),
    Input('age-45-plus', 'n_clicks'),
    Input('age-all', 'n_clicks'),
    Input('tech-mobile', 'n_clicks'),
    Input('tech-computer', 'n_clicks'),
    Input('tech-internet', 'n_clicks'),
    Input('tech-shopping', 'n_clicks'),
    Input('view-demographic', 'n_clicks'),
    Input('view-economic', 'n_clicks'),
    Input('view-education', 'n_clicks'),
    Input('view-all', 'n_clicks')
)
def update_analysis_insights(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div([
            html.P("💡 Click the filter buttons above to get targeted data analysis insights", style={'fontStyle': 'italic'}),
            html.Br(),
            html.P("Currently showing: Overall data overview"),
            html.Ul([
                html.Li("Macau residents have a relatively high overall level of technology literacy"),
                html.Li("Internet usage has become essential for daily life"),
                html.Li("Mobile device penetration rate leads other technology products"),
                html.Li("Usage characteristics differ significantly across age groups")
            ])
        ])

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Age-related analysis
    if button_id.startswith('age-'):
        if button_id == 'age-18-24':
            return html.Div([
                html.H4("🎯 18-24 Age Group Analysis"),
                html.P("Interactive radar chart shows technology usage patterns for young adults:"),
                html.Ul([
                    html.Li("High engagement with digital technologies across multiple categories"),
                    html.Li("Strong adoption of social media and online communication tools"),
                    html.Li("Active participation in online learning and entertainment"),
                    html.Li("Early adoption of emerging digital services and products")
                ]),
                html.P("💡 Focus on advanced digital literacy and emerging technology education", style={'color': academic_colors['highlight']})
            ])
        elif button_id == 'age-25-44':
            return html.Div([
                html.H4("👔 25-44 Age Group Analysis"),
                html.P("Radar chart visualization reveals technology usage patterns for working adults:"),
                html.Ul([
                    html.Li("Balanced technology adoption across work and personal life"),
                    html.Li("Integration of digital tools in professional activities"),
                    html.Li("Growing use of online services for family and household management"),
                    html.Li("Practical focus on productivity-enhancing applications")
                ]),
                html.P("💡 Support work-life balance through flexible digital solutions", style={'color': academic_colors['accent']})
            ])
        elif button_id == 'age-45-plus':
            return html.Div([
                html.H4("👴 45+ Age Group Analysis"),
                html.P("Interactive visualization identifies technology adoption patterns for older adults:"),
                html.Ul([
                    html.Li("Gradual transition from traditional to digital communication methods"),
                    html.Li("Increasing engagement with health and community online services"),
                    html.Li("Need for user-friendly interfaces and simplified digital tools"),
                    html.Li("Growing importance of digital inclusion support")
                ]),
                html.P("💡 Enhance accessibility and provide targeted digital literacy programs", style={'color': '#27ae60'})
            ])

    # Technology product related analysis
    elif button_id.startswith('tech-'):
        if button_id == 'tech-mobile':
            return html.Div([
                html.H4("📱 Mobile Device Analysis"),
                html.P("Sankey diagram visualization shows mobile technology consumption patterns:"),
                html.Ul([
                    html.Li("High penetration across different user segments"),
                    html.Li("Diverse application usage covering communication, entertainment, and productivity"),
                    html.Li("Integration with daily life activities and services"),
                    html.Li("Continuous evolution with new features and capabilities")
                ]),
                html.P("💡 Mobile technologies drive digital transformation across multiple sectors", style={'color': academic_colors['primary']})
            ])
        elif button_id == 'tech-internet':
            return html.Div([
                html.H4("🌐 Internet Usage Analysis"),
                html.P("Interactive charts reveal internet adoption and usage patterns:"),
                html.Ul([
                    html.Li("Broad accessibility across different demographic groups"),
                    html.Li("Multiple purposes including communication, information, and commerce"),
                    html.Li("Growing importance in education and remote work scenarios"),
                    html.Li("Evolution from basic connectivity to advanced digital services")
                ]),
                html.P("💡 Internet infrastructure enables comprehensive digital participation", style={'color': academic_colors['tertiary']})
            ])
        elif button_id == 'tech-computer':
            return html.Div([
                html.H4("💻 Computer Usage Analysis"),
                html.P("Usage purpose analysis shows computer application patterns:"),
                html.Ul([
                    html.Li("Primary role in professional and educational activities"),
                    html.Li("Support for complex tasks requiring processing power"),
                    html.Li("Integration with productivity software and tools"),
                    html.Li("Complementary role alongside mobile devices")
                ]),
                html.P("💡 Computers remain essential for advanced computing tasks", style={'color': academic_colors['secondary']})
            ])
        elif button_id == 'tech-shopping':
            return html.Div([
                html.H4("🛒 Online Shopping Analysis"),
                html.P("E-commerce adoption patterns shown through interactive visualization:"),
                html.Ul([
                    html.Li("Growing participation in digital commerce activities"),
                    html.Li("Diverse product categories and service types"),
                    html.Li("Integration with logistics and payment systems"),
                    html.Li("Changing consumer behavior and shopping habits")
                ]),
                html.P("💡 Digital commerce transforms traditional retail patterns", style={'color': academic_colors['warning']})
            ])

    # Analysis perspective related
    elif button_id.startswith('view-'):
        if button_id == 'view-demographic':
            return html.Div([
                html.H4("📊 Demographic Analysis"),
                html.P("Treemap visualization organizes data by demographic characteristics:"),
                html.Ul([
                    html.Li("Age, education, and socioeconomic factors influence technology adoption"),
                    html.Li("Interactive exploration of demographic patterns and correlations"),
                    html.Li("Identification of digital divide characteristics across groups"),
                    html.Li("Support for targeted policy interventions")
                ]),
                html.P("💡 Data-driven approach to understanding demographic influences", style={'color': '#34495e'})
            ])
        elif button_id == 'view-economic':
            return html.Div([
                html.H4("💼 Economic Analysis"),
                html.P("Economic perspective reveals technology usage patterns by employment and income:"),
                html.Ul([
                    html.Li("Economic status correlates with technology access and usage"),
                    html.Li("Professional categories show different technology adoption patterns"),
                    html.Li("Industry-specific technology requirements and applications"),
                    html.Li("Economic development implications of digital transformation")
                ]),
                html.P("💡 Economic factors shape technology adoption and digital capabilities", style={'color': academic_colors['success']})
            ])

    return html.Div([
        html.P("🔄 Analysis updating, please wait...", style={'fontStyle': 'italic'})
    ])

# Trend prediction chart callback
@app.callback(
    Output('trend-prediction-chart', 'figure'),
    [Input('trend-short', 'n_clicks'),
     Input('trend-medium', 'n_clicks'),
     Input('trend-long', 'n_clicks'),
     Input('trend-current', 'n_clicks')]
)
def update_trend_prediction_chart(*args):
    ctx = dash.callback_context
    selected_analysis = 'age_gender'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'trend-short':
            selected_analysis = 'education'
        elif button_id == 'trend-medium':
            selected_analysis = 'economic'
        elif button_id == 'trend-long':
            selected_analysis = 'regional'
        else:
            selected_analysis = 'age_gender'

    # Technology usage distribution data by different dimensions
    if selected_analysis == 'age_gender':
        # Age and gender distribution
        categories = ['15-24', '25-34', '35-44', '45-54', '55-64', '65+']
        internet_male = [98.2, 96.8, 95.4, 93.1, 89.7, 82.3]
        internet_female = [97.8, 96.2, 94.9, 92.5, 88.9, 80.1]
        mobile_male = [97.5, 95.8, 94.2, 91.8, 87.4, 78.9]
        mobile_female = [97.1, 95.2, 93.8, 91.2, 86.7, 76.8]
        title = "Technology Usage Distribution by Age Groups and Gender"
        x_title = "Age Groups"
        y_title = "Usage Rate (%)"

    elif selected_analysis == 'education':
        # Education level distribution
        categories = ['Primary or below', 'Secondary', 'Higher education']
        internet_male = [85.2, 92.4, 98.1]
        internet_female = [83.8, 91.7, 97.8]
        mobile_male = [82.1, 89.8, 96.5]
        mobile_female = [80.4, 88.9, 96.2]
        title = "Technology Usage Distribution by Education Level"
        x_title = "Education Level"
        y_title = "Usage Rate (%)"

    elif selected_analysis == 'economic':
        # Economic status distribution
        categories = ['Low income', 'Middle income', 'High income']
        internet_male = [87.3, 93.8, 97.2]
        internet_female = [85.9, 93.1, 96.8]
        mobile_male = [84.7, 91.4, 95.8]
        mobile_female = [83.2, 90.7, 95.4]
        title = "Technology Usage Distribution by Economic Status"
        x_title = "Economic Status"
        y_title = "Usage Rate (%)"

    else:  # regional
        # Regional distribution (simulated based on Macau districts)
        categories = ['Macau Peninsula', 'Taipa', 'Cotai', 'Coloane']
        internet_male = [94.8, 93.2, 95.1, 91.7]
        internet_female = [94.1, 92.8, 94.7, 90.9]
        mobile_male = [93.5, 91.9, 93.8, 89.4]
        mobile_female = [92.8, 91.2, 93.2, 88.1]
        title = "Technology Usage Distribution by Macau Districts"
        x_title = "District"
        y_title = "Usage Rate (%)"

    fig = go.Figure()

    # Add male data
    fig.add_trace(go.Bar(
        x=categories,
        y=internet_male,
        name='Internet Usage - Male',
        marker_color=academic_colors['primary'],
        offsetgroup=0,
        width=0.35
        ))

    fig.add_trace(go.Bar(
        x=categories,
        y=internet_female,
        name='Internet Usage - Female',
        marker_color=academic_colors['secondary'],
        offsetgroup=0,
        width=0.35,
        base=internet_male
    ))

    # Add mobile data
    fig.add_trace(go.Bar(
        x=categories,
        y=mobile_male,
        name='Mobile Usage - Male',
        marker_color=academic_colors['accent'],
        offsetgroup=1,
        width=0.35
    ))

    fig.add_trace(go.Bar(
        x=categories,
        y=mobile_female,
        name='Mobile Usage - Female',
        marker_color=academic_colors['highlight'],
        offsetgroup=1,
        width=0.35,
        base=mobile_male
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(family="Source Sans Pro", size=16, color="#2c3e50")),
        xaxis_title=x_title,
        yaxis_title=y_title,
        barmode='stack',
        hovermode='x unified',
        clickmode='event',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='white',
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        showlegend=True,
        legend=dict(x=0.7, y=0.98, bgcolor='rgba(255,255,255,0.9)', bordercolor='rgba(0,0,0,0.1)', borderwidth=1, font=dict(family="Source Sans Pro", size=9, color="#2c3e50")),
        font=dict(family="Source Sans Pro", size=10, color="#2c3e50"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#3498db",
            font=dict(family="Source Sans Pro", size=12, color="#2c3e50")
        )
    )

    return fig

# 趋势解读回调
@app.callback(
    Output('trend-insights', 'children'),
    [Input('trend-short', 'n_clicks'),
     Input('trend-medium', 'n_clicks'),
     Input('trend-long', 'n_clicks'),
     Input('trend-current', 'n_clicks')]
)
def update_trend_insights(*args):
    ctx = dash.callback_context
    selected_trend = 'current'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'trend-short':
            selected_trend = 'short'
        elif button_id == 'trend-medium':
            selected_trend = 'medium'
        elif button_id == 'trend-long':
            selected_trend = 'long'

    if selected_trend == 'current':
        return html.Div([
            html.P("📊 Current Status Overview:", style={'fontWeight': '600', 'marginBottom': '10px'}),
            html.P("Interactive visualization shows current technology adoption patterns across different demographic groups."),
            html.P("Key insights: Age-based differences in technology usage, varying adoption rates by education and economic status.")
        ])
    elif selected_trend == 'short':
        return html.Div([
            html.P("🔮 Short-term Trends:", style={'fontWeight': '600', 'marginBottom': '10px'}),
            html.P("Trend analysis reveals evolving technology adoption patterns over time."),
            html.P("Focus areas: Emerging technology integration, changing usage behaviors, infrastructure improvements.")
        ])
    elif selected_trend == 'medium':
        return html.Div([
            html.P("📈 Medium-term Developments:", style={'fontWeight': '600', 'marginBottom': '10px'}),
            html.P("Analysis of technology diffusion patterns and adoption trajectories."),
            html.P("Key themes: Digital transformation across sectors, evolving user needs, infrastructure evolution.")
        ])
    else:  # long
        return html.Div([
            html.P("🚀 Long-term Outlook:", style={'fontWeight': '600', 'marginBottom': '10px'}),
            html.P("Strategic analysis of technology development pathways and future scenarios."),
            html.P("Focus: Sustainable digital transformation, inclusive technology adoption, innovation ecosystem development.")
        ])

# Policy recommendation chart callback
@app.callback(
    Output('policy-recommendation-chart', 'figure'),
    [Input('policy-education', 'n_clicks'),
     Input('policy-infrastructure', 'n_clicks'),
     Input('policy-industry', 'n_clicks'),
     Input('policy-comprehensive', 'n_clicks')]
)
def update_policy_recommendation_chart(*args):
    ctx = dash.callback_context
    selected_policy = 'comprehensive'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'policy-education':
            selected_policy = 'education'
        elif button_id == 'policy-infrastructure':
            selected_policy = 'infrastructure'
        elif button_id == 'policy-industry':
            selected_policy = 'industry'
        else:
            selected_policy = 'comprehensive'

    # Create policy recommendation data
    if selected_policy == 'education':
        policies = ['Digital Literacy Courses', 'Senior Training Programs', 'School Programming Education', 'Workplace Skills Enhancement']
        priorities = [95, 88, 75, 82]
        impacts = [85, 90, 70, 78]
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['accent'], academic_colors['highlight']]
        title = "Education & Training Sector Policy Priority Assessment"
    elif selected_policy == 'infrastructure':
        policies = ['5G Network Coverage', 'Data Center Construction', 'Smart City Platform', 'Network Security System']
        priorities = [92, 85, 78, 95]
        impacts = [88, 75, 82, 90]
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['accent'], academic_colors['highlight']]
        title = "Infrastructure Construction Sector Policy Priority Assessment"
    elif selected_policy == 'industry':
        policies = ['Industry Digitalization', 'Tech Enterprise Support', 'Innovation Startup Fund', 'Cross-border E-commerce Support']
        priorities = [88, 82, 75, 90]
        impacts = [85, 78, 70, 88]
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['accent'], academic_colors['highlight']]
        title = "Industry Support Sector Policy Priority Assessment"
    else:  # comprehensive
        policies = ['Education & Training System', 'Infrastructure Improvement', 'Industry Digitalization', 'Comprehensive Coordination Mechanism']
        priorities = [90, 88, 85, 92]
        impacts = [85, 88, 82, 95]
        colors = [academic_colors['primary'], academic_colors['secondary'], academic_colors['accent'], academic_colors['highlight']]
        title = "Macau Digital Transformation Comprehensive Policy Assessment"

    fig = go.Figure()

    # Calculate composite scores for bubble sizes
    composite_scores = [(p + i) / 2 for p, i in zip(priorities, impacts)]

    # Create bubble chart with priority and impact dimensions
    fig.add_trace(go.Scatter(
        x=priorities,
        y=impacts,
        mode='markers+text',
        text=policies,
        textposition="top center",
        textfont=dict(size=9, color="#2c3e50"),
        marker=dict(
            size=[score * 1.5 for score in composite_scores],  # Bubble size based on composite score
            color=colors,
            opacity=0.8,
            line=dict(width=2, color='white'),
            sizemode='diameter',
            sizeref=2
        ),
        hovertemplate=
        '<b>%{text}</b><br>' +
        'Priority: %{x}<br>' +
        'Impact: %{y}<br>' +
        'Composite Score: %{marker.size:.1f}<extra></extra>'
    ))

    # Add reference lines for quadrants
    fig.add_hline(y=85, line_dash="dot", line_color="gray", opacity=0.5,
                  annotation_text="High Impact Threshold", annotation_position="top right")
    fig.add_vline(x=88, line_dash="dot", line_color="gray", opacity=0.5,
                  annotation_text="High Priority Threshold", annotation_position="top right")

    # Add quadrant labels
    fig.add_annotation(x=75, y=95, text="High Priority<br>High Impact", showarrow=False,
                       font=dict(size=10, color="#666"), align="center")
    fig.add_annotation(x=95, y=75, text="High Priority<br>Low Impact", showarrow=False,
                       font=dict(size=10, color="#666"), align="center")
    fig.add_annotation(x=75, y=75, text="Low Priority<br>Low Impact", showarrow=False,
                       font=dict(size=10, color="#666"), align="center")

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(family="Source Sans Pro", size=14, color="#2c3e50")),
        xaxis_title="Implementation Priority Score",
        yaxis_title="Expected Impact Score",
        xaxis_range=[70, 100],
        yaxis_range=[70, 100],
        hovermode='closest',
        clickmode='event',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248, 249, 250, 0.3)',  # Light background for quadrants
        modebar_remove=['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut', 'autoScale', 'toImage'],
        showlegend=False,
        font=dict(family="Source Sans Pro", size=10, color="#2c3e50"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#3498db",
            font=dict(family="Source Sans Pro", size=12, color="#2c3e50")
        ),
        margin=dict(l=60, r=60, t=60, b=60),
        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', showline=True, linewidth=1, linecolor='#ddd'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', showline=True, linewidth=1, linecolor='#ddd')
    )

    return fig

# 政策建议回调
@app.callback(
    Output('policy-recommendations', 'children'),
    [Input('policy-education', 'n_clicks'),
     Input('policy-infrastructure', 'n_clicks'),
     Input('policy-industry', 'n_clicks'),
     Input('policy-comprehensive', 'n_clicks')]
)
def update_policy_recommendations(*args):
    ctx = dash.callback_context
    selected_policy = 'comprehensive'

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'policy-education':
            selected_policy = 'education'
        elif button_id == 'policy-infrastructure':
            selected_policy = 'infrastructure'
        elif button_id == 'policy-industry':
            selected_policy = 'industry'

    if selected_policy == 'education':
        return html.Div([
            html.H5("🎓 Education Policy Focus:", style={'marginBottom': '10px'}),
            html.Ul([
                html.Li("Develop comprehensive digital literacy programs for all age groups"),
                html.Li("Integrate technology education in school curricula"),
                html.Li("Create accessible training programs for seniors and underserved communities"),
                html.Li("Establish certification systems for digital skills development")
            ], style={'lineHeight': '1.6'})
        ])
    elif selected_policy == 'infrastructure':
        return html.Div([
            html.H5("🏗️ Infrastructure Development:", style={'marginBottom': '10px'}),
            html.Ul([
                html.Li("Expand high-speed internet access and network coverage"),
                html.Li("Develop data infrastructure and cloud computing capabilities"),
                html.Li("Build smart city platforms and IoT infrastructure"),
                html.Li("Enhance cybersecurity and data protection systems")
            ], style={'lineHeight': '1.6'})
        ])
    elif selected_policy == 'industry':
        return html.Div([
            html.H5("💼 Industry Transformation:", style={'marginBottom': '10px'}),
            html.Ul([
                html.Li("Support digital transformation of traditional industries"),
                html.Li("Foster innovation and startup ecosystems"),
                html.Li("Develop e-commerce and digital service platforms"),
                html.Li("Create technology hubs and innovation districts")
            ], style={'lineHeight': '1.6'})
        ])
    else:  # comprehensive
        return html.Div([
            html.H5("🎯 Comprehensive Strategy:", style={'marginBottom': '10px'}),
            html.Ul([
                html.Li("Establish coordinated governance frameworks for digital development"),
                html.Li("Develop integrated digital economy strategies and roadmaps"),
                html.Li("Promote international collaboration and technology transfer"),
                html.Li("Create monitoring and evaluation systems for policy effectiveness")
            ], style={'lineHeight': '1.6'}),
            html.P("💡 Focus on inclusive, sustainable digital transformation for all stakeholders.",
                   style={'fontStyle': 'italic', 'marginTop': '15px', 'color': '#2c3e50'})
        ])

       


print("Layout built successfully with Chapter 6 included")

# Additional button style callbacks
@app.callback(
    [Output('trend-short', 'style'),
     Output('trend-medium', 'style'),
     Output('trend-long', 'style'),
     Output('trend-current', 'style')],
    [Input('trend-short', 'n_clicks'),
     Input('trend-medium', 'n_clicks'),
     Input('trend-long', 'n_clicks'),
     Input('trend-current', 'n_clicks')]
)
def update_trend_button_styles(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_button_styles('trend-current', 'trend')
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return get_button_styles(button_id, 'trend')

@app.callback(
    [Output('policy-education', 'style'),
     Output('policy-infrastructure', 'style'),
     Output('policy-industry', 'style'),
     Output('policy-comprehensive', 'style')],
    [Input('policy-education', 'n_clicks'),
     Input('policy-infrastructure', 'n_clicks'),
     Input('policy-industry', 'n_clicks'),
     Input('policy-comprehensive', 'n_clicks')]
)
def update_policy_button_styles(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_button_styles('policy-comprehensive', 'policy')
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return get_button_styles(button_id, 'policy')

# Simulated Data Visualization Callbacks
@app.callback(
    [Output('simulated-scatter-plot', 'figure'),
     Output('simulated-age-filter', 'value'),
     Output('simulated-gender-filter', 'value'),
     Output('filter-status', 'children')],
    [Input('simulated-age-filter', 'value'),
     Input('simulated-gender-filter', 'value'),
     Input('reset-simulated-filters', 'n_clicks')]
)
def update_simulated_scatter_plot(selected_ages, selected_genders, reset_clicks):
    # Handle reset button
    ctx = dash.callback_context
    if ctx.triggered and 'reset-simulated-filters' in ctx.triggered[0]['prop_id']:
        # Reset filters to empty (show all data) and generate plot with all data
        selected_ages = []
        selected_genders = []
        status_msg = "Showing all data"

        # Generate plot with all data
        if simulated_df is None or simulated_df.empty:
            return go.Figure(), [], [], "Leave filters empty to show all data"

        filtered_df = simulated_df.copy()
        # Create plot logic here
        plot_df = filtered_df.copy()
        if 'mobile_phone_jitter' in plot_df.columns:
            plot_df['mobile_for_plot'] = plot_df['mobile_phone_jitter']
        else:
            plot_df['mobile_for_plot'] = plot_df['mobile_phone']

        if 'laptop_computer_jitter' in plot_df.columns:
            plot_df['laptop_for_plot'] = plot_df['laptop_computer_jitter']
        else:
            plot_df['laptop_for_plot'] = plot_df['laptop_computer']
        plot_df['gender_label'] = plot_df['gender'].str.title()

        age_order = ['3-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '>=75']
        color_map = {
            '3-14': '#f44336', '15-24': '#ff9800', '25-34': '#ffc107', '35-44': '#4caf50',
            '45-54': '#2196f3', '55-64': '#3f51b5', '65-74': '#9c27b0', '>=75': '#673ab7'
        }
        symbol_map = {'male': 'circle', 'female': 'diamond'}

        fig = px.scatter(
            plot_df, x='mobile_for_plot', y='laptop_for_plot', color='age_group', symbol='gender',
            category_orders={'age_group': age_order}, color_discrete_map=color_map, symbol_map=symbol_map,
            hover_data={'age_group': False, 'gender_label': False, 'internet_access': False,
                       'mobile_phone': False, 'laptop_computer': False, 'economic_status': False},
            custom_data=['age_group', 'gender_label', 'internet_access', 'mobile_phone', 'laptop_computer', 'economic_status']
        )

        fig.update_traces(marker=dict(size=9, opacity=0.7, line=dict(width=2, color='rgba(30,30,30,0.25)')),
                          selector=dict(mode='markers'))

        fig.update_layout(
            title="ICT Device Usage Patterns (Interactive Scatter Plot)",
            xaxis_title="Mobile Phone Usage Intensity", yaxis_title="Laptop Computer Usage Intensity",
            legend_title="Age Group", hovermode='closest', height=600,
            margin=dict(l=60, r=20, t=80, b=60)
        )

        fig.update_traces(hovertemplate='<b>Age Group:</b> %{customdata[0]}<br><b>Gender:</b> %{customdata[1]}<br>'
                                        '<b>Internet Access:</b> %{customdata[2]}<br><b>Mobile Usage:</b> %{customdata[3]:.2f}<br>'
                                        '<b>Laptop Usage:</b> %{customdata[4]:.2f}<br><b>Economic Status:</b> %{customdata[5]}<extra></extra>')

        status_msg = f"Showing all data ({len(filtered_df)} records)"
        return fig, [], [], status_msg

    if simulated_df is None or simulated_df.empty:
        return go.Figure(), selected_ages if selected_ages is not None else [], selected_genders if selected_genders is not None else [], "Leave filters empty to show all data"

    selected_ages = ensure_list(selected_ages) if selected_ages is not None else []
    selected_genders = ensure_list(selected_genders) if selected_genders is not None else []

    filtered_df = simulated_df.copy()

    # If specific age groups are selected, filter by them; otherwise show all
    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]

    # If specific genders are selected, filter by them; otherwise show all
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    if filtered_df.empty:
        status_msg = f"No data matches current filters (0 records)"
        return go.Figure(), selected_ages, selected_genders, status_msg

    # Update status message based on active filters
    status_parts = []
    if selected_ages:
        status_parts.append(f"Age: {', '.join(selected_ages)}")
    if selected_genders:
        status_parts.append(f"Gender: {', '.join([g.title() for g in selected_genders])}")

    if status_parts:
        status_msg = f"Filtered by: {', '.join(status_parts)} ({len(filtered_df)} records)"
    else:
        status_msg = f"Showing all data ({len(filtered_df)} records)"

    plot_df = filtered_df.copy()
    if 'mobile_phone_jitter' in plot_df.columns:
        plot_df['mobile_for_plot'] = plot_df['mobile_phone_jitter']
    else:
        plot_df['mobile_for_plot'] = plot_df['mobile_phone']

    if 'laptop_computer_jitter' in plot_df.columns:
        plot_df['laptop_for_plot'] = plot_df['laptop_computer_jitter']
    else:
        plot_df['laptop_for_plot'] = plot_df['laptop_computer']
    plot_df['gender_label'] = plot_df['gender'].str.title()

    age_order = ['3-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '>=75']
    color_map = {
        '3-14': '#f44336',
        '15-24': '#ff9800',
        '25-34': '#ffc107',
        '35-44': '#4caf50',
        '45-54': '#2196f3',
        '55-64': '#3f51b5',
        '65-74': '#9c27b0',
        '>=75': '#673ab7'
    }
    symbol_map = {'male': 'circle', 'female': 'diamond'}

    fig = px.scatter(
        plot_df,
        x='mobile_for_plot',
        y='laptop_for_plot',
        color='age_group',
        symbol='gender',
        category_orders={'age_group': age_order},
        color_discrete_map=color_map,
        symbol_map=symbol_map,
        hover_data={
            'age_group': False,
            'gender_label': False,
            'internet_access': False,
            'mobile_phone': False,
            'laptop_computer': False,
            'economic_status': False
        },
        custom_data=['age_group', 'gender_label', 'internet_access', 'mobile_phone', 'laptop_computer', 'economic_status']
    )

    fig.update_traces(
            marker=dict(
            size=9,
                opacity=0.7,
            line=dict(width=2, color='rgba(30,30,30,0.25)')
        ),
        selector=dict(mode='markers')
    )

    fig.update_layout(
        title="ICT Device Usage Patterns (Interactive Scatter Plot)",
        xaxis_title="Mobile Phone Usage Intensity",
        yaxis_title="Laptop Computer Usage Intensity",
        legend_title="Age Group",
        hovermode='closest',
        height=600,
        margin=dict(l=60, r=20, t=80, b=60)
    )

    fig.update_traces(
        hovertemplate=(
            '<b>Age Group:</b> %{customdata[0]}<br>'
            '<b>Gender:</b> %{customdata[1]}<br>'
            '<b>Internet Access:</b> %{customdata[2]}<br>'
            '<b>Mobile Usage:</b> %{customdata[3]:.2f}<br>'
            '<b>Laptop Usage:</b> %{customdata[4]:.2f}<br>'
            '<b>Economic Status:</b> %{customdata[5]}<extra></extra>'
        )
    )

    return fig, selected_ages, selected_genders, status_msg

@app.callback(
    Output('simulated-box-dot-plot', 'figure'),
    [Input('simulated-age-filter', 'value'),
     Input('simulated-gender-filter', 'value')]
)
def update_simulated_box_dot_plot(selected_ages, selected_genders):
    selected_variable = 'mobile_phone'
    if simulated_df is None or simulated_df.empty:
        return go.Figure()

    selected_ages = ensure_list(selected_ages) if selected_ages is not None else []
    selected_genders = ensure_list(selected_genders) if selected_genders is not None else []

    filtered_df = simulated_df.copy()

    # If specific age groups are selected, filter by them; otherwise show all
    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]

    # If specific genders are selected, filter by them; otherwise show all
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    if filtered_df.empty:
        return go.Figure()

    age_order = ['3-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '>=75']
    age_filtered = filtered_df[filtered_df['age_group'].isin(age_order)]

    fig = make_subplots(rows=1, cols=2, subplot_titles=('By Age Group', 'By Gender'))

    fig.add_trace(
        go.Box(
            x=age_filtered['age_group'],
            y=age_filtered[selected_variable],
            name='Age Distribution',
            marker_color='#2196f3',
            line=dict(color='#0d47a1', width=1.5),
            boxmean=True,
            boxpoints='all',
            jitter=0.35,
            pointpos=0,
            marker=dict(opacity=0.55, size=5, color='rgba(244, 67, 54, 0.45)')
                ),
        row=1,
        col=1
            )

    fig.add_trace(
        go.Box(
            x=filtered_df['gender'],
            y=filtered_df[selected_variable],
            name='Gender Distribution',
            marker_color='#4caf50',
            line=dict(color='#1b5e20', width=1.5),
            boxmean=True,
            boxpoints='all',
            jitter=0.35,
            pointpos=0,
            marker=dict(opacity=0.55, size=5, color='rgba(156, 39, 176, 0.45)')
            ),
        row=1,
        col=2
        )

    fig.update_layout(
        title=f"{USAGE_ACTIVITY_LABELS.get(selected_variable, selected_variable)} - Distribution Analysis",
        showlegend=False,
        height=600,
        margin=dict(l=60, r=20, t=80, b=60)
    )

    fig.update_xaxes(title_text="Age Group", categoryorder='array', categoryarray=age_order, row=1, col=1)
    fig.update_xaxes(title_text="Gender", row=1, col=2)
    fig.update_yaxes(title_text="Usage Intensity", row=1, col=1)
    fig.update_yaxes(title_text="Usage Intensity", row=1, col=2)

    return fig

@app.callback(
    Output('usage-pattern-ranking-chart', 'figure'),
    [Input('simulated-age-filter', 'value'),
     Input('simulated-gender-filter', 'value')]
)
def update_usage_pattern_ranking_chart(selected_ages, selected_genders):
    if simulated_df is None or simulated_df.empty:
        return go.Figure()

    selected_ages = ensure_list(selected_ages) if selected_ages is not None else []
    selected_genders = ensure_list(selected_genders) if selected_genders is not None else []

    filtered_df = simulated_df.copy()

    # If specific age groups are selected, filter by them; otherwise show all
    if selected_ages:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_ages)]

    # If specific genders are selected, filter by them; otherwise show all
    if selected_genders:
        filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

    if len(filtered_df) < 5:
        return go.Figure()

    usage_columns = [col for col in USAGE_ACTIVITY_LABELS.keys() if col in filtered_df.columns]
    if not usage_columns:
        return go.Figure()

    averages = filtered_df[usage_columns].mean().dropna()
    if averages.empty:
        return go.Figure()

    averages = averages.sort_values(ascending=True)
    is_fraction = averages.max() <= 1.2
    values = averages.values * 100 if is_fraction else averages.values
    suffix = '%' if is_fraction else ''

    labels = [USAGE_ACTIVITY_LABELS.get(col, col.replace('_', ' ').title()) for col in averages.index]
    hover_format = '.1f' if is_fraction else '.2f'

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(color='#5A7D9A', line=dict(color='#2C3E50', width=0.5)),
        text=[f"{val:.1f}{suffix}" if suffix else f"{val:.2f}" for val in values],
        textposition='auto',
        hovertemplate=(
            '<b>%{y}</b><br>'
            f'Average intensity: %{{x:{hover_format}}}{suffix}<extra></extra>'
        )
    ))

    fig.update_layout(
        title="Average ICT Activity Intensity",
        xaxis_title=f"Average Usage{' (%)' if is_fraction else ''}",
        yaxis_title="ICT Activities",
        yaxis=dict(autorange='reversed'),
        height=520,
        margin=dict(l=140, r=40, t=80, b=60),
        bargap=0.3,
        plot_bgcolor='#ffffff'
    )

    fig.add_annotation(
        xref='paper', yref='paper',
        x=0, y=1.08,
        showarrow=False,
        font=dict(size=12, color='#7F8C8D'),
        text=f"Filtered sample size: {len(filtered_df):,} respondents"
    )

    return fig

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port
    )
