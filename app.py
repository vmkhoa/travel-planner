from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from datetime import datetime, timedelta
from chatbot.agents import ask_agent
import os

app = Flask(__name__)

mongo = MongoClient("mongodb+srv://vankh:e4mkOZJLxWTkeeXZ@cluster0.x2q91uh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo["travel_demo"]
chat_col = db["chat_history"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["message"]
        now = datetime.utcnow()

        # Save user message
        chat_col.insert_one({
            "userId": "demo",
            "role": "user",
            "message": user_input,
            "timestamp": now
        })

        # Get recent context
        history = list(chat_col.find({"userId": "demo"}).sort("timestamp", -1).limit(10))
        history.reverse()

        # Guide replies
        guide_reply = ask_agent("guide", history)
        chat_col.insert_one({
            "userId": "demo",
            "role": "guide",
            "message": guide_reply,
            "timestamp": datetime.utcnow()
        })

        # Trigger advertiser if needed
        ad_keywords = ["boston", "hotel", "restaurant", "event"]
        combined_text = user_input.lower() + " " + guide_reply.lower()
        last_ad = chat_col.find_one({"userId": "demo", "role": "advertiser"}, sort=[("timestamp", -1)])
        cooldown_ok = not last_ad or (now - last_ad["timestamp"]) > timedelta(minutes=2)

        if any(k in combined_text for k in ad_keywords) and cooldown_ok:
            ad_reply = ask_agent("advertiser", [{"role": "user", "message": combined_text}])
            chat_col.insert_one({
                "userId": "demo",
                "role": "advertiser",
                "message": ad_reply,
                "timestamp": datetime.utcnow()
            })

        return redirect("/")

    # Load chat history
    history = list(chat_col.find({"userId": "demo"}).sort("timestamp", 1))
    return render_template("index.html", history=history)

@app.route("/plan")
def plan():
    return render_template("plan.html", plan=[])

if __name__ == "__main__":
    app.run(debug=True)