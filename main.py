import os
import json
import re
import csv
from collections import defaultdict
import shutil
import subprocess
from pantomime import normalize_mimetype
from playwright.sync_api import sync_playwright

with open('domains.txt') as f:
    domains = f.readlines()

def add_mime(response, sizes, urls):
    mime = normalize_mimetype(response.header_value('Content-Type'))
    for size in response.request.sizes().values():
        sizes[mime] += size
    urls[mime].append(response.request.url)

output = []
fieldnames = set()
for domain in domains:
    user_dir = 'tmp/playwright'
    user_dir = os.path.join(os.getcwd(), user_dir)
    shutil.rmtree(user_dir, ignore_errors=True)
    
    mime_sizes = defaultdict(lambda: 0)
    mime_urls = defaultdict(lambda: [])

    with sync_playwright() as p:
        # Generate default preferences, resolve any redirects in domain and capture all mime sizes
        browser = p.chromium.launch_persistent_context(user_dir, headless=False)
        page = browser.new_page()
        page.on('response', lambda response: add_mime(response, mime_sizes, mime_urls))
        page.goto("https://" + domain)
        domain = page.url
        browser.close()

    del(mime_urls["text/html"])
    for mime, urls in mime_urls.items():
        print("Testing " + mime + " on " + domain)
        subprocess.run(["python", "load.py", user_dir, domain, "1", json.dumps(urls)])
        row = {"domain": domain, "mime": mime, "size": mime_sizes[mime]}
        with open("powerlog.csv") as f:
            lines = f.readlines()
            for line in lines:
                match = re.search(r'\"Cumulative (.*) Energy_0 \(mWh\) = (.*)\"', line)
                if match:
                    row[match.group(1).lower()] = float(match.group(2))
        output.append(row)
        fieldnames.update(row.keys())

# Write output to csv
with open('output.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
    writer.writeheader()
    writer.writerows(output)