# ChainMonitor 设置指南

本指南将帮助你配置和运行ChainMonitor系统，使frontend与backend运行环境完全匹配。

## 系统架构

```
┌─────────────────┐      HTTP API      ┌──────────────────┐      SQLite      ┌─────────────┐
│                 │ ←────────────────→ │                  │ ←───────────────→ │             │
│   Frontend      │    localhost:8000  │   API Server     │                  │  Database   │
│  (React+Vite)   │                    │   (FastAPI)      │                  │  监控数据    │
│  Port: 5173     │                    │   Port: 8000     │                  │             │
└─────────────────┘                    └──────────────────┘                  └─────────────┘
                                              ↑
                                              │ 读取数据
                                              ↓
                                       ┌──────────────────┐
                                       │  Monitor Script  │
                                       │  (monitor.py)    │
                                       │  监控链上数据     │
                                       └──────────────────┘
```

## 快速开始

### 方式1: 一键启动 (推荐)

```bash
# 在项目根目录执行
./start_all.sh
```

这将自动启动:
- ✅ API服务器 (http://localhost:8000)
- ✅ Frontend (http://localhost:5173)

### 方式2: 分别启动

#### 1. 启动API服务器

```bash
cd backend
./start_api.sh
```

API服务器将运行在 `http://localhost:8000`
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/

#### 2. 启动Frontend

```bash
cd frontend
npm install      # 首次运行需要安装依赖
npm run dev
```

Frontend将运行在 `http://localhost:5173`

#### 3. 启动监控服务 (可选)

```bash
cd backend
./start_monitor.sh
```

监控服务会持续采集链上数据并存储到数据库。

## 环境配置

### Backend配置

在 `backend` 目录下创建 `.env` 文件：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，填写必要的配置：

```env
# 以太坊主网RPC (必需)
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY

# Sepolia测试网RPC (可选，用于部署合约)
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY

# 私钥 (可选，仅用于更新链上风险等级)
PRIVATE_KEY=your_private_key_here
```

### Frontend配置

Frontend的 `.env` 文件已自动创建，默认配置如下：

```env
# API服务器地址
VITE_API_BASE_URL=http://localhost:8000/api

# 合约地址 (可选)
VITE_CONTRACT_ADDRESS=0x...

# RPC配置 (可选)
VITE_SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
VITE_MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
```

## 安装依赖

### Backend依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

主要依赖:
- `fastapi` - Web框架
- `uvicorn` - ASGI服务器
- `web3` - 以太坊交互
- `sqlite3` - 数据库 (Python内置)

### Frontend依赖

```bash
cd frontend
npm install
```

主要依赖:
- `react` - UI框架
- `vite` - 构建工具
- `axios` - HTTP客户端
- `wagmi` - Web3钱包连接

## API端点说明

API服务器提供以下REST API端点：

### 市场相关
- `GET /api/markets` - 获取所有市场列表
- `GET /api/markets/{id}` - 获取市场详情
- `GET /api/markets/{id}/risk-history` - 获取风险历史 (支持hours参数)
- `GET /api/markets/{id}/factors` - 获取风险因子详情
- `GET /api/markets/{id}/transactions` - 获取交易记录

### 告警与统计
- `GET /api/alerts` - 获取告警列表 (支持severity过滤)
- `GET /api/stats/overview` - 获取总览统计

详细API文档请访问: http://localhost:8000/docs

## 数据流程

1. **监控服务** (`monitor.py`) 定期采集链上数据
   - DEX交易数据
   - 巨鲸行为
   - CEX净流入
   - 计算风险等级并存储到SQLite

2. **API服务器** (`api_server.py`) 提供REST API
   - 读取SQLite数据库
   - 格式化数据为JSON
   - 提供给Frontend

3. **Frontend** 通过HTTP请求获取数据
   - 调用 `http://localhost:8000/api/*` 端点
   - 展示实时监控数据
   - 可视化风险趋势

## 故障排查

### API服务器无法启动

**问题**: `ModuleNotFoundError: No module named 'fastapi'`

**解决**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend无法连接API

**问题**: `Network Error` 或 `CORS错误`

**解决**:
1. 确认API服务器已启动: http://localhost:8000
2. 检查Frontend的 `.env` 配置:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```
3. 重启Frontend服务:
   ```bash
   cd frontend
   npm run dev
   ```

### 数据库为空

**问题**: API返回空数据

**解决**:
1. 启动监控服务采集数据:
   ```bash
   cd backend
   ./start_monitor.sh
   ```
2. 等待至少1-2个监控周期 (默认60秒/轮)
3. 检查数据库:
   ```bash
   sqlite3 backend/defi_monitor.db "SELECT COUNT(*) FROM trades;"
   ```

### 监控服务错误

**问题**: `No ETH_RPC_URL found`

**解决**:
1. 配置 `backend/.env` 文件
2. 填写有效的以太坊RPC URL
3. 推荐使用 Infura 或 Alchemy

## 开发建议

### 添加新的监控市场

编辑 `backend/markets.json`:

```json
{
  "label": "UNISWAP_DAI_USDC",
  "type": "dex_pool",
  "pairAddress": "0xAE461cA67B15dc8dc81CE7615e0320dA1A9aB8D5",
  "description": "Uniswap V2 DAI/USDC pool"
}
```

### 扩展API端点

在 `backend/api_server.py` 中添加新的路由:

```python
@app.get("/api/custom-endpoint")
def custom_endpoint():
    # 你的逻辑
    return {"data": "value"}
```

### 修改风险评分算法

编辑 `backend/monitor.py` 中的 `RISK_CONFIG` 配置。

## 生产部署

### 使用Docker (推荐)

1. 构建镜像:
   ```bash
   docker build -t chainmonitor-api ./backend
   docker build -t chainmonitor-frontend ./frontend
   ```

2. 运行容器:
   ```bash
   docker run -d -p 8000:8000 chainmonitor-api
   docker run -d -p 3000:80 chainmonitor-frontend
   ```

### 使用进程管理器

使用 `PM2` 或 `systemd` 管理后台服务:

```bash
# PM2示例
pm2 start backend/api_server.py --name chainmonitor-api
pm2 start backend/monitor.py --name chainmonitor-monitor
```

## 技术支持

如有问题，请查看:
- API文档: http://localhost:8000/docs
- 项目README
- GitHub Issues

## 更新日志

### v1.0.0 (当前版本)
- ✅ 创建FastAPI后端服务器
- ✅ 实现所有Frontend需要的API端点
- ✅ 配置CORS允许跨域访问
- ✅ 环境变量配置
- ✅ 启动脚本
- ✅ 完整文档
