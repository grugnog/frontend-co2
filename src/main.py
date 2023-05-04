"""Iterates over a list of domains and captures the power usage of each by mime type."""

import csv
import json
import os
import re
import shutil
import subprocess
import time
import platform
import sys
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Union

from pantomime import normalize_mimetype
from playwright.sync_api import sync_playwright


def add_mime(
    response: Any, sizes: DefaultDict[str, int], urls: DefaultDict[str, List[str]]
) -> None:
    """Add the size and urls for each mime type to dictionaries."""
    # Normalize the mime type and remove experimental x- prefix.
    mime: str = normalize_mimetype(response.header_value("Content-Type")).replace(
        "/x-", "/"
    )
    for size in response.request.sizes().values():
        sizes[mime] += size
    urls[mime].append(response.request.url)


iterations = 100
if int(sys.argv[1]) > 0:
    iterations = int(sys.argv[1])

powerlog = "/Applications/Intel Power Gadget/PowerLog"
if platform.system() == "Windows":
    powerlog = "PowerLog3.0.exe"

with open(os.path.join(os.getcwd(), "data", "domains.csv"), encoding="utf-8") as f:
    domains: List[str] = f.readlines()

user_dir: str = "tmp/playwright"
user_dir = os.path.join(os.getcwd(), user_dir)
output: List[Dict[str, Union[str, float, int]]] = []

for domain in domains:
    domain = domain.strip()
    shutil.rmtree(user_dir, ignore_errors=True)

    mime_sizes: DefaultDict[str, int] = defaultdict(lambda: 0)
    mime_urls: DefaultDict[str, List[str]] = defaultdict(lambda: [])
    mime_urls["none"] = []

    # Resolve any redirects in domain and capture all mime sizes/urls
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(user_dir, headless=False)
    page = browser.new_page()
    # pylint: disable-next=cell-var-from-loop
    page.on("response", lambda response: add_mime(response, mime_sizes, mime_urls))
    page.goto("https://" + domain)
    page.wait_for_load_state("load")
    page.wait_for_timeout(500)
    url = page.url
    browser.close()
    playwright.stop()

    for mime, urls in mime_urls.items():
        # Give a few seconds to ensure all browser processes are completely closed.
        time.sleep(3)
        row: Dict[str, Union[str, float, int]] = {
            "domain": url,
            "mime_blocked": mime,
            "size": mime_sizes[mime],
            "requests": len(urls),
        }
        # Log size only for html
        if mime != "text/html":
            print(domain + " excluding " + mime + " (" + str(len(urls)) + " URLs)")
            # Pass URL list as JSON file, since it can get long
            with open("tmp.json", "w", encoding="utf-8") as f:
                json.dump(urls, f)

            subprocess.run(
                [
                    powerlog,
                    "-file",
                    os.path.join(os.getcwd(), "data", "powerlog.csv"),
                    "-cmd",
                    "python",
                    os.path.join(os.getcwd(), "src", "load.py"),
                    user_dir,
                    url,
                    str(iterations),
                ],
                check=True,
            )
            # Extract the cumulative power data from the log file
            with open(
                os.path.join(os.getcwd(), "data", "powerlog.csv"), encoding="utf-8"
            ) as f:
                lines = f.readlines()
                for line in lines:
                    # Time and power is per-iteration, so we can (somewhat) compare
                    # across runs with different iteration numbers
                    match = re.search(r"\"Total Elapsed Time \(sec\) = (.*)\"", line)
                    if match:
                        row["time"] = float(match.group(1)) / iterations
                    match = re.search(
                        r"\"Cumulative (.*) Energy_0 \(mWh\) = (.*)\"", line
                    )
                    if match:
                        row[match.group(1).lower()] = float(match.group(2)) / iterations
        output.append(row)
    # Write output to csv - we do this per domain, so we don't lose data if incomplete
    with open(
        os.path.join(os.getcwd(), "data", domain + ".csv"), "w", encoding="utf-8"
    ) as f:
        fieldnames = [
            "domain",
            "mime_blocked",
            "size",
            "requests",
            "time",
            "package",
            "ia",
            "dram",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)
