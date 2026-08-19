from playwright.sync_api import sync_playwright
import os

def run_cuj(page):
    page.goto('http://localhost:5173/')
    page.fill('input[type="email"]', 'test@test.com')
    page.fill('input[type="password"]', 'test1234')
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)

    # Enter a list
    page.click('.banner-card')
    page.wait_for_timeout(2000)

    # Click the trigger button to open modal
    page.click('.add-trigger-btn')
    page.wait_for_timeout(500)

    # Take screenshot of the search modal with the new barcode button
    page.screenshot(path="frontend_verification.png")
    page.wait_for_timeout(500)

    # Click barcode button
    page.click('.barcode-btn')
    page.wait_for_timeout(2000)

    # We should be on the scanner UI now
    page.screenshot(path="frontend_scanner.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="verification_videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
