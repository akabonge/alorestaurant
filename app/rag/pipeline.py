"""
Full RAG pipeline: retrieve relevant context, then generate a response.

LLM selection:
  - Uses Claude (Anthropic) if ANTHROPIC_API_KEY is set in .env
  - Falls back to Ollama (local) otherwise
"""
from app.config import get_settings
from app.rag.retriever import retrieve

SYSTEM_PROMPT = """You are Aria, the friendly assistant for Casa Alo's Bistro in Fredericksburg, VA.

Your job is to help guests with questions about our menu, hours, reservations, dietary options, parking, events, and anything else about the restaurant.

Tone and style:
- Sound like a warm, knowledgeable person — not a chatbot. Write the way a great host would talk.
- Keep responses short and easy to read. One or two sentences for simple questions. A clean numbered list for anything with multiple items.
- No emojis. No bold headers. No marketing language.
- When listing dishes, hours, or options: use a simple numbered list (1. 2. 3.) — nothing more.
- End with one natural follow-up question when it makes sense, not always.

Rules:
- Only answer questions about Casa Alo's Bistro. If someone asks something unrelated, warmly redirect them.
- Use ONLY the information provided below. Never invent prices, dishes, or policies.
- If the answer isn't in the provided information, say: "I'm not sure about that — give us a call at (540) 555-0123 or email hello@casaalosbistro.com and we'll sort it out for you."

Restaurant Information:
{context}"""


def generate_response(query: str, history: list[dict]) -> tuple[str, list[str], str]:
    """
    Returns (response_text, sources, provider_name).
    history is a list of {"role": "user"/"assistant", "content": "..."} dicts.
    """
    settings = get_settings()
    context, sources = retrieve(query)
    system = SYSTEM_PROMPT.format(context=context if context else "No specific context retrieved.")

    if settings.anthropic_api_key:
        return _call_claude(system, query, history, settings), sources, "claude"
    return _call_ollama(system, query, history, settings), sources, "ollama"


def _call_claude(system: str, query: str, history: list[dict], settings) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    messages = list(history) + [{"role": "user", "content": query}]

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _call_ollama(system: str, query: str, history: list[dict], settings) -> str:
    import ollama

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    response = ollama.chat(
        model=settings.ollama_model,
        messages=messages,
    )
    return response["message"]["content"]
