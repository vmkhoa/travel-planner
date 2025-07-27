import os
from google import genai
from dotenv import load_dotenv
from .config import AGENTS
from chatbot.config import AD_KEYWORDS, SPONSOR_ADS

load_dotenv()
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_agent(agent, message_history):
    chat_log = [
        f"{msg['role'].capitalize()}: {msg['message']}" 
        for msg in message_history
    ]
    prompt = "\n".join(chat_log)

    if agent == "advertiser":
        # Dynamically load relevant ad options from config
        from chatbot.config import SPONSOR_ADS
        ad_context = []

        for keyword in SPONSOR_ADS:
            if keyword in prompt.lower():
                for ad in SPONSOR_ADS[keyword]:
                    ad_context.append(
                        f"- {ad['title']}: {ad['message']} [Link: {ad['link']}]"
                    )

        if ad_context:
            prompt += "\n\nRelevant sponsor offers:\n" + "\n".join(ad_context)
            prompt += (
                "\n\nAdvertiser: Pick one ad and rephrase it naturally. Keep the link clear and helpful."
            )

    prompt += f"\n{agent.capitalize()}:"

    try:
        response = genai_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"{agent.capitalize()} error: {str(e)}"

