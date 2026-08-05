import asyncio
from playwright.async_api import async_playwright
import requests

base_url = "http://localhost:5173"
api_url = "http://localhost:8000"

async def test_sync():
    # Register two users
    u1 = {"email": "p5@e.com", "password": "pwd", "display_name": "P5"}
    u2 = {"email": "p6@e.com", "password": "pwd", "display_name": "P6"}
    requests.post(f"{api_url}/api/auth/register", json=u1)
    requests.post(f"{api_url}/api/auth/register", json=u2)

    # Get tokens
    token1 = requests.post(f"{api_url}/api/auth/login", json={"email": "p5@e.com", "password": "pwd"}).json()["access_token"]
    token2 = requests.post(f"{api_url}/api/auth/login", json={"email": "p6@e.com", "password": "pwd"}).json()["access_token"]

    # Create list as P1
    list_data = requests.post(f"{api_url}/api/lists", json={"name": "PlaywrightList3", "icon": "Cart"}, headers={"Authorization": f"Bearer {token1}"}).json()
    list_id = list_data["id"]
    share_code = list_data["share_code"]

    # P2 joins
    requests.post(f"{api_url}/api/lists/join", json={"share_code": share_code}, headers={"Authorization": f"Bearer {token2}"})

    # Wait, the bug description says:
    # "Wenn an einer geteilten Liste zwei Menschen gleichzeitig arbeiten, muss die synchronisierung immer sofort da sein, auch ohne aktualisierung. Das ganze hatte schon funktioniert, ich meine über webhooks. seit ein paar Feature Updates geht es aber nicht mehr."

    # Let's test P1 adding an item via the UI, and P2 seeing it.
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

        # Wait a bit just in case WS connects
        await page1.wait_for_timeout(1000)
        await page2.wait_for_timeout(1000)

        # P1 adds item via UI
        print("P1 adding item via UI...")
        await page1.click(".add-trigger-btn")

        # We need to find the correct input in the modal
        # Check if modal is visible
        await page1.wait_for_selector(".modal-overlay")
        await page1.fill("input[placeholder='Artikel suchen...']", "Apple")
        await page1.click("button:has-text('Hinzufügen')")

        # P2 should see it immediately
        try:
            await page2.wait_for_selector(".item-name:has-text('Apple')", timeout=3000)
            print("Sync create via UI works!")
        except Exception as e:
            print("Sync create via UI failed!", e)

        await browser.close()

asyncio.run(test_sync())
