import os
import json
from typing import List, Dict

class InstagramBulkExtractor:
    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = raw_data_dir
        self.posts_file = os.path.join(raw_data_dir, "saved_posts.json")
        self.collections_file = os.path.join(raw_data_dir, "saved_collections.json")

    def _parse_label_values(self, label_values_list: List[Dict]) -> tuple:
        """
        Helper method to look inside the modern Meta 'label_values' array structure
        and extract the targeted URL and Caption parameters.
        """
        url = None
        caption = None

        for Entry in label_values_list:
            label = Entry.get("label")
            value = Entry.get("value")
            
            if label == "URL":
                # Prefer 'href' if present, fallback to raw string value
                url = Entry.get("href", value)
            elif label == "Caption":
                caption = value

        return url, caption

    def load_all_saved_items(self) -> List[Dict[str, str]]:
        """
        Combs through both files, normalizes their modern Meta schema profiles,
        deduplicates by URL, and updates the processing log ledger queue.
        """
        combined_posts = {}

        # 1. Ingest Personal Saved Posts File
        if os.path.exists(self.posts_file):
            print("[STAGE 1A] Extracting from modern saved_posts.json schema...")
            try:
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if data is wrapped in a top-level dict or direct list layout
                items_list = data if isinstance(data, list) else data.get("saved_saved_media", []) or data.get("saved_posts", [])
                
                for item in items_list:
                    label_values = item.get("label_values", [])
                    if label_values:
                        url, caption = self._parse_label_values(label_values)
                        if url and caption:
                            combined_posts[url] = caption
                            
            except Exception as e:
                print(f"  ⚠️ Error parsing saved_posts.json template: {e}")
        else:
            print("  ℹ️ saved_posts.json missing from workspace directory. Skipping.")

        # 2. Ingest Saved Collections File
        if os.path.exists(self.collections_file):
            print("[STAGE 1B] Extracting from modern saved_collections.json schema...")
            try:
                with open(self.collections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                collections_list = data if isinstance(data, list) else data.get("saved_collections", []) or data.get("collections_saved_collections", [])

                for collection in collections_list:
                    # Collections pack their posts inside an underlying media collection array block
                    media_list = collection.get("media_list", []) or collection.get("saved_media", [])
                    
                    for item in media_list:
                        label_values = item.get("label_values", [])
                        if label_values:
                            url, caption = self._parse_label_values(label_values)
                            if url and caption:
                                combined_posts[url] = caption
                                
            except Exception as e:
                print(f"  ⚠️ Error parsing saved_collections.json template: {e}")
        else:
            print("  ℹ️ saved_collections.json missing from workspace directory. Skipping.")

        # Map combined dictionary pool back into structured rows array list
        normalized_output = [{"url": url, "caption": cap} for url, cap in combined_posts.items()]
        print(f"\n[SUCCESS] Extracted {len(normalized_output)} unique entries matching the updated format.")
        return normalized_output