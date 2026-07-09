from langchain_groq import ChatGroq

from app.config import settings


def get_agent_llm():
    """Primary model used by the LangGraph agent for reasoning + tool routing.

    gemma2-9b-it on Groq is small and fast, which is what we want for a
    conversational CRM agent that needs low-latency turn-taking with the rep.
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.2,
    )


def get_summarization_llm():
    """Larger model used inside the log_interaction / suggest_talking_points
    tools where reasoning quality matters more than latency. Falls back to
    the same small model if no separate key/model is configured.
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_fallback_model,
        temperature=0.3,
    )
