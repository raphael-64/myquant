# Add path to parent directory
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
import psycopg2
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from typing import Dict, List, Any
import numpy as np

# Import message models from data agents
from src.agents.data.price_agent import PriceRequest, PriceResponse
from src.agents.data.sentiment_agent import SentimentRequest, SentimentResponse

# Define message models
class AnalysisRequest(Model):
    asset_id: str
    timestamp: str
    current_data: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    
class StrategyResponse(Model):
    asset_id: str
    timestamp: str
    prediction: Dict[str, Any]
    confidence: float
    reasoning: str
    strategy_name: str

class MetaDecision(Model):
    asset_id: str
    timestamp: str
    action: str
    confidence: float
    reasoning: str
    predictions: List[Dict[str, Any]]
    weighted_predictions: List[Dict[str, Any]]

# Initialize the meta agent with stable seed
meta_agent = Agent(
    name="investment_meta_agent",
    port=8000,
    endpoint=["http://localhost:8000/submit"],
    seed="meta_agent_seed_phrase",
)

# Fund the agent if needed
fund_agent_if_low(meta_agent.wallet.address())

# Print agent information
print(f"Meta agent: Investment Orchestrator")
print(f"Address: {meta_agent.address}")
print(f"Endpoint: http://localhost:8000/submit")

# Run each agent separately and get their addresses by running:
# - python src/agents/data/price_agent.py
# - python src/agents/data/sentiment_agent.py
# - python src/agents/strategies/mean_reversion.py
# - python src/agents/strategies/momentum.py
# - python src/agents/strategies/sentiment_momentum.py
# Then update these addresses:

# Data agent addresses - WILL BE STABLE WITH SEED PHRASES
DATA_AGENTS = {
    # Get these values from console output when running agents
    "price": "agent1qdckcdrtgfuqvj6f0txq77qz6tqgqhep5kfhf7xnfnqmynhdfptc89a2fx4",
    "sentiment": "agent1q0pf2lt7tdg0nxkuw33zylx3gtm39zcvqml257mvcmk5a0dzvg6kmqfm2e",
}

# Strategy agent addresses - WILL BE STABLE WITH SEED PHRASES
STRATEGY_AGENTS = {
    # Get these values from console  output when running agents
    "mean_reversion": "agent1qvx5w6z9f38t9m85k2nqzdsdh3auz30ag6szkkuyrr3lmtsmstssxrfk7l",
    "momentum": "agent1qwu2l8ayyr5xztyqqwpukzsrkyhd4t2g3s7jcduvn53qp0he5tjnq9gq4k",
    "sentiment_momentum": "agent1q0hwxnluasmvhlcxpcv2rj5zr4wpagrc6t8dzhwz42rk4k9v6drvkgn05d",
}

PENDING_REGISTRATIONS = []

# Run the agents and update the addresses before starting the meta agent

# Database connection
def get_db_connection():
    conn =  psycopg2.connect(
        dbname=os.getenv("DB_NAME", "myquant"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    DEC2FLOAT = psycopg2.extensions.new_type(
        psycopg2.extensions.DECIMAL.values,
        'DEC2FLOAT',
        lambda value, curs: float(value) if value is not None else None
    )
    psycopg2.extensions.register_type(DEC2FLOAT)

    return conn
    

# Initialize the database
def init_db():
    """Create tables if they don't exist"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create assets table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL UNIQUE,
                    name VARCHAR(255),
                    asset_type VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create market_data table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id SERIAL PRIMARY KEY,
                    asset_id VARCHAR(20) REFERENCES assets(ticker),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    price DECIMAL(20,8),
                    volume BIGINT,
                    sentiment_score DECIMAL(5,4),
                    sentiment_magnitude DECIMAL(5,4),
                    currency VARCHAR(10),
                    source VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asset_id, timestamp)
                )
            """)
            
            # Create predictions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    asset_id VARCHAR(20) REFERENCES assets(ticker),
                    strategy_name VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    prediction JSONB NOT NULL,
                    confidence DECIMAL(5,4) NOT NULL,
                    reasoning TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asset_id, strategy_name, timestamp)
                )
            """)
            
            # Create decisions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id SERIAL PRIMARY KEY,
                    asset_id VARCHAR(20) REFERENCES assets(ticker),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    confidence_score DECIMAL(5,4) NOT NULL,
                    reasoning TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create strategy_weights table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS strategy_weights (
                    id SERIAL PRIMARY KEY,
                    strategy_name VARCHAR(100) NOT NULL UNIQUE,
                    weight DECIMAL(5,4) NOT NULL DEFAULT 1.0,
                    performance_score DECIMAL(10,4),
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create performance_history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS performance_history (
                    id SERIAL PRIMARY KEY,
                    asset_id VARCHAR(20) REFERENCES assets(ticker),
                    strategy_name VARCHAR(100) NOT NULL,
                    prediction_id INTEGER REFERENCES predictions(id),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    predicted_action VARCHAR(20) NOT NULL,
                    actual_outcome DECIMAL(10,4),
                    performance_score DECIMAL(10,4),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize strategy weights if not exists
            for strategy in STRATEGY_AGENTS.keys():
                cur.execute("""
                    INSERT INTO strategy_weights (strategy_name, weight)
                    VALUES (%s, 1.0)
                    ON CONFLICT (strategy_name) DO NOTHING
                """, (strategy,))
            
            conn.commit()
    finally:
        conn.close()

# Initialize DB on startup
init_db()

@meta_agent.on_interval(period=30.0)  # Run every 30 seconds
async def analyze_investments(ctx: Context):
    """Main analysis loop that runs periodically"""
    # Get list of assets to analyze from database
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT ticker FROM assets")
            assets = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    
    # For each asset, get market data and analyze
    for asset_id in assets:
        timestamp = datetime.now().isoformat()
        
        # First, update performance of previous predictions
        await update_performance(ctx, asset_id)
        
        # Then, collect new data and make new predictions
        await collect_and_analyze(ctx, asset_id, timestamp)

# Handle price response
@meta_agent.on_message(PriceResponse)
async def handle_price_data(ctx: Context, sender: str, msg: PriceResponse):
    """Handle incoming price data"""
    ctx.logger.info(f"Received price data for {msg.ticker}")
    
    # Store price data in database
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO market_data 
                (asset_id, timestamp, price, volume, currency)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (asset_id, timestamp) 
                DO UPDATE SET price = EXCLUDED.price, volume = EXCLUDED.volume
            """, (
                msg.ticker,
                datetime.fromisoformat(msg.timestamp),
                msg.current_price,
                msg.volume,
                msg.currency
            ))
            conn.commit()
    finally:
        conn.close()
    
    # Request sentiment analysis
    await ctx.send(
        DATA_AGENTS["sentiment"],
        SentimentRequest(
            ticker=msg.ticker,
            timestamp=msg.timestamp
        )
    )

# Handle sentiment response
@meta_agent.on_message(SentimentResponse)
async def handle_sentiment_data(ctx: Context, sender: str, msg: SentimentResponse):
    """Handle incoming sentiment data"""
    ctx.logger.info(f"Received sentiment data for {msg.ticker}")
    
    # Store sentiment data in database
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO market_data 
                (asset_id, timestamp, sentiment_score, sentiment_magnitude)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (asset_id, timestamp) 
                DO UPDATE SET sentiment_score = EXCLUDED.sentiment_score, 
                              sentiment_magnitude = EXCLUDED.sentiment_magnitude
            """, (
                msg.ticker,
                datetime.fromisoformat(msg.timestamp),
                msg.sentiment_score,
                msg.sentiment_magnitude
            ))
            conn.commit()
            
            # Proceed with analysis after sentiment data is stored
            await perform_analysis(ctx, msg.ticker, msg.timestamp)
    finally:
        conn.close()

async def update_performance(ctx: Context, asset_id: str):
    """Update performance of previous predictions"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get previous predictions that need performance evaluation
            cur.execute("""
                SELECT p.id, p.strategy_name, p.prediction, p.timestamp
                FROM predictions p
                LEFT JOIN performance_history ph ON p.id = ph.prediction_id
                WHERE p.asset_id = %s 
                AND ph.id IS NULL
                AND p.timestamp < NOW() - INTERVAL '7 days'  -- Enough time to evaluate
            """, (asset_id,))
            
            predictions = cur.fetchall()
            
            for pred_id, strategy_name, prediction_json, pred_timestamp in predictions:
                prediction = json.loads(prediction_json)
                predicted_action = prediction.get("action", "hold")
                target_price = prediction.get("target_price")
                
                # Get actual price data from after the prediction
                cur.execute("""
                    SELECT price
                    FROM market_data
                    WHERE asset_id = %s AND timestamp > %s
                    ORDER BY timestamp
                    LIMIT 1
                """, (asset_id, pred_timestamp))
                
                before_price_row = cur.fetchone()
                before_price = before_price_row[0] if before_price_row else 0
                
                # Get current price (or most recent)
                cur.execute("""
                    SELECT price
                    FROM market_data
                    WHERE asset_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (asset_id,))
                
                current_price_row = cur.fetchone()
                current_price = current_price_row[0] if current_price_row else 0
                
                # Calculate actual price change
                price_change_pct = (current_price - before_price) / before_price if before_price > 0 else 0
                
                # Calculate performance score based on prediction accuracy
                performance_score = calculate_performance_score(predicted_action, target_price, before_price, current_price)
                
                # Store performance data
                cur.execute("""
                    INSERT INTO performance_history
                    (asset_id, strategy_name, prediction_id, timestamp, predicted_action, actual_outcome, performance_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    asset_id,
                    strategy_name,
                    pred_id,
                    pred_timestamp,
                    predicted_action,
                    price_change_pct,
                    performance_score
                ))
                
                # Update strategy weights based on performance
                await update_strategy_weight(cur, strategy_name, performance_score)
            
            conn.commit()
    finally:
        conn.close()

def calculate_performance_score(predicted_action: str, target_price: float, 
                               before_price: float, current_price: float) -> float:
    """Calculate a performance score for the prediction"""
    # Simple implementation - can be made more sophisticated
    price_change_pct = (current_price - before_price) / before_price if before_price > 0 else 0
    
    # For buy predictions, positive change is good
    if predicted_action == "buy":
        return price_change_pct
    # For sell predictions, negative change is good
    elif predicted_action == "sell":
        return -price_change_pct
    # For hold predictions, small change (either direction) is good
    else:
        return 1.0 - abs(price_change_pct)

async def update_strategy_weight(cursor, strategy_name: str, performance_score: float):
    """Update the weight of a strategy based on its performance"""
    # Get current weight
    cursor.execute("""
        SELECT weight
        FROM strategy_weights
        WHERE strategy_name = %s
    """, (strategy_name,))
    
    current_weight = cursor.fetchone()[0]
    
    # Update weight using a learning rate
    learning_rate = 0.1
    new_weight = current_weight * (1 + learning_rate * performance_score)
    
    # Ensure weight stays within reasonable bounds
    new_weight = max(0.1, min(2.0, new_weight))
    
    # Update the weight
    cursor.execute("""
        UPDATE strategy_weights
        SET weight = %s, performance_score = %s, last_updated = %s
        WHERE strategy_name = %s
    """, (new_weight, performance_score, datetime.now(), strategy_name))

async def collect_and_analyze(ctx: Context, asset_id: str, timestamp: str):
    """Collect fresh market data for an asset"""
    # First get price data
    await ctx.send(
        DATA_AGENTS["price"],
        PriceRequest(ticker=asset_id)
    )
    # Sentiment data will be requested in the price response handler
    # Analysis will be triggered in the sentiment response handler

async def perform_analysis(ctx: Context, asset_id: str, timestamp: str):
    """Perform analysis on an asset using all strategies"""
    # Get latest market data
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT price, volume, sentiment_score, sentiment_magnitude, currency, timestamp
                FROM market_data
                WHERE asset_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (asset_id,))
            latest_data = cur.fetchone()
            
            if not latest_data:
                ctx.logger.warning(f"No market data available for {asset_id}")
                return
            


            
            price, volume, sentiment_score, sentiment_magnitude, currency, data_timestamp = latest_data

            ctx.logger.info(f"[DEBUG] Latest market_data row for {asset_id}: " f"price={price!r}, sentiment={sentiment_score!r}, ts={data_timestamp!r}")
            
            # Get historical data
            cur.execute("""
                SELECT price, volume, sentiment_score, sentiment_magnitude, timestamp
                FROM market_data
                WHERE asset_id = %s
                ORDER BY timestamp DESC
                LIMIT 90
            """, (asset_id,))
            
            historical_rows = cur.fetchall()
            historical_data = [
                {
                    "price": row[0],
                    "volume": row[1],
                    "sentiment_score": row[2],
                    "sentiment_magnitude": row[3],
                    "timestamp": row[4].isoformat() if hasattr(row[4], 'isoformat') else str(row[4])
                }
                for row in historical_rows
            ]
    finally:
        conn.close()
    
    # Current market data
    current_data = {
        "price": price,
        "volume": volume,
        "sentiment_score": sentiment_score,
        "sentiment_magnitude": sentiment_magnitude,
        "currency": currency,
        "timestamp": data_timestamp.isoformat() if hasattr(data_timestamp, 'isoformat') else str(data_timestamp)
    }
    
    # Request analysis from each strategy agent
    predictions = []
    for strategy_name, agent_address in STRATEGY_AGENTS.items():
        ctx.logger.info(f"Requesting analysis from {strategy_name} for {asset_id}")
        
        try:
            # Send analysis request to strategy agent
            request = AnalysisRequest(
                asset_id=asset_id,
                timestamp=timestamp,
                current_data=current_data,
                historical_data=historical_data
            )
            
            # Send the request to the strategy agent
            await ctx.send(agent_address, request)
            ctx.logger.info(f"Sent analysis request to {strategy_name}")
            
            # NOTE: In a real system, we would await the response
            # For now, we'll use a simulated response for demonstration
            response = await simulate_strategy_response(strategy_name, asset_id, timestamp, current_data, historical_data)
            
            # Store prediction in database
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO predictions 
                        (asset_id, strategy_name, timestamp, prediction, confidence, reasoning)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        asset_id,
                        strategy_name,
                        datetime.now(),
                        json.dumps(response.prediction),
                        response.confidence,
                        response.reasoning
                    ))
                    conn.commit()
            finally:
                conn.close()
            
            predictions.append({
                "strategy": strategy_name,
                "prediction": response.prediction,
                "confidence": response.confidence,
                "reasoning": response.reasoning
            })
        
        except Exception as e:
            ctx.logger.error(f"Error getting prediction from {strategy_name}: {str(e)}")
    
    # Make meta-decision based on weighted predictions
    decision = await make_meta_decision(ctx, asset_id, timestamp, predictions)
    
    # Store decision
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO decisions 
                (asset_id, timestamp, action, confidence_score, reasoning)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                asset_id,
                datetime.now(),
                decision.action,
                decision.confidence,
                decision.reasoning
            ))
            conn.commit()
    finally:
        conn.close()
    
    ctx.logger.info(f"Decision for {asset_id}: {decision.action} (confidence: {decision.confidence})")

async def simulate_strategy_response(strategy_name: str, asset_id: str, timestamp: str, 
                                    current_data: Dict[str, Any], 
                                    historical_data: List[Dict[str, Any]]) -> StrategyResponse:
    """Simulate a response from a strategy agent (for demonstration)"""
    # In a real implementation, you would wait for the actual agent response
    # This is just a placeholder
    import random
    
    actions = ["buy", "sell", "hold"]
    confidence = random.uniform(0.5, 0.9)
    action = random.choice(actions)
    
    return StrategyResponse(
        asset_id=asset_id,
        timestamp=timestamp,
        prediction={
            "action": action,
            "target_price": current_data["price"] * (1 + random.uniform(-0.1, 0.1))
        },
        confidence=confidence,
        reasoning=f"Simulated {strategy_name} analysis",
        strategy_name=strategy_name
    )

async def make_meta_decision(ctx: Context, asset_id: str, timestamp: str, 
                           predictions: List[Dict[str, Any]]) -> MetaDecision:
    """Make a meta-decision based on weighted predictions from all strategies"""
    # Get strategy weights
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            strategy_weights = {}
            cur.execute("SELECT strategy_name, weight FROM strategy_weights")
            for row in cur.fetchall():
                strategy_weights[row[0]] = row[1]
    finally:
        conn.close()
    
    # Calculate weighted predictions
    weighted_predictions = []
    for pred in predictions:
        strategy = pred["strategy"]
        weight = strategy_weights.get(strategy, 1.0)
        weighted_predictions.append({
            "strategy": strategy,
            "prediction": pred["prediction"],
            "confidence": pred["confidence"],
            "weight": weight,
            "weighted_confidence": pred["confidence"] * weight
        })
    
    # Aggregate predictions
    buy_confidence = sum(wp["weighted_confidence"] for wp in weighted_predictions 
                        if wp["prediction"]["action"] == "buy")
    sell_confidence = sum(wp["weighted_confidence"] for wp in weighted_predictions 
                         if wp["prediction"]["action"] == "sell")
    hold_confidence = sum(wp["weighted_confidence"] for wp in weighted_predictions 
                         if wp["prediction"]["action"] == "hold")
    
    total_weighted_confidence = buy_confidence + sell_confidence + hold_confidence
    
    if total_weighted_confidence == 0:
        action = "hold"
        confidence = 0.5
        reasoning = "No confident predictions available"
    else:
        # Normalize confidence scores
        buy_score = buy_confidence / total_weighted_confidence
        sell_score = sell_confidence / total_weighted_confidence
        hold_score = hold_confidence / total_weighted_confidence
        
        # Decision rules
        confidence_threshold = 0.4  # Minimum confidence to make a decision
        
        if buy_score > confidence_threshold and buy_score > sell_score and buy_score > hold_score:
            action = "buy"
            confidence = buy_score
        elif sell_score > confidence_threshold and sell_score > buy_score and sell_score > hold_score:
            action = "sell"
            confidence = sell_score
        else:
            action = "hold"
            confidence = max(hold_score, 0.5)  # Default to at least 0.5 confidence for holds
        
        # Generate reasoning text
        reasoning = (
            f"Buy confidence: {buy_score:.2f}, Sell confidence: {sell_score:.2f}, Hold confidence: {hold_score:.2f}\n"
            f"Based on {len(predictions)} strategy predictions with relative weights."
        )
    
    return MetaDecision(
        asset_id=asset_id,
        timestamp=timestamp,
        action=action,
        confidence=confidence,
        reasoning=reasoning,
        predictions=predictions,
        weighted_predictions=weighted_predictions
    )


@meta_agent.on_event("startup")
async def register_agents(ctx: Context):
    for address, endpoint in PENDING_REGISTRATIONS:
        ctx.register(address, endpoint)
    ctx.logger.info(f"Registered {len(PENDING_REGISTRATIONS)} strategy agents.")



# testing this 

def set_strategy_addresses(addresses_and_endpoints):
    global STRATEGY_AGENTS
    STRATEGY_AGENTS.clear()

    for strat_name, info in addresses_and_endpoints.items():
        STRATEGY_AGENTS[strat_name] = info["address"]

if __name__ == "__main__":
    meta_agent.run() 