# Multi-Agent Quantitative Trading System

A multi-agent system for quantitative trading using Fetch.ai's uAgents framework.

## Overview

This system demonstrates a multi-agent architecture for algorithmic trading with the following components:

- **Strategy Agents**: Independent agents implementing different trading strategies
  - Momentum Strategy
  - Mean Reversion Strategy
  - Sentiment-Momentum Strategy
- **Meta Agent**: Orchestrates the strategy agents and makes final decisions
- **Data Agents**: Collect and provide market data and sentiment information

The system uses the uAgents framework from Fetch.ai to enable agent autonomy, communication, and coordination.

## Architecture

```
                  ┌─────────────┐
                  │             │
                  │  Meta Agent │
                  │             │
                  └──────┬──────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼───────┐  ┌─────▼────────┐
│              │  │              │  │              │
│   Momentum   │  │     Mean     │  │   Sentiment  │
│    Agent     │  │  Reversion   │  │    Agent     │
│              │  │    Agent     │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Fetch.ai wallet (for agent funding)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/myquant.git
cd myquant
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the database:

```bash
# Create a PostgreSQL database named investment_db
# The meta_agent will automatically create tables on first run
```

### Running the System

#### Testing Individual Agents

You can test individual strategy agents using the test script:

```bash
# Test all agents
python src/test_agents.py

# Test specific agent
python src/test_agents.py --test momentum
python src/test_agents.py --test mean_reversion
python src/test_agents.py --test sentiment

# Test integration of all agents
python src/test_agents.py --test integration
```

#### Running the Full System

To run the full system with all agents:

```bash
python src/main.py
```

This will start all agents and they will communicate with each other using the uAgents protocol.

## Agent Details

### Strategy Agents

1. **Momentum Agent**

   - Based on price momentum principles
   - Analyzes short, medium, and long-term price movements
   - Generates buy/sell signals based on momentum strength

2. **Mean Reversion Agent**

   - Identifies assets that have deviated from their mean price
   - Uses statistical measures like Z-score
   - Generates trades expecting price to revert to the mean

3. **Sentiment Momentum Agent**
   - Combines news/social sentiment analysis with price momentum
   - Identifies alignment between sentiment and price direction
   - Generates higher conviction signals when sentiment and price align

### Meta Agent

- Coordinates all strategy agents
- Aggregates and weighs predictions from different strategies
- Makes final trading decisions
- Updates strategy weights based on performance

## Database Schema

The system uses a PostgreSQL database with the following tables:

- `assets`: Asset information
- `market_data`: Price and volume data
- `predictions`: Strategy predictions
- `decisions`: Final trading decisions
- `strategy_weights`: Weights for each strategy
- `performance_history`: Performance tracking for strategies

## Agent Communication

Agents communicate using defined message models:

- `AnalysisRequest`: Request for strategy analysis
- `AgentResponse`: Response from strategy agents
- `MetaDecision`: Final decision from meta agent

## Contributing

Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Fetch.ai](https://fetch.ai/) for the uAgents framework
- [uAgents documentation](https://docs.fetch.ai/uAgents/)
