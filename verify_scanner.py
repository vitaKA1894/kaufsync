from playwright.sync_api import sync_playwright
import os

def run_cuj(page):
    page.goto('http://localhost:5173/')
    # Wait for the login screen to be ready
    page.wait_for_selector('input[type="email"]', state='visible', timeout=10000)
    page.fill('input[type="email"]', 'test@test.com')
    page.fill('input[type="password"]', 'test1234')
    page.click('button[type="submit"]')

    # Wait to land on Dashboard
    page.wait_for_selector('.banner-card', state='visible', timeout=10000)
    print("Logged in, on dashboard.")

    # Enter a list
    page.click('.banner-card')

    # Wait for List View
    page.wait_for_selector('.add-trigger-btn', state='visible', timeout=10000)
    print("In list view.")

    # Click the trigger button to open modal
    page.click('.add-trigger-btn')
    page.wait_for_selector('.modal-content', state='visible', timeout=10000)
    page.wait_for_selector('.barcode-btn', state='visible', timeout=10000)
    print("Modal opened.")

    # Take screenshot of the search modal with the new barcode button
    page.screenshot(path="frontend_verification.png")
    page.wait_for_timeout(500)

    # Click barcode button
    page.click('.barcode-btn')
    page.wait_for_selector('.scanner-container', state='visible', timeout=10000)
    print("Scanner opened.")

    # Take a screenshot to show it doesn't collapse anymore
    page.screenshot(path="frontend_scanner.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Give permission for camera, otherwise we get prompts or it fails
        context = browser.new_context(
            record_video_dir="verification_videos",
            permissions=['camera']
        )
        page = context.new_page()
        try:
            run_cuj(page)
            print("Successfully finished CUJ")
        finally:
            context.close()
            browser.close()
