"""
LangGraph tools for the HCP Interaction Agent.

Required tools (per task spec):
  1. log_interaction        - captures a new HCP interaction, using the LLM
                               to summarize free-text notes and extract
                               sentiment / products discussed / next steps.
  2. edit_interaction        - modifies a previously logged interaction.
  3. get_hcp_history         - pulls prior interactions for an HCP so the
                               agent has context before logging/suggesting.
  4. schedule_follow_up      - creates a follow-up task tied to a visit.
  5. suggest_talking_points  - LLM-generated, compliance-aware talking
                               points for the rep's next visit.

Bonus tool:
  6. check_compliance_flags  - lightweight compliance screen on interaction
                               text (off-label claims, promissory language,
                               gifting/inducement mentions) before it's saved.

Each tool opens/closes its own short-lived DB session so it can be called
directly by the LangGraph ToolNode without needing request-scoped FastAPI
dependencies threaded through.
"""
import datetime as dt
import json
from typing import Optional

from langchain_core.tools import tool

from app.database import SessionLocal
from app.models import HCP, Interaction, FollowUp
from app.agent.llm import get_summarization_llm

COMPLIANCE_KEYWORDS = [
    "guarantee", "guaranteed", "off-label", "off label", "free trip",
    "kickback", "cash gift", "under the table", "no side effects",
    "cures", "risk-free",
]


def _get_or_create_hcp(db, hcp_name: str) -> HCP:
    hcp = db.query(HCP).filter(HCP.name.ilike(hcp_name.strip())).first()
    if not hcp:
        hcp = HCP(name=hcp_name.strip())
        db.add(hcp)
        db.commit()
        db.refresh(hcp)
    return hcp


def _extract_structured_fields(notes: str) -> dict:
    """Calls the LLM to turn raw rep notes into structured fields."""
    llm = get_summarization_llm()
    prompt = (
        "You are a pharma CRM assistant. Read the field rep's raw notes about "
        "a visit with a healthcare professional (HCP) and return ONLY a JSON "
        "object (no markdown, no commentary) with these keys:\n"
        '  "summary": one or two sentence summary of the interaction\n'
        '  "sentiment": one of "positive", "neutral", "negative"\n'
        '  "products_discussed": comma-separated product names mentioned, or "" if none\n'
        '  "next_steps": short actionable next step, or "" if none mentioned\n\n'
        f"Rep notes:\n{notes}"
    )
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.split("\n", 1)[1] if "\n" in content else content
        data = json.loads(content)
    except Exception:
        data = {
            "summary": notes[:200],
            "sentiment": "neutral",
            "products_discussed": "",
            "next_steps": "",
        }
    return data


@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    notes: str,
    interaction_date: Optional[str] = None,
) -> str:
    """Log a new interaction with a healthcare professional (HCP).

    Use this whenever the rep describes a visit, call, email, or conference
    interaction they just had. Pass the HCP's name, the interaction_type
    ("visit", "call", "email", or "conference"), and the rep's raw notes
    describing what happened. The tool will use an LLM to summarize the
    notes, detect sentiment, and extract products discussed / next steps,
    then save everything to the database.

    interaction_date is optional, format YYYY-MM-DD; defaults to today.
    """
    db = SessionLocal()
    try:
        hcp = _get_or_create_hcp(db, hcp_name)
        fields = _extract_structured_fields(notes)

        parsed_date = dt.datetime.utcnow()
        if interaction_date:
            try:
                parsed_date = dt.datetime.strptime(interaction_date, "%Y-%m-%d")
            except ValueError:
                pass

        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=interaction_type if interaction_type in
            ("visit", "call", "email", "conference") else "visit",
            interaction_date=parsed_date,
            raw_notes=notes,
            summary=fields.get("summary", ""),
            sentiment=fields.get("sentiment", "neutral"),
            products_discussed=fields.get("products_discussed", ""),
            next_steps=fields.get("next_steps", ""),
            created_via="chat",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return (
            f"Logged interaction #{interaction.id} with {hcp.name} "
            f"({interaction.interaction_type} on {parsed_date.date()}). "
            f"Summary: {interaction.summary}. Sentiment: {interaction.sentiment}. "
            f"Products discussed: {interaction.products_discussed or 'none'}. "
            f"Next steps: {interaction.next_steps or 'none noted'}."
        )
    finally:
        db.close()


@tool
def edit_interaction(
    interaction_id: int,
    notes: Optional[str] = None,
    interaction_type: Optional[str] = None,
    products_discussed: Optional[str] = None,
    next_steps: Optional[str] = None,
) -> str:
    """Edit/modify a previously logged interaction by its ID.

    Use this when the rep wants to correct or add information to an
    interaction they already logged (e.g. "actually we also discussed
    Product X" or "change that visit to a call"). Only pass the fields
    that need to change; anything left blank is unchanged. If `notes` is
    provided, the LLM re-summarizes and re-extracts sentiment/next_steps
    from the updated notes.
    """
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return f"No interaction found with id {interaction_id}."

        if interaction_type:
            interaction.interaction_type = interaction_type
        if products_discussed:
            interaction.products_discussed = products_discussed
        if next_steps:
            interaction.next_steps = next_steps
        if notes:
            interaction.raw_notes = notes
            fields = _extract_structured_fields(notes)
            interaction.summary = fields.get("summary", interaction.summary)
            interaction.sentiment = fields.get("sentiment", interaction.sentiment)
            if not products_discussed:
                interaction.products_discussed = fields.get(
                    "products_discussed", interaction.products_discussed
                )
            if not next_steps:
                interaction.next_steps = fields.get("next_steps", interaction.next_steps)

        interaction.updated_at = dt.datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        return (
            f"Updated interaction #{interaction.id}. "
            f"Summary: {interaction.summary}. Sentiment: {interaction.sentiment}. "
            f"Products discussed: {interaction.products_discussed or 'none'}. "
            f"Next steps: {interaction.next_steps or 'none noted'}."
        )
    finally:
        db.close()


@tool
def get_hcp_history(hcp_name: str, limit: int = 5) -> str:
    """Retrieve the most recent interaction history for a named HCP.

    Use this before logging a new interaction or suggesting talking points,
    so the response can reference what was discussed previously (continuity
    matters a lot in HCP relationship management).
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(hcp_name.strip())).first()
        if not hcp:
            return f"No HCP found named '{hcp_name}'. This would be a first interaction."

        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.interaction_date.desc())
            .limit(limit)
            .all()
        )
        if not interactions:
            return f"{hcp.name} has no logged interactions yet."

        lines = [f"History for {hcp.name} ({hcp.specialty or 'specialty unknown'}):"]
        for i in interactions:
            lines.append(
                f"- {i.interaction_date.date()} [{i.interaction_type}]: "
                f"{i.summary or i.raw_notes} (sentiment: {i.sentiment}, "
                f"products: {i.products_discussed or 'none'}, "
                f"next steps: {i.next_steps or 'none'})"
            )
        return "\n".join(lines)
    finally:
        db.close()


@tool
def schedule_follow_up(interaction_id: int, due_date: str, note: str) -> str:
    """Schedule a follow-up task tied to a logged interaction.

    due_date format: YYYY-MM-DD. Use this when the rep says things like
    "remind me to follow up next month" or "schedule a sample drop-off for
    next Tuesday".
    """
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return f"No interaction found with id {interaction_id}; log the interaction first."

        try:
            parsed_due = dt.datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            parsed_due = dt.datetime.utcnow() + dt.timedelta(days=7)

        follow_up = FollowUp(
            interaction_id=interaction.id,
            due_date=parsed_due,
            note=note,
            status="open",
        )
        db.add(follow_up)
        db.commit()
        db.refresh(follow_up)

        return (
            f"Follow-up #{follow_up.id} scheduled for {parsed_due.date()} "
            f"on interaction #{interaction.id}: {note}"
        )
    finally:
        db.close()


@tool
def suggest_talking_points(hcp_name: str, product: str) -> str:
    """Suggest compliance-safe talking points for the rep's next visit
    with a given HCP about a given product, grounded in that HCP's
    interaction history (uses get_hcp_history internally).
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(hcp_name.strip())).first()
        history_text = "No prior interactions on file."
        if hcp:
            interactions = (
                db.query(Interaction)
                .filter(Interaction.hcp_id == hcp.id)
                .order_by(Interaction.interaction_date.desc())
                .limit(5)
                .all()
            )
            if interactions:
                history_text = "\n".join(
                    f"- {i.interaction_date.date()}: {i.summary or i.raw_notes} "
                    f"(sentiment: {i.sentiment})"
                    for i in interactions
                )
    finally:
        db.close()

    llm = get_summarization_llm()
    prompt = (
        f"You are a pharma sales enablement assistant. Draft 3-4 concise, "
        f"compliance-safe talking points a field rep could use in their next "
        f"conversation with Dr. {hcp_name} about {product}. Ground the points "
        f"in the prior interaction history below where relevant. Do not make "
        f"any efficacy guarantees, do not suggest off-label use, and do not "
        f"mention gifts or incentives.\n\n"
        f"Prior interaction history:\n{history_text}"
    )
    response = llm.invoke(prompt)
    return response.content.strip()


@tool
def check_compliance_flags(text: str) -> str:
    """Scan interaction notes or a draft message for potential compliance
    risks (off-label claims, guarantees, mentions of gifts/inducements)
    before it is saved or sent. Returns a short list of flags, or
    'No compliance flags detected.' if clean.
    """
    lowered = text.lower()
    flags = [kw for kw in COMPLIANCE_KEYWORDS if kw in lowered]
    if not flags:
        return "No compliance flags detected."
    return (
        "Potential compliance flags detected: "
        + ", ".join(sorted(set(flags)))
        + ". Recommend rephrasing before logging/sending."
    )


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    get_hcp_history,
    schedule_follow_up,
    suggest_talking_points,
    check_compliance_flags,
]
