"""
The LangGraph agent that powers the "Log Interaction" chat mode.

Design:
  START -> agent (LLM decides: answer directly, or call a tool)
  agent -> tools (if the LLM emitted tool calls) -> agent (loop back with
           tool results so the LLM can respond in natural language, or
           chain another tool call, e.g. get_hcp_history -> log_interaction)
  agent -> END (once the LLM responds without requesting a tool call)

This is the standard "ReAct-style" LangGraph loop, built explicitly (rather
than via the `create_react_agent` helper) so the control flow is easy to
narrate/demo on video.
"""
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from app.agent.llm import get_agent_llm
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = SystemMessage(content=(
    "You are the AI assistant embedded in a pharma CRM's HCP module. Field "
    "reps talk to you conversationally to log interactions with healthcare "
    "professionals (HCPs), edit past logs, schedule follow-ups, pull HCP "
    "history, and get compliance-safe talking points for their next visit.\n\n"
    "Rules:\n"
    "- When a rep describes a visit/call/email that already happened, call "
    "log_interaction with the HCP name, interaction type, and their notes.\n"
    "- When a rep wants to change something already logged, call "
    "edit_interaction with the interaction_id they reference (ask for it if "
    "genuinely unknown).\n"
    "- Before suggesting talking points, you may call get_hcp_history for "
    "context.\n"
    "- If notes contain risky claims (guarantees, off-label use, gifts), "
    "call check_compliance_flags and warn the rep before logging.\n"
    "- Always confirm back to the rep in plain language what was saved.\n"
    "- Keep responses concise; this is a chat UI on a busy rep's phone."
))


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_graph():
    llm = get_agent_llm().bind_tools(ALL_TOOLS)

    def call_model(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SYSTEM_PROMPT] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once at import time and reused across requests.
agent_graph = build_graph()
