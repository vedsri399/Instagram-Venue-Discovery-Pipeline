import os
import time
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class ExtractedVenue(BaseModel):
    venue_name: str = Field(description="The formal name of the restaurant, bar, or popup event venue mentioned.")
    city: str = Field(description="The specific city or metropolitan neighborhood where this venue is located.")
    category: str = Field(description="Strictly classify as: 'Restaurant', 'Bar', 'Popup Event', or 'Cafe'.")
    context_note: str = Field(description="A short 1-sentence summary of why the creator recommends this spot.")

class InstagramCaptionParser:
    def __init__(self):
        self.client = genai.Client()

    def parse_caption(self, caption_text: str, max_retries: int = 3, initial_delay: int = 2) -> Optional[ExtractedVenue]:
        """
        Submits unstructured caption data to Gemini and forces a structured JSON schema output.
        Includes a retry loop with exponential backoff to handle temporary 503 server overloads.
        """
        if not caption_text or len(caption_text.strip()) < 10:
            return None

        prompt = f"""
        Analyze the following Instagram post caption describing a local hotspot, venue, or popup event.
        Extract the structured details cleanly. If no explicit venue or restaurant can be found, return null.
        
        Caption Text:
        \"\"\"{caption_text}\"\"\"
        """

        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ExtractedVenue,
                        temperature=0.1
                    ),
                )
                return ExtractedVenue.model_validate_json(response.text)
                
            except Exception as e:
                # Check if it looks like a server traffic / capacity error
                err_msg = str(e)
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
                    print(f"    ⏳ [Server Busy] Gemini experiencing high demand. Retrying attempt {attempt + 1}/{max_retries} in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Double the wait time for the next attempt (Exponential Backoff)
                else:
                    # If it's a different error (e.g. invalid API key), fail immediately instead of retrying
                    print(f"[ERROR] Fatal parser error: {e}")
                    return None
                    
        print(f"[ERROR] Failed to parse caption after {max_retries} retry attempts due to server availability.")
        return None