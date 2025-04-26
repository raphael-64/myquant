"""
Comprehensive test script for testing agents in the multi-agent system
This script provides functions to test individual agents and their interactions
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime, timedelta
import random
from pprint import pprint
from typing import Dict, List, Any, Optional
from uagents import Agent, Context, Model, Bureau

# Import agent models
from src.agents.base_agent import AnalysisRequest, AgentResponse
from src.agents.strategies.momentum import MomentumAgent
from src.agents.strategies.mean_reversion import MeanReversionAgent
from src.agents.strategies.sentiment_momentum import SentimentMomentumAgent

# Test cases
TEST_ASSETS = ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN"]

# Sample data generator
def generate_sample_data(ticker: str, days: int = 90, with_sentiment: bool = False):
    """Generate sample price and optional sentiment data for testing"""
    base_price = random.uniform(100.0, 500.0)  # Random starting price
    current_price = base_price
    historical_data = []
    
    # Generate historical data with some randomness and trend
    now = datetime.now()
    
    # Generate a random trend type
    trend_type = random.choice(["uptrend", "downtrend", "volatile", "sideways"])
    
    for i in range(days, 0, -1):
        # Base change component
        base_change = random.uniform(-2.0, 2.0)
        
        # Add trend component based on trend type
        if trend_type == "uptrend":
            trend = random.uniform(0.1, 0.5)
        elif trend_type == "downtrend":
            trend = random.uniform(-0.5, -0.1)
        elif trend_type == "volatile":
            trend = random.uniform(-1.0, 1.0)
        else:  # sideways
            trend = random.uniform(-0.1, 0.1)
        
        price = current_price + base_change + trend
        current_price = max(0.01, price)  # Ensure price doesn't go negative
        
        timestamp = (now - timedelta(days=i)).isoformat()
        
        data_point = {
            "price": price,
            "volume": random.randint(1000000, 10000000),
            "timestamp": timestamp
        }
        
        # Add sentiment if requested
        if with_sentiment:
            # For testing, sentiment can be correlated or anti-correlated with price
            if random.random() > 0.3:  # 70% chance of correlation
                sentiment = 0.5 + ((price - base_price) / base_price)
                sentiment = max(-1.0, min(1.0, sentiment))  # Clamp to [-1.0, 1.0]
            else:
                sentiment = random.uniform(-1.0, 1.0)
                
            data_point["sentiment_score"] = sentiment
            data_point["sentiment_magnitude"] = abs(sentiment) * random.uniform(0.5, 1.0)
        
        historical_data.append(data_point)
    
    # Current data (most recent point)
    current_data = {
        "price": current_price + random.uniform(-1.0, 1.0),
        "volume": random.randint(1000000, 10000000),
        "timestamp": now.isoformat()
    }
    
    # Add sentiment to current data if requested
    if with_sentiment:
        if random.random() > 0.3:  # 70% chance of correlation
            sentiment = 0.5 + ((current_data["price"] - base_price) / base_price)
            sentiment = max(-1.0, min(1.0, sentiment))  # Clamp to [-1.0, 1.0]
        else:
            sentiment = random.uniform(-1.0, 1.0)
            
        current_data["sentiment_score"] = sentiment
        current_data["sentiment_magnitude"] = abs(sentiment) * random.uniform(0.5, 1.0)
    
    return current_data, historical_data, trend_type

# Tester agent class
class AgentTester:
    def __init__(self, agent_name: str, agent_address: str, port: int = 8900):
        self.agent_name = agent_name
        self.agent_address = agent_address
        self.responses = []
        
        # Create test agent
        self.agent = Agent(
            name=f"tester_{agent_name}",
            port=port,
            endpoint=[f"http://localhost:{port}/submit"],
        )
        
        # Define response handler
        @self.agent.on_message(AgentResponse)
        async def on_response(ctx: Context, sender: str, msg: AgentResponse):
            self.responses.append(msg)
            ctx.logger.info(f"Received response from {msg.strategy_name}")
            ctx.logger.info(f"Asset: {msg.asset_id}")
            ctx.logger.info(f"Action: {msg.prediction.get('action')}")
            ctx.logger.info(f"Confidence: {msg.confidence}")
            ctx.logger.info(f"Reasoning:\n{msg.reasoning}")
            ctx.logger.info("-" * 50)
    
    async def test_agent(self, asset_id: str, with_sentiment: bool = False):
        """Test an agent with sample data"""
        print(f"\nTesting {self.agent_name} agent with {asset_id}...")
        
        # Generate sample data
        current_data, historical_data, trend_type = generate_sample_data(
            asset_id, days=120, with_sentiment=with_sentiment
        )
        
        print(f"Generated {len(historical_data)} days of historical data")
        print(f"Trend type: {trend_type}")
        print(f"Current price: {current_data['price']:.2f}")
        
        # Create request
        request = AnalysisRequest(
            asset_id=asset_id,
            current_data=current_data,
            historical_data=historical_data
        )
        
        # Send request
        await self.agent.context.send(self.agent_address, request)
        print(f"Request sent to {self.agent_name} agent")
        
        # Wait for response
        await asyncio.sleep(2)
        
        return self.responses[-1] if self.responses else None

# Test strategies
async def test_momentum_strategy():
    """Test the momentum strategy agent"""
    print("\n===== TESTING MOMENTUM STRATEGY =====")
    
    # Start agent
    momentum_agent = MomentumAgent(port=8101)
    
    # Start tester
    tester = AgentTester("momentum", momentum_agent.get_agent().address, port=8901)
    
    # Create bureau
    bureau = Bureau(endpoint=["http://localhost:8101/submit"])
    bureau.add(momentum_agent.get_agent())
    bureau.add(tester.agent)
    
    # Run bureau in background
    bureau_task = asyncio.create_task(bureau.run())
    
    try:
        # Give agents time to start
        await asyncio.sleep(2)
        
        # Test with different assets
        results = []
        for asset in TEST_ASSETS:
            response = await tester.test_agent(asset)
            if response:
                results.append({
                    "asset": asset,
                    "action": response.prediction.get("action"),
                    "confidence": response.confidence,
                    "momentum_strength": response.prediction.get("momentum_strength", 0)
                })
        
        print("\nMomentum Strategy Results:")
        pprint(results)
        
        # Give some time for logs to print
        await asyncio.sleep(1)
        
    finally:
        # Stop the bureau
        bureau_task.cancel()
        try:
            await bureau_task
        except asyncio.CancelledError:
            pass

async def test_mean_reversion_strategy():
    """Test the mean reversion strategy agent"""
    print("\n===== TESTING MEAN REVERSION STRATEGY =====")
    
    # Start agent
    mean_reversion_agent = MeanReversionAgent(port=8102)
    
    # Start tester
    tester = AgentTester("mean_reversion", mean_reversion_agent.get_agent().address, port=8902)
    
    # Create bureau
    bureau = Bureau(endpoint=["http://localhost:8101/submit"])
    bureau.add(mean_reversion_agent.get_agent())
    bureau.add(tester.agent)
    
    # Run bureau in background
    bureau_task = asyncio.create_task(bureau.run())
    
    try:
        # Give agents time to start
        await asyncio.sleep(2)
        
        # Test with different assets
        results = []
        for asset in TEST_ASSETS:
            response = await tester.test_agent(asset)
            if response:
                results.append({
                    "asset": asset,
                    "action": response.prediction.get("action"),
                    "confidence": response.confidence,
                    "expected_reversion": response.prediction.get("expected_reversion")
                })
        
        print("\nMean Reversion Strategy Results:")
        pprint(results)
        
        # Give some time for logs to print
        await asyncio.sleep(1)
        
    finally:
        # Stop the bureau
        bureau_task.cancel()
        try:
            await bureau_task
        except asyncio.CancelledError:
            pass

async def test_sentiment_momentum_strategy():
    """Test the sentiment momentum strategy agent"""
    print("\n===== TESTING SENTIMENT MOMENTUM STRATEGY =====")
    
    # Start agent
    sentiment_momentum_agent = SentimentMomentumAgent(port=8103)
    
    # Start tester
    tester = AgentTester("sentiment_momentum", sentiment_momentum_agent.get_agent().address, port=8903)
    
    # Create bureau
    bureau = Bureau(endpoint=["http://localhost:8101/submit"])
    bureau.add(sentiment_momentum_agent.get_agent())
    bureau.add(tester.agent)
    
    # Run bureau in background
    bureau_task = asyncio.create_task(bureau.run())
    
    try:
        # Give agents time to start
        await asyncio.sleep(2)
        
        # Test with different assets
        results = []
        for asset in TEST_ASSETS:
            response = await tester.test_agent(asset, with_sentiment=True)
            if response:
                results.append({
                    "asset": asset,
                    "action": response.prediction.get("action"),
                    "confidence": response.confidence,
                    "sentiment_strength": response.prediction.get("sentiment_strength", 0),
                    "price_momentum": response.prediction.get("price_momentum", 0)
                })
        
        print("\nSentiment Momentum Strategy Results:")
        pprint(results)
        
        # Give some time for logs to print
        await asyncio.sleep(1)
        
    finally:
        # Stop the bureau
        bureau_task.cancel()
        try:
            await bureau_task
        except asyncio.CancelledError:
            pass

async def test_integration():
    """Test the integration of all agents"""
    print("\n===== TESTING INTEGRATION OF ALL AGENTS =====")
    
    # Start all agents
    momentum_agent = MomentumAgent(port=8101)
    mean_reversion_agent = MeanReversionAgent(port=8102)
    sentiment_momentum_agent = SentimentMomentumAgent(port=8103)
    
    # Create bureau with all agents
    bureau = Bureau(endpoint=["http://localhost:8101/submit"])
    bureau.add(momentum_agent.get_agent())
    bureau.add(mean_reversion_agent.get_agent())
    bureau.add(sentiment_momentum_agent.get_agent())
    
    # Create testers for each agent
    momentum_tester = AgentTester("momentum", momentum_agent.get_agent().address, port=8901)
    mean_reversion_tester = AgentTester("mean_reversion", mean_reversion_agent.get_agent().address, port=8902)
    sentiment_tester = AgentTester("sentiment_momentum", sentiment_momentum_agent.get_agent().address, port=8903)
    
    # Add testers to bureau
    bureau.add(momentum_tester.agent)
    bureau.add(mean_reversion_tester.agent)
    bureau.add(sentiment_tester.agent)
    
    # Run bureau in background
    bureau_task = asyncio.create_task(bureau.run())
    
    try:
        # Give agents time to start
        await asyncio.sleep(2)
        
        # Test with one asset but all strategies
        asset = random.choice(TEST_ASSETS)
        print(f"\nTesting all strategies with {asset}")
        
        # Generate the same dataset for all agents to use
        current_data, historical_data, trend_type = generate_sample_data(
            asset, days=120, with_sentiment=True
        )
        
        print(f"Generated {len(historical_data)} days of historical data")
        print(f"Trend type: {trend_type}")
        print(f"Current price: {current_data['price']:.2f}")
        
        # Create request
        request = AnalysisRequest(
            asset_id=asset,
            current_data=current_data,
            historical_data=historical_data
        )
        
        # Send request to all agents
        await momentum_tester.agent.context.send(momentum_agent.get_agent().address, request)
        await mean_reversion_tester.agent.context.send(mean_reversion_agent.get_agent().address, request)
        await sentiment_tester.agent.context.send(sentiment_momentum_agent.get_agent().address, request)
        
        # Wait for responses
        await asyncio.sleep(5)
        
        # Collect and compare results
        results = {
            "momentum": momentum_tester.responses[-1] if momentum_tester.responses else None,
            "mean_reversion": mean_reversion_tester.responses[-1] if mean_reversion_tester.responses else None,
            "sentiment_momentum": sentiment_tester.responses[-1] if sentiment_tester.responses else None
        }
        
        # Process results
        print("\nIntegration Test Results:")
        for strategy, response in results.items():
            if response:
                print(f"\n{strategy.upper()} STRATEGY:")
                print(f"Action: {response.prediction.get('action')}")
                print(f"Confidence: {response.confidence}")
                print(f"Reasoning:\n{response.reasoning}")
        
        # Give some time for logs to print
        await asyncio.sleep(1)
        
    finally:
        # Stop the bureau
        bureau_task.cancel()
        try:
            await bureau_task
        except asyncio.CancelledError:
            pass

# Main function
async def main():
    parser = argparse.ArgumentParser(description="Test agents in the multi-agent system")
    parser.add_argument("--test", choices=["momentum", "mean_reversion", "sentiment", "integration", "all"], 
                        default="all", help="Select which test to run")
    args = parser.parse_args()
    
    if args.test == "momentum" or args.test == "all":
        await test_momentum_strategy()
    
    if args.test == "mean_reversion" or args.test == "all":
        await test_mean_reversion_strategy()
    
    if args.test == "sentiment" or args.test == "all":
        await test_sentiment_momentum_strategy()
    
    if args.test == "integration" or args.test == "all":
        await test_integration()

if __name__ == "__main__":
    bureau = Bureau(endpoint=["http://localhost:8101/submit"])
    agent = MomentumAgent(port=8101)
    bureau.add(agent.get_agent())
    bureau.run() 