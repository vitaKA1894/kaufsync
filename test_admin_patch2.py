import requests

response = requests.post("http://localhost:8000/api/auth/login", json={"email": "test@test.com", "password": "test1234"})
data = response.json()
token = data["access_token"]
user_id = data["user"]["id"]

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
# Try invalid payload
patch_response = requests.patch(f"http://localhost:8000/api/admin/users/{user_id}/status", json={"state": "active"}, headers=headers)
print("Response:", patch_response.status_code)
print("Body:", patch_response.json())
