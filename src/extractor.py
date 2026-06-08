import os
import json
from typing import List, Dict

class LocalJSONExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_cached_reels(self) -> List[Dict[str, str]]:
        """
        Reads the locally stored JSON cache file containing downloaded or mock
        Instagram reels data, prepping them for the AI parser module.
        """
        if not os.path.exists(self.file_path):
            print(f"[WARNING] Local JSON cache archive missing at: {self.file_path}")
            print(" -> Please ensure your saved links or test payloads exist in that path location.")
            return []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            print(f"[SUCCESS] Ingested {len(scraped_data)} cached data records from local disk storage.")
            return scraped_data

        except json.JSONDecodeError:
            print(f"[ERROR] The file at {self.file_path} is not valid JSON. Check formatting parameters.")
            return []
        except Exception as e:
            print(f"[ERROR] An unexpected read error occurred: {e}")
            return []