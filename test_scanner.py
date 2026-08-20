from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:5173')

    # We probably need to login first or wait for something else
    page.screenshot(path='home.png')
    browser.close()
