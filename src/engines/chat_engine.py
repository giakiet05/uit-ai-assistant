"""
Chat Engine with conversation memory support.
Uses LlamaIndex's CondensePlusContextChatEngine for handling follow-up questions.
"""

import chromadb
from typing import Optional
from datetime import datetime

# Config
from src.config import settings

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex,
    PromptTemplate,
    Settings as LlamaSettings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage as LlamaChatMessage, MessageRole

# Local imports
from src.llm import create_llm
from src.engines.memory import InMemoryStore, ChatMessage


class ChatEngine:
    """
    Main Chat Engine with conversation memory and context understanding.

    Key Features:
    - Remembers conversation history per session
    - Understands follow-up questions
    - Condenses chat history into standalone questions for better retrieval
    """

    # Custom prompt cho condensing chat history + new question
    CONDENSE_PROMPT_VI = PromptTemplate("""
Cho trước một lịch sử hội thoại và câu hỏi mới nhất từ người dùng,
nhiệm vụ của bạn là diễn đạt lại câu hỏi mới thành một câu hỏi độc lập (standalone question)
có thể hiểu được mà KHÔNG CẦN dựa vào lịch sử hội thoại.

KHÔNG trả lời câu hỏi, chỉ cần diễn đạt lại nếu cần thiết, nếu không thì trả về nguyên văn.

Lịch sử hội thoại:
{chat_history}

Câu hỏi mới: {question}

Câu hỏi độc lập (tiếng Việt):""")

    # QA Prompt - tương tự QueryEngine nhưng aware của conversation context
    QA_PROMPT_VI = PromptTemplate("""
Bạn là một trợ lý AI chuyên gia về lĩnh vực giáo dục đại học.
Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên một cách chính xác và chi tiết dựa trên thông tin từ các tài liệu được cung cấp.

QUY TẮC BẮT BUỘC:
1. TRẢ LỜI HOÀN TOÀN BẰNG TIẾNG VIỆT.
2. Chỉ sử dụng thông tin từ "Ngữ cảnh tài liệu" bên dưới. Tuyệt đối không bịa đặt thông tin hoặc dùng kiến thức bên ngoài.
3. Nếu thông tin không có trong ngữ cảnh để trả lời câu hỏi, hãy nói rõ ràng là: "Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."
4. Duy trì ngữ cảnh từ cuộc hội thoại trước đó nếu có liên quan.

Ngữ cảnh tài liệu:
{context_str}

Câu hỏi: {query_str}

Câu trả lời chi tiết của bạn (bằng tiếng Việt):""")

    def __init__(self):
        """Initialize Chat Engine with vector store and memory."""
        print("[INFO] Initializing ChatEngine...")

        # 1. Setup global LlamaIndex settings
        if not settings.env.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env")

        LlamaSettings.embed_model = OpenAIEmbedding(
            model=settings.env.EMBED_MODEL,
            api_key=settings.env.OPENAI_API_KEY
        )
        LlamaSettings.node_parser = SemanticSplitterNodeParser.from_defaults(
            breakpoint_percentile_threshold=95
        )
        self.llm = create_llm(
            provider=settings.env.LLM_PROVIDER,
            model=settings.env.LLM_MODEL
        )
        LlamaSettings.llm = self.llm

        # 2. Load Vector Store
        print(f"[INFO] Loading vector store from: {settings.paths.VECTOR_STORE_DIR}")
        db = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))
        chroma_collection = db.get_or_create_collection("uit_documents_openai")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        self.index = VectorStoreIndex.from_vector_store(vector_store)

        # 3. Initialize custom memory store
        self.memory_store = InMemoryStore()

        # 4. Cache of active chat engines per session
        self._session_engines = {}

        print("✅ ChatEngine initialized successfully")

    def _get_or_create_engine(self, session_id: str) -> CondensePlusContextChatEngine:
        """
        Get existing chat engine for session or create new one.
        Each session has its own LlamaIndex ChatEngine with memory.
        """
        if session_id in self._session_engines:
            return self._session_engines[session_id]

        print(f"[INFO] Creating new chat engine for session: {session_id}")

        # Get chat history from our custom store
        history_messages = self.memory_store.get_history(
            session_id,
            max_messages=settings.chat.MAX_HISTORY_MESSAGES
        )

        # Convert to LlamaIndex ChatMessage format
        llama_history = []
        for msg in history_messages:
            role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
            llama_history.append(LlamaChatMessage(role=role, content=msg.content))

        # Create memory buffer with history
        memory = ChatMemoryBuffer.from_defaults(
            chat_history=llama_history,
            token_limit=settings.chat.MEMORY_TOKEN_LIMIT
        )

        # Create CondensePlusContext engine
        chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=self.index.as_retriever(
                similarity_top_k=settings.retrieval.SIMILARITY_TOP_K
            ),
            memory=memory,
            llm=self.llm,
            context_prompt=self.QA_PROMPT_VI,
            condense_prompt=self.CONDENSE_PROMPT_VI,
            verbose=True
        )

        # Cache it
        self._session_engines[session_id] = chat_engine
        return chat_engine

    def chat(
        self,
        message: str,
        session_id: str = "default",
        return_source_nodes: bool = False
    ) -> dict:
        """
        Main chat method with session support.

        Args:
            message: User's message
            session_id: Unique session identifier for this conversation
            return_source_nodes: Whether to return retrieved source nodes

        Returns:
            dict with 'response', 'session_id', optional 'source_nodes'
        """
        print(f"\n{'='*60}")
        print(f"[CHAT] Session: {session_id}")
        print(f"[CHAT] User: {message}")
        print(f"{'='*60}")

        try:
            # 1. Save user message to our custom memory
            user_msg = ChatMessage(role="user", content=message)
            self.memory_store.add_message(session_id, user_msg)

            # 2. Get or create chat engine for this session
            chat_engine = self._get_or_create_engine(session_id)

            # 3. Generate response
            response = chat_engine.chat(message)

            # 4. Save assistant response to our custom memory
            assistant_msg = ChatMessage(role="assistant", content=str(response))
            self.memory_store.add_message(session_id, assistant_msg)

            print(f"[CHAT] Assistant: {response}\n")

            # 5. Build result
            result = {
                "response": str(response),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

            if return_source_nodes:
                result["source_nodes"] = response.source_nodes

            return result

        except Exception as e:
            print(f"[ERROR] Chat failed: {e}")
            import traceback
            traceback.print_exc()

            error_response = "Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn."

            # Still save error to memory for debugging
            assistant_msg = ChatMessage(role="assistant", content=error_response)
            self.memory_store.add_message(session_id, assistant_msg)

            return {
                "response": error_response,
                "session_id": session_id,
                "error": str(e)
            }

    def reset_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        print(f"[INFO] Resetting session: {session_id}")
        self.memory_store.clear_session(session_id)
        if session_id in self._session_engines:
            del self._session_engines[session_id]

    def get_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        history = self.memory_store.get_history(session_id)
        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp.isoformat()}
            for msg in history
        ]

    def get_memory_stats(self) -> dict:
        """Get memory storage statistics."""
        return self.memory_store.get_stats()

    def stream_chat(self, message: str, session_id: str = "default"):
        """
        Streaming version of chat (for real-time response display).
        TODO: Implement if needed for better UX.
        """
        # This requires using streaming mode in LlamaIndex
        # Can be implemented in Phase 1.5 if needed
        raise NotImplementedError("Streaming not yet implemented")
