from playwright.sync_api import sync_playwright
import time
import subprocess
import os

def start_servers():
    print("Starting backend...")
    backend = subprocess.Popen(["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=os.path.join(os.getcwd(), 'backend'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Starting frontend...")
    frontend = subprocess.Popen(["npm", "run", "dev", "--prefix", "frontend"], cwd=os.getcwd(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(5) # wait for servers to start
    return backend, frontend

def run_cuj(page):
    print("Running CUJ...")
    page.goto("http://localhost:5173")
    page.wait_for_timeout(2000)

    try:
        page.locator("#email").fill("test@test.com")
        page.wait_for_timeout(500)
        page.locator("#password").fill("test1234")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Einloggen").click()
        page.wait_for_timeout(2000)

        # Dashboard -> click first list
        page.locator(".ks-card").first.click()
        page.wait_for_timeout(1000)
    except Exception as e:
        print("Login/Navigation failed, continuing with direct view if possible...", e)

    try:
        # Click add item
        page.locator(".fab").click()
        page.wait_for_timeout(1000)

        # Type something unknown
        page.get_by_placeholder("Artikel suchen...").fill("Gegnerischer")
        page.wait_for_timeout(1000)

        # Click the "Neuen Artikel anlegen" button
        page.get_by_text("Neuen Artikel anlegen:").click()
        page.wait_for_timeout(1000)

        page.screenshot(path="verification/screenshots/verification1.png")

        # Change category to something else
        page.locator("select").select_option("Obst & Gemüse")
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Zur Liste hinzufügen").click()
        page.wait_for_timeout(2000)

        # Search for "Wurst"
        page.locator(".fab").click()
        page.wait_for_timeout(1000)
        page.get_by_placeholder("Artikel suchen...").fill("Wurst")
        page.wait_for_timeout(1000)

        page.screenshot(path="verification/screenshots/verification2.png")
        page.wait_for_timeout(1000)
    except Exception as e:
        print("Failed to run full CUJ sequence.", e)

if __name__ == "__main__":
    backend, frontend = start_servers()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                record_video_dir="verification/videos"
            )
            page = context.new_page()
            try:
                run_cuj(page)
            finally:
                context.close()
                browser.close()
    finally:
        print("Cleaning up servers...")
        backend.kill()
        frontend.kill()
