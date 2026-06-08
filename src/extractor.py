import json
import os
from typing import List, Dict

class InstagramExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_saved_posts(self) -> List[Dict[str, str]]:
        """
        Parses Instagram's downloaded 'saved_posts.json' file.
        Returns a list of dictionaries containing URLs and captions if available.
        """
        if not os.path.exists(self.file_path):
            print(f"[WARNING] Data export file not found at: {self.file_path}")
            return []

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        extracted_posts = []
        
        # Instagram's export schema typically nests saved media links under a list
        # Adjust key parsing depending on the exact version of the Meta data export schema
        saved_items = data.get("saved_saved_media", []) or data.get("saved_posts", [])
        
        for item in saved_items:
            # Safely extract post details
            title = item.get("title", "") # Often holds the original caption or account name
            string_map_data = item.get("string_map_data", {})
            
            # Extract URL
            link_info = string_map_data.get("Link", {})
            url = link_info.get("href", "")
            
            if url:
                extracted_posts.append({
                    "url": url,
                    "caption": title
                })
                
        print(f"[INFO] Successfully extracted {len(extracted_posts)} saved entries from local archive.")
        return extracted_posts