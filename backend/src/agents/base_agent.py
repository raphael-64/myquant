from uagents import Agent, Context, Model, Bureau
from uagents.setup import fund_agent_if_low
from typing import Dict, List, Optional, Any
import uuid
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class AgentResponse(Model):
    asset_id: str
    timestamp: str
    prediction: Dict[str, Any]
    confidence: float
    reasoning: str
    strategy_name: str

class AnalysisRequest(Model):
    asset_id: str
    current_data: Dict[str, Any]
    historical_data: Optional[List[Dict[str, Any]]] = None

class BaseStrategyAgent:
    """Base class for all strategy agents"""
    
    def __init__(self, strategy_name: str, port: int):
        self.strategy_name = strategy_name
        self.agent_id = f"{strategy_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Create a seed phrase for consistent agent address
        seed = f"{strategy_name.lower().replace(' ', '_')}_seed_phrase"
        
        self.agent = Agent(
            name=self.agent_id,
            port=port,
            endpoint=[f"http://localhost:{port}/submit"],
            seed=seed,  # Use consistent seed for stable address
        )
        
        # Fund the agent if needed
        fund_agent_if_low(self.agent.wallet.address())
        
        # Print agent information for discovery
        print(f"Strategy agent: {self.strategy_name}")
        print(f"Address: {self.agent.address}")
        print(f"Endpoint: http://localhost:{port}/submit")
        
        # Register message handler
        @self.agent.on_message(AnalysisRequest)
        async def handle_request(ctx: Context, sender: str, msg: AnalysisRequest):
            try:
                # Process the request using the strategy-specific implementation
                prediction, confidence, reasoning = self.analyze(
                    msg.asset_id, 
                    msg.current_data, 
                    msg.historical_data
                )
                
                # Return the response
                await ctx.send(
                    sender,
                    AgentResponse(
                        asset_id=msg.asset_id,
                        timestamp=msg.current_data.get("timestamp", ""),
                        prediction=prediction,
                        confidence=confidence,
                        reasoning=reasoning,
                        strategy_name=self.strategy_name
                    )
                )
                
                ctx.logger.info(f"Analysis completed for {msg.asset_id} using {self.strategy_name}")
                
            except Exception as e:
                ctx.logger.error(f"Error analyzing {msg.asset_id}: {str(e)}")
                # Send error response
                await ctx.send(
                    sender,
                    AgentResponse(
                        asset_id=msg.asset_id,
                        timestamp=msg.current_data.get("timestamp", ""),
                        prediction={"error": str(e), "action": "hold"},
                        confidence=0.0,
                        reasoning=f"Error occurred: {str(e)}",
                        strategy_name=self.strategy_name
                    )
                )
    
    def analyze(self, asset_id: str, current_data: Dict[str, Any], 
                historical_data: Optional[List[Dict[str, Any]]] = None) -> tuple:
        """
        Implement this method in each strategy subclass.
        
        Args:
            asset_id: The identifier for the asset
            current_data: Current market data for the asset
            historical_data: Optional historical data
            
        Returns:
            tuple: (prediction_dict, confidence_score, reasoning_text)
        """
        raise NotImplementedError("Each strategy must implement its own analyze method")
    
    def run(self):
        """Start the agent"""
        self.agent.run()
    
    def get_agent(self):
        """Return the agent instance for bureau registration"""
        return self.agent 