# src/api/main.py
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
# import requests
import yfinance as yf

# Load environment variables
load_dotenv()

# Print environment variables for debugging
print("Environment variables:")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_PASSWORD is set: {'DB_PASSWORD' in os.environ}")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL is fine
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, DELETE, etc
    allow_headers=["*"],  # allow any headers
)

# Database connection
def get_db_connection():
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    
    print(f"Attempting to connect to database:")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=os.getenv("DB_PASSWORD", ""),
            host=db_host,
            port=db_port
        )
        return conn
    except Exception as e:
        print(f"Connection error: {str(e)}")
        raise

# API Models
class Asset(BaseModel):
    ticker: str
    name: Optional[str] = None
    asset_type: str = "stock"

class MarketData(BaseModel):
    asset_id: str
    timestamp: datetime
    price: float
    volume: int
    sentiment_score: Optional[float] = None
    sentiment_magnitude: Optional[float] = None
    currency: str = "USD"
    source: str = "system"

class Prediction(BaseModel):
    asset_id: str
    strategy_name: str
    timestamp: datetime
    prediction: Dict[str, Any]
    confidence: float
    reasoning: Optional[str] = None

class Decision(BaseModel):
    asset_id: str
    timestamp: datetime
    action: str
    confidence: float
    reasoning: Optional[str] = None

class StrategyWeight(BaseModel):
    strategy_name: str
    weight: float
    performance_score: Optional[float] = None

class Performance(BaseModel):
    asset_id: str
    strategy_name: str
    prediction_id: Optional[int] = None
    timestamp: datetime
    predicted_action: str
    actual_outcome: float
    performance_score: float



@app.post("/assets")
async def create_asset(asset: Asset):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 🛠 If no name provided, auto-fetch it
            if not asset.name or asset.name.strip() == "":
                asset.name = fetch_company_name(asset.ticker)

            cur.execute("""
                INSERT INTO assets (ticker, name, asset_type)
                VALUES (%s, %s, %s)
                RETURNING ticker, name, asset_type
            """, (asset.ticker, asset.name, asset.asset_type))
            
            result = cur.fetchone()
            conn.commit()
            return {"ticker": result[0], "name": result[1], "asset_type": result[2]}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="Asset already exists")
    finally:
        conn.close()

@app.get("/assets")
async def get_assets():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT ticker, name, asset_type FROM assets")
            return [{"ticker": row[0], "name": row[1], "asset_type": row[2]} for row in cur.fetchall()]
    finally:
        conn.close()

@app.get("/assets/{ticker}")
async def get_asset(ticker: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT ticker, name, asset_type FROM assets WHERE ticker = %s", (ticker,))
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Asset not found")
            return {"ticker": result[0], "name": result[1], "asset_type": result[2]}
    finally:
        conn.close()

@app.delete("/assets/{ticker}")
async def delete_asset(ticker: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:

            # Step 1: Delete performance history first (because it depends on predictions)
            cur.execute("""
                DELETE FROM performance_history 
                WHERE asset_id = %s 
                OR prediction_id IN (
                    SELECT id FROM predictions WHERE asset_id = %s
                )
            """, (ticker, ticker))
            
            # Step 2: Delete market data
            cur.execute("DELETE FROM market_data WHERE asset_id = %s", (ticker,))
            
            # Step 3: Delete predictions
            cur.execute("DELETE FROM predictions WHERE asset_id = %s", (ticker,))
            
            # Step 4: Delete decisions
            cur.execute("DELETE FROM decisions WHERE asset_id = %s", (ticker,))
            
            # Step 5: Finally delete the asset itself
            cur.execute("DELETE FROM assets WHERE ticker = %s RETURNING ticker", (ticker,))
            
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Asset not found")
            conn.commit()
            return {"message": f"Asset '{ticker}' deleted successfully"}
    finally:
        conn.close()

@app.post("/market-data")
async def create_market_data(data: MarketData):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO market_data 
                (asset_id, timestamp, price, volume, sentiment_score, sentiment_magnitude, currency, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (asset_id, timestamp) DO UPDATE SET
                    price = EXCLUDED.price,
                    volume = EXCLUDED.volume,
                    sentiment_score = EXCLUDED.sentiment_score,
                    sentiment_magnitude = EXCLUDED.sentiment_magnitude
                RETURNING id
            """, (
                data.asset_id, data.timestamp, data.price, data.volume,
                data.sentiment_score, data.sentiment_magnitude,
                data.currency, data.source
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0]}
    finally:
        conn.close()

@app.get("/market-data/{asset_id}")
async def get_market_data(asset_id: str, limit: int = 30):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, price, volume, sentiment_score, sentiment_magnitude, currency, source
                FROM market_data
                WHERE asset_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (asset_id, limit))
            return [
                {
                    "timestamp": row[0],
                    "price": row[1],
                    "volume": row[2],
                    "sentiment_score": row[3],
                    "sentiment_magnitude": row[4],
                    "currency": row[5],
                    "source": row[6]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()



@app.post("/predictions")
async def create_prediction(prediction: Prediction):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO predictions 
                (asset_id, strategy_name, timestamp, prediction, confidence, reasoning)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                prediction.asset_id, prediction.strategy_name, prediction.timestamp,
                prediction.prediction, prediction.confidence, prediction.reasoning
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0]}
    finally:
        conn.close()


@app.get("/predictions/{asset_id}")
async def get_predictions(asset_id: str, limit: int = 30):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT strategy_name, timestamp, prediction, confidence, reasoning
                FROM predictions
                WHERE asset_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (asset_id, limit))
            return [
                {
                    "strategy_name": row[0],
                    "timestamp": row[1],
                    "prediction": row[2],
                    "confidence": row[3],
                    "reasoning": row[4]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()

@app.post("/decisions")
async def create_decision(decision: Decision):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO decisions 
                (asset_id, timestamp, action, confidence_score, reasoning)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                decision.asset_id, decision.timestamp,
                decision.action, decision.confidence, decision.reasoning
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0]}
    finally:
        conn.close()

@app.get("/decisions/{asset_id}")
async def get_decisions(asset_id: str, limit: int = 100):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, action, confidence_score, reasoning
                FROM decisions
                WHERE asset_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (asset_id, limit))
            return [
                {
                    "timestamp": row[0],
                    "action": row[1],
                    "confidence": row[2],
                    "reasoning": row[3]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()

@app.post("/strategy-weights")
async def create_strategy_weight(weight: StrategyWeight):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO strategy_weights 
                (strategy_name, weight, performance_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (strategy_name) DO UPDATE SET
                    weight = EXCLUDED.weight,
                    performance_score = EXCLUDED.performance_score,
                    last_updated = CURRENT_TIMESTAMP
                RETURNING strategy_name, weight, performance_score, last_updated
            """, (weight.strategy_name, weight.weight, weight.performance_score))
            result = cur.fetchone()
            conn.commit()
            return {
                "strategy_name": result[0],
                "weight": result[1],
                "performance_score": result[2],
                "last_updated": result[3]
            }
    finally:
        conn.close()

@app.get("/strategy-weights")
async def get_strategy_weights():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT strategy_name, weight, performance_score, last_updated 
                FROM strategy_weights
            """)
            return [
                {
                    "strategy_name": row[0],
                    "weight": row[1],
                    "performance_score": row[2],
                    "last_updated": row[3]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()

@app.post("/performance")
async def create_performance(performance: Performance):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO performance_history 
                (asset_id, strategy_name, prediction_id, timestamp, 
                 predicted_action, actual_outcome, performance_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                performance.asset_id, performance.strategy_name,
                performance.prediction_id, performance.timestamp,
                performance.predicted_action, performance.actual_outcome,
                performance.performance_score
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0]}
    finally:
        conn.close()

@app.get("/performance/{asset_id}")
async def get_performance(asset_id: str, limit: int = 100):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT strategy_name, timestamp, predicted_action, 
                       actual_outcome, performance_score
                FROM performance_history
                WHERE asset_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (asset_id, limit))
            return [
                {
                    "strategy_name": row[0],
                    "timestamp": row[1],
                    "predicted_action": row[2],
                    "actual_outcome": row[3],
                    "performance_score": row[4]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()

# Test endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Trading System API"}

# Test database connection
@app.get("/test-db")
async def test_db():
    try:
        # Method 1: Try with environment variables
        print("\nTrying Method 1: Environment variables")
        conn1 = get_db_connection()
        conn1.close()
        print("Method 1: Success")
        
        return {"status": "success", "message": "Database connection successful"}
    except Exception as e:
        print(f"\nError details: {str(e)}")
        return {"status": "error", "message": str(e)}
    

# helper shit
# def fetch_company_name(ticker: str) -> str:
#     url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=price"
#     resp = requests.get(url)
#     if resp.status_code != 200:
#         raise HTTPException(status_code=400, detail="Failed to fetch company name")
    
#     data = resp.json()
#     try:
#         return data["quoteSummary"]["result"][0]["price"]["longName"]
#     except (KeyError, IndexError, TypeError):
#         raise HTTPException(status_code=400, detail="Invalid ticker or no company name found")
def fetch_company_name(ticker: str) -> str:
    """
    Given a stock ticker, returns the company’s longName or shortName.
    Raises HTTPException(400) if the ticker is invalid or name not found.
    """
    try:
        tk = yf.Ticker(ticker)
        info = tk.info  # pulls the “quoteSummary” data for you
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data for {ticker}: {e}")

    name = info.get("longName") or info.get("shortName")
    if not name:
        raise HTTPException(
            status_code=400,
            detail=f"No company name found for ticker '{ticker}'"
        )
    return name