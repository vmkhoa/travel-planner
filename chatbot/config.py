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
