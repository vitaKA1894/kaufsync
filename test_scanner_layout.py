from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # We need to simulate a camera, so we grant permissions and use fake device
    context = browser.new_context(
        permissions=['camera'],
        ignore_https_errors=True
    )
    page = context.new_page()
    page.goto('http://localhost:5173')

    # Check if there is a login form
    if page.locator('text="Einloggen"').count() > 0:
        # Mock the login state by setting localStorage manually
        page.evaluate("localStorage.setItem('token', 'fake-token');")
        page.reload()

    # wait for the UI
    try:
        page.wait_for_selector('text="Neuen Artikel hinzufügen"', timeout=5000)
        page.click('text="Neuen Artikel hinzufügen"')
        page.wait_for_selector('.modal-content', timeout=5000)
        page.screenshot(path='modal_open.png')

        page.click('.barcode-btn')
        time.sleep(2) # Wait for camera animation/loading
        page.screenshot(path='scanner_open.png')
    except Exception as e:
        print("Error:", e)
        page.screenshot(path='error.png')

    browser.close()
