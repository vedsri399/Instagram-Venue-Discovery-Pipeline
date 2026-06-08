import os
from dotenv import load_dotenv
import pandas as pd
from src.extractor import LocalJSONExtractor
from src.parser import InstagramCaptionParser
from src.mapper import GoogleMapsInterface

# Load secure API environment parameters
load_dotenv()

def run_pipeline():
    print("==================================================")
    print("🚀 RUNNING LOCAL ARCHIVE DATA & MAPPING PIPELINE")
    print("==================================================\n")

    # Define standardized artifact file paths
    RAW_JSON_CACHE = os.path.join("data", "raw", "saved_reels_download.json")
    FINAL_CSV_DATA = os.path.join("data", "outputs", "mapped_locations.csv")
    MAP_VIEW_HTML = os.path.join("data", "outputs", "interactive_map_view.html")

    # API Keys Validation
    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_key:
        print("[CRITICAL] Missing GOOGLE_MAPS_API_KEY config. Execution aborted.")
        return

    # --- STAGE 1: LOCAL DATA INGESTION ---
    print("[STAGE 1] Ingesting local file metrics from JSON storage...")
    extractor = LocalJSONExtractor(file_path=RAW_JSON_CACHE)
    downloaded_posts = extractor.load_cached_reels()

    if not downloaded_posts:
        print("[NOTICE] Pipeline halted. Populate data array records to proceed.")
        return

    # Initialize Processing Layers
    ai_parser = InstagramCaptionParser()
    mapper = GoogleMapsInterface(api_key=google_key)
    processed_records = []

    # --- STAGES 2 & 3: PROCESSING & GEOCODING ---
    print("\n[STAGE 2/3] Processing text profiles and tracking map coordinates...")
    for idx, post in enumerate(downloaded_posts):
        caption_snippet = post.get('caption', '')[:40].replace('\n', ' ')
        print(f" -> Processing post {idx + 1}/{len(downloaded_posts)}: \"{caption_snippet}...\"")
        
        # AI parsing logic
        structured_venue = ai_parser.parse_caption(post.get('caption', ''))
        
        if structured_venue:
            print(f"    ✨ Entity Discovered: {structured_venue.venue_name} ({structured_venue.city})")
            
            # Coordinate lookup
            geo_details = mapper.geocode_venue(structured_venue.venue_name, structured_venue.city)
            
            if geo_details['latitude']:
                processed_records.append({
                    "Instagram_URL": post.get('url', ''),
                    "Name": structured_venue.venue_name,
                    "Category": structured_venue.category,
                    "Description": structured_venue.context_note,
                    "Address": geo_details['formatted_address'],
                    "latitude": geo_details['latitude'],
                    "longitude": geo_details['longitude'],
                    "Google_Place_ID": geo_details['place_id']
                })
            else:
                print(f"    ⚠️ Could not geocode '{structured_venue.venue_name}' on Google Maps.")
        else:
            print("    Skip: No explicit local venue resolved by AI.")

    # --- STAGE 4: RENDERING AND COMPILATION ---
    print("\n[STAGE 4] Exporting data registers and compiling map visualization canvas...")
    if processed_records:
        # Export structured data matrices
        os.makedirs(os.path.dirname(FINAL_CSV_DATA), exist_ok=True)
        pd.DataFrame(processed_records).to_csv(FINAL_CSV_DATA, index=False)
        print(f"[SUCCESS] CSV Ledger compiled at: {FINAL_CSV_DATA}")

        # Build and render the browser-ready interactive map canvas view
        mapper.generate_interactive_map_view(processed_records, MAP_VIEW_HTML)
    else:
        print("[WARNING] Zero valid location entries processed successfully. No map files created.")

    print("\n==================================================")
    print("✅ EXECUTION COMPLETE. REVIEWS YOUR OUTPUTS DIRECTORY.")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()