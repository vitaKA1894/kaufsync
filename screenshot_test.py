from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        page.goto('http://localhost:5173/')
        page.fill('input[type="email"]', 'test@test.com')
        page.fill('input[type="password"]', 'test1234')
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)

        page.screenshot(path='dashboard.png', full_page=True)
        print("Test complete. Saved screenshot.")
        browser.close()

if __name__ == '__main__':
    run()
