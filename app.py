from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from datetime import datetime, timedelta
from chatbot.agents import ask_agent
import os
from chatbot.config import AD_KEYWORDS, SPONSOR_ADS
import random

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
        combined_text = user_input.lower() + " " + guide_reply.lower()
        last_ad = chat_col.find_one({"userId": "demo", "role": "advertiser"}, sort=[("timestamp", -1)])
        cooldown_ok = not last_ad or (now - last_ad["timestamp"]) > timedelta(minutes=2)

        if any(k in combined_text for k in SPONSOR_ADS) and cooldown_ok:
            matched_ads = []
            for keyword in SPONSOR_ADS:
                if keyword in combined_text:
                    matched_ads.extend(SPONSOR_ADS[keyword])

            if matched_ads:
                ad = random.choice(matched_ads)

            # Let Gemini rewrite the ad copy, but include the context
            ad_prompt = (
                f"Write a short, friendly sponsored message (2–3 lines max) for the following offer:\n"
                f"Title: {ad['title']}\n"
                f"Message: {ad['message']}\n"
                f"Don't mention the word 'ad'. Just make it natural and relevant.\n"
            )

            gemini_response = ask_agent("advertiser", [{"role": "user", "message": ad_prompt}])

            # Insert clickable link manually
            ad_reply = f"""
            <b>{ad['title']}</b>: {gemini_response.strip()} —
            <a href="{ad['link']}" class="text-blue-600 underline hover:text-blue-800" target="_blank">Learn more</a>'
            """

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

@app.route("/plan", methods=["GET", "POST"])
def plan():
    if request.method == "POST":
        try:
            day = int(request.form.get("day", 1))
            time = request.form.get("time", "").strip()
            title = request.form.get("title", "").strip()
            note = request.form.get("note", "").strip()
            entry_type = request.form.get("type", "activity")

            if not time or not title:
                raise ValueError("Missing required fields")

            db.trip_plan.update_one(
                {"userId": "demo", "day": day},
                {"$push": {"items": {
                    "time": time,
                    "type": entry_type,
                    "title": title,
                    "notes": note
                }}},
                upsert=True
            )

            return redirect("/plan")
        except Exception as e:
            print("Form submission error:", e)
            # Optionally: flash message to user

    # Always return current plan
    plans = list(db.trip_plan.find({"userId": "demo"}).sort("day", 1))
    return render_template("plan.html", plans=plans)

if __name__ == "__main__":
    app.run(debug=True)