from typing import List, Optional
from datetime import datetime
import uuid

# LlamaIndex imports
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage as LlamaChatMessage
from llama_index.core.llms import MessageRole


# TODO: Remove InMemoryStore from here
# from ...shared.agent.memory import InMemoryStore

# Project imports
from ...shared.config.settings import settings
from ...shared.agent.agent import UITAgent, SharedResources
from ..repositories.chat_repository import ChatSessionRepository, ChatMessageRepository
from ..models.chat_model import ChatSession, ChatMessage
from ..dtos.chat_dto import ChatSessionCreateRequest, ChatMessageCreateRequest
from sqlalchemy.ext.asyncio import AsyncSession


class AgentService:
    """
    Service layer for managing agents with session-based memory.

    This handles:
    - Memory persistence (load/save from DB) via repositories
    - Agent creation per request
    - Session management
    """

    def __init__(
        self,
        resources: SharedResources, # Injected from application startup
        chat_session_repo: ChatSessionRepository,
        chat_message_repo: ChatMessageRepository,
    ):
        print("[AGENT SERVICE] Initializing...")
        self.resources = resources
        self.chat_session_repo = chat_session_repo
        self.chat_message_repo = chat_message_repo
        self._tools_loaded = False # Will be loaded during app startup


    async def load_tools(self):
        """
        Load MCP tools asynchronously.

        This should be called once after initialization in an async context (e.g., app startup).
        """
        if not self._tools_loaded:
            await self.resources.load_tools_async()
            self._tools_loaded = True

    async def chat(
        self,
        db: AsyncSession, # Injected by FastAPI dependency
        message: str,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> ChatMessage: # Returns the assistant's response as a SQLAlchemy ChatMessage object
        """
        Chat with agent for a given session.

        Handles the full lifecycle:
        1. Ensure session exists (create if new)
        2. Load conversation history from DB
        3. Create LlamaIndex ChatMemoryBuffer with history
        4. Create agent instance (stateless)
        5. Run agent with new message
        6. Save new messages (user's query and agent's response) to DB

        Args:
            db: SQLAlchemy AsyncSession for database operations.
            message: User's message
            user_id: ID of the current user.
            session_id: Session identifier for conversation history. If None, a new session is created.

        Returns:
            ChatMessage: The assistant's response message as a SQLAlchemy model.
        """
        print(f"\n{'='*60}")
        print(f"[AGENT SERVICE] User ID: {user_id}")
        print(f"[AGENT SERVICE] Session ID: {session_id}")
        print(f"[AGENT SERVICE] User Message: {message}")
        print(f"{'='*60}")

        current_session: Optional[ChatSession] = None
        if session_id:
            current_session = await self.chat_session_repo.get(db, id=session_id)

        if not current_session:
            # Create a new session if not provided or not found
            session_create_dto = ChatSessionCreate(user_id=user_id, title=message[:50]) # Use first 50 chars as title
            current_session = await self.chat_session_repo.create(db, obj_in=session_create_dto)
            session_id = current_session.id
            print(f"[AGENT SERVICE] Created new session: {session_id}")
        else:
            session_id = current_session.id


        # 1. Load conversation history from DB
        # Note: LlamaIndex ChatMemoryBuffer uses LlamaChatMessage, not our ChatMessage model
        history_db_models: List[ChatMessage] = await self.chat_message_repo.get_history_by_session_id(
            db, session_id=str(session_id), limit=settings.chat.MAX_HISTORY_MESSAGES
        )
        history_llama_messages: List[LlamaChatMessage] = [
            LlamaChatMessage(role=MessageRole(msg.role), content=msg.content) for msg in history_db_models
        ]

        print(f"[AGENT SERVICE] Loaded {len(history_llama_messages)} messages from history for session {session_id}")

        # 2. Create LlamaIndex ChatMemoryBuffer and restore history
        llama_memory = ChatMemoryBuffer.from_defaults(
            token_limit=settings.chat.MEMORY_TOKEN_LIMIT,
            llm=self.resources.llm
        )
        for msg in history_llama_messages:
            llama_memory.put(msg)

        # 3. Create agent instance (lightweight, stateless)
        agent = UITAgent(self.resources)

        # 4. Run agent with user's message
        response_llama_message: LlamaChatMessage = await agent.chat(message, llama_memory)

        # 5. Extract new messages (user's query and agent's response) from LlamaIndex memory and save to DB
        # User message
        user_llama_message = LlamaChatMessage(role=MessageRole.USER, content=message)
        await self.chat_message_repo.create(
            db, obj_in=ChatMessageCreateRequest(
                session_id=session_id,
                role=user_llama_message.role.value,
                content=user_llama_message.content,
                metadata_=None
            )
        )

        # Assistant message (after stripping tool calls/reasoning)
        assistant_content = response_llama_message.content
        if "assistant" in str(response_llama_message.role).lower():
            if "Thought:" in assistant_content or "Action:" in assistant_content or "Observation:" in assistant_content:
                if "Answer:" in assistant_content:
                    assistant_content = assistant_content.split("Answer:")[-1].strip()
                else:
                    # If no final answer, log and skip saving this intermediate step
                    print(f"[AGENT SERVICE] Skipping intermediate assistant message (no final Answer)")
                    # Return a placeholder or raise an error if no final answer is expected
                    # For now, let's return an error message
                    raise Exception("Agent did not produce a final answer.")

        assistant_db_message = await self.chat_message_repo.create(
            db, obj_in=ChatMessageCreate(
                session_id=session_id,
                role=response_llama_message.role.value,
                content=assistant_content,
                metadata_=None # Can be populated with tool outputs if needed
            )
        )
        print(f"[AGENT SERVICE] Saved user message and assistant message to session {session_id}")

        # Update session's updated_at timestamp
        if current_session:
            current_session.updated_at = datetime.now()
            db.add(current_session)
            await db.commit()
            await db.refresh(current_session)


        return assistant_db_message # Return the newly created assistant message from DB