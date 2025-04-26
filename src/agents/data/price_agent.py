from uagents import Agent, Context, Model
import yfinance as yf
from datetime import datetime
from uagents.setup import fund_agent_if_low


class PriceRequest(Model):
    ticker: str


class PriceResponse(Model):
    ticker: str
    timestamp: str
    current_price: float
    currency: str
    volume: int


# Initialize the price agent
price_agent = Agent(
    name="price_fetcher",
    port=8003,
    endpoint=["http://localhost:8003/submit"],
    seed="price_fetcher_seed_phrase",  # Consistent seed for stable address
)

# Fund the agent if needed
fund_agent_if_low(price_agent.wallet.address())

# Print agent information for discovery
print(f"Data agent: Price Fetcher")
print(f"Address: {price_agent.address}")
print(f"Endpoint: http://localhost:8003/submit")


@price_agent.on_message(PriceRequest)
async def handle_request(ctx: Context, sender: str, msg: PriceRequest):
    ctx.logger.info(f"Received price request for ticker: {msg.ticker} from {sender}")
    
    try:
        # Get stock data
        ctx.logger.info(f"Fetching data for {msg.ticker} using yfinance...")
        stock = yf.Ticker(msg.ticker)
        
        # Get more comprehensive market data
        current_price = stock.info.get('currentPrice', 0)
        if current_price == 0:  # Sometimes yfinance returns currentPrice as 0
            current_price = stock.info.get('regularMarketPrice', 0)
            ctx.logger.info(f"Using regularMarketPrice: {current_price}")
        else:
            ctx.logger.info(f"Using currentPrice: {current_price}")
            
        currency = stock.info.get('currency', 'USD')
        volume = stock.info.get('volume', 0)
        timestamp = datetime.now().isoformat()
        
        ctx.logger.info(f"Data fetched successfully: {current_price} {currency}, volume: {volume}")
        
        # Prepare response
        response = PriceResponse(
            ticker=msg.ticker,
            timestamp=timestamp,
            current_price=current_price,
            currency=currency,
            volume=volume
        )
        
        ctx.logger.info(f"Sending response back to {sender}")
        
        # Send response back
        await ctx.send(
            sender,
            response
        )
        ctx.logger.info(f"Response sent successfully for {msg.ticker}")
        
    except Exception as e:
        ctx.logger.error(f"Error fetching price: {str(e)}")
        import traceback
        ctx.logger.error(traceback.format_exc())


if __name__ == "__main__":
    price_agent.run() 