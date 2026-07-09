# AI-First HCP CRM — Log Interaction Module

An AI-first CRM module for pharma/life-science field reps to log interactions
with Healthcare Professionals (HCPs) — either through a **structured form**
or a **conversational chat interface** backed by a **LangGraph agent**
running on **Groq's `gemma2-9b-it`**.

---

## 1. Tech stack

| Layer            | Tech                                                        |
|-------------------|-------------------------------------------------------------|
| Frontend          | React + Redux Toolkit                                       |
| Backend           | Python + FastAPI                                             |
| AI agent framework| LangGraph                                                    |
| LLM               | Groq `gemma2-9b-it` (agent reasoning/tool routing), `llama-3.3-70b-versatile` (used inside tools for higher-quality summarization) |
| Database          | SQLAlchemy ORM — works with SQLite (zero-setup default), Postgres, or MySQL |
| Font              | Google Inter                                                 |

---

## 2. Project structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router registration
│   │   ├── config.py          # settings loaded from .env
│   │   ├── database.py        # SQLAlchemy engine/session (SQLite/Postgres/MySQL)
│   │   ├── models.py          # HCP, Interaction, FollowUp tables
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── hcps.py            # HCP CRUD
│   │   │   ├── interactions.py    # Interaction CRUD (used by the structured form)
│   │   │   └── chat.py            # POST /api/chat -> invokes the LangGraph agent
│   │   └── agent/
│   │       ├── llm.py         # Groq ChatGroq client setup
│   │       ├── tools.py       # the 6 LangGraph tools
│   │       └── graph.py       # the LangGraph StateGraph (agent <-> tools loop)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── public/index.html      # loads Google Inter
    └── src/
        ├── App.js / App.css
        ├── store/              # Redux slices: hcps, interactions, chat
        ├── api/api.js           # axios client
        └── components/
            ├── LogInteractionScreen.jsx  # Form/Chat mode toggle
            ├── InteractionForm.jsx       # structured logging form
            ├── ChatInterface.jsx         # conversational logging (agent)
            ├── InteractionsList.jsx      # recent logs, inline edit/delete
            └── HCPPicker.jsx
```

---

## 3. How to run it

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your Groq API key (create one at https://console.groq.com/keys)
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (docs at `/docs`). By default it
uses a local SQLite file (`hcp_crm.db`) so there's nothing else to install.
To use Postgres or MySQL instead, just change `DATABASE_URL` in `.env`, e.g.:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/hcp_crm
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/hcp_crm
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000` and talks to the backend at
`http://localhost:8000` (override with `REACT_APP_API_BASE` if needed).

---

## 4. The Log Interaction screen

The screen has a segmented toggle at the top: **Structured Form** vs **Chat
with Agent**. Both write to the same `interactions` table, so a rep can mix
and match — log most visits by voice/text through chat, but use the form
when they want precise control over every field (or are logging from a
desktop between visits).

- **Structured Form**: HCP picker (with inline "+ New HCP"), interaction
  type, date, free-text notes, and optional products/next-steps fields. On
  submit, the backend still runs the notes through the same LLM
  summarization used by the chat agent, so a rep who just dumps quick notes
  still gets an auto-generated summary/sentiment.
- **Chat with Agent**: a normal chat UI. The rep types naturally
  ("I met Dr. Rao today, discussed Cardiozen, she was positive, follow up in
  2 weeks") and the LangGraph agent decides which tool(s) to call. Each
  agent reply shows a small chip for any tool it invoked, so the tool use is
  visible/demoable on video.
- The **Recent interactions** panel on the right reflects both entry points
  in real time, so you can show the same record being created via chat and
  then edited via the form (or vice-versa) in the demo video.

---

## 5. Role of the LangGraph agent

The LangGraph agent is the reasoning layer that sits behind the chat
interface. Its job is to turn a rep's unstructured, conversational
description of what just happened in the field into structured CRM data,
and to let the rep manage that data (edit, follow up, get history, get
prep material) without leaving the conversation.

Concretely, the agent:

1. **Interprets intent** — decides whether the rep is logging a new
   interaction, editing an old one, asking for history, asking for
   follow-up scheduling, or asking for talking-point prep.
2. **Routes to the right tool(s)**, in sequence if needed (e.g. it may call
   `get_hcp_history` before `suggest_talking_points`, or
   `check_compliance_flags` before `log_interaction` if the notes look
   risky).
3. **Uses the LLM twice, for two different jobs**: `gemma2-9b-it` is bound
   to the tools and handles the fast, cheap job of turn-by-turn intent
   routing and conversational replies; a larger model
   (`llama-3.3-70b-versatile`) is used inside a couple of tools where
   summarization/extraction quality matters more than latency.
4. **Keeps the rep in natural language** the whole time — after a tool
   runs, the agent reads the tool's result and replies conversationally
   ("Logged your visit with Dr. Rao. Sentiment: positive. Follow-up set for
   in 2 weeks.") rather than surfacing raw JSON.

The graph itself (see `agent/graph.py`) is a small loop: `agent` node (the
LLM, with tools bound) → conditional edge → `tools` node (executes whichever
tool(s) the LLM requested) → back to `agent` (so the LLM can read the tool
result and either call another tool or respond) → `END` once the LLM
replies without requesting a tool call.

---

## 6. The 6 LangGraph tools

Five tools were required; a sixth (compliance check) is included as a
bonus since HCP compliance is central to real pharma CRMs.

### 1. `log_interaction` *(required)*
**Inputs:** `hcp_name`, `interaction_type` (visit/call/email/conference),
`notes`, optional `interaction_date`.
**What it does:** looks up (or creates) the HCP record, then sends the raw
notes to the LLM with a prompt asking for a strict JSON object containing a
short `summary`, a `sentiment` (positive/neutral/negative), a
`products_discussed` list, and a `next_steps` string. It parses that JSON,
creates an `Interaction` row with both the raw notes and the LLM-derived
fields, and returns a plain-language confirmation (including the new
interaction ID, which the rep can reference later to edit it). This is the
same extraction logic the structured form's backend endpoint reuses, so
form-created and chat-created records are equally enriched.

### 2. `edit_interaction` *(required)*
**Inputs:** `interaction_id`, plus any subset of `notes`,
`interaction_type`, `products_discussed`, `next_steps`.
**What it does:** loads the interaction by ID, applies whichever fields
were provided (leaving the rest untouched), and — if `notes` changed — reruns
the same LLM extraction so `summary`/`sentiment` stay consistent with the
updated notes. This lets a rep say things like *"Edit interaction 3, we also
discussed Cardiozen"* or *"change that visit to a call"* entirely in chat.

### 3. `get_hcp_history`
**Inputs:** `hcp_name`, optional `limit`.
**What it does:** pulls the most recent interactions logged for that HCP
(summary, sentiment, products, next steps) so the agent has continuity —
used automatically before logging a new interaction with an HCP the rep has
seen before, and before generating talking points.

### 4. `schedule_follow_up`
**Inputs:** `interaction_id`, `due_date`, `note`.
**What it does:** creates a `FollowUp` row tied to a logged interaction, so
"remind me to follow up in two weeks" from inside the same message that
logs the visit results in both an `Interaction` and a linked `FollowUp`.

### 5. `suggest_talking_points`
**Inputs:** `hcp_name`, `product`.
**What it does:** pulls that HCP's history, then asks the LLM for 3–4
concise talking points for the *next* visit, explicitly instructed to avoid
efficacy guarantees, off-label suggestions, or mentions of gifts/incentives
— i.e. the compliance rules are baked into the generation prompt itself,
not just checked after the fact.

### 6. `check_compliance_flags` *(bonus)*
**Inputs:** `text`.
**What it does:** scans notes or a draft message for red-flag phrases
(off-label mentions, guarantees, gift/inducement language) before the agent
saves or shows something. The agent is instructed to call this
proactively when notes look risky, and to warn the rep before logging.

---

## 7. Design notes

- The two entry points (form vs. chat) intentionally share backend logic
  (`_extract_structured_fields` in `agent/tools.py`, reused by the plain
  REST `POST /api/interactions` endpoint) so an interaction logged either
  way looks the same in the database and in the UI — the chat agent isn't
  a separate, disconnected feature from the "real" CRM data.
- Conversation history per chat session is kept in-memory
  (`routers/chat.py`) for simplicity; swap in Redis or a DB table keyed by
  session for multi-instance deployments.
- The compliance tool is intentionally simple (keyword screen) rather than
  a second LLM call, to keep the demo fast and cheap — in production this
  would likely be a dedicated classifier or a curated regulated-phrase list
  maintained by legal/compliance.

---

## 8. What this project is / isn't

This was built as a technical assignment to demonstrate an AI-first CRM
concept end-to-end (React/Redux UI → FastAPI → LangGraph agent → Groq LLM →
SQL database), not a production pharma compliance system. Authentication,
role-based access, audit logging, and real MLR/compliance review workflows
would be required before this touched real HCP data.
