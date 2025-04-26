from uagents import Agent, Context, Model
import sys


class PriceRequest(Model):
    ticker: str


class PriceResponse(Model):
    ticker: str
    current_price: float
    currency: str


# Initialize the client agent
client = Agent(
    name="price_client",
    port=8004,
    endpoint="http://localhost:8004/submit",
)


PRICE_AGENT_ADDRESS = "agent1q23r0nlpl3rg9luwdrpvewp8rn9nhyqls6hpnzrxq9d3hh0k7ukkw8n5w9s"


@client.on_event("startup")
async def send_price_request(ctx: Context):
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Please enter a stock ticker symbol (e.g., AAPL): ").upper()
    
    await ctx.send(PRICE_AGENT_ADDRESS, PriceRequest(ticker=ticker))
    ctx.logger.info(f"Sent price request for ticker: {ticker}")


@client.on_message(PriceResponse)
async def handle_price_response(ctx: Context, sender: str, msg: PriceResponse):
    ctx.logger.info(f"Current price for {msg.ticker}: {msg.current_price} {msg.currency}")


if __name__ == "__main__":
    client.run() 