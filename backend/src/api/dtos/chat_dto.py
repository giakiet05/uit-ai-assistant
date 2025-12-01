import uuid
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ==================================
# Chat Message DTOs
# ==================================

# DTO for creating a new chat message (request body)
class ChatMessageCreateRequest(BaseModel):
    content: str
    role: str # "user" or "assistant"
    metadata_: Optional[dict] = None

# DTO for API response (a single chat message)
class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    content: str
    role: str
    metadata_: Optional[dict] = None
    created_at: datetime

    class Config:
        orm_mode = True

# ==================================
# Chat Session DTOs
# ==================================

# DTO for creating a new chat session (request body)
class ChatSessionCreateRequest(BaseModel):
    user_id: uuid.UUID
    title: Optional[str] = "New Chat"

# DTO for updating an existing chat session (request body)
class ChatSessionUpdateRequest(BaseModel):
    title: Optional[str] = None

# DTO for API response (a single chat session)
class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# DTO for API response including all messages in a session
class ChatSessionWithMessagesResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []
