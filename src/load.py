"""Generates load by repeatedly loading a page whilst blocking a list of urls."""

import json
import sys

from playwright.sync_api import sync_playwright

user_dir = sys.argv[1]
domain = sys.argv[2]
loops = sys.argv[3]
# Retrieve URL list as JSON file, since it can get long
with open("tmp.json", encoding="utf-8") as f:
    urls = json.load(f)


def handle_route(route):
    """If URL is in list of urls, abort the request, otherwise continue."""
    if route.request.url in urls:
        route.abort("blockedbyclient")
    else:
        route.continue_()


playwright = sync_playwright().start()
browser = playwright.chromium.launch_persistent_context(user_dir, headless=False)
browser.route("**", handle_route)
page = browser.new_page()
for i in range(int(loops)):
    try:
        page.goto(domain)
        page.wait_for_load_state("load", timeout=3000)
        page.wait_for_timeout(500)
    except Exception as e:
        print("Timeout exceeded: " + str(e))
page.close()
browser.close()
playwright.stop()
