<div align="center">

# 📍 Instagram Venue Discovery Pipeline

**Turn your Instagram saved posts into a live, interactive map — automatically.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Scraper-Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![Claude API](https://img.shields.io/badge/AI-Claude%20API-7C3AED?style=flat-square)](https://anthropic.com)
[![Folium](https://img.shields.io/badge/Maps-Folium-77B829?style=flat-square)](https://python-visualization.github.io/folium)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## The problem

I had 200+ Instagram saved posts — restaurants, popup dinners, bars, markets — all sitting in a list I never opened. No way to see *where* they all were, no way to plan a night out from them.

This pipeline fixes that. Run it once, get a map. Run it again, it only processes new posts.

---

## How it works

```
Instagram saved posts
        │
        ▼
 Playwright scraper          ← logs into your own account, no third-party auth
        │
        ▼
  Caption parser             ← cleans text, extracts hashtags, deduplicates
        │
        ▼
  Claude API enricher        ← extracts venue name + city + type from messy captions
        │
        ▼
  Google Geocoding API       ← converts "Smyth Restaurant Chicago" → lat/lng
        │
        ▼
    SQLite store             ← incremental: reruns skip already-processed posts
        │
        ├──▶  Folium HTML map    (open in browser or deploy to GitHub Pages)
        └──▶  KML export         (import directly into Google My Maps)
```

The key design decision: Instagram captions are chaos — emojis, run-on sentences, zero consistent structure. Regex fails immediately. A single Claude API call per post extracts clean, structured JSON (`venue_name`, `venue_city`, `venue_type`) from any caption format, for a fraction of a cent per post.

---

## Demo

> *Add a screenshot of your map here once you've run the pipeline.*

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/instagram-map.git
cd instagram-map
pip install -r requirements.txt
playwright install chromium
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Then edit `.env`:

```env
ANTHROPIC_API_KEY=your_key_here
GOOGLE_GEOCODING_API_KEY=your_key_here
```

**Get your keys:**
- Anthropic API → [console.anthropic.com](https://console.anthropic.com)
- Google Geocoding API → [console.cloud.google.com](https://console.cloud.google.com) (enable "Geocoding API")

### 3. Log in to Instagram (one-time only)

```bash
python scraper/instagram.py --login
```

A real browser window opens. Log in manually, then press Enter. Your session is saved locally — you won't need to do this again.

### 4. Run the full pipeline

```bash
python run.py
```

Output:
- `output/map.html` — interactive map, open in any browser
- `output/locations.kml` — import into [Google My Maps](https://www.google.com/mymaps)

---

## Project structure

```
instagram-map/
├── scraper/
│   └── instagram.py        # Playwright browser automation
├── pipeline/
│   ├── parser.py            # Caption cleaning, hashtag extraction, SQLite I/O
│   ├── enricher.py          # Claude API — venue extraction from captions
│   └── geocoder.py          # Venue name → lat/lng (Google or Nominatim)
├── output/
│   ├── map_generator.py     # Folium interactive HTML map
│   └── kml_exporter.py      # KML file for Google My Maps
├── data/
│   └── locations.db         # SQLite store (gitignored)
├── run.py                   # One-command pipeline orchestrator
├── .env.example
└── requirements.txt
```

---

## Configuration

Edit the top of `run.py` to tune behaviour:

| Option | Default | Description |
|---|---|---|
| `MAX_POSTS` | `100` | Max saved posts to scrape per run |
| `GEOCODER` | `"google"` | `"google"` or `"nominatim"` (free, no key needed) |
| `ENRICH_DELAY` | `0.5s` | Pause between Claude API calls |
| `SKIP_EXISTING` | `True` | Reruns skip already-processed posts |

---

## Map output options

**Option A — Self-hosted HTML (Folium)**
Open `output/map.html` directly, or deploy to GitHub Pages for a shareable live link.

**Option B — Google My Maps**
1. Go to [Google My Maps](https://www.google.com/mymaps)
2. Create map → Import → Upload `output/locations.kml`
3. Your pins appear with venue names and types as labels

---

## Cost

Claude API calls are billed per token. Location extraction from a typical Instagram caption costs roughly **$0.0001 per post** (claude-sonnet). Running the pipeline on 200 posts costs less than $0.02 total.

Google Geocoding API has a free tier of 40,000 requests/month. For personal use you will not exceed this.

---

## Notes on Instagram's Terms of Service

This tool only accesses **your own** saved posts using your own authenticated session. It does not scrape public profiles, does not collect other users' data, and does not interact with Instagram at scale. Use responsibly and avoid running it at high frequency.

---

## License

MIT — do whatever you want with it.
