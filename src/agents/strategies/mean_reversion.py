from src.agents.base_agent import BaseStrategyAgent
from typing import Dict, List, Optional, Any
import numpy as np
from scipy import stats

class MeanReversionAgent(BaseStrategyAgent):
    """
    Mean Reversion Strategy Agent
    
    This strategy is based on the concept that asset prices tend to revert to their mean over time.
    When an asset's price deviates significantly from its historical average, it suggests
    a potential mean reversion opportunity.
    """
    
    def __init__(self, port: int = 8101):
        super().__init__("Mean Reversion", port)
        
        # Strategy-specific parameters
        self.z_score_threshold = 2.0  # Standard deviations from mean to trigger signal
        self.lookback_period = 30     # Days to use for calculating the mean
    
    def analyze(self, asset_id: str, current_data: Dict[str, Any], 
                historical_data: Optional[List[Dict[str, Any]]] = None) -> tuple:
        """
        Analyze the asset using mean reversion strategy
        
        Args:
            asset_id: The asset identifier
            current_data: Current market data
            historical_data: Historical price data
            
        Returns:
            tuple: (prediction_dict, confidence_score, reasoning_text)
        """
        if not historical_data or len(historical_data) < self.lookback_period:
            return (
                {"action": "hold", "target_price": None}, 
                0.0,
                "Insufficient historical data for mean reversion analysis"
            )
        
        # Extract closing prices from historical data
        prices = [data.get("price", 0) for data in historical_data]
        
        # Calculate mean and standard deviation
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        # Get current price
        current_price = current_data.get("price", 0)
        
        # Calculate Z-score (how many standard deviations from the mean)
        if std_price == 0:  # Avoid division by zero
            z_score = 0
        else:
            z_score = (current_price - mean_price) / std_price
        
        # Make prediction based on Z-score
        if z_score > self.z_score_threshold:
            # Price is significantly above mean, expect reversion downward
            action = "sell"
            target_price = mean_price
            confidence = min(0.9, abs(z_score) / 5)  # Scale confidence based on deviation
        elif z_score < -self.z_score_threshold:
            # Price is significantly below mean, expect reversion upward
            action = "buy"
            target_price = mean_price
            confidence = min(0.9, abs(z_score) / 5)  # Scale confidence based on deviation
        else:
            # Price is within normal range
            action = "hold"
            target_price = current_price
            confidence = 0.5
        
        # Calculate additional statistical metrics for reasoning
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed p-value
        
        # Prepare prediction and reasoning
        prediction = {
            "action": action,
            "target_price": target_price,
            "expected_reversion": mean_price,
            "timeframe": f"{self.lookback_period // 2} days"  # Expect reversion in half the lookback period
        }
        
        reasoning = (
            f"Z-Score: {z_score:.2f} (threshold: ±{self.z_score_threshold})\n"
            f"Current price: {current_price} vs Historical mean: {mean_price:.2f}\n"
            f"Standard deviation: {std_price:.2f}\n"
            f"Statistical significance: p-value = {p_value:.4f}\n"
            f"Based on {self.lookback_period}-day historical data"
        )
        
        return prediction, confidence, reasoning

if __name__ == "__main__":
    # Run the agent if the script is executed directly
    agent = MeanReversionAgent()
    agent.run() 