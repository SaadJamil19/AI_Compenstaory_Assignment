"""Google Gemini AI integration for ticket analysis and chatbot."""
import json
import logging
import re
from typing import List, Optional

from config import settings

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"billing", "technical", "account", "shipping", "general"}
VALID_SENTIMENTS = {"positive", "neutral", "negative", "frustrated"}

_model = None


def _get_model():
    global _model
    if not settings.GEMINI_API_KEY:
        return None
    if _model is None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            _model = genai.GenerativeModel(settings.GEMINI_MODEL)
        except Exception as e:
            logger.warning("Failed to initialize Gemini: %s", e)
            return None
    return _model


def is_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


def _call_gemini(prompt: str) -> Optional[str]:
    model = _get_model()
    if not model:
        return None
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else None
    except Exception as e:
        logger.warning("Gemini API call failed: %s", e)
        return None


def _parse_json_field(text: str) -> Optional[dict]:
    if not text:
        return None
    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract JSON object from markdown or mixed text
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def categorize_and_sentiment(title: str, description: str) -> dict:
    """Auto-categorize ticket and detect sentiment. Returns defaults on failure."""
    defaults = {"category": "general", "sentiment": "neutral"}
    prompt = f"""Analyze this support ticket and respond with ONLY valid JSON, no markdown:
{{"category": "<one of: billing, technical, account, shipping, general>", "sentiment": "<one of: positive, neutral, negative, frustrated>"}}

Title: {title}
Description: {description}"""

    text = _call_gemini(prompt)
    parsed = _parse_json_field(text) if text else None
    if not parsed:
        return defaults

    category = str(parsed.get("category", "general")).lower().strip()
    sentiment = str(parsed.get("sentiment", "neutral")).lower().strip()
    if category not in VALID_CATEGORIES:
        category = "general"
    if sentiment not in VALID_SENTIMENTS:
        sentiment = "neutral"
    return {"category": category, "sentiment": sentiment}


def test_categorization() -> dict:
    return categorize_and_sentiment(
        "Cannot access billing portal",
        "I am frustrated because the billing page returns error 403 and I need to pay an invoice today.",
    )


def escalation_recommendation(title: str, description: str, sentiment: str, priority: str) -> dict:
    defaults = {"recommended_priority": priority, "reason": ""}
    if sentiment == "frustrated" and priority in {"low", "medium"}:
        defaults = {"recommended_priority": "high", "reason": "Frustrated customer sentiment requires faster attention."}
    prompt = f"""Analyze escalation risk for this support ticket. Respond with ONLY valid JSON:
{{"recommended_priority":"<one of: low, medium, high, critical>", "reason":"<short reason>"}}

Rules: critical only for outages, data loss, payment-blocking incidents, security issues, or repeated angry escalation.

Title: {title}
Description: {description}
Current priority: {priority}
Sentiment: {sentiment}"""
    text = _call_gemini(prompt)
    parsed = _parse_json_field(text) if text else None
    if not parsed:
        return defaults
    recommended = str(parsed.get("recommended_priority", priority)).lower().strip()
    if recommended not in {"low", "medium", "high", "critical"}:
        recommended = defaults["recommended_priority"]
    reason = str(parsed.get("reason", defaults["reason"])).strip()
    return {"recommended_priority": recommended, "reason": reason}


def generate_summary(title: str, description: str, comments: List[str]) -> str:
    """Generate AI summary when ticket is resolved."""
    comments_text = "\n".join(f"- {c}" for c in comments) if comments else "(no comments)"
    prompt = f"""Write a brief professional resolution summary (2-4 sentences) for this support ticket.

Title: {title}
Description: {description}
Activity log:
{comments_text}

Summary:"""

    text = _call_gemini(prompt)
    if text:
        return text
    return f"Ticket '{title}' was resolved. {len(comments)} comment(s) on record."


def suggest_reply(ticket: dict, comments: List[str]) -> str:
    comments_text = "\n".join(f"- {c}" for c in comments) if comments else "(no comments yet)"
    prompt = f"""Draft a professional customer support reply for this ticket.
Keep it concise, empathetic, and action-oriented. Do not invent resolved facts.

Customer: {ticket.get("customer_name", "Customer")}
Title: {ticket.get("title")}
Description: {ticket.get("description")}
Category: {ticket.get("category")}
Sentiment: {ticket.get("sentiment")}
Status: {ticket.get("status")}
Priority: {ticket.get("priority")}
Internal activity:
{comments_text}

Draft reply:"""
    text = _call_gemini(prompt)
    if text:
        return text
    return (
        f"Hello {ticket.get('customer_name', 'there')}, thank you for contacting support. "
        "We have reviewed your request and our team is working on the next steps. "
        "We will keep you updated as soon as there is progress."
    )


def chat(message: str, history: Optional[List[dict]] = None) -> str:
    """FAQ chatbot response scoped to CRM/ticket support."""
    history = history or []
    history_lines = ""
    for h in history[-6:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        history_lines += f"{role}: {content}\n"

    prompt = f"""You are a helpful FAQ assistant for an AI-Enhanced CRM & Ticket Management System.
Answer questions about: creating tickets, ticket statuses (open, in_progress, resolved, closed),
priorities (low, medium, high, critical), customer management, and how agents/managers use the system.
Keep answers concise and friendly.

Conversation:
{history_lines}
user: {message}
assistant:"""

    text = _call_gemini(prompt)
    if text:
        return text
    if not settings.GEMINI_API_KEY:
        return "AI is not configured. Please set GEMINI_API_KEY in your .env file."
    return "Sorry, I could not generate a response right now. Please try again."
