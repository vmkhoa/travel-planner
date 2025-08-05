from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
from uuid import uuid4
import random
from chatbot.agents import ask_agent
from chatbot.config import AD_KEYWORDS, SPONSOR_ADS
from database import db
from bson import ObjectId
app = Flask(__name__)

chat_col = db["chat_history"]
session_col = db["chat_sessions"]
trip_col = db["trip_plan"]

@app.route("/")
def home():
    return redirect("/sessions")

# Sessions list
@app.route("/sessions")
def sessions():
    all_sessions = list(session_col.find({"userId": "demo"}).sort("createdAt", -1))
    return render_template("sessions.html", sessions=all_sessions)

# Create new session
@app.route("/new")
def new_session():
    session_id = str(uuid4())
    now = datetime.utcnow()
    session_col.insert_one({
        "userId": "demo",
        "sessionId": session_id,
        "title": f"New Session {now.strftime('%Y-%m-%d %H:%M')}",
        "createdAt": now
    })
    return redirect(f"/chat/{session_id}")

# Chat view per session
@app.route("/chat/<session_id>", methods=["GET", "POST"])
def chat(session_id):
    now = datetime.utcnow()

    if request.method == "POST":
        user_input = request.form["message"]

        # Save user message
        chat_col.insert_one({
            "sessionId": session_id,
            "role": "user",
            "message": user_input,
            "timestamp": now
        })

        # Get recent context
        history = list(chat_col.find({"sessionId": session_id}).sort("timestamp", -1).limit(10))
        history.reverse()

        # Guide replies
        guide_reply = ask_agent("guide", history)
        chat_col.insert_one({
            "sessionId": session_id,
            "role": "guide",
            "message": guide_reply,
            "timestamp": datetime.utcnow()
        })

        # Trigger advertiser
        combined_text = user_input.lower() + " " + guide_reply.lower()
        last_ad = chat_col.find_one({"sessionId": session_id, "role": "advertiser"}, sort=[("timestamp", -1)])
        cooldown_ok = not last_ad or (now - last_ad["timestamp"]) > timedelta(minutes=2)

        if any(k in combined_text for k in SPONSOR_ADS) and cooldown_ok:
            matched_ads = []
            for keyword in SPONSOR_ADS:
                if keyword in combined_text:
                    matched_ads.extend(SPONSOR_ADS[keyword])
            if matched_ads:
                ad = random.choice(matched_ads)
                ad_prompt = (
                    f"Write a short, friendly sponsored message (2–3 lines max) for the following offer:\n"
                    f"Title: {ad['title']}\n"
                    f"Message: {ad['message']}\n"
                    f"Don't mention the word 'ad'. Just make it natural and relevant.\n"
                )
                gemini_response = ask_agent("advertiser", [{"role": "user", "message": ad_prompt}])
                ad_reply = f"""
                <b>{ad['title']}</b>: {gemini_response.strip()} —
                <a href="{ad['link']}" class="text-blue-600 underline hover:text-blue-800" target="_blank">Learn more</a>
                """
                chat_col.insert_one({
                    "sessionId": session_id,
                    "role": "advertiser",
                    "message": ad_reply,
                    "timestamp": datetime.utcnow()
                })

        return redirect(f"/chat/{session_id}")

    # GET request: load chat history
    history = list(chat_col.find({"sessionId": session_id}).sort("timestamp", 1))
    return render_template("index.html", history=history, session_id=session_id)

@app.route("/sessions/delete/<session_id>", methods=["POST"])
def delete_session(session_id):
    db.chat_sessions.delete_one({"userId": "demo", "sessionId": session_id})
    db.chat_history.delete_many({"userId": "demo", "sessionId": session_id})
    return redirect("/sessions")

# Trip Planning
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

            trip_col.update_one(
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

    plans = list(trip_col.find({"userId": "demo"}).sort("day", 1))
    return render_template("plan.html", plans=plans)

@app.route("/plan/delete", methods=["POST"])
def delete_all_plans():
    trip_col.delete_many({"userId": "demo"})
    return redirect("/plan")

@app.route("/plan/delete/<int:day>", methods=["POST"])
def delete_day_plan(day):
    trip_col.delete_one({"userId": "demo", "day": day})
    return redirect("/plan")

if __name__ == "__main__":
    app.run(debug=True)
