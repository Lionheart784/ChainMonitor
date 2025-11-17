"""
ChainMonitor API Server
提供REST API接口，连接frontend和backend SQLite数据库
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import json
from pathlib import Path
from web3 import Web3

# 数据库路径
DB_PATH = Path(__file__).resolve().parent / "defi_monitor.db"
MARKETS_PATH = Path(__file__).resolve().parent / "markets.json"

app = FastAPI(title="ChainMonitor API", version="1.0.0")

# 配置CORS，允许frontend访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Pydantic 模型
# ============================================

class Market(BaseModel):
    id: str
    label: str
    type: str
    address: str
    token0: str
    token1: str
    riskLevel: int
    riskScore: float
    lastUpdated: Optional[str]
    isActive: bool


class RiskHistoryPoint(BaseModel):
    timestamp: str
    level: int
    score: float


class RiskFactors(BaseModel):
    dex: Dict[str, Any]
    whale: Dict[str, Any]
    cex: Dict[str, Any]
    updatedAt: str


class Transaction(BaseModel):
    txHash: str
    blockNumber: int
    timestamp: int
    tokenIn: str
    tokenOut: str
    amountIn: str
    amountOut: str
    trader: str
    createdAt: str


class Alert(BaseModel):
    id: int
    marketId: str
    marketLabel: str
    type: str
    severity: str
    previousLevel: Optional[int]
    newLevel: int
    message: Optional[str]
    isResolved: bool
    createdAt: str


class OverviewStats(BaseModel):
    totalMarkets: int
    highRiskMarkets: int
    todayTransactions: int
    unresolvedAlerts: int


# ============================================
# 数据库辅助函数
# ============================================

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_markets_config() -> List[Dict[str, Any]]:
    """加载markets.json配置"""
    try:
        with open(MARKETS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def calc_market_id(label: str) -> str:
    """计算market ID (keccak256哈希)"""
    return Web3.keccak(text=label).hex()


def get_latest_risk_level(market_id: str) -> tuple:
    """获取最新的风险等级和分数"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT level, created_at
        FROM risk_levels
        WHERE market_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (market_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        # 风险等级映射到分数（0-100）
        level = row[0]
        score = level * 25 + 12.5  # 0->12.5, 1->37.5, 2->62.5, 3->87.5
        return level, score, row[1]

    return 0, 0.0, None


# ============================================
# API 端点
# ============================================

@app.get("/")
def root():
    """健康检查"""
    return {"status": "ok", "message": "ChainMonitor API is running"}


@app.get("/api/markets")
def get_markets():
    """获取所有市场列表"""
    markets_config = load_markets_config()
    markets = []

    for config in markets_config:
        # 只返回DEX池子市场
        if config.get("type") != "dex_pool":
            continue

        label = config["label"]
        market_id = calc_market_id(label)
        level, score, last_updated = get_latest_risk_level(market_id)

        # 解析token对
        if "pairAddress" in config or "address" in config:
            # 从label中提取token信息，例如 "UNISWAP_USDC_WETH"
            parts = label.split("_")
            token0 = parts[-2] if len(parts) >= 2 else "TOKEN0"
            token1 = parts[-1] if len(parts) >= 1 else "TOKEN1"
        else:
            token0 = "TOKEN0"
            token1 = "TOKEN1"

        market = Market(
            id=label,
            label=label,
            type=config.get("type", "dex_pool"),
            address=config.get("pairAddress") or config.get("address", ""),
            token0=token0,
            token1=token1,
            riskLevel=level,
            riskScore=score,
            lastUpdated=last_updated,
            isActive=True
        )
        markets.append(market)

    return {"markets": markets}


@app.get("/api/markets/{market_id}")
def get_market_detail(market_id: str):
    """获取单个市场详情"""
    markets_config = load_markets_config()

    # 查找市场配置
    market_config = None
    for config in markets_config:
        if config["label"] == market_id:
            market_config = config
            break

    if not market_config:
        raise HTTPException(status_code=404, detail="Market not found")

    # 计算market_id hash
    market_id_hash = calc_market_id(market_id)
    level, score, last_updated = get_latest_risk_level(market_id_hash)

    # 解析token对
    parts = market_id.split("_")
    token0 = parts[-2] if len(parts) >= 2 else "TOKEN0"
    token1 = parts[-1] if len(parts) >= 1 else "TOKEN1"

    market = Market(
        id=market_id,
        label=market_id,
        type=market_config.get("type", "dex_pool"),
        address=market_config.get("pairAddress") or market_config.get("address", ""),
        token0=token0,
        token1=token1,
        riskLevel=level,
        riskScore=score,
        lastUpdated=last_updated,
        isActive=True
    )

    return market


@app.get("/api/markets/{market_id}/risk-history")
def get_risk_history(market_id: str, hours: int = Query(24, ge=1, le=168)):
    """获取市场风险历史"""
    market_id_hash = calc_market_id(market_id)

    # 计算时间范围
    cutoff_time = datetime.now() - timedelta(hours=hours)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT level, created_at
        FROM risk_levels
        WHERE market_id = ? AND created_at >= ?
        ORDER BY created_at ASC
        """,
        (market_id_hash, cutoff_time.isoformat())
    )

    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        level = row[0]
        score = level * 25 + 12.5  # 映射到分数

        history.append(RiskHistoryPoint(
            timestamp=row[1],
            level=level,
            score=score
        ))

    return {"history": history}


@app.get("/api/markets/{market_id}/factors")
def get_risk_factors(market_id: str):
    """获取风险因子详情"""
    # 注意：当前数据库中没有单独存储各个因子的详细数据
    # 这里返回模拟数据，实际应该扩展monitor.py来保存因子详情

    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取最近的交易统计
    cursor.execute(
        """
        SELECT COUNT(*), SUM(CAST(amount_in AS REAL))
        FROM trades
        WHERE created_at >= datetime('now', '-1 hour')
        """
    )
    row = cursor.fetchone()
    tx_count = row[0] or 0
    total_volume = row[1] or 0

    conn.close()

    # 返回估算的因子数据
    factors = RiskFactors(
        dex={
            "score": 20,
            "volumeRatio": 0.05,
            "txCount": tx_count,
            "liquidity": 1000000
        },
        whale={
            "score": 15,
            "sellVolume": 50000,
            "activeCount": 2,
            "sellRatio": 0.05
        },
        cex={
            "score": 10,
            "totalInflow": 100000,
            "totalOutflow": 80000,
            "netInflow": 20000,
            "netInflowRatio": 0.02
        },
        updatedAt=datetime.now().isoformat()
    )

    return {"factors": factors}


@app.get("/api/markets/{market_id}/transactions")
def get_transactions(market_id: str, limit: int = Query(100, ge=1, le=1000)):
    """获取交易记录"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT tx_hash, block_number, timestamp, token_in, token_out,
               amount_in, amount_out, created_at
        FROM trades
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    transactions = []
    for row in rows:
        tx = Transaction(
            txHash=row[0],
            blockNumber=row[1],
            timestamp=row[2],
            tokenIn=row[3],
            tokenOut=row[4],
            amountIn=row[5],
            amountOut=row[6],
            trader="0x0000000000000000000000000000000000000000",  # 待实现
            createdAt=row[7]
        )
        transactions.append(tx)

    return {"transactions": transactions}


@app.get("/api/alerts")
def get_alerts(severity: Optional[str] = None):
    """获取告警列表"""
    # 注意：当前数据库中没有alerts表
    # 这里根据风险等级变化生成告警

    conn = get_db_connection()
    cursor = conn.cursor()

    # 查找风险等级变化
    cursor.execute(
        """
        SELECT r1.id, r1.market_id, r1.level, r1.created_at,
               (SELECT level FROM risk_levels r2
                WHERE r2.market_id = r1.market_id
                AND r2.id < r1.id
                ORDER BY r2.id DESC LIMIT 1) as prev_level
        FROM risk_levels r1
        ORDER BY r1.created_at DESC
        LIMIT 50
        """
    )

    rows = cursor.fetchall()
    conn.close()

    markets_config = load_markets_config()
    market_labels = {calc_market_id(m["label"]): m["label"] for m in markets_config}

    alerts = []
    for row in rows:
        alert_id = row[0]
        market_id = row[1]
        new_level = row[2]
        created_at = row[3]
        prev_level = row[4]

        # 只有等级变化才生成告警
        if prev_level is None or prev_level != new_level:
            severity_map = {0: "low", 1: "medium", 2: "high", 3: "critical"}
            alert_severity = severity_map.get(new_level, "low")

            # 如果指定了severity过滤
            if severity and alert_severity != severity:
                continue

            market_label = market_labels.get(market_id, market_id[:8])

            alert = Alert(
                id=alert_id,
                marketId=market_id,
                marketLabel=market_label,
                type="risk_level_change",
                severity=alert_severity,
                previousLevel=prev_level,
                newLevel=new_level,
                message=f"Risk level changed from {prev_level} to {new_level}",
                isResolved=False,
                createdAt=created_at
            )
            alerts.append(alert)

    return {"alerts": alerts}


@app.get("/api/stats/overview")
def get_overview_stats():
    """获取总览统计"""
    markets_config = load_markets_config()

    # 统计DEX市场数量
    dex_markets = [m for m in markets_config if m.get("type") == "dex_pool"]
    total_markets = len(dex_markets)

    # 统计高风险市场
    high_risk_count = 0
    for market in dex_markets:
        market_id = calc_market_id(market["label"])
        level, _, _ = get_latest_risk_level(market_id)
        if level >= 2:  # 风险等级2或3
            high_risk_count += 1

    # 统计今日交易数
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM trades
        WHERE created_at >= date('now')
        """
    )
    today_tx = cursor.fetchone()[0] or 0

    # 统计未解决的告警（最近的高风险等级变化）
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM risk_levels
        WHERE level >= 2 AND created_at >= datetime('now', '-24 hours')
        """
    )
    unresolved_alerts = cursor.fetchone()[0] or 0

    conn.close()

    stats = OverviewStats(
        totalMarkets=total_markets,
        highRiskMarkets=high_risk_count,
        todayTransactions=today_tx,
        unresolvedAlerts=unresolved_alerts
    )

    return stats


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ChainMonitor API Server on http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
