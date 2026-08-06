import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from main import manager, app

# We can mock a websocket that raises RuntimeError on send_json
class MockWebSocket:
    async def send_json(self, data):
        raise RuntimeError("Cannot call 'send' once a close message has been sent.")

async def test():
    manager.active_connections["test"] = [MockWebSocket(), MockWebSocket()]
    try:
        await manager.broadcast("test", {"hello": "world"})
        print("Success")
    except Exception as e:
        print("Broadcast crashed:", type(e), e)

asyncio.run(test())
