import asyncio
import websockets
import requests

base_url = "http://localhost:8000"
ws_base_url = "ws://localhost:8000"

user1 = {"email": "u1@e.com", "password": "pwd", "display_name": "U1"}
requests.post(f"{base_url}/api/auth/register", json=user1)
token1 = requests.post(f"{base_url}/api/auth/login", json={"email": "u1@e.com", "password": "pwd"}).json()["access_token"]
headers1 = {"Authorization": f"Bearer {token1}"}

list_data = requests.post(f"{base_url}/api/lists", json={"name": "List", "icon": "Cart"}, headers=headers1).json()
list_id = list_data["id"]

async def connect_and_drop():
    ws = await websockets.connect(f"{ws_base_url}/ws/{list_id}")
    # Abruptly close
    ws.transport.close()
    await asyncio.sleep(0.5)

asyncio.run(connect_and_drop())

# Now try to create an item
item_data = {"name": "T2", "category": "Food", "quantity": 1, "unit": "kg", "note": "", "tags": ""}
resp = requests.post(f"{base_url}/api/lists/{list_id}/items", json=item_data, headers=headers1)
print(resp.status_code, resp.text)
