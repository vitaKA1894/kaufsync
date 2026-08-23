from playwright.sync_api import sync_playwright
import time
import subprocess
import os
import signal

print("Starting backend...")
backend_process = subprocess.Popen(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"], cwd="backend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Starting frontend...")
frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd="frontend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(5)  # Wait for servers to start

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(10000)

        print("Logging in...")
        page.goto("http://localhost:5173")
        page.fill("#email", "test@test.com")
        page.fill("#password", "test1234")
        page.click("button:has-text('Einloggen')")

        time.sleep(2)

        print("Opening first list...")
        page.wait_for_selector(".banner-card")
        page.locator(".banner-card").first.click()
        time.sleep(2)

        # We just want to get to the Share Sheet and Changelog now.
        print("Opening Share Sheet...")
        # Get the right button - aria-label="Teilen" is on the icon button in the header
        page.locator("button[aria-label='Teilen']").click(force=True)
        # Wait for the sheet animation
        time.sleep(2)
        # Try to screenshot the specific sheet content or whole page
        page.screenshot(path="share_sheet_qr_code.png")
        page.locator(".ks-sheet-scrim").click(force=True)
        time.sleep(2)

        print("Opening Changelog...")
        page.locator("button[aria-label='Aktivitätenprotokoll']").click(force=True)
        time.sleep(2)
        page.screenshot(path="changelog_grouped.png")

        browser.close()
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    print("Cleaning up servers...")
    os.kill(backend_process.pid, signal.SIGTERM)
    os.kill(frontend_process.pid, signal.SIGTERM)
