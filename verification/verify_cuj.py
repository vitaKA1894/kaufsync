import os
import subprocess
import time
from playwright.sync_api import sync_playwright

def start_servers():
    print("Starting backend...")
    backend = subprocess.Popen(["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=os.path.join(os.getcwd(), 'backend'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Starting frontend...")
    frontend = subprocess.Popen(["npm", "run", "dev", "--prefix", "frontend"], cwd=os.getcwd(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    return backend, frontend

def run_cuj(page):
    print("Running CUJ...")
    page.goto("http://localhost:5173")
    page.wait_for_timeout(1000)

    # Authenticate via localStorage
    page.evaluate("localStorage.setItem('token', 'dummy');")
    page.evaluate("localStorage.setItem('user', JSON.stringify({id: 1, email: 'test@test.com', display_name: 'Test'}));")
    page.evaluate("localStorage.setItem('isLoggedIn', 'true');")

    page.reload()
    page.wait_for_timeout(2000)

    try:
        # Create a list if none exists
        if page.get_by_text("Liste erstellen / beitreten").is_visible():
            page.get_by_text("Liste erstellen / beitreten").click()
            page.wait_for_timeout(500)
            page.get_by_text("Neue Liste erstellen").click()
            page.wait_for_timeout(500)
            page.get_by_role("textbox").fill("Einkauf")
            page.wait_for_timeout(500)
            page.get_by_text("Erstellen", exact=True).click()
            page.wait_for_timeout(2000)
            if page.locator(".banner-card").count() > 0:
                page.locator(".banner-card").first.click()
            page.wait_for_timeout(1000)

        # Click on the list
        pass
        page.wait_for_timeout(1000)
    except Exception as e:
        print(f"List navigation failed: {e}")

    # We should now be on the ListView
    page.wait_for_timeout(2000)
    page.screenshot(path="/app/verification/list_view_verification.png")

if __name__ == "__main__":
    backend, frontend = start_servers()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(record_video_dir="/app/verification/videos")
            page = context.new_page()
            try:
                run_cuj(page)
            finally:
                context.close()
                browser.close()
    finally:
        print("Cleaning up servers...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
