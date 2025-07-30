import asyncio
import time
from playwright.async_api import async_playwright
import subprocess
import os


def open_image(path):
    try:
        subprocess.Popen(["xdg-open", path])
    except FileNotFoundError:
        print(f"Warning: 'xdg-open' not found. Cannot open image {path}.")
    except Exception as e:
        print(f"Error opening image {path}: {e}")


async def process_url(browser_instance, url, screenshot_filename, semaphore):
    async with semaphore:
        page = None
        browser_context = None
        try:
            browser_context = await browser_instance.new_context()
            page = await browser_context.new_page()
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="load", timeout=15000)

            if "tez-tour.com" in url:
                print("checkinf for button 'close'")
                close_button_locator = page.locator("#fancybox-close")
                try:
                    await close_button_locator.wait_for(state="visible", timeout=5000)
                    print("cliking...")
                    await close_button_locator.click()

                    await page.wait_for_selector(
                        "#fancybox-overlay", state="hidden", timeout=3000
                    )
                except Exception as e:
                    print(
                        f"Pop-up close button not found or could't be clicked within time{e}"
                    )

            print(f"Taking screenshot: {screenshot_filename}...")
            await page.screenshot(path=screenshot_filename, full_page=True)
            print(f"Screenshot saved as {screenshot_filename}.")

            open_image(screenshot_filename)

        except Exception as e:
            print(f"An error occurred while processing {url}: {e}")
        finally:
            if page:
                await page.close()
            if browser_context:
                await browser_context.close()


async def main():
    urls = [
        "https://bytur.by/",
        "https://www.tez-tour.com/",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("Browser launched.")

        concurrency_limit = 5
        semaphore = asyncio.Semaphore(concurrency_limit)
        print(f"Concurrency limit set to {concurrency_limit}.")

        tasks = []
        for i, url in enumerate(urls):
            screenshot_name = os.path.join(f"screenshot_{i + 1}.png")
            print(f"\n--- Scheduling processing for {url} ---")
            tasks.append(process_url(browser, url, screenshot_name, semaphore))

        print(
            f"\nStarting {len(tasks)} tasks with a concurrency limit of {concurrency_limit}..."
        )
        await asyncio.gather(*tasks)

        await browser.close()
        print("Browser closed.")

    print("\nAll scheduled tasks completed.")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    total_time = time.time() - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds")
