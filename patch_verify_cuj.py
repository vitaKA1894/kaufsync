import re

with open('/home/jules/verification/verify_cuj2.py', 'r') as f:
    content = f.read()

# Make the test just create a list directly if there are none, or intercept requests
# Actually, the quickest way to test AddItemModal is to navigate directly or mock.
# Wait, if `.banner-card` is missing, maybe we need to create a list first?
# The UI has "Neue Liste erstellen" maybe?

content = content.replace('page.wait_for_selector(".banner-card")', '''
    try:
        page.wait_for_selector(".banner-card", timeout=3000)
        page.locator(".banner-card").first.click()
    except:
        print("No lists found, creating one...")
        page.get_by_role("button", name="Neue Liste").click()
        page.wait_for_timeout(500)
        page.locator("input[placeholder='Name der Liste']").fill("Test Liste")
        page.get_by_role("button", name="Speichern").click()
        page.wait_for_timeout(1000)
        page.locator(".banner-card").first.click()
''')

# Fix wait_for_timeout for .banner-card click inside except just to be safe
content = content.replace('page.locator(".banner-card").first.click()', 'page.locator(".banner-card").first.click()', 1)

with open('/home/jules/verification/verify_cuj2.py', 'w') as f:
    f.write(content)
