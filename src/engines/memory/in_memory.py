"""
In-memory implementation of conversation memory.
Good for development and single-instance deployments.
"""
from typing import List, Dict
from collections import defaultdict
from .base_memory import BaseMemory, ChatMessage


class InMemoryStore(BaseMemory):
    """
    Stores conversation history in Python dict.
    WARNING: Data lost on restart. Use Redis for production.
    """

    def __init__(self):
        self._storage: Dict[str, List[ChatMessage]] = defaultdict(list)
        print("[MEMORY] Initialized InMemoryStore")

    def add_message(self, session_id: str, message: ChatMessage) -> None:
        """Add a message to the session's history."""
        self._storage[session_id].append(message)
        print(f"[MEMORY] Added {message.role} message to session {session_id}")

    def get_history(self, session_id: str, max_messages: int = 10) -> List[ChatMessage]:
        """Get last N messages from session history."""
        history = self._storage.get(session_id, [])
        # Return last max_messages
        return history[-max_messages:] if len(history) > max_messages else history

    def clear_session(self, session_id: str) -> None:
        """Clear session history."""
        if session_id in self._storage:
            del self._storage[session_id]
            print(f"[MEMORY] Cleared session {session_id}")

    def session_exists(self, session_id: str) -> bool:
        """Check if session has any history."""
        return session_id in self._storage and len(self._storage[session_id]) > 0

    def get_stats(self) -> Dict:
        """Get storage statistics."""
        return {
            "total_sessions": len(self._storage),
            "total_messages": sum(len(msgs) for msgs in self._storage.values())
        }
