from src.agents.base_agent import BaseStrategyAgent
from typing import Dict, List, Optional, Any
import numpy as np
from scipy import stats

class MomentumAgent(BaseStrategyAgent):
    """
    Momentum Strategy Agent
    
    This strategy is based on the premise that assets that have performed well in the past 
    will continue to perform well in the near future, and assets that have performed poorly 
    will continue to underperform.
    """
    
    def __init__(self, port: int = 8102):
        super().__init__("Momentum", port)
        
        # Strategy-specific parameters
        self.short_window = 10    # Days for short-term momentum
        self.medium_window = 30   # Days for medium-term momentum
        self.long_window = 90     # Days for long-term momentum
        self.momentum_threshold = 0.05  # 5% threshold for significant momentum
    
    def analyze(self, asset_id: str, current_data: Dict[str, Any], 
                historical_data: Optional[List[Dict[str, Any]]] = None) -> tuple:
        """
        Analyze the asset using momentum strategy
        
        Args:
            asset_id: The asset identifier
            current_data: Current market data
            historical_data: Historical price data
            
        Returns:
            tuple: (prediction_dict, confidence_score, reasoning_text)
        """
        if not historical_data or len(historical_data) < self.long_window:
            return (
                {"action": "hold", "target_price": None}, 
                0.0,
                "Insufficient historical data for momentum analysis"
            )
        
        # Sort historical data by timestamp (newest last)
        sorted_data = sorted(historical_data, key=lambda x: x.get("timestamp", ""))
        
        # Extract closing prices
        prices = np.array([float(data.get("price", 0)) for data in sorted_data])
        current_price = float(current_data.get("price", 0))
        
        # Calculate returns for different windows
        short_return = self._calculate_return(prices, self.short_window)
        medium_return = self._calculate_return(prices, self.medium_window)
        long_return = self._calculate_return(prices, self.long_window)
        
        # Weight the returns (giving more importance to recent momentum)
        weighted_momentum = (0.5 * short_return + 0.3 * medium_return + 0.2 * long_return)
        
        # Make prediction based on weighted momentum
        if weighted_momentum > self.momentum_threshold:
            # Strong positive momentum
            action = "buy"
            # Project future price based on momentum
            target_price = current_price * (1 + weighted_momentum / 2)
            confidence = min(0.9, weighted_momentum * 5)  # Scale confidence based on momentum strength
        elif weighted_momentum < -self.momentum_threshold:
            # Strong negative momentum
            action = "sell"
            # Project future price based on momentum
            target_price = current_price * (1 + weighted_momentum / 2)
            confidence = min(0.9, abs(weighted_momentum) * 5)  # Scale confidence based on momentum strength
        else:
            # Weak or mixed momentum
            action = "hold"
            target_price = current_price
            confidence = 0.5
        
        # Calculate additional metrics for reasoning
        volatility = np.std(prices[-30:]) / np.mean(prices[-30:]) if len(prices) >= 30 else 0
        
        # Prepare prediction and reasoning
        prediction = {
            "action": action,
            "target_price": target_price,
            "momentum_strength": weighted_momentum,
            "timeframe": "14 days"  # Standard momentum timeframe
        }
        
        reasoning = (
            f"Short-term momentum ({self.short_window} days): {short_return:.2%}\n"
            f"Medium-term momentum ({self.medium_window} days): {medium_return:.2%}\n"
            f"Long-term momentum ({self.long_window} days): {long_return:.2%}\n"
            f"Weighted momentum: {weighted_momentum:.2%} (threshold: ±{self.momentum_threshold:.2%})\n"
            f"30-day volatility: {volatility:.2%}"
        )
        
        return prediction, confidence, reasoning
    
    def _calculate_return(self, prices: np.ndarray, window: int) -> float:
        """Calculate the return over the specified window"""
        if len(prices) < window:
            return 0.0
        
        # Get price at start and end of window
        start_price = prices[-window]
        end_price = prices[-1]
        
        # Avoid division by zero
        if start_price == 0:
            return 0.0
            
        # Calculate return
        return (end_price - start_price) / start_price

if __name__ == "__main__":
    # Run the agent if the script is executed directly
    agent = MomentumAgent()
    agent.run() 