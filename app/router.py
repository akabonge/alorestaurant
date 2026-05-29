from fastapi import APIRouter, HTTPException, Request
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.rag.pipeline import generate_response
from app.rag.embedder import get_collection
from app.config import get_settings
from app.guardrails import check_input, check_output

router = APIRouter()

# In-memory session store: session_id -> list of message dicts
# Good enough for a demo; swap for Redis in production
_sessions: dict[str, list[dict]] = {}


def _get_history(session_id: str) -> list[dict]:
    return _sessions.get(session_id, [])


def _update_history(session_id: str, role: str, content: str) -> None:
    settings = get_settings()
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})
    # Keep only the last N messages to avoid ballooning context
    max_msgs = settings.max_history_messages
    if len(_sessions[session_id]) > max_msgs:
        _sessions[session_id] = _sessions[session_id][-max_msgs:]


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    ip = request.headers.get("X-Forwarded-For", request.client.host or "").split(",")[0].strip()

    guard = check_input(payload.message, payload.session_id, ip=ip)
    if not guard.allowed:
        return ChatResponse(
            response=guard.reason,
            sources=[],
            session_id=payload.session_id,
            provider="guardrail",
        )

    history = _get_history(payload.session_id)

    try:
        response_text, sources, provider = generate_response(guard.cleaned_input, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    _, validated_response = check_output(response_text)

    _update_history(payload.session_id, "user", guard.cleaned_input)
    _update_history(payload.session_id, "assistant", validated_response)

    return ChatResponse(
        response=validated_response,
        sources=sources,
        session_id=payload.session_id,
        provider=provider,
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"cleared": session_id}


@router.get("/health", response_model=HealthResponse)
async def health():
    settings = get_settings()
    provider = "claude" if settings.anthropic_api_key else "ollama"
    try:
        count = get_collection().count()
    except Exception:
        count = -1
    return HealthResponse(status="ok", provider=provider, collection_count=count)
