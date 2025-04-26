from typing import Dict, List
from uagents import Agent, Context, Model
import yfinance as yf
from datetime import datetime
import requests
import numpy as np


try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    FINBERT_AVAILABLE = True
except ImportError:
    FINBERT_AVAILABLE = False
    print("FinBERT not available, falling back to basic sentiment analysis")

class SentimentRequest(Model):
    ticker: str
    timestamp: str           # trying this shit

class SentimentResponse(Model):
    ticker: str
    timestamp: str
    sentiment_score: float
    sentiment_magnitude: float
    news_count: int

# Initialize the sentiment agent
sentiment_agent = Agent(
    name="sentiment_analyzer",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
    seed="sentiment_analyzer_seed_phrase",  # Consistent seed for stable address
)

# Fund the agent if needed
from uagents.setup import fund_agent_if_low
fund_agent_if_low(sentiment_agent.wallet.address())

# Print agent information for discovery
print(f"Data agent: Sentiment Analyzer")
print(f"Address: {sentiment_agent.address}")
print(f"Endpoint: http://localhost:8001/submit")

# Initialize FinBERT model and tokenizer if available
if FINBERT_AVAILABLE:
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

def get_sentiment_finbert(text: str) -> Dict[str, float]:
    """Get sentiment using FinBERT with continuous scores"""
    if not FINBERT_AVAILABLE:
        return {"positive": 0.5, "negative": 0.0, "neutral": 0.5}
        
    if not text.strip():
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = model(**inputs)
    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    # Convert to numpy array and get probabilities
    probs = predictions.detach().numpy()[0]
    
    # Return dictionary with sentiment probabilities
    return {
        "positive": float(probs[0]),
        "negative": float(probs[1]),
        "neutral": float(probs[2])
    }

def get_basic_sentiment(text: str) -> Dict[str, float]:
    """Fallback function for basic sentiment analysis"""
    # Simple keyword-based approach
    positive_words = ['up', 'increase', 'grow', 'positive', 'profit', 'gain', 'bull', 'good']
    negative_words = ['down', 'decrease', 'shrink', 'negative', 'loss', 'decline', 'bear', 'bad']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total = positive_count + negative_count
    if total == 0:
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
    
    positive_score = positive_count / total
    negative_score = negative_count / total
    neutral_score = 1.0 - (positive_score + negative_score)
    
    return {
        "positive": positive_score,
        "negative": negative_score,
        "neutral": neutral_score
    }

def get_overall_sentiment(sentiment_scores: dict) -> float:
    """Calculate overall sentiment score from -1 (very negative) to 1 (very positive)"""
    return sentiment_scores["positive"] - sentiment_scores["negative"]

def analyze_news_sentiment(ticker: str) -> Dict:
    """Analyze sentiment for a ticker's news"""
    # Get company info from yfinance
    stock = yf.Ticker(ticker)
    
    # Get recent news
    news = stock.news
    
    # Process each news item
    sentiment_scores = []
    for item in news[:15]:  # Get top 15 news items
        try:
            summary = item.get('content', '').get('summary','')
            print(summary)
            if 'summary' in item:
                summary += " " + item.get('content', '').get('summary','')
                
            # Analyze sentiment
            if FINBERT_AVAILABLE:
                sentiment = get_sentiment_finbert(summary)
            else:
                sentiment = get_basic_sentiment(summary)
                
            score = get_overall_sentiment(sentiment)
            sentiment_scores.append(score)
        except Exception as e:
            print(f"Error processing news item: {e}")
    
    # Calculate average sentiment and magnitude
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        sentiment_magnitude = sum(abs(score) for score in sentiment_scores) / len(sentiment_scores)
        news_count = len(sentiment_scores)
    else:
        avg_sentiment = 0.0
        sentiment_magnitude = 0.0
        news_count = 0
    
    return {
        "sentiment_score": avg_sentiment,
        "sentiment_magnitude": sentiment_magnitude,
        "news_count": news_count
    }

@sentiment_agent.on_message(SentimentRequest)
async def handle_request(ctx: Context, sender: str, msg: SentimentRequest):
    ctx.logger.info(f"Received sentiment request for ticker: {msg.ticker}")
    
    try:
        # Get news sentiment analysis
        sentiment_data = analyze_news_sentiment(msg.ticker)
        timestamp = msg.timestamp
        
        # Send response back
        await ctx.send(
            sender,
            SentimentResponse(
                ticker=msg.ticker,
                timestamp=timestamp,
                sentiment_score=float(sentiment_data["sentiment_score"]),
                sentiment_magnitude=float(sentiment_data["sentiment_magnitude"]),
                news_count=sentiment_data["news_count"]
            )
        )
        ctx.logger.info(f"Sent sentiment data for {msg.ticker}: {sentiment_data}")
        
    except Exception as e:
        ctx.logger.error(f"Error processing sentiment request: {str(e)}")

if __name__ == "__main__":
    sentiment_agent.run() 