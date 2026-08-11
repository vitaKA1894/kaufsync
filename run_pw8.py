import asyncio
from playwright.async_api import async_playwright
import secrets

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 375, 'height': 812}, record_video_dir="videos/")
        page = await context.new_page()

        print("Goto page")
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1000)

        # Navigate to Register
        print("Click register")
        await page.click("text='Noch kein Konto? Registrieren'")
        await page.wait_for_timeout(500)

        # Fill register
        username = "testuser" + secrets.token_hex(4)
        print(f"Register {username}")
        await page.fill("input[type='text']", username)
        await page.fill("input[type='email']", username + "@example.com")
        await page.fill("input[type='password']", "password")
        await page.click("button:has-text('Registrieren')")

        await page.wait_for_timeout(2000) # Wait for register to show login form

        print("Click login")
        await page.click("button:has-text('Einloggen')")

        # Don't wait for url, instead wait for an element in the home page like 'Liste erstellen / beitreten'
        await page.wait_for_timeout(3000)
        print("URL is now", page.url)
        await page.screenshot(path="pw_post_login.png")

        # Create list
        print("Create list")
        await page.click("button:has-text('Liste erstellen / beitreten')")
        await page.wait_for_timeout(500)
        await page.fill("input[placeholder='Listenname']", "My Test List")
        await page.click("button:has-text('Speichern')")

        await page.wait_for_timeout(1000)

        print("Click into list")
        await page.click("text='My Test List'")

        await page.wait_for_timeout(1000)

        print("Add item")
        await page.click("button:has-text('Neuen Artikel hinzufügen')")

        await page.wait_for_timeout(500)
        await page.fill("input[placeholder='Artikelname']", "Apfel")
        await page.click("button:has-text('Speichern')")

        await page.wait_for_timeout(1000)
        await page.screenshot(path="pw_list_final.png")

        print("Long press item")
        item_locator = page.locator(".grid-card.active").first
        box = await item_locator.bounding_box()

        if box:
            print("Found box", box)
            await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await page.mouse.down()
            await page.wait_for_timeout(600)
            await page.mouse.up()
            print("Long press done")
        else:
            print("Could not find box")

        await page.wait_for_timeout(1000)
        await page.screenshot(path="pw_edit_final.png")

        await browser.close()

asyncio.run(main())
