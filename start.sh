#!/bin/bash

# 设置默认端口
PORT=${PORT:-8050}

# 启动gunicorn服务器
echo "Starting server on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 macau_tech_analysis:app
