from typing import List
from uagents import Agent, Context, Model


class FinancialNewsSentimentRequest(Model):
    ticker: str


# class NewsSentiment(Model):
#     # url: str
#     # summary: str
#     overall_sentiment: float


class FinancialNewsSentimentResponse(Model):
    sentiment: float


agent = Agent(
    name="user",
    port=8002,
    endpoint="http://localhost:8002/submit",
)


AI_AGENT_ADDRESS = "agent1qfreuv4u6shhu83hhd6n37hwetz8p0uu674x0h4kdjvm84dkl5uhvlshut7"

ticker = "AAPL"


@agent.on_event("startup")
async def send_message(ctx: Context):
    await ctx.send(AI_AGENT_ADDRESS, FinancialNewsSentimentRequest(ticker=ticker))
    ctx.logger.info(f"Sent prompt to AI agent: {ticker}")


@agent.on_message(FinancialNewsSentimentResponse)
async def handle_response(ctx: Context, sender: str, msg: FinancialNewsSentimentResponse):
    ctx.logger.info(f"Received response from {sender}:")
    ctx.logger.info(f"{ticker} sentiment: {msg.sentiment}")


if __name__ == "__main__":
    agent.run()
