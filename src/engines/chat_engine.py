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
from src.indexing.hierarchical_markdown_parser import HierarchicalMarkdownParser
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
        if not settings.credentials.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env")

        LlamaSettings.embed_model = OpenAIEmbedding(
            model=settings.retrieval.EMBED_MODEL,
            api_key=settings.credentials.OPENAI_API_KEY
        )
        # Use custom HierarchicalMarkdownParser
        LlamaSettings.node_parser = HierarchicalMarkdownParser(
            max_tokens=7000,
            sub_chunk_size=1024,
            sub_chunk_overlap=128
        )

        self.llm = create_llm(
            provider=settings.llm.PROVIDER,
            model=settings.llm.MODEL
        )
        LlamaSettings.llm = self.llm

        # 2. Load multi-collection vector stores
        print(f"[INFO] Loading vector stores from: {settings.paths.VECTOR_STORE_DIR}")
        db = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))

        self.collections = {}
        for category in settings.query_routing.AVAILABLE_COLLECTIONS:
            print(f"[INFO] Loading collection: {category}")
            chroma_collection = db.get_or_create_collection(category)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            self.collections[category] = VectorStoreIndex.from_vector_store(vector_store)

        print(f"[INFO] Loaded {len(self.collections)} collections: {list(self.collections.keys())}")

        # 3. Initialize query router
        from src.engines.routing.router_factory import create_router
        self.router = create_router()
        print(f"[INFO] Using routing strategy: {settings.query_routing.STRATEGY}")

        # 4. Initialize custom memory store
        self.memory_store = InMemoryStore()

        # 5. Cache of active chat engines per session
        self._session_engines = {}

        print("✅ ChatEngine initialized successfully")

    def _condense_question(self, chat_history: str, new_question: str) -> str:
        """
        Condense chat history + new question into standalone question.

        Args:
            chat_history: Formatted chat history
            new_question: New user question

        Returns:
            Standalone question
        """
        if not chat_history.strip():
            # No history, return original question
            return new_question

        # Use condense prompt to create standalone question
        condense_prompt = self.CONDENSE_PROMPT_VI.format(
            chat_history=chat_history,
            question=new_question
        )

        response = self.llm.complete(condense_prompt)
        standalone_question = response.text.strip()

        print(f"[INFO] Condensed question: {standalone_question}")
        return standalone_question

    def _retrieve_from_collections(self, question: str, target_collections: list) -> list:
        """
        Retrieve relevant nodes from multiple collections.

        Args:
            question: Query question
            target_collections: List of collection names to query

        Returns:
            List of retrieved nodes, sorted by score
        """
        all_nodes = []

        for collection_name in target_collections:
            if collection_name not in self.collections:
                print(f"[WARNING] Collection '{collection_name}' not found, skipping")
                continue

            print(f"[INFO] Retrieving from collection: {collection_name}")
            retriever = self.collections[collection_name].as_retriever(
                similarity_top_k=settings.retrieval.SIMILARITY_TOP_K
            )
            nodes = retriever.retrieve(question)
            all_nodes.extend(nodes)

        # Sort by score (descending) and limit
        all_nodes.sort(key=lambda x: x.score if hasattr(x, 'score') else 0, reverse=True)
        top_nodes = all_nodes[:settings.retrieval.SIMILARITY_TOP_K]

        print(f"[INFO] Retrieved {len(top_nodes)} nodes from {len(target_collections)} collections")
        return top_nodes

    def chat(
        self,
        message: str,
        session_id: str = "default",
        return_source_nodes: bool = False
    ) -> dict:
        """
        Main chat method with multi-collection support and routing.

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
            # 1. Get chat history
            history_messages = self.memory_store.get_history(
                session_id,
                max_messages=settings.chat.MAX_HISTORY_MESSAGES
            )

            # Format history for condensing
            chat_history = "\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in history_messages
            ])

            # 2. Condense question with chat history
            standalone_question = self._condense_question(chat_history, message)

            # 3. Route query to get target collections
            routing_decision = self.router.route(standalone_question)
            target_collections = routing_decision.collections  # Extract list from RoutingDecision
            print(f"[INFO] Routed to collections: {target_collections} (strategy: {routing_decision.strategy})")

            # 4. Retrieve from multi-collections
            retrieved_nodes = self._retrieve_from_collections(
                standalone_question,
                target_collections
            )

            # 5. Build context from retrieved nodes
            context_str = "\n\n".join([
                f"[Tài liệu {i+1}]\n{node.text}"
                for i, node in enumerate(retrieved_nodes)
            ])

            # 6. Generate response with QA prompt
            qa_prompt = self.QA_PROMPT_VI.format(
                context_str=context_str,
                query_str=message  # Use original question, not condensed
            )

            response = self.llm.complete(qa_prompt)
            response_text = response.text.strip()

            # 7. Save to memory
            user_msg = ChatMessage(role="user", content=message)
            self.memory_store.add_message(session_id, user_msg)

            assistant_msg = ChatMessage(role="assistant", content=response_text)
            self.memory_store.add_message(session_id, assistant_msg)

            print(f"[CHAT] Assistant: {response_text[:200]}...\n")

            # 8. Build result
            result = {
                "response": response_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "routed_collections": target_collections
            }

            if return_source_nodes:
                result["source_nodes"] = [
                    {
                        "text": node.text[:200] + "...",
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": node.metadata if hasattr(node, 'metadata') else {}
                    }
                    for node in retrieved_nodes
                ]

            return result

        except Exception as e:
            print(f"[ERROR] Chat failed: {e}")
            import traceback
            traceback.print_exc()

            error_response = "Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn."

            # Still save error to memory for debugging
            user_msg = ChatMessage(role="user", content=message)
            assistant_msg = ChatMessage(role="assistant", content=error_response)
            self.memory_store.add_message(session_id, user_msg)
            self.memory_store.add_message(session_id, assistant_msg)

            return {
                "response": error_response,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
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
