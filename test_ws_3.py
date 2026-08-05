import asyncio
import websockets
import requests

base_url = "http://localhost:8000"
ws_base_url = "ws://localhost:8000"

user1 = {"email": "u6@e.com", "password": "pwd", "display_name": "U6"}
requests.post(f"{base_url}/api/auth/register", json=user1)
token1 = requests.post(f"{base_url}/api/auth/login", json={"email": "u6@e.com", "password": "pwd"}).json()["access_token"]
headers1 = {"Authorization": f"Bearer {token1}"}

list_data = requests.post(f"{base_url}/api/lists", json={"name": "CrashList2", "icon": "Cart"}, headers=headers1).json()
list_id = list_data["id"]

async def run():
    ws1 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")
    ws2 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")
    ws3 = await websockets.connect(f"{ws_base_url}/ws/{list_id}")

    # We want ws2 to drop in a way that the server does not handle cleanly,
    # or just normal close and hope the server tries to broadcast to it before it is removed.
    # A cleaner way to simulate a dropped connection is closing the underlying socket
    ws2.transport.close()

    # Wait just a tiny bit but maybe not enough for the server to process the disconnect?
    # Actually, we can just send the request
    item_data = {"name": "T6", "category": "Food", "quantity": 1, "unit": "kg", "note": "", "tags": ""}
    resp = requests.post(f"{base_url}/api/lists/{list_id}/items", json=item_data, headers=headers1)

    try:
        msg = await asyncio.wait_for(ws1.recv(), timeout=2.0)
        print("ws1 received:", msg)
    except Exception as e:
        print("ws1 failed:", e)

    try:
        msg = await asyncio.wait_for(ws3.recv(), timeout=2.0)
        print("ws3 received:", msg)
    except Exception as e:
        print("ws3 failed:", e)

    await ws1.close()
    await ws3.close()

asyncio.run(run())
