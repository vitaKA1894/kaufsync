import requests

# Assuming local servers are running on port 8000
# Let's login and get a token
response = requests.post("http://localhost:8000/api/auth/login", json={"email": "test@test.com", "password": "test1234"})
data = response.json()
token = data["access_token"]
user_id = data["user"]["id"]

# Now we try to patch the status
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
patch_response = requests.patch(f"http://localhost:8000/api/admin/users/{user_id}/status", json={"status": "active"}, headers=headers)
print("Response:", patch_response.status_code)
print("Body:", patch_response.json())
