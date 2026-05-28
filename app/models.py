from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(default="default")


class ChatResponse(BaseModel):
    response: str
    sources: list[str]
    session_id: str
    provider: str


class HealthResponse(BaseModel):
    status: str
    provider: str
    collection_count: int
