from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )

    print("Connected to Brave!")
    print("Open tabs:")

    for i, page in enumerate(browser.contexts[0].pages):
        print(f"{i}: {page.title()} | {page.url}")

    # Do not close the browser or its context.