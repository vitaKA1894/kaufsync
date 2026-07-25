import sys
from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        page.goto('http://localhost:5174/')
        page.fill('input[type="email"]', 'test@test.com')
        page.fill('input[type="password"]', 'test1234')
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)

        # Enter a list
        page.click('.list-card')
        page.wait_for_timeout(2000)

        # Add test items to verify icon and clear logic
        items = ["Bananen", "Tomaten", "Nutella", "Apfel"]
        for item in items:
            page.fill('input[placeholder="Artikel hinzufügen…"]', item)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)

        page.wait_for_timeout(2000)

        # Click an item to mark completed
        page.click('.grid-card.active')
        page.wait_for_timeout(1000)

        page.screenshot(path='frontend_test_icons.png')
        print("Test complete. Saved screenshot.")
        browser.close()

if __name__ == '__main__':
    verify_frontend()
