# Intelligent Customer Support System

A base project for an AI-assisted customer support chatbot. It classifies user
messages against a knowledge base of intents using TF-IDF + cosine similarity,
answers automatically when confident, and **escalates to a human agent
ticket** when it isn't — no external API keys or paid LLM calls required.

## Features

- **Intent classification** — lightweight NLP engine (scikit-learn TF-IDF +
  cosine similarity), no external API needed.
- **Auto-escalation** — low-confidence or "talk to a human" messages
  automatically create a support ticket.
- **Ticket queue / agent dashboard** — view and update ticket status
  (open → in progress → resolved → closed).
- **Chat history logging** — every exchange is stored in SQLite with the
  matched intent and confidence score.
- **Editable knowledge base** — `data/faqs.json` defines all intents,
  example phrasings, and canned responses. Add new intents without touching
  code.
- **Clean, dependency-light stack** — Flask + SQLite + scikit-learn. No
  frontend build step.

## Project structure

```
support_system/
├── app.py              # Flask routes / API
├── nlp_engine.py        # TF-IDF intent classifier
├── database.py           # SQLite access layer (tickets, chat logs)
├── data/
│   └── faqs.json          # Knowledge base: intents, patterns, responses
├── templates/
│   ├── index.html          # Chat UI
│   └── agent.html           # Agent dashboard (ticket queue)
├── static/
│   ├── style.css
│   └── chat.js
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open:
- `http://localhost:5000/` — the customer-facing chat widget
- `http://localhost:5000/agent` — the agent dashboard for managing tickets

The SQLite database (`support_system.db`) is created automatically on first
run.

## How escalation works

Every incoming message is matched against the knowledge base. If the best
match's similarity score is **below 0.35** (tunable in `nlp_engine.py` via
`CONFIDENCE_THRESHOLD`), or the message maps to the `human_agent` intent, the
system:

1. Creates a ticket in the `tickets` table (`priority` is set to `high` if
   confidence is very low, i.e. the bot has essentially no idea what was
   asked).
2. Still replies to the user, letting them know a human will follow up.
3. Surfaces the ticket in the agent dashboard for a real person to handle.

## Extending it

- **Add new intents**: edit `data/faqs.json` — add an `intent` name, a list
  of example `patterns`, and a `response`. No retraining step; the
  vectorizer refits from the JSON file each time the app starts.
- **Swap in a real LLM**: replace `SupportNLPEngine.classify()` in
  `nlp_engine.py` with a call to your model of choice, keeping the same
  return shape (`intent`, `response`, `confidence`, `resolved`).
- **Add authentication**: the agent dashboard has no auth in this base
  version — add login before deploying.
- **Swap SQLite for Postgres/MySQL**: `database.py` is a thin wrapper; only
  the connection logic needs to change.

## API reference

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/chat` | Send `{message, session_id}`, get back the bot's reply, matched intent, confidence, and escalation status. |
| `GET` | `/api/tickets` | List all support tickets. |
| `POST` | `/api/tickets/<id>/status` | Update a ticket's status (`open`, `in_progress`, `resolved`, `closed`). |
| `GET` | `/api/history/<session_id>` | Full chat log for a session. |

## Notes

This is a **base/starter project** — production use would want: user auth,
rate limiting, a persistent multi-user database, better confidence
calibration (e.g. a proper ML classifier or embeddings), and real agent
notifications (email/Slack webhook) on new tickets.
