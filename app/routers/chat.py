from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app import schemas
from app.agent.graph import agent_graph

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple in-memory conversation store keyed by session_id.
# Fine for a demo/assignment; swap for Redis/DB-backed history in production.
_SESSIONS: dict[str, list] = {}


@router.post("/", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest):
    history = _SESSIONS.setdefault(payload.session_id, [])
    history.append(HumanMessage(content=payload.message))
    prior_len = len(history)

    result = agent_graph.invoke({"messages": history})
    messages = result["messages"]
    _SESSIONS[payload.session_id] = messages
    new_messages = messages[prior_len:]

    tool_calls = []
    reply = ""
    for msg in new_messages:
        if isinstance(msg, ToolMessage):
            tool_calls.append(
                schemas.ChatToolCall(tool=msg.name or "tool", output=str(msg.content))
            )
        if isinstance(msg, AIMessage) and msg.content:
            reply = msg.content

    return schemas.ChatResponse(reply=reply, tool_calls=tool_calls)


@router.post("/reset")
def reset_session(session_id: str = "default"):
    _SESSIONS.pop(session_id, None)
    return {"ok": True}
