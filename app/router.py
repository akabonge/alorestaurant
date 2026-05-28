from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.rag.pipeline import generate_response
from app.rag.embedder import get_collection
from app.config import get_settings

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
async def chat(request: ChatRequest):
    history = _get_history(request.session_id)

    try:
        response_text, sources, provider = generate_response(request.message, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    _update_history(request.session_id, "user", request.message)
    _update_history(request.session_id, "assistant", response_text)

    return ChatResponse(
        response=response_text,
        sources=sources,
        session_id=request.session_id,
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
