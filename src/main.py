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

from src.orchestrator.meta_agent import set_strategy_addresses

# Import orchestrator
from src.orchestrator.meta_agent import meta_agent

def main():
    """Main entry point for the application"""
    print("Starting MultiAgent Quantitative Trading System")
    
    # Create Bureau for agent coordination
    # bureau = Bureau()
    bureau = Bureau(endpoint=["http://localhost:8000/submit"])
    
    # Initialize all strategy agents
    momentum = MomentumAgent(port=8101)
    mean_reversion = MeanReversionAgent(port=8102)
    sentiment_momentum = SentimentMomentumAgent(port=8103)


    # Print agent addresses for reference
    print("\nAgent Addresses:")
    print(f"Momentum Agent: {momentum.get_agent().address}")
    print(f"Mean Reversion Agent: {mean_reversion.get_agent().address}")
    print(f"Sentiment Momentum Agent: {sentiment_momentum.get_agent().address}")
    print(f"Meta Agent: {meta_agent.address}")

    addresses = {
    "mean_reversion": mean_reversion.get_agent().address,
    "momentum": momentum.get_agent().address,
    "sentiment_momentum": sentiment_momentum.get_agent().address
    }
    
    set_strategy_addresses(addresses)
    
    # Add all agents to the bureau
    bureau.add(momentum.get_agent())
    bureau.add(mean_reversion.get_agent())
    bureau.add(sentiment_momentum.get_agent())
    bureau.add(meta_agent)
    

    
    # Run the bureau
    bureau.run()

if __name__ == "__main__":
    main() 