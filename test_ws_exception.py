import asyncio
import websockets
import requests

base_url = "http://localhost:8000"
ws_base_url = "ws://localhost:8000"

user1 = {"email": "p9@e.com", "password": "pwd", "display_name": "P9"}
requests.post(f"{base_url}/api/auth/register", json=user1)
token1 = requests.post(f"{base_url}/api/auth/login", json={"email": "p9@e.com", "password": "pwd"}).json()["access_token"]
headers1 = {"Authorization": f"Bearer {token1}"}

list_data = requests.post(f"{base_url}/api/lists", json={"name": "CrashList", "icon": "Cart"}, headers=headers1).json()
list_id = list_data["id"]

async def run():
    ws1 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")
    ws2 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")
    ws3 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")

    # We want to close ws2 abruptly and instantly broadcast so that the server hasn't processed the disconnect yet
    ws2.transport.close()

    item_data = {"name": "T5", "category": "Food", "quantity": 1, "unit": "kg", "note": "", "tags": ""}
    resp = requests.post(f"{base_url}/api/lists/{list_id}/items", json=item_data, headers=headers1)

    try:
        msg1 = await asyncio.wait_for(ws1.recv(), timeout=1.0)
        print("ws1 received:", msg1)
    except Exception as e:
        print("ws1 failed:", e)

    try:
        msg3 = await asyncio.wait_for(ws3.recv(), timeout=1.0)
        print("ws3 received:", msg3)
    except Exception as e:
        print("ws3 failed:", e)

    await ws1.close()
    await ws3.close()

asyncio.run(run())
