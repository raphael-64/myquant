from typing import Dict, TypedDict, List
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
import psycopg2
from datetime import datetime
import json
import pprint

# Define the state that will be passed between nodes
class AgentState(TypedDict):
    messages: List[HumanMessage | AIMessage]
    current_asset: str
    market_data: Dict
    predictions: List[Dict]
    decision: Dict
    performance_metrics: Dict

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname="investment_db",
        user="postgres",
        password="your_password",
        host="localhost"
    )

# Tools for interacting with the database
# @tool
# def fetch_market_data(asset_id: str) -> Dict:
#     """Fetch latest market data for an asset"""
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 SELECT * FROM market_data 
#                 WHERE asset_id = %s 
#                 ORDER BY timestamp DESC 
#                 LIMIT 1
#             """, (asset_id,))
#             return cur.fetchone()
#     finally:
#         conn.close()
def fetch_market_data(asset_id: str) -> Dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM market_data 
                WHERE asset_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (asset_id,))
            row = cur.fetchone()
            if row is None:
                return {}
            colnames = [desc[0] for desc in cur.description]
            return dict(zip(colnames, row))
    finally:
        conn.close()

# @tool
def get_analysis_strategies() -> List[Dict]:
    """Get all available analysis strategies"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysis_strategies")
            return cur.fetchall()
    finally:
        conn.close()

# @tool
def store_prediction(asset_id: str, strategy_id: int, prediction: Dict) -> None:
    """Store a new prediction in the database"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO predictions 
                (asset_id, strategy_id, timestamp, prediction_type, prediction_value, confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                asset_id,
                strategy_id,
                datetime.now(),
                prediction['type'],
                json.dumps(prediction['value']),
                prediction['confidence']
            ))
            conn.commit()
    finally:
        conn.close()

# Define the nodes in our graph
def data_collection_node(state: AgentState) -> AgentState:
    """Node for collecting market data"""
    # Fetch market data using your existing uAgents
    market_data = fetch_market_data(state["current_asset"])
    return {**state, "market_data": market_data}

def analysis_node(state: AgentState) -> AgentState:
    """Node for running analysis strategies"""
    strategies = get_analysis_strategies()
    predictions = []
    
    for strategy in strategies:
        # Here you would call your analysis agents
        # For now, we'll use a placeholder
        prediction = {
            "strategy_id": strategy["id"],
            "type": "price_prediction",
            "value": {"predicted_price": 100.0},
            "confidence": 0.85
        }
        store_prediction(state["current_asset"], strategy["id"], prediction)
        predictions.append(prediction)
    
    return {**state, "predictions": predictions}

def decision_node(state: AgentState) -> AgentState:
    """Node for making investment decisions"""
    # Get weights for each strategy
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM decision_weights")
            weights = cur.fetchall()
    finally:
        conn.close()
    
    # Calculate weighted decision
    weighted_predictions = []
    for pred in state["predictions"]:
        weight = next((w["weight"] for w in weights if w["strategy_id"] == pred["strategy_id"]), 0.5)
        weighted_predictions.append({
            "prediction": pred,
            "weight": weight
        })
    
    # Make decision based on weighted predictions
    decision = {
        "action": "buy",  # This would be calculated based on your logic
        "confidence": 0.8,
        "reasoning": "Weighted analysis suggests upward movement"
    }
    
    return {**state, "decision": decision}

def performance_tracking_node(state: AgentState) -> AgentState:
    """Node for tracking performance and updating weights"""
    # Store the decision
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO decisions 
                (asset_id, timestamp, action, confidence_score, reasoning)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                state["current_asset"],
                datetime.now(),
                state["decision"]["action"],
                state["decision"]["confidence"],
                state["decision"]["reasoning"]
            ))
            decision_id = cur.fetchone()[0]
            
            # Update weights based on performance
            # This is where you'd implement your pseudo-backpropagation
            for pred in state["predictions"]:
                performance_score = 0.8  # This would be calculated based on actual outcomes
                cur.execute("""
                    UPDATE decision_weights 
                    SET weight = weight * %s,
                        last_updated = %s
                    WHERE strategy_id = %s
                """, (performance_score, datetime.now(), pred["strategy_id"]))
            
            conn.commit()
    finally:
        conn.close()
    
    return state

# Create the graph
def create_investment_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("data_collection_node", data_collection_node)
    workflow.add_node("analysis_node", analysis_node)
    workflow.add_node("decision_node", decision_node)
    workflow.add_node("performance_tracking_node", performance_tracking_node)
    
    # Define edges
    workflow.add_edge("data_collection_node", "analysis_node")
    workflow.add_edge("analysis_node", "decision_node")
    workflow.add_edge("decision_node", "performance_tracking_node")
    
    # Set entry point
    workflow.set_entry_point("data_collection_node")
    
    # Compile the graph
    return workflow.compile()

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create analysis_strategies table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_strategies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                )
            """)
            # Create decision_weights table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS decision_weights (
                    id SERIAL PRIMARY KEY,
                    strategy_name VARCHAR(100),
                    weight DECIMAL,
                    last_updated TIMESTAMP
                )
            """)
            # Add other CREATE TABLE IF NOT EXISTS statements as needed
            conn.commit()
    finally:
        conn.close()

# Example usage
if __name__ == "__main__":
    init_db()
    # Initialize the graph
    graph = create_investment_graph()
    
    # Run the graph for a specific asset
    initial_state = {
        "messages": [],
        "current_asset": "AAPL",
        "market_data": {},
        "predictions": [],
        "decision": {},
        "performance_metrics": {}
    }
    
    result = graph.invoke(initial_state)
    pprint.pprint(result)              
    # print("Final state:", result)