from uagents import Agent, Context, Model
import yfinance as yf


class PriceRequest(Model):
    ticker: str


class PriceResponse(Model):
    ticker: str
    current_price: float
    currency: str


# Initialize the price agent
price_agent = Agent(
    name="price_fetcher",
    port=8003,
    endpoint=["http://localhost:8003/submit"],
)


@price_agent.on_message(PriceRequest)
async def handle_request(ctx: Context, sender: str, msg: PriceRequest):
    ctx.logger.info(f"Received price request for ticker: {msg.ticker}")
    
    try:
        # Get stock data
        stock = yf.Ticker(msg.ticker)
        current_price = stock.info.get('currentPrice', 0)
        currency = stock.info.get('currency', 'USD')
        
        # Send response back
        await ctx.send(
            sender,
            PriceResponse(
                ticker=msg.ticker,
                current_price=current_price,
                currency=currency
            )
        )
        ctx.logger.info(f"Sent price data for {msg.ticker}: {current_price} {currency}")
        
    except Exception as e:
        ctx.logger.error(f"Error fetching price: {str(e)}")


if __name__ == "__main__":
    price_agent.run() 