
from playwright.sync_api import sync_playwright

URL = "https://www.nytimes.com/games/wordle/index.html"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            executable_path=(
                "/Applications/Brave Browser.app/"
                "Contents/MacOS/Brave Browser"
            ),
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Try closing the privacy modal if it is present.
        close_button = page.get_by_role("button", name="Close modal")
        if close_button.count() > 0:
            close_button.first.click()
            page.wait_for_timeout(2000)

        print("\nPAGE TITLE:", page.title())
        print("URL:", page.url)

        # Inspect visible custom elements and board-related attributes.
        details = page.evaluate("""() => {
            const found = [];
            const seen = new Set();

            function walk(root) {
                if (!root || seen.has(root)) return;
                seen.add(root);

                for (const el of root.querySelectorAll("*")) {
                    const tag = el.tagName.toLowerCase();
                    const attrs = [...el.attributes].map(
                        a => `${a.name}="${a.value}"`
                    ).join(" ");

                    if (
                        tag.includes("game") ||
                        tag.includes("keyboard") ||
                        tag.includes("tile") ||
                        /board|row|tile|keyboard|letter|state/i.test(attrs)
                    ) {
                        found.push({
                            tag,
                            attrs: attrs.slice(0, 250),
                            text: (el.innerText || "").slice(0, 60)
                        });
                    }

                    if (el.shadowRoot) walk(el.shadowRoot);
                }
            }

            walk(document);
            return found;
        }""")

        for item in details:
            print(item)

        input("\nPress Enter to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
