import asyncio
import websockets
import json
import requests
import sys

base_url = "http://localhost:8000"
ws_base_url = "ws://localhost:8000"

# Register users
user1 = {"email": "user1@example.com", "password": "password123", "display_name": "User 1"}
user2 = {"email": "user2@example.com", "password": "password123", "display_name": "User 2"}

requests.post(f"{base_url}/api/auth/register", json=user1)
requests.post(f"{base_url}/api/auth/register", json=user2)

# Login
token1 = requests.post(f"{base_url}/api/auth/login", json={"email": user1["email"], "password": user1["password"]}).json()["access_token"]
token2 = requests.post(f"{base_url}/api/auth/login", json={"email": user2["email"], "password": user2["password"]}).json()["access_token"]

headers1 = {"Authorization": f"Bearer {token1}"}
headers2 = {"Authorization": f"Bearer {token2}"}

# Create list as user1
list_resp = requests.post(f"{base_url}/api/lists", json={"name": "Test List", "icon": "Cart"}, headers=headers1)
list_data = list_resp.json()
list_id = list_data["id"]
share_code = list_data["share_code"]

# Join as user2
requests.post(f"{base_url}/api/lists/join", json={"share_code": share_code}, headers=headers2)

async def test_ws():
    print(f"Connecting to {ws_base_url}/ws/{list_id}")
    async with websockets.connect(f"{ws_base_url}/ws/{list_id}") as ws:
        print("Connected!")
        # Create item as user 2
        item_data = {"name": "Test Item", "category": "Food", "quantity": 1, "unit": "kg", "note": "", "tags": ""}
        resp = requests.post(f"{base_url}/api/lists/{list_id}/items", json=item_data, headers=headers2)
        print("Item created:", resp.json())

        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            print("Received:", msg)
        except Exception as e:
            print("Did not receive message:", e)

asyncio.run(test_ws())
