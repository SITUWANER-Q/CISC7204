#!/usr/bin/env python3
"""
澳门住户资讯科技使用状况分析 - 启动脚本
"""

import subprocess
import sys
import os

def main():
    """启动Dash应用"""
    print("启动澳门住户资讯科技使用状况分析应用...")
    print("=" * 50)

    # 检查必要的文件是否存在
    required_files = [
        'app.py',
        'viz_data.json',
        'detailed_analysis.json'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print(f"错误：缺少必要的文件: {', '.join(missing_files)}")
        print("请确保所有文件都在同一目录下。")
        sys.exit(1)

    # 启动应用
    try:
        print("正在启动Dash服务器...")
        print("应用将在 http://localhost:8050 启动")
        print("按 Ctrl+C 停止服务器")
        print("=" * 50)

        subprocess.run([sys.executable, 'app.py'],
                      check=True)

    except KeyboardInterrupt:
        print("\n服务器已停止。")
    except subprocess.CalledProcessError as e:
        print(f"启动应用时出错: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("错误：找不到Python解释器或应用文件。")
        sys.exit(1)

if __name__ == "__main__":
    main()
