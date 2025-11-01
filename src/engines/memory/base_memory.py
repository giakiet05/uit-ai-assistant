"""
Abstract base class for memory storage.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    """Represents a single message in conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseMemory(ABC):
    """Abstract interface for conversation memory storage."""

    @abstractmethod
    def add_message(self, session_id: str, message: ChatMessage) -> None:
        """Add a message to session history."""
        pass

    @abstractmethod
    def get_history(self, session_id: str, max_messages: int = 10) -> List[ChatMessage]:
        """Retrieve conversation history for a session."""
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        pass
