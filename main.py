import os
from dotenv import load_dotenv
from src.extractor import InstagramExtractor
from src.parser import InstagramCaptionParser
from src.mapper import GoogleMapsInterface

# Load environmental configs
load_dotenv()

def run_pipeline():
    print("==================================================")
    print("🚀 STARTING INSTAGRAM-TO-MAPS AUTOMATED PIPELINE   ")
    print("==================================================\n")

    # Path Configuration
    RAW_INPUT_PATH = os.path.join("data", "raw", "saved_posts.json")
    OUTPUT_CSV_PATH = os.path.join("data", "outputs", "my_saved_places.csv")

    # API Keys Validation
    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_key:
        print("[CRITICAL] Missing GOOGLE_MAPS_API_KEY in environment variables.")
        return

    # 1. Extraction Phase
    print("[STAGE 1] Ingesting Instagram Local Export Archives...")
    extractor = InstagramExtractor(RAW_INPUT_PATH)
    raw_posts = extractor.extract_saved_posts()
    
    if not raw_posts:
        print(f"\n[NOTICE] Please drop a mock or real 'saved_posts.json' file into {RAW_INPUT_PATH} to run the full stack.")
        print("Pipeline terminated gracefully.")
        return

    # Initialize processing systems
    ai_parser = InstagramCaptionParser()
    mapper = GoogleMapsInterface(api_key=google_key)
    
    final_locations_pool = []

    # 2. Parsing & Geocoding Phase
    print("\n[STAGE 2/3] Processing text with AI & fetching coordinates from Google Maps...")
    for idx, post in enumerate(raw_posts):
        print(f" -> Processing post {idx + 1}/{len(raw_posts)}...")
        
        # AI Extraction
        structured_venue = ai_parser.parse_caption(post['caption'])
        
        if structured_venue:
            print(f"    ✨ AI Found: {structured_venue.venue_name} ({structured_venue.city})")
            
            # Map Geocoding
            geo_details = mapper.geocode_venue(structured_venue.venue_name, structured_venue.city)
            
            if geo_details['latitude']:
                # Merge data payloads
                location_record = {
                    "Instagram_URL": post['url'],
                    "Name": structured_venue.venue_name,
                    "Category": structured_venue.category,
                    "Description": structured_venue.context_note,
                    "Address": geo_details['formatted_address'],
                    "latitude": geo_details['latitude'],
                    "longitude": geo_details['longitude'],
                    "Google_Place_ID": geo_details['place_id']
                }
                final_locations_pool.append(location_record)
            else:
                print(f"    ⚠️ Could not geocode '{structured_venue.venue_name}' on Google Maps.")
        else:
            print("    Skip: No valid local venue found in caption text.")

    # 4. Compilation & Export Phase
    print("\n[STAGE 4] Saving compilation outputs...")
    mapper.export_to_mapping_formats(final_locations_pool, OUTPUT_CSV_PATH)
    print("\n==================================================")
    print("✅ PIPELINE EXECUTION COMPLETE. READY FOR MY MAPS.")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()