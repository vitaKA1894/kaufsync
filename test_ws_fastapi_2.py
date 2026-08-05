import asyncio
import websockets
import requests

base_url = "http://localhost:8000"
ws_base_url = "ws://localhost:8000"

user1 = {"email": "u5@e.com", "password": "pwd", "display_name": "U5"}
requests.post(f"{base_url}/api/auth/register", json=user1)
token1 = requests.post(f"{base_url}/api/auth/login", json={"email": "u5@e.com", "password": "pwd"}).json()["access_token"]
headers1 = {"Authorization": f"Bearer {token1}"}

list_data = requests.post(f"{base_url}/api/lists", json={"name": "CrashList", "icon": "Cart"}, headers=headers1).json()
list_id = list_data["id"]

async def run():
    ws1 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")
    ws2 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")

    # Do NOT await ws1.close(), close connection un-gracefully
    ws1.transport.close()

    # immediately create item, server might try to broadcast to ws1 before it notices it's closed
    # This might throw an error and break the loop for ws2!

    item_data = {"name": "T5", "category": "Food", "quantity": 1, "unit": "kg", "note": "", "tags": ""}
    resp = requests.post(f"{base_url}/api/lists/{list_id}/items", json=item_data, headers=headers1)

    try:
        msg = await asyncio.wait_for(ws2.recv(), timeout=2.0)
        print("ws2 received:", msg)
    except Exception as e:
        print("ws2 failed to receive:", e)

    await ws2.close()

asyncio.run(run())
