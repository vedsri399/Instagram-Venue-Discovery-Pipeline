import googlemaps
import pandas as pd
import os
from typing import List, Dict, Any

class GoogleMapsInterface:
    def __init__(self, api_key: str):
        self.gmaps = googlemaps.Client(key=api_key)

    def geocode_venue(self, venue_name: str, city: str) -> Dict[str, Any]:
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

    def generate_interactive_map_view(self, processed_data: List[Dict[str, Any]], html_output_path: str):
        """
        Compiles an interactive HTML map view that can be launched instantly in any browser.
        """
        if not processed_data:
            return

        import folium  # Lightweight interactive map builder

        df = pd.DataFrame(processed_data).dropna(subset=['latitude', 'longitude'])
        if df.empty:
            print("[WARNING] View engine mapping aborted: No valid geo coordinates found.")
            return

        # Center the map canvas on the average coordinate node of your dataset
        center_lat = df['latitude'].mean()
        center_lng = df['longitude'].mean()
        interactive_map = folium.Map(location=[center_lat, center_lng], zoom_start=12, tiles="OpenStreetMap")

        # Drop markers on the map canvas
        for _, row in df.iterrows():
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 200px;">
                <h4><b>{row['Name']}</b></h4>
                <p style="color: gray; font-size: 11px;">{row['Category']}</p>
                <p>"{row['Description']}"</p>
                <a href="{row['Instagram_URL']}" target="_blank" style="color: #E1306C; font-weight: bold;">View Original Reel</a>
            </div>
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row['Name'],
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(interactive_map)

        os.makedirs(os.path.dirname(html_output_path), exist_ok=True)
        interactive_map.save(html_output_path)
        print(f"[SUCCESS] Standalone HTML Map View compiled successfully at: {html_output_path}")