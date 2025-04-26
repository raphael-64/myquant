import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestrator.meta_agent import get_db_connection

def register_asset(ticker: str, name: str, asset_type: str = "stock"):
    """Register a new asset in the database"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assets (ticker, name, asset_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (ticker) DO NOTHING
            """, (ticker, name, asset_type))
            conn.commit()
            print(f"Successfully registered {ticker} ({name}) in the database")
    finally:
        conn.close()

if __name__ == "__main__":
    # Register AAPL
    register_asset("MMM", "3M Company")