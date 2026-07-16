"""
app.py
Intelligent Customer Support System - Flask backend.

Routes:
  GET  /                  -> chat UI
  GET  /agent              -> agent dashboard (view/manage escalated tickets)
  POST /api/chat            -> send a message, get bot reply (JSON)
  GET  /api/tickets         -> list all tickets (JSON)
  POST /api/tickets/<id>/status -> update a ticket's status (JSON)
  GET  /api/history/<session_id> -> chat history for a session (JSON)
"""

import uuid

from flask import Flask, request, jsonify, render_template, session

import database
from nlp_engine import SupportNLPEngine

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

nlp_engine = SupportNLPEngine()
database.init_db()


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html", session_id=session["session_id"])


@app.route("/agent")
def agent_dashboard():
    return render_template("agent.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id") or session.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "message is required"}), 400

    result = nlp_engine.classify(message)

    # Auto-escalate to a human ticket when the bot isn't confident,
    # or when the user explicitly asks for a human.
    escalated = False
    ticket_id = None
    if not result["resolved"] or result["intent"] == "human_agent":
        ticket_id = database.create_ticket(
            session_id=session_id,
            subject=f"Escalation: {message[:60]}",
            message=message,
            priority="high" if result["confidence"] < 0.15 else "normal",
        )
        escalated = True

    database.log_chat(
        session_id=session_id,
        user_message=message,
        bot_response=result["response"],
        matched_intent=result["intent"],
        confidence=result["confidence"],
    )

    return jsonify({
        "response": result["response"],
        "intent": result["intent"],
        "confidence": result["confidence"],
        "resolved": result["resolved"],
        "escalated": escalated,
        "ticket_id": ticket_id,
        "session_id": session_id,
    })


@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    return jsonify(database.get_all_tickets())


@app.route("/api/tickets/<int:ticket_id>/status", methods=["POST"])
def set_ticket_status(ticket_id):
    data = request.get_json(force=True) or {}
    status = data.get("status", "open")
    if status not in ("open", "in_progress", "resolved", "closed"):
        return jsonify({"error": "invalid status"}), 400
    database.update_ticket_status(ticket_id, status)
    return jsonify({"success": True})


@app.route("/api/history/<session_id>", methods=["GET"])
def chat_history(session_id):
    return jsonify(database.get_chat_history(session_id))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
