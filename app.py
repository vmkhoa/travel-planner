from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from datetime import datetime
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)

mongo = MongoClient("mongodb+srv://vankh:e4mkOZJLxWTkeeXZ@cluster0.x2q91uh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo["travel_demo"]
chat_col = db["chat_history"]

# Gemini API wrapper
def ask_gemini(message_history):
    chat_log = [
        f"{msg['role'].capitalize()}: {msg['message']}"
        for msg in message_history
    ]
    prompt = "\n".join(chat_log)

    try:
        response = genai_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini error: {str(e)}"
    
# Chat Route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["message"]

        # Save user message
        chat_col.insert_one({
            "userId": "demo",
            "role": "user",
            "message": user_input,
            "timestamp": datetime.utcnow()
        })

        # Load last 5 messages for context
        history = list(chat_col.find({"userId": "demo"}).sort("timestamp", -1).limit(5))
        history.reverse()

        # Ask Gemini
        guide_reply = ask_gemini(history)

        # Save guide reply
        chat_col.insert_one({
            "userId": "demo",
            "role": "guide",
            "message": guide_reply,
            "timestamp": datetime.utcnow()
        })

        return redirect("/")

   # Load entire chat history
    history = list(chat_col.find({"userId": "demo"}).sort("timestamp", 1))
    return render_template("index.html", history=history)

@app.route("/plan")
def plan():
    plan_items = []  # Placeholder for future logic
    return render_template("plan.html", plan=plan_items)

if __name__ == "__main__":
    app.run(debug=True)
