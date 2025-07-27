import os
from google import genai
from dotenv import load_dotenv
from .config import AGENTS

load_dotenv()
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_agent(agent_name, message_history):
    agent = AGENTS[agent_name]
    prompt = agent["system_prompt"] + "\n\n" + "\n".join(
        f"{m['role'].capitalize()}: {m['message']}" for m in message_history if m.get("message")
    )
    try:
        response = genai_client.models.generate_content(
            model=agent["model"],
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"{agent_name.capitalize()} error: {str(e)}"
