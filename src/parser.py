import os
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Define the exact data contract we want the AI to return
class ExtractedVenue(BaseModel):
    venue_name: str = Field(description="The formal name of the restaurant, bar, or popup event venue mentioned.")
    city: str = Field(description="The specific city or metropolitan neighborhood where this venue is located.")
    category: str = Field(description="Strictly classify as: 'Restaurant', 'Bar', 'Popup Event', or 'Cafe'.")
    context_note: str = Field(description="A short 1-sentence summary of why the creator recommends this spot.")

class InstagramCaptionParser:
    def __init__(self):
        # Initializes the client using the GEMINI_API_KEY environment variable automatically
        self.client = genai.Client()

    def parse_caption(self, caption_text: str) -> Optional[ExtractedVenue]:
        """
        Submits unstructured caption data to Gemini and forces a structured JSON schema output.
        """
        if not caption_text or len(caption_text.strip()) < 10:
            return None

        prompt = f"""
        Analyze the following Instagram post caption describing a local hotspot, venue, or popup event.
        Extract the structured details cleanly. If no explicit venue or restaurant can be found, return null.
        
        Caption Text:
        \"\"\"{caption_text}\"\"\"
        """

        try:
            # We utilize the fast, highly capable gemini-2.5-flash model for cost-effective parsing
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedVenue,
                    temperature=0.1 # Low temperature ensures deterministic, analytical extractions
                ),
            )
            
            # Validate and parse the text directly back into our Pydantic schema object
            return ExtractedVenue.model_validate_json(response.text)
            
        except Exception as e:
            print(f"[ERROR] Failed parsing caption with Gemini API: {e}")
            return None