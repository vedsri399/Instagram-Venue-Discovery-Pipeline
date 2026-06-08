import os
import time  # NEW: Adds a local retry pause if Google throttles us
from typing import Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError  # NEW: Catch exact Google API errors

class ExtractedVenue(BaseModel):
    is_food_or_bar_event: bool = Field(description="True ONLY for restaurants, bars, cafes, lounges, or culinary popups.")
    venue_name: Optional[str] = Field(default=None, description="Formal venue name.")
    city: Optional[str] = Field(default=None, description="City location.")
    category: Optional[Literal['Restaurant', 'Bar', 'Popup Event', 'Cafe']] = Field(default=None)
    context_note: Optional[str] = Field(default=None, description="1-sentence summary recommendation.")

class InstagramCaptionParser:
    def __init__(self):
        self.client = genai.Client()

    def parse_caption(self, caption_text: str) -> Optional[ExtractedVenue]:
        if not caption_text or len(caption_text.strip()) < 5:
            return None

        prompt = f"""
        Analyze this Instagram caption. If it is an actual physical food establishment, bar, or culinary popup, 
        set `is_food_or_bar_event` to true and extract details. Otherwise set it to false and leave fields null.
        
        Caption Text:
        \"\"\"{caption_text}\"\"\"
        """

        # Self-healing retry logic block (Attempts up to 3 times if throttled)
        max_retries = 3
        backoff_delay = 10  # Seconds to wait if we hit a 429

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ExtractedVenue,
                        temperature=0.0
                    ),
                )
                return ExtractedVenue.model_validate_json(response.text)

            except APIError as e:
                # Check explicitly for the 429 Rate Limit status code
                if e.code == 429:
                    print(f"\n    ⚠️ [RATE LIMIT CHILL] Google Free Tier limit hit. Retrying attempt {attempt + 1}/{max_retries} in {backoff_delay}s...")
                    time.sleep(backoff_delay)
                    backoff_delay *= 2  # Exponential backoff (10s, then 20s)
                    continue
                else:
                    print(f"[ERROR] Gemini API Error: {e}")
                    return None
            except Exception as e:
                print(f"[ERROR] Unexpected parsing error: {e}")
                return None

        print("    ❌ [FAILED] Skipped post after failing multiple rate limit retries.")
        return None