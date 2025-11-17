#!/bin/bash
# 启动完整的ChainMonitor系统（API服务器 + Frontend）

echo "🚀 启动 ChainMonitor 完整系统"
echo "================================"
echo ""

# 检查是否在项目根目录
if [ ! -f "package.json" ] && [ ! -d "backend" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 函数：在后台启动进程
start_service() {
    local name=$1
    local command=$2
    local dir=$3

    echo "📦 启动 $name..."
    cd "$dir" || exit
    $command &
    local pid=$!
    echo "   PID: $pid"
    cd - > /dev/null || exit
}

# 启动API服务器
echo "1️⃣  启动 API 服务器..."
cd backend || exit
if [ ! -d "venv" ]; then
    echo "   创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
python api_server.py &
API_PID=$!
echo "   ✅ API服务器已启动 (PID: $API_PID)"
echo "   📍 地址: http://localhost:8000"
echo "   📚 文档: http://localhost:8000/docs"
cd ..

sleep 2

# 启动Frontend
echo ""
echo "2️⃣  启动 Frontend..."
cd frontend || exit
if [ ! -d "node_modules" ]; then
    echo "   安装npm依赖..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
echo "   ✅ Frontend已启动 (PID: $FRONTEND_PID)"
echo "   📍 地址: http://localhost:5173"
cd ..

echo ""
echo "================================"
echo "✅ ChainMonitor 系统已启动"
echo ""
echo "📊 访问地址:"
echo "   Frontend:  http://localhost:5173"
echo "   API:       http://localhost:8000"
echo "   API文档:   http://localhost:8000/docs"
echo ""
echo "💡 提示:"
echo "   - 按 Ctrl+C 停止所有服务"
echo "   - 监控服务需要单独启动: cd backend && ./start_monitor.sh"
echo ""

# 捕获Ctrl+C信号
trap "echo ''; echo '🛑 停止所有服务...'; kill $API_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# 等待
wait
