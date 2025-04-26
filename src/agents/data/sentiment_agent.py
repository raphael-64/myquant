from typing import List
from uagents import Agent, Context, Model
import yfinance as yf
import requests
from datetime import datetime, timedelta
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np


class SentimentRequest(Model):
    ticker: str


# class NewsSentiment(Model):
#     #url: str
#     #summary: str
#     overall_sentiment: float


class SentimentResponse(Model):
    sentiment: float


# Initialize FinBERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")


def get_sentiment(text: str) -> dict:
    """Get sentiment using FinBERT with continuous scores"""
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


def get_overall_sentiment(sentiment_scores: dict) -> float:
    """Calculate overall sentiment score from -1 (very negative) to 1 (very positive)"""
    return sentiment_scores["positive"] - sentiment_scores["negative"]


# Initialize the sentiment agent
sentiment_agent = Agent(
    name="sentiment_analyzer",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)


def get_news_sentiment(ticker: str) -> float:
    # Get company info from yfinance
    stock = yf.Ticker(ticker)
    company_name = stock.info.get('longName', ticker)
    
    # Get recent news
    news = stock.news
    
    # Process each news item
    sentiment_results = 0
    for item in news[:15]:  # Get top 15 news items
        summary = item.get('content', '').get('summary', '')
        #url = item.get('link', '')
            
        # Analyze sentiment using FinBERT
        sentiment_scores = get_sentiment(summary)
        overall_sentiment = get_overall_sentiment(sentiment_scores)
        
        # Create sentiment label based on overall score
        #sentiment_label = "Positive" if overall_sentiment > 0.1 else "Negative" if overall_sentiment < -0.1 else "Neutral"
        
        sentiment_results += overall_sentiment
        # sentiment_results.append(
        #     NewsSentiment(
        #         #url=url,
        #         #summary=f"News about {company_name} with {sentiment_label.lower()} sentiment (score: {overall_sentiment:.3f})",
        #         overall_sentiment=overall_sentiment
        #     )
        # )
    
    return sentiment_results


@sentiment_agent.on_message(SentimentRequest)
async def handle_request(ctx: Context, sender: str, msg: SentimentRequest):
    ctx.logger.info(f"Received request for ticker: {msg.ticker}")
    
    try:
        # Get news sentiment analysis
        sentiment_data = get_news_sentiment(msg.ticker)
        
        # Send response back
        await ctx.send(
            sender,
            SentimentResponse(sentiment=sentiment_data)
        )
        ctx.logger.info(f"Sent response to {sender}")
        
    except Exception as e:
        ctx.logger.error(f"Error processing request: {str(e)}")


if __name__ == "__main__":
    sentiment_agent.run() 