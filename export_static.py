#!/usr/bin/env python3
"""
将Dash应用导出为静态HTML文件，用于GitHub Pages部署
"""

import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
import os
from collections import Counter

# 加载数据
def load_data():
    """加载必要的分析数据"""
    try:
        with open('viz_data.json', 'r', encoding='utf-8') as f:
            viz_data = json.load(f)

        with open('detailed_analysis.json', 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # 尝试加载模拟数据
        try:
            simulated_df = pd.read_csv('simulated_samples_clean.csv')
            print(f"Loaded simulated data: {simulated_df.shape}")
        except:
            simulated_df = None
            print("Could not load simulated data")

        return viz_data, analysis_data, simulated_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None

def create_static_charts(viz_data, analysis_data, simulated_df):
    """创建静态图表"""
    charts = {}

    # 1. 创建年龄分布图
    if viz_data and 'age_distribution' in viz_data:
        age_data = viz_data['age_distribution']
        fig = px.bar(
            x=list(age_data.keys()),
            y=list(age_data.values()),
            title="年龄分布",
            labels={'x': '年龄段', 'y': '人数'}
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Source Sans Pro', size=12)
        )
        charts['age_distribution'] = fig.to_html(full_html=False, include_plotlyjs=False)

    # 2. 创建教育水平分布
    if viz_data and 'education_distribution' in viz_data:
        edu_data = viz_data['education_distribution']
        fig = px.pie(
            values=list(edu_data.values()),
            names=list(edu_data.keys()),
            title="教育水平分布"
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Source Sans Pro', size=12)
        )
        charts['education_distribution'] = fig.to_html(full_html=False, include_plotlyjs=False)

    # 3. 创建科技产品使用情况
    if simulated_df is not None:
        tech_cols = ['mobile_phone', 'laptop_computer', 'desktop_computer', 'tablet']
        available_cols = [col for col in tech_cols if col in simulated_df.columns]

        if available_cols:
            usage_data = simulated_df[available_cols].mean() * 100
            fig = px.bar(
                x=usage_data.index,
                y=usage_data.values,
                title="科技产品使用率 (%)",
                labels={'x': '产品类型', 'y': '使用率 (%)'}
            )
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Source Sans Pro', size=12)
            )
            charts['tech_usage'] = fig.to_html(full_html=False, include_plotlyjs=False)

    # 4. 创建互联网接入方式分布
    if simulated_df is not None and 'internet_access' in simulated_df.columns:
        internet_data = simulated_df['internet_access'].value_counts()
        fig = px.bar(
            x=internet_data.index,
            y=internet_data.values,
            title="互联网接入情况",
            labels={'x': '接入类型', 'y': '人数'}
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Source Sans Pro', size=12)
        )
        charts['internet_access'] = fig.to_html(full_html=False, include_plotlyjs=False)

    return charts

def create_wordcloud():
    """创建关键词云"""
    try:
        # 这里可以根据你的数据创建词云
        # 暂时创建一个示例词云
        text = "澳门 科技 使用 互联网 移动电话 电脑 教育 就业 数字化 发展 创新"
        wordcloud = WordCloud(
            font_path=None,  # 使用默认字体
            width=800,
            height=400,
            background_color='white',
            max_words=50
        ).generate(text)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')

        # 转换为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        print(f"Error creating wordcloud: {e}")
        return None

def export_to_static():
    """导出静态版本"""

    # 创建输出目录
    static_dir = 'docs'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # 加载数据
    viz_data, analysis_data, simulated_df = load_data()

    # 创建静态图表
    charts = create_static_charts(viz_data, analysis_data, simulated_df)

    # 创建词云
    wordcloud_img = create_wordcloud()

    # 创建HTML内容
    html_content = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>澳门住户资讯科技使用状况分析</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.2em;
            }}
            .content {{
                padding: 30px;
            }}
            .chart-container {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background: #f8f9fa;
            }}
            .chart-title {{
                font-size: 1.5em;
                font-weight: 600;
                margin-bottom: 15px;
                color: #495057;
            }}
            .notice {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 30px;
                margin: 30px 0;
            }}
            .full-width {{
                grid-column: 1 / -1;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #6c757d;
                border-top: 1px solid #e9ecef;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e9ecef;
                text-align: center;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: 600;
                color: #667eea;
            }}
            .stat-label {{
                color: #6c757d;
                margin-top: 5px;
            }}
            .wordcloud-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .wordcloud-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>澳门住户资讯科技使用状况分析</h1>
                <p>基于2024年澳门统计数据的可视化分析</p>
            </div>

            <div class="content">
                <div class="notice">
                    <strong>📊 静态版本说明：</strong> 这是为了GitHub Pages部署而生成的静态版本。
                    完整的交互功能请查看 <a href="https://github.com/[你的用户名]/[仓库名]" target="_blank">GitHub仓库</a> 并本地运行。
                </div>

                <h2>数据概览</h2>
                <p>这份分析基于澳门统计暨普查局2024年的数据，涵盖了澳门居民在资讯科技使用方面的关键统计特征。</p>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">10</div>
                        <div class="stat-label">统计维度</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">1000+</div>
                        <div class="stat-label">样本数据</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">2024</div>
                        <div class="stat-label">数据年份</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">5</div>
                        <div class="stat-label">分析章节</div>
                    </div>
                </div>

                <div class="grid">
    '''

    # 添加图表
    if 'age_distribution' in charts:
        html_content += f'''
                    <div class="chart-container">
                        <div class="chart-title">年龄分布</div>
                        <div class="chart">
                            {charts['age_distribution']}
                        </div>
                    </div>
        '''

    if 'education_distribution' in charts:
        html_content += f'''
                    <div class="chart-container">
                        <div class="chart-title">教育水平分布</div>
                        <div class="chart">
                            {charts['education_distribution']}
                        </div>
                    </div>
        '''

    if 'tech_usage' in charts:
        html_content += f'''
                    <div class="chart-container full-width">
                        <div class="chart-title">科技产品使用率</div>
                        <div class="chart">
                            {charts['tech_usage']}
                        </div>
                    </div>
        '''

    if 'internet_access' in charts:
        html_content += f'''
                    <div class="chart-container">
                        <div class="chart-title">互联网接入情况</div>
                        <div class="chart">
                            {charts['internet_access']}
                        </div>
                    </div>
        '''

    # 添加词云
    if wordcloud_img:
        html_content += f'''
                    <div class="chart-container full-width">
                        <div class="chart-title">关键词分析</div>
                        <div class="wordcloud-container">
                            <img src="{wordcloud_img}" alt="关键词云分析">
                        </div>
                    </div>
        '''

    html_content += '''
                </div>

                <h2>核心发现</h2>
                <ul>
                    <li><strong>数据覆盖全面：</strong>涵盖10个主要统计维度，展现澳门居民科技使用全景</li>
                    <li><strong>人口统计维度突出：</strong>年龄、教育程度和活动状态是三大核心分析维度</li>
                    <li><strong>职业影响显著：</strong>互联网和通信工具使用情况受到职业特征显著影响</li>
                    <li><strong>经济发展映射：</strong>商业用途科技应用反映澳门经济发展特征</li>
                </ul>

                <h2>分析章节</h2>
                <ol>
                    <li><strong>数字鸿沟的代际差异：</strong>不同年龄段的科技使用差异分析</li>
                    <li><strong>科技产品的使用偏好：</strong>各类科技产品在澳门的受欢迎程度</li>
                    <li><strong>多视角综合分析：</strong>从不同维度审视澳门的数字化进程</li>
                    <li><strong>趋势预测与展望：</strong>澳门数字化发展的未来趋势</li>
                    <li><strong>政策建议与行动计划：</strong>缩小数字鸿沟的政策建议</li>
                </ol>

                <h2>技术栈</h2>
                <ul>
                    <li><strong>前端框架:</strong> Dash (Plotly)</li>
                    <li><strong>数据处理:</strong> Pandas, NumPy</li>
                    <li><strong>可视化:</strong> Plotly, NetworkX, WordCloud</li>
                    <li><strong>部署:</strong> GitHub Pages (静态版本)</li>
                </ul>
            </div>

            <div class="footer">
                <p>© 2024 澳门住户资讯科技使用状况分析 | 数据来源：澳门统计暨普查局</p>
                <p>如需完整交互版本，请访问 <a href="https://github.com/[你的用户名]/[仓库名]" target="_blank">GitHub仓库</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

    # 写入文件
    with open(os.path.join(static_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 复制assets文件夹
    import shutil
    if os.path.exists('assets'):
        assets_dest = os.path.join(static_dir, 'assets')
        if os.path.exists(assets_dest):
            shutil.rmtree(assets_dest)
        shutil.copytree('assets', assets_dest)

    print(f"静态网站已生成到 {static_dir} 目录")
    print("推送代码后，GitHub Actions将自动部署到GitHub Pages")

if __name__ == '__main__':
    export_to_static()
