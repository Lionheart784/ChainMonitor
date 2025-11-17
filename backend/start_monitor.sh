#!/bin/bash
# ChainMonitor 监控脚本启动

echo "🔍 启动 ChainMonitor 监控服务..."
echo ""

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，请先配置环境变量"
    echo "   复制 .env.example 到 .env 并填写配置"
    exit 1
fi

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

# 启动监控
echo ""
echo "✅ 启动监控..."
python monitor.py
