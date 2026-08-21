import sys
from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        page.goto('http://localhost:5173/')
        page.fill('input[type="email"]', 'test@test.com')
        page.fill('input[type="password"]', 'test1234')
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)

        # Enter a list
        page.click('.banner-card')
        page.wait_for_timeout(2000)

        # Add test items via the new modal logic
        items = ["Bananen", "Tomaten", "Apfelsaft", "Milch"]
        for item in items:
            # Click the trigger button to open modal
            page.click('button:has-text("Neuen Artikel hinzufügen")', force=True)
            page.wait_for_timeout(500)

            # Type in the modal input
            page.fill('.modal-input', item)
            page.wait_for_timeout(1000) # Wait for debounce & search

            # Select the first result
            results = page.locator('.result-item')
            if results.count() > 0:
                results.first.click()
                page.wait_for_timeout(500)

                # If there are tags, click the first one as an example
                tags = page.locator('.tag-chip')
                if tags.count() > 0:
                    tags.first.click()
                    page.wait_for_timeout(300)

                # Confirm selection
                if page.locator('.modal-footer button:has-text("Zur Liste hinzufügen")').is_visible():
                    page.click('.modal-footer button:has-text("Zur Liste hinzufügen")', force=True)
            else:
                # Add custom item if no results
                page.keyboard.press("Enter")
                if page.locator('.modal-footer button:has-text("Zur Liste hinzufügen")').is_visible():
                    page.click('.modal-footer button:has-text("Zur Liste hinzufügen")', force=True)

            page.wait_for_timeout(1000)

        page.screenshot(path='frontend_test_items.png', full_page=True)
        print("Test complete. Saved screenshot.")
        browser.close()

if __name__ == '__main__':
    verify_frontend()
