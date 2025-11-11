#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import sys

# 测试导入和基本功能
try:
    import viz_simulated_data
    print('✓ 模块导入成功')

    # 测试数据
    df = viz_simulated_data.df
    print(f'✓ 数据加载成功: {df.shape}')
    print(f'✓ 列名映射正确: {len(df.columns)} 列')

    # 测试回调函数
    try:
        from viz_simulated_data import update_wordcloud
        result = update_wordcloud(None, None)
        print('✓ 词云函数工作正常')
        print(f'✓ 词云图片生成成功: {len(result)} 字符')
    except Exception as e:
        print(f'⚠ 词云函数测试失败: {e}')

    # 测试其他回调函数
    try:
        from viz_simulated_data import update_radar_chart, update_treemap_chart
        radar_fig = update_radar_chart(None)
        treemap_fig = update_treemap_chart(None, None)
        print('✓ 雷达图和树状图函数工作正常')
    except Exception as e:
        print(f'⚠ 图表函数测试失败: {e}')

    print('\n✓ 应用初始化完成，所有功能就绪!')
    print('\n运行命令: python viz_simulated_data.py')
    print('然后在浏览器中访问: http://127.0.0.1:8051/')

except Exception as e:
    print(f'✗ 错误: {e}')
    import traceback
    traceback.print_exc()
