
from uagents import Model, Agent, Context, Bureau

class Message(Model):
    message: str
    
    

# Create agents named Alice and Bob
alice = Agent(
    name = "Alice",
    seed = "igfdba9pub4590bgdbgdfjbgdlkhbkdhbdhkd89ht"
)
bob = Agent(
    name = "Bob",
    seed = "ldsjbg9bqw7bt390bsbdgjfsbgkdfgiseht8h0agh"
)

# Alice's on message task
@alice.on_message(model = Message)

async def alice_message_handler(ctx: Context, sender: str, msg: Message):

    ctx.logger.info(f"I've received a message from {sender}: '{msg.message}'")

   
    msg = Message(message = "Hello, Bob! I'm agent Alice.")
    await ctx.send(bob.address, msg)

# Bob's on interval task
@bob.on_interval(period = 4.0)
async def start_conversation(ctx: Context):

    msg = Message(message = "Hello, Alice! I'm agent Bob.")

    await ctx.send(alice.address, msg)

# Bob's on message task
@bob.on_message(model = Message)
async def bob_message_handler(ctx: Context, sender: str, msg: Message):

    ctx.logger.info(f"I've received a message from {sender}: '{msg.message}'")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)


if __name__ == "__main__":
    bureau.run()
