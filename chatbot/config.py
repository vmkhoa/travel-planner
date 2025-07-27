import os
import json

# Load ad trigger keywords
TRIGGER_WORDS_PATH = os.path.join(os.path.dirname(__file__), "ad_triggers.txt")
with open(TRIGGER_WORDS_PATH) as f:
    AD_KEYWORDS = [line.strip().lower() for line in f if line.strip()]

# Load sponsor ads
SPONSORS_PATH = os.path.join(os.path.dirname(__file__), "sponsors.json")
with open(SPONSORS_PATH) as f:
    SPONSOR_ADS = json.load(f)
    
AGENTS = {
    "guide": {
        "system_prompt": (
            "You are a friendly and knowledgeable travel guide. "
            "Give helpful, upbeat answers in natural language about places, travel planning, and tips."
        ),
        "model": "gemini-1.5-flash"
    },
    "advertiser": {
        "system_prompt": (
            "You are an advertiser assistant. If the input mentions a location or travel activity, "
            "generate a short, exciting sponsored suggestion. Only respond if a clear promotional fit exists."
        ),
        "model": "gemini-1.5-flash"
    }
}
