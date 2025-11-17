# ChainMonitor - DeFi市场风险监控系统

一个完整的DeFi市场监控系统，结合链上数据分析、实时风险评估和智能合约。

## 系统架构

```
Frontend (React) ←→ API Server (FastAPI) ←→ SQLite Database ←← Monitor Script
     ↓                      ↓                       ↓                    ↓
  可视化界面            REST API               持久化存储            链上数据采集
```

## 主要功能

- 🔍 **实时监控**: 监控Uniswap等DEX池子的交易活动
- 📊 **风险评估**: 基于DEX活跃度、巨鲸行为、CEX净流入的综合风险评分
- 📈 **数据可视化**: React前端展示风险趋势和市场数据
- 🔗 **智能合约**: 将风险等级上链存储到Sepolia测试网
- 🚨 **告警系统**: 风险等级变化自动告警

## 目录结构

```
ChainMonitor/
├── frontend/              # React + Vite 前端应用
│   ├── src/
│   │   ├── hooks/        # API数据获取hooks
│   │   ├── components/   # React组件
│   │   └── utils/        # 工具函数
│   └── .env              # 前端环境配置
├── backend/              # Python 后端服务
│   ├── api_server.py     # FastAPI服务器 (新增!)
│   ├── monitor.py        # 链上数据监控脚本
│   ├── db.py             # SQLite数据库操作
│   ├── chain_data.py     # 链上数据获取
│   ├── whale_cex.py      # 巨鲸和CEX数据分析
│   └── requirements.txt  # Python依赖
├── contracts/            # Solidity智能合约
│   └── RiskMonitor.sol   # 风险监控合约
├── scripts/              # 部署脚本
│   └── deployRiskMonitor.js
└── start_all.sh          # 一键启动脚本
```

## 快速开始

### 🚀 一键启动 (推荐)

```bash
# 1. 克隆项目
git clone <repo-url>
cd ChainMonitor

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填写 ETH_RPC_URL

# 3. 一键启动
chmod +x start_all.sh
./start_all.sh
```

访问:
- Frontend: http://localhost:5173
- API文档: http://localhost:8000/docs

### 📋 分步启动

#### 1. 启动API服务器

```bash
cd backend
chmod +x start_api.sh
./start_api.sh
```

API服务器将运行在 `http://localhost:8000`

#### 2. 启动Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend将运行在 `http://localhost:5173`

#### 3. 启动监控服务 (可选)

```bash
cd backend
chmod +x start_monitor.sh
./start_monitor.sh
```

#### 4. 部署智能合约 (可选)

```bash
# 安装依赖
npm install

# 编译合约
npx hardhat compile

# 部署到Sepolia测试网
npm run deploy:sepolia
```

## 环境配置

### Backend配置 (`backend/.env`)

```env
# 以太坊主网RPC (必需)
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY

# Sepolia测试网RPC (可选)
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY

# 私钥 (可选，用于上链)
PRIVATE_KEY=your_private_key_here

# 合约地址 (部署后填写)
CONTRACT_ADDRESS=0x...
```

### Frontend配置 (`frontend/.env`)

```env
# API服务器地址 (默认配置)
VITE_API_BASE_URL=http://localhost:8000/api

# 其他配置...
```

## API端点

完整的REST API文档请访问: http://localhost:8000/docs

主要端点:
- `GET /api/markets` - 获取所有市场
- `GET /api/markets/{id}/risk-history` - 风险历史
- `GET /api/markets/{id}/transactions` - 交易记录
- `GET /api/alerts` - 告警列表
- `GET /api/stats/overview` - 总览统计

## 技术栈

### Frontend
- React 18
- Vite 5
- TypeScript
- Wagmi (Web3钱包)
- Recharts (图表)
- Axios (HTTP)

### Backend
- FastAPI (API服务器)
- Web3.py (以太坊交互)
- SQLite (数据存储)
- Uvicorn (ASGI服务器)

### Smart Contract
- Solidity 0.8.20
- Hardhat
- Sepolia测试网

## 开发指南

详细的设置和开发指南请查看: [SETUP_GUIDE.md](./SETUP_GUIDE.md)

包含:
- 详细的系统架构说明
- 环境配置步骤
- API端点详解
- 故障排查
- 生产部署建议

## 风险评分算法

系统基于三个因子计算综合风险评分:

1. **DEX活跃度** (40分): 交易量和交易笔数
2. **巨鲸抛压** (35分): 大额卖出行为
3. **CEX净流入** (30分): 交易所资金流动

总分映射到风险等级:
- 0-19: 低风险 (Level 0)
- 20-39: 中风险 (Level 1)
- 40-69: 高风险 (Level 2)
- 70-100: 极高风险 (Level 3)

## 故障排查

### API服务器启动失败

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python api_server.py
```

### Frontend无法连接API

确保:
1. API服务器已启动 (http://localhost:8000)
2. `.env` 配置正确
3. 检查控制台错误信息

### 数据库为空

启动监控服务采集数据:
```bash
cd backend
./start_monitor.sh
```

更多问题请查看 [SETUP_GUIDE.md](./SETUP_GUIDE.md)

## 贡献

欢迎提交Issue和Pull Request!

## License

MIT License