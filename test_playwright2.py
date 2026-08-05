import asyncio
from playwright.async_api import async_playwright
import requests

base_url = "http://localhost:5173"
api_url = "http://localhost:8000"

async def test_sync():
    # Register two users
    u1 = {"email": "p3@e.com", "password": "pwd", "display_name": "P3"}
    u2 = {"email": "p4@e.com", "password": "pwd", "display_name": "P4"}
    requests.post(f"{api_url}/api/auth/register", json=u1)
    requests.post(f"{api_url}/api/auth/register", json=u2)

    # Get tokens
    token1 = requests.post(f"{api_url}/api/auth/login", json={"email": "p3@e.com", "password": "pwd"}).json()["access_token"]
    token2 = requests.post(f"{api_url}/api/auth/login", json={"email": "p4@e.com", "password": "pwd"}).json()["access_token"]

    # Create list as P1
    list_data = requests.post(f"{api_url}/api/lists", json={"name": "PlaywrightList2", "icon": "Cart"}, headers={"Authorization": f"Bearer {token1}"}).json()
    list_id = list_data["id"]
    share_code = list_data["share_code"]

    # P2 joins
    requests.post(f"{api_url}/api/lists/join", json={"share_code": share_code}, headers={"Authorization": f"Bearer {token2}"})

    # P1 creates an item
    item_data = {"name": "Bananas", "category": "Food", "quantity": 1, "unit": "kg", "note": "", "tags": ""}
    resp = requests.post(f"{api_url}/api/lists/{list_id}/items", json=item_data, headers={"Authorization": f"Bearer {token1}"})
    item_id = resp.json()["id"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx1 = await browser.new_context()
        ctx2 = await browser.new_context()

        # Inject tokens into localStorage
        page1 = await ctx1.new_page()
        await page1.goto(base_url)
        await page1.evaluate(f"localStorage.setItem('token', '{token1}')")
        await page1.goto(f"{base_url}/list/{list_id}")

        page2 = await ctx2.new_page()
        await page2.goto(base_url)
        await page2.evaluate(f"localStorage.setItem('token', '{token2}')")
        await page2.goto(f"{base_url}/list/{list_id}")

        # Wait for pages to load
        await page1.wait_for_selector(".list-title")
        await page2.wait_for_selector(".list-title")

        await page1.wait_for_timeout(1000)
        await page2.wait_for_timeout(1000)

        print("P1 toggling item status...")
        # write directly to API via python, then check UI on P2!
        requests.put(f"{api_url}/api/items/{item_id}", json={"status": "completed"}, headers={"Authorization": f"Bearer {token1}"})

        # P2 should see it immediately
        try:
            await page2.wait_for_selector(".completed-section .item-name:has-text('Bananas')", timeout=3000)
            print("Sync update works!")
        except Exception as e:
            print("Sync update failed!", e)

        print("P1 deleting item...")
        requests.delete(f"{api_url}/api/items/{item_id}", headers={"Authorization": f"Bearer {token1}"})

        try:
            await page2.wait_for_selector(".completed-section .item-name:has-text('Bananas')", state='hidden', timeout=3000)
            print("Sync delete works!")
        except Exception as e:
            print("Sync delete failed!", e)

        await browser.close()

asyncio.run(test_sync())
