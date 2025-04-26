import os
import requests

AV_API_KEY = os.getenv("AV_API_KEY") or "3NW3NFP2BF9YBR3M"

def get_real_stock_price(ticker):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": AV_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

print(get_real_stock_price("NVDA"))