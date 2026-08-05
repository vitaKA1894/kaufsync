import asyncio
from main import manager

class MockWebSocket:
    def __init__(self, name):
        self.name = name
    async def send_json(self, data):
        if self.name == "bad":
            raise RuntimeError("Cannot call 'send' once a close message has been sent.")
        print(f"{self.name} sent")

async def test():
    manager.active_connections["test"] = [MockWebSocket("bad"), MockWebSocket("good")]
    try:
        await manager.broadcast("test", {"hello": "world"})
        print("Success")
    except Exception as e:
        print("Broadcast crashed:", type(e), e)

asyncio.run(test())
