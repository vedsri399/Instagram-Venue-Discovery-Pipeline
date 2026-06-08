import os
import time  # NEW: Required for pacing our API requests
import pandas as pd
from dotenv import load_dotenv
from src.extractor import InstagramBulkExtractor
from src.parser import InstagramCaptionParser
from src.mapper import GoogleMapsInterface

# Load secure API environment parameters from local configurations
load_dotenv()

def run_pipeline():
    print("==================================================")
    print("🚀 RUNNING FULL BULK INSTAGRAM ARCHIVE PIPELINE   ")
    print("🎯 TARGET: FOOD, BAR, & LOCAL EVENT HOTSPOTS      ")
    print("==================================================\n")

    # Define standardized artifact file paths
    RAW_DATA_DIR = os.path.join("data", "raw")
    FINAL_CSV_DATA = os.path.join("data", "outputs", "mapped_locations.csv")
    MAP_VIEW_HTML = os.path.join("data", "outputs", "interactive_map_view.html")

    # Core Security Key Validation
    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_key:
        print("[CRITICAL] Missing GOOGLE_MAPS_API_KEY in environment configuration.")
        return

    # --- STAGE 1: UNIFIED ARCHIVE DATA INGESTION ---
    extractor = InstagramBulkExtractor(raw_data_dir=RAW_DATA_DIR)
    all_posts = extractor.load_all_saved_items()

    if not all_posts:
        print("[NOTICE] Pipeline halted. Ensure your json files exist inside data/raw/ and contain items.")
        return

    # Initialize Processing Layers
    ai_parser = InstagramCaptionParser()
    mapper = GoogleMapsInterface(api_key=google_key)
    processed_records = []

    # --- STAGES 2 & 3: CONTEXTUAL PROCESSING & GEOCODING ---
    print("\n[STAGE 2/3] Executing AI entity extractions & coordinate tracing...")
    for idx, post in enumerate(all_posts):
        caption_snippet = post.get('caption', '')[:40].replace('\n', ' ')
        print(f" -> Analyzing item {idx + 1}/{len(all_posts)}: \"{caption_snippet}...\"")
        
        # Extract structured location data and check the guardrail filter
        structured_venue = ai_parser.parse_caption(post.get('caption', ''))
        
        # NEW: Rate-limiting safety pause. Spacing calls out to stay completely clear of the 15 RPM Free Tier cap.
        print("    ⏳ Pacing API cadence (4s cooldown)...")
        time.sleep(4)
        
        # Check if Gemini found a valid food/bar venue and flagged it to be included
        if structured_venue and structured_venue.is_food_or_bar_event and structured_venue.venue_name:
            detected_city = structured_venue.city if structured_venue.city else "Chicago"
            print(f"    ✨ Target Match Discovered: {structured_venue.venue_name} ({detected_city})")
            
            # Fetch coordinates from Google Maps Places API
            geo_details = mapper.geocode_venue(structured_venue.venue_name, detected_city)
            
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
            print("    🛡️ Skipped: Item does not match food, bar, or local culinary event criteria.")

    # --- STAGE 4: COMPILATION & VIEW RENDERING ---
    print("\n[STAGE 4] Exporting data registers and compiling map canvas...")
    if processed_records:
        os.makedirs(os.path.dirname(FINAL_CSV_DATA), exist_ok=True)
        pd.DataFrame(processed_records).to_csv(FINAL_CSV_DATA, index=False)
        print(f"[SUCCESS] CSV Ledger compiled cleanly at: {FINAL_CSV_DATA}")
        mapper.generate_interactive_map_view(processed_records, MAP_VIEW_HTML)
    else:
        print("[WARNING] Zero valid location entries processed successfully. No map files created.")

    print("\n==================================================")
    print("✅ PIPELINE EXECUTION COMPLETE. CHECK YOUR OUTPUTS.")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()