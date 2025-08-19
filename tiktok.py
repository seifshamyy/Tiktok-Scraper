import csv
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager


def setup_driver():
    """Set up Firefox driver with headless mode"""
    firefox_options = Options()
    firefox_options.add_argument("--width=1920")
    firefox_options.add_argument("--height=1080")
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--disable-gpu")
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")

    print("🦊 Setting up Firefox driver...")
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver


def scroll_page(driver, scrolls=50, delay=4):
    """Scroll down the page to load more content"""
    for i in range(scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)  # longer wait to let videos load
        print(f"   Scrolled {i+1}/{scrolls} times...")


def extract_tiktok_links(search_query, output_file="tiktok_links.csv", max_scrolls=50):
    """Extract TikTok video links from search results"""
    driver = setup_driver()
    video_links = set()  # use set for auto-deduplication

    try:
        search_url = f"https://www.tiktok.com/search?lang=en&q={search_query}"
        print(f"🌐 Navigating to: {search_url}")
        driver.get(search_url)

        print("⏳ Waiting for page to load...")
        time.sleep(7)

        print("📜 Scrolling page...")
        scroll_page(driver, max_scrolls)

        selectors_to_try = [
            "a[href*='/video/']",
            "div[data-e2e='search-result'] a",
            "[data-e2e='search-result-video'] a",
            "div[data-e2e='search-video-item'] a"
        ]

        print("🔍 Extracting video links from all selectors...")
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                before_count = len(video_links)
                for element in elements:
                    href = element.get_attribute("href")
                    if href and "/video/" in href:
                        video_links.add(href)
                print(f"   Selector '{selector}' → found {len(video_links) - before_count} new links")
            except Exception as e:
                print(f"   Error with selector {selector}: {e}")
                continue

        if not video_links:
            print("⚠️ No links found. TikTok may block bots or require login.")
            return []

        # Save CSV locally
        print(f"💾 Saving {len(video_links)} unique links to {output_file}...")
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Video_Link", "Index", "Search_Term"])
            for idx, link in enumerate(video_links, 1):
                writer.writerow([link, idx, search_query])

        return list(video_links)

    except TimeoutException:
        print("❌ Timeout: Page took too long to load.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🦊 Closing Firefox...")
        driver.quit()


def send_to_webhook(file_path, webhook_url):
    """Send the generated CSV file to the webhook"""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "text/csv")}
            response = requests.post(webhook_url, files=files)
            if response.status_code == 200:
                print(f"✅ Successfully sent CSV to webhook: {webhook_url}")
            else:
                print(f"⚠️ Webhook error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Failed to send CSV: {e}")


def main():
    print("🦊 TikTok Scraper Starting...")
    print("=" * 60)

    search_term = "عقارات"
    output_filename = "tiktok_links_firefox.csv"
    scroll_count = 50  # more scrolls for better coverage
    webhook_url = "https://primary-production-9e01d.up.railway.app/webhook/64226a93-e904-494e-b4eb-6b5db7503d89"

    links = extract_tiktok_links(search_term, output_filename, scroll_count)

    if links:
        print(f"\n📊 Extracted {len(links)} unique links.")
        send_to_webhook(output_filename, webhook_url)
    else:
        print("⚠️ No links extracted.")

    print("\n✨ Script completed!")


if __name__ == "__main__":
    main()

