#!/bin/bash
# ChainMonitor API服务器启动脚本

echo "🚀 启动 ChainMonitor API 服务器..."
echo "📍 API地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""

# 检查Python虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未检测到虚拟环境，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 检查依赖..."
pip install -r requirements.txt -q

# 启动API服务器
echo ""
echo "✅ 启动服务器..."
python api_server.py
