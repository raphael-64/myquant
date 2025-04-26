# Imports
from uagents import Model, Agent, Context

ALICE_ADDRESS = "agent1qtkp83xdzjn6pupps8jj309mu5km6h58cgcwzl3afw9frrnmqhk9kwrur80"


class Message(Model):
    message: str


bob = Agent(
    name = "Bob",
    seed = "kjbgfsipzwvgpifdsfncoerubcgbjbgfj",
    port = 8001,
    endpoint = ["http://127.0.0.1:8001/submit"]
)


@bob.on_interval(period = 2.0)
# Define send_message function which will be called every 2 seconds
async def send_message(ctx: Context):
    msg = Message(message = "Hello, Alice! I'm agent Bob.")
    
    await ctx.send(ALICE_ADDRESS, msg)

# Bob's on message task
@bob.on_message(model = Message)

async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"I've received a message from {sender}: '{msg.message}'")

# Run the agent
if __name__ == "__main__":
    bob.run()