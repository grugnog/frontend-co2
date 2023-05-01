import sys
import json
from playwright.sync_api import sync_playwright

user_dir = sys.argv[1]
domain = sys.argv[2]
loops = sys.argv[3]
urls = json.loads(sys.argv[4])

def handle_route(route):
    if route.request.url in urls:
        route.abort('blockedbyclient')
    else:
        route.continue_()

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(user_dir, headless=False)
    browser.route("**", handle_route)
    for i in range(int(loops)):
        page = browser.new_page()
        page.goto(domain, wait_until='load')
        page.close()