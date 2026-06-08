import googlemaps
import pandas as pd
from typing import List, Dict, Any

class GoogleMapsInterface:
    def __init__(self, api_key: str):
        self.gmaps = googlemaps.Client(key=api_key)

    def geocode_venue(self, venue_name: str, city: str) -> Dict[str, Any]:
        """
        Uses the Places Text Search endpoint to discover the exact coordinates and details of a venue.
        """
        query = f"{venue_name}, {city}"
        try:
            places_result = self.gmaps.places(query=query)
            
            if places_result.get('status') == 'OK' and len(places_result.get('results', [])) > 0:
                top_match = places_result['results'][0]
                
                return {
                    "formatted_address": top_match.get("formatted_address"),
                    "latitude": top_match['geometry']['location']['lat'],
                    "longitude": top_match['geometry']['location']['lng'],
                    "place_id": top_match.get("place_id")
                }
        except Exception as e:
            print(f"[ERROR] Google Maps lookup failed for '{query}': {e}")
            
        return {"formatted_address": None, "latitude": None, "longitude": None, "place_id": None}

    def export_to_mapping_formats(self, processed_data: List[Dict[str, Any]], csv_output_path: str):
        """
        Converts the finalized processing arrays into structural sheets ready for direct Google My Maps imports.
        """
        if not processed_data:
            print("[WARNING] Zero valid location logs generated. Export skipped.")
            return

        df = pd.DataFrame(processed_data)
        
        # Clean up any missed hits
        df = df.dropna(subset=['latitude', 'longitude'])
        
        # Save output to disk
        df.to_csv(csv_output_path, index=False)
        print(f"[SUCCESS] Mapping matrix compiled and saved cleanly to: {csv_output_path}")