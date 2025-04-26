
from src.agents.base_agent import BaseStrategyAgent
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime, timedelta

class SentimentMomentumAgent(BaseStrategyAgent):
    """
    News Sentiment-Driven Momentum Strategy
    
    This strategy combines news sentiment analysis with price momentum to identify
    potential trading opportunities. It looks for assets where positive sentiment 
    coincides with positive price momentum, or negative sentiment with negative momentum.
    """
    
    def __init__(self, port: int = 8103):
        super().__init__("Sentiment Momentum", port)
        
        # Strategy-specific parameters
        self.sentiment_threshold = 0.3    # Threshold for significant sentiment
        self.momentum_window = 5          # Days for price momentum calculation
        self.sentiment_window = 3         # Days for sentiment analysis
        self.confidence_multiplier = 0.8  # Factor to adjust confidence
    
    def analyze(self, asset_id: str, current_data: Dict[str, Any], 
                historical_data: Optional[List[Dict[str, Any]]] = None) -> tuple:
        """
        Analyze the asset using sentiment-driven momentum strategy
        
        Args:
            asset_id: The asset identifier
            current_data: Current market data with sentiment
            historical_data: Historical price and sentiment data
            
        Returns:
            tuple: (prediction_dict, confidence_score, reasoning_text)
        """
        if not historical_data or len(historical_data) < self.momentum_window:
            return (
                {"action": "hold", "target_price": None}, 
                0.0,
                "Insufficient historical data for sentiment momentum analysis"
            )
        
        # Sort historical data by timestamp (newest last)
        sorted_data = sorted(historical_data, key=lambda x: x.get("timestamp", ""))
        
        # Extract sentiment and price data
        current_sentiment = current_data.get("sentiment_score", 0)
        current_price = current_data.get("price", 0)
        
        prices = [data.get("price", 0) for data in sorted_data[-self.momentum_window:]]
        sentiments = [data.get("sentiment_score", 0) for data in sorted_data[-self.sentiment_window:]]
        
        # Calculate price momentum (percent change)
        start_price = prices[0] if prices else 0
        momentum = (current_price - start_price) / start_price if start_price != 0 else 0
        
        # Calculate average recent sentiment
        avg_sentiment = np.mean(sentiments) if sentiments else 0
        
        # Combined signal: sentiment aligned with momentum direction
        sentiment_momentum_alignment = momentum * avg_sentiment
        
        # Determine action based on alignment and strength
        if avg_sentiment > self.sentiment_threshold and momentum > 0:
            # Positive sentiment and positive momentum
            action = "buy"
            projected_return = momentum * avg_sentiment * 2  # Project higher based on alignment
            target_price = current_price * (1 + projected_return)
            confidence = min(0.9, abs(avg_sentiment * self.confidence_multiplier))
        elif avg_sentiment < -self.sentiment_threshold and momentum < 0:
            # Negative sentiment and negative momentum
            action = "sell"
            projected_return = momentum * avg_sentiment * 2  # Project lower based on alignment
            target_price = current_price * (1 + projected_return)
            confidence = min(0.9, abs(avg_sentiment * self.confidence_multiplier))
        else:
            # Mixed or weak signals
            action = "hold"
            target_price = current_price
            confidence = 0.5
        
        # Prepare prediction and reasoning
        prediction = {
            "action": action,
            "target_price": target_price,
            "sentiment_strength": avg_sentiment,
            "price_momentum": momentum,
            "timeframe": "7 days"  # Expected timeframe for the prediction
        }
        
        reasoning = (
            f"Current sentiment: {current_sentiment:.2f}\n"
            f"{self.sentiment_window}-day average sentiment: {avg_sentiment:.2f}\n"
            f"{self.momentum_window}-day price momentum: {momentum:.2%}\n"
            f"Sentiment-momentum alignment: {sentiment_momentum_alignment:.4f}\n"
            f"Sentiment threshold: ±{self.sentiment_threshold:.2f}"
        )
        
        return prediction, confidence, reasoning

if __name__ == "__main__":
    # Run the agent if the script is executed directly
    agent = SentimentMomentumAgent()
    agent.run() 