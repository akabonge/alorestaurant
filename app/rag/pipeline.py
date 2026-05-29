"""
Agentic RAG pipeline: retrieve context, then run Claude with tool use.
Claude can check availability, book reservations, and query specials
in a multi-turn tool loop before returning the final response.

LLM selection:
  - Uses Claude (Anthropic) if ANTHROPIC_API_KEY is set in .env
  - Falls back to Ollama (local, no tool use) otherwise
"""
import json
from app.config import get_settings
from app.rag.retriever import retrieve
from app.tools.definitions import TOOLS
from app.tools.handlers import execute_tool

SYSTEM_PROMPT = """You are Aria, the friendly AI host for Casa Alo's Bistro in Fredericksburg, VA.

You have direct access to the live reservation system and can:
- Check real table availability for any date and party size
- Book reservations instantly — guests do not need to call
- Pull up today's specials
- Look up existing reservations by name or phone

Guidelines:
- Sound like a warm, knowledgeable person — not a chatbot. Write the way a great host would talk.
- Keep responses short and natural. Use a simple numbered list only when showing multiple slots or items.
- No emojis. No bold headers. No marketing language.
- When a guest wants to check availability or book, always use your tools — never tell them to call.
- Before booking, confirm all required details with the guest (name, email, date, time, party size).
- Only answer questions about Casa Alo's Bistro. Warmly redirect anything off-topic.
- If the answer is not in your tools or the context below, say: "I'm not sure — give us a call at (540) 555-0123 or email hello@casaalosbistro.com and we'll sort it out."

Restaurant Knowledge:
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
        return _call_claude_agentic(system, query, history, settings), sources, "claude"
    return _call_ollama(system, query, history, settings), sources, "ollama"


def _call_claude_agentic(system: str, query: str, history: list[dict], settings) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = list(history) + [{"role": "user", "content": query}]

    for _ in range(6):  # max 6 tool-call rounds per response
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=TOOLS,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            # Append assistant turn (contains tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # Execute every tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "I ran into a snag with that request. Please try again or call us at (540) 555-0123."


def _call_ollama(system: str, query: str, history: list[dict], settings) -> str:
    import ollama

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    response = ollama.chat(
        model=settings.ollama_model,
        messages=messages,
        options={"num_predict": 512},
    )
    return response["message"]["content"]
