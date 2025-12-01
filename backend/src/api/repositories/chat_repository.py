from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.chat_model import ChatSession, ChatMessage
from ..dtos.chat_dto import ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate, ChatMessageUpdate
from .base_repository import BaseRepository

# Repository for ChatSession model
class ChatSessionRepository(BaseRepository[ChatSession]):
    async def get_by_user(self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """
        Get all chat sessions for a specific user.
        """
        statement = select(self.model).filter_by(user_id=user_id).order_by(self.model.updated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()


# Repository for ChatMessage model
class ChatMessageRepository(BaseRepository[ChatMessage]):
    async def get_history_by_session_id(
        self, db: AsyncSession, *, session_id: str, limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get the last N messages for a specific chat session, ordered by creation time.
        """
        statement = (
            select(self.model)
            .filter_by(session_id=session_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(statement)
        # Reverse the result to have the oldest message first
        return list(reversed(result.scalars().all()))


# Create singleton instances of the repositories
chat_session_repository = ChatSessionRepository(ChatSession)
chat_message_repository = ChatMessageRepository(ChatMessage)
