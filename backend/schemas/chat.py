from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: list[ChatMessage] = []
    trace_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    offers: Optional[list] = None
    suggested_actions: Optional[list[str]] = None
    needs_clarification: bool = False
    missing_fields: Optional[list[str]] = None
    timestamp: datetime = datetime.now()
    trace_id: Optional[str] = None
