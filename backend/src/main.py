"""
Main entry point for the multi-agent system
This file coordinates all agents using Bureau for proper management
"""

import os
import sys
import asyncio
from uagents import Bureau
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Import strategy agents
from src.agents.strategies.momentum import MomentumAgent
from src.agents.strategies.mean_reversion import MeanReversionAgent
from src.agents.strategies.sentiment_momentum import SentimentMomentumAgent
from src.agents.data.price_agent import price_agent       # ← your data agents
from src.agents.data.sentiment_agent import sentiment_agent

from src.orchestrator.meta_agent import set_strategy_addresses

# Import orchestrator
from src.orchestrator.meta_agent import meta_agent

def main():
    """Main entry point for the application"""
    print("Starting MultiAgent Quantitative Trading System")
    
    # Create Bureau for agent coordination
    # bureau = Bureau()
    bureau = Bureau(endpoint=["http://localhost:8000/submit"])

    # 3) instantiate strategy agents
    momentum          = MomentumAgent(port=8101)
    mean_reversion    = MeanReversionAgent(port=8102)
    sentiment_mom     = SentimentMomentumAgent(port=8103)

    # 4) add _everybody_ into the same Bureau
    bureau.add(price_agent)
    bureau.add(sentiment_agent)
    # bureau.add(price_agent.get_agent())
    # bureau.add(sentiment_agent.get_agent())
    bureau.add(momentum.get_agent())
    bureau.add(mean_reversion.get_agent())
    bureau.add(sentiment_mom.get_agent())
    bureau.add(meta_agent)


#    5) override DATA_AGENTS in your orchestrator so meta knows where to send price/sentiment
    import src.orchestrator.meta_agent as orchestrator
    orchestrator.DATA_AGENTS = {
        "price":     price_agent.address,
        "sentiment": sentiment_agent.address
    }   
    
    # Initialize all strategy agents
    momentum = MomentumAgent(port=8101)
    mean_reversion = MeanReversionAgent(port=8102)
    sentiment_momentum = SentimentMomentumAgent(port=8103)
    
    # Add all agents to the bureau
    bureau.add(momentum.get_agent())
    bureau.add(mean_reversion.get_agent())
    bureau.add(sentiment_momentum.get_agent())
    bureau.add(meta_agent)
    
    # Print agent addresses for reference
    print("\nAgent Addresses:")
    print(f"Momentum Agent: {momentum.get_agent().address}")
    print(f"Mean Reversion Agent: {mean_reversion.get_agent().address}")
    print(f"Sentiment Momentum Agent: {sentiment_momentum.get_agent().address}")
    print(f"Meta Agent: {meta_agent.address}")

    # addresses = {
    # "mean_reversion": mean_reversion.get_agent().address,
    # "momentum": momentum.get_agent().address,
    # "sentiment_momentum": sentiment_momentum.get_agent().address
    # }

    addresses = {
    "momentum": {
        "address": momentum.get_agent().address,
        "endpoint": "http://localhost:8101/submit"
    },
    "mean_reversion": {
        "address": mean_reversion.get_agent().address,
        "endpoint": "http://localhost:8102/submit"
    },
    "sentiment_momentum": {
        "address": sentiment_momentum.get_agent().address,
        "endpoint": "http://localhost:8103/submit"
    }
}

    set_strategy_addresses(addresses)
    
    # Run the bureau
    bureau.run()

if __name__ == "__main__":
    main() 