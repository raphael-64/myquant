
from uagents import Model, Agent, Context

class Message(Model):
    message: str

# Create an agent named Alice
alice = Agent(
    name = "Alice",
    seed = "khavaioghgjabougrvbosubvisgvgjfkf",
    port = 8000,
    endpoint = ["http://127.0.0.1:8000/submit"]
)

# alice and bob are connected normaly

# Alice's on message task
@alice.on_message(model = Message)

async def on_message(ctx: Context, sender: str, msg: Message):
    
    ctx.logger.info(f"I've received a message from {sender}: '{msg.message}'")

    msg = Message(message = "Hello, Bob! I'm agent Alice.")
   
    await ctx.send(sender, msg)

# Run the agent
if __name__ == "__main__":
    alice.run()
