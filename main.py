import os
from dotenv import load_dotenv
from src.extractor import InstagramScraper
from src.parser import InstagramCaptionParser
from src.mapper import GoogleMapsInterface

load_dotenv()

def run_pipeline():
    print("==================================================")
    print("🚀 RUNNING AUTOMATED DOWNLOAD & MAPPING ENGINE")
    print("==================================================\n")

    # Define standardized artifact file paths
    RAW_JSON_CACHE = os.path.join("data", "raw", "saved_reels_download.json")
    FINAL_CSV_DATA = os.path.join("data", "outputs", "mapped_locations.csv")
    MAP_VIEW_HTML = os.path.join("data", "outputs", "interactive_map_view.html")

    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_key:
        print("[CRITICAL] Missing configuration keys. Execution aborted.")
        return

    # --- STAGE 1: LIVE INSTAGRAM DOWNLOAD ---
    print("[STAGE 1] Initiating automated Instagram Saved Reels downloadd...")
    scraper = InstagramScraper(output_path=RAW_JSON_CACHE)
    downloaded_posts = scraper.run_automated_download()

    if not downloaded_posts:
        print("[ERROR] No post content downloaded. Verify credentials or layout selectors.")
        return

    # Initialize Processing Layers
    ai_parser = InstagramCaptionParser()
    mapper = GoogleMapsInterface(api_key=google_key)
    processed_records = []

    # --- STAGES 2 & 3: PROCESSING & GEOCODING ---
    print("\n[STAGE 2/3] Processing text profiles and tracking map coordinates...")
    for idx, post in enumerate(downloaded_posts):
        print(f" -> Processing element {idx + 1}/{len(downloaded_posts)}...")
        
        # AI parsing logic
        structured_venue = ai_parser.parse_caption(post['caption'])
        
        if structured_venue:
            print(f"    ✨ Entity Discovered: {structured_venue.venue_name} in {structured_venue.city}")
            # Coordinate lookup
            geo_details = mapper.geocode_venue(structured_venue.venue_name, structured_venue.city)
            
            if geo_details['latitude']:
                processed_records.append({
                    "Instagram_URL": post['url'],
                    "Name": structured_venue.venue_name,
                    "Category": structured_venue.category,
                    "Description": structured_venue.context_note,
                    "Address": geo_details['formatted_address'],
                    "latitude": geo_details['latitude'],
                    "longitude": geo_details['longitude'],
                    "Google_Place_ID": geo_details['place_id']
                })

    # --- STAGE 4: RENDERING AND COMPILATION ---
    print("\n[STAGE 4] Exporting final database files and visualizations...")
    # Export data matrices
    import pandas as pd
    if processed_records:
        os.makedirs(os.path.dirname(FINAL_CSV_DATA), exist_ok=True)
        pd.DataFrame(processed_records).to_csv(FINAL_CSV_DATA, index=False)
        print(f"[SUCCESS] CSV Ledger compiled at: {FINAL_CSV_DATA}")

    # Build and render the browser-ready interactive map canvas view
    mapper.generate_interactive_map_view(processed_records, MAP_VIEW_HTML)

    print("\n==================================================")
    print("✅ EXECUTION COMPLETE. OPEN THE HTML FILE TO VIEW THE MAP.")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()