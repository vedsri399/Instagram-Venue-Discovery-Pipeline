import os
import json
import time
from typing import List, Dict
from playwright.sync_api import sync_playwright

class InstagramScraper:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")

    def run_automated_download(self) -> List[Dict[str, str]]:
        """
        Launches a headless browser, logs into Instagram, scrapes saved posts/reels,
        and caches them into a local structured JSON file.
        """
        if not self.username or not self.password:
            print("[ERROR] Instagram credentials missing from .env file.")
            return []

        scraped_data = []

        with sync_playwright() as p:
            print(" -> Launching browser instance...")
            # For debugging, you can set headless=False to watch the automation run
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # 1. Handle Login Execution
            print(" -> Navigating to Instagram Login...")
            page.goto("https://www.instagram.com/accounts/login/")
            page.wait_for_selector('input[name="username"]')
            
            page.fill('input[name="username"]', self.username)
            page.fill('input[name="password"]', self.password)
            page.click('button[type="submit"]')
            
            print(" -> Authenticating account credentials...")
            page.wait_for_url("https://www.instagram.com/**")
            time.sleep(5)  # Safe buffer to ensure session cookies settle

            # 2. Navigate straight to the Saved Posts dashboard
            print(" -> Routing to Saved Posts dashboard...")
            page.goto(f"https://www.instagram.com/{self.username}/saved/all-posts/")
            time.sleep(4)

            # 3. Dynamic Infinite Scroll to capture lazily loaded items
            print(" -> Executing viewport scroll optimization...")
            last_height = page.evaluate("document.body.scrollHeight")
            
            # Limit scrolls to prevent account throttling (adjust as needed)
            max_scroll_cycles = 5 
            for _ in range(max_scroll_cycles):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3) # Let content populate
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # 4. Target and Extract individual post nodes
            # Instagram wraps grid posts in standard anchor links containing "/p/" or "/reels/"
            links = page.query_selector_all('a[href*="/p/"], a[href*="/reel/"]')
            post_urls = list(set([f"https://www.instagram.com{link.get_attribute('href')}" for link in links]))
            
            print(f" -> Discovered {len(post_urls)} raw saved links. Extracting details...")

            # 5. Extract Details per post
            # NOTE: Deep scraping captions requires opening each post or parsing network traffic.
            # As a standard portfolio strategy, we fetch structural meta-tags or fallback summaries.
            for idx, url in enumerate(post_urls[:15]): # Limiting batch scope for safety
                try:
                    page.goto(url)
                    page.wait_for_selector('h1') # Captions are typically stored inside h1 tags on desktop layouts
                    caption_element = page.query_selector('h1')
                    caption_text = caption_element.inner_text() if caption_element else ""
                    
                    scraped_data.append({
                        "url": url,
                        "caption": caption_text
                    })
                except Exception as e:
                    print(f"    ⚠️ Could not fully parse metrics for post {idx+1}: {e}")

            browser.close()

        # Save the live-downloaded data to your JSON storage system
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=4, ensure_ascii=False)
            
        print(f"[SUCCESS] Download completed. Cached {len(scraped_data)} entries directly into {self.output_path}")
        return scraped_data