import asyncio
import time
from playwright.async_api import async_playwright
import subprocess


def open_image(path):
    try:
        subprocess.Popen(["xdg-open", path])
    except FileNotFoundError:
        print(f"Warning: 'xdg-open' not found. Cannot open image {path}.")
    except Exception as e:
        print(f"Error opening image {path}: {e}")


async def process_url(browser_instance, url, semaphore):
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
                    # await close_button_locator.wait_for(state="visible", timeout=5000)
                    print("cliking...")
                    await close_button_locator.click()

                    await page.wait_for_selector(
                        "#fancybox-overlay", state="hidden", timeout=3000
                    )
                except Exception as e:
                    print(
                        f"Pop-up close button not found or could't be clicked within time{e}"
                    )

                price_elements = await page.locator(".title-price").all()

            if "tez-tour.com" in url:
                print(f"Extracting prices from {url}...")
                price_elements = await page.locator(".tile-price").all()

                if price_elements:
                    print(f"Found {len(price_elements)} price elements:")
                    extracted_prices = []
                    for element in price_elements:
                        price_text = await element.text_content()
                        if price_text:
                            cleaned_price = price_text.strip().replace(" ", "")
                            print(f" - {cleaned_price}")
                            extracted_prices.append(cleaned_price)
                    # return extracted_prices
                else:
                    print("No elements with class 'tile-price' found on this page.")
            else:
                print(f"Skipping price extraction for {url} as it's not tez-tour.com.")

            # if "https://www.teztour.by/ru/minsk/sale.html" in url:
            #     print("Start search sales...")
            #     prices = await page.locator(".hotel-list-td4").all()
            #     # places = await page.locator("[class*='country']").all()
            #     places = await page.locator(".country-1104").all()
            #     print(len(prices))
            #     print(len(places))
            #     print("printing all prices")
            #     for element in prices:
            #         price_text = await element.text_content()
            #         print(price_text)
            #     for element in places:
            #         place_text = await element.text_content()
            #         print(place_text)

            # print(f"Taking screenshot: {screenshot_filename}...")
            # await page.screenshot(path=screenshot_filename, full_page=True)
            # print(f"Screenshot saved as {screenshot_filename}.")
            #
            # open_image(screenshot_filename)

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
        "https://www.teztour.by/ru/minsk/sale.html",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("Browser launched.")

        concurrency_limit = 5
        semaphore = asyncio.Semaphore(concurrency_limit)
        print(f"Concurrency limit set to {concurrency_limit}.")

        tasks = []
        for i, url in enumerate(urls):
            # screenshot_name = os.path.join(f"screenshot_{i + 1}.png")
            print(f"\n--- Scheduling processing for {url} ---")
            tasks.append(process_url(browser, url, semaphore))

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
