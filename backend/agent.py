"""
LangChain + NVIDIA AI agent for generating water intake insights.

The agent gets the user's intake data passed in directly (no tool calls needed —
simpler and more reliable). It produces a concise, friendly summary covering:
  - How much water the user has drunk today
  - How much more they should drink to hit their goal
  - Encouragement / tips grounded in the actual numbers
"""

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")

# Lazy-init so we don't error out at import time if the key isn't set yet.
_chat: ChatNVIDIA | None = None


def get_chat() -> ChatNVIDIA:
    """Lazily initialize and cache the ChatNVIDIA client."""
    global _chat
    if _chat is None:
        if not NVIDIA_API_KEY or NVIDIA_API_KEY == "your_nvidia_api_key_here":
            raise RuntimeError(
                "NVIDIA_API_KEY is not set. Edit backend/.env and paste your key "
                "from https://build.nvidia.com/"
            )
        _chat = ChatNVIDIA(model=NVIDIA_MODEL, api_key=NVIDIA_API_KEY)
    return _chat


def generate_insight(
    user_name: str,
    total_intake_ml: int,
    goal_ml: int,
    remaining_ml: int,
    entries_summary: str,
) -> str:
    """
    Ask the NVIDIA LLM to write a short, personalized daily water summary.

    Args:
        user_name:       The user's name.
        total_intake_ml: Total millilitres logged today.
        goal_ml:         Daily goal in millilitres.
        remaining_ml:    How many ml left to reach the goal (negative if exceeded).
        entries_summary: Human-readable list of today's log entries (times + amounts).

    Returns:
        A markdown string with the AI's summary and recommendation.
    """
    chat = get_chat()

    system_prompt = (
        "You are a friendly hydration coach. You analyze a user's water intake "
        "for the day and write a SHORT, encouraging summary in 3-5 sentences.\n"
        "Rules:\n"
        "- Address the user by name.\n"
        "- State clearly how much water they have drunk today and their goal.\n"
        "- Tell them exactly how many ml more they should drink to reach the goal "
        "(or congratulate them if they met/exceeded it).\n"
        "- Give one brief, practical tip (e.g. 'keep a bottle on your desk').\n"
        "- Keep it concise. No long lectures. Use plain language."
    )

    human_prompt = (
        f"User: {user_name}\n"
        f"Total water drunk today: {total_intake_ml} ml\n"
        f"Daily goal: {goal_ml} ml\n"
        f"Remaining to reach goal: {remaining_ml} ml\n"
        f"Today's log entries:\n{entries_summary}\n\n"
        "Write the summary now."
    )

    response = chat.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])
    return response.content if hasattr(response, "content") else str(response)


def generate_chat_answer(
    user_name: str,
    message: str,
    total_intake_ml: int,
    goal_ml: int,
    remaining_ml: int,
) -> str:
    """
    Free-form chat: answer the user's question, grounded in their actual intake data.
    """
    chat = get_chat()

    system_prompt = (
        "You are a friendly hydration coach assistant embedded in a water tracker app. "
        "You have access to the user's water intake data for today — use it to answer "
        "their questions accurately.\n"
        "Keep answers concise and helpful. If they ask about their progress, reference "
        "their actual numbers."
    )

    human_prompt = (
        f"User: {user_name}\n"
        f"Today's intake so far: {total_intake_ml} ml\n"
        f"Daily goal: {goal_ml} ml\n"
        f"Remaining to reach goal: {remaining_ml} ml\n\n"
        f"User's question: {message}\n\n"
        "Answer:"
    )

    response = chat.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])
    return response.content if hasattr(response, "content") else str(response)
