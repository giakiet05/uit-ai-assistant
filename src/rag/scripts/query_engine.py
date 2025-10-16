"""
Query engine module for RAG system
Handles question answering with context retrieval
"""

from typing import Optional, Dict, List
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.prompts import PromptTemplate
from config import Config
from vector_store import VectorStoreManager
from llm_config import LLMConfigurator

class RAGQueryEngine:
    """RAG Query Engine for answering questions"""
    
    QA_PROMPT_TEMPLATE = """
Bạn là trợ lý AI chuyên về giáo dục đại học tại Việt Nam. Bạn PHẢI tuân thủ các quy tắc sau:

QUAN TRỌNG - QUY TẮC BẮT BUỘC:
1. BẮT BUỘC trả lời HOÀN TOÀN bằng tiếng Việt
2. KHÔNG được trả lời bằng tiếng Anh dù trong bất kỳ trường hợp nào
3. Chỉ sử dụng thông tin từ ngữ cảnh được cung cấp bên dưới
4. Nếu không tìm thấy thông tin, hãy nói: "Tôi không tìm thấy thông tin này trong tài liệu"

NGỮ CẢNH TÀI LIỆU:
{context_str}

CÂU HỎI CỦA SINH VIÊN: {query_str}

HƯỚNG DẪN TRẢ LỜI:
- Đọc kỹ ngữ cảnh và tìm thông tin liên quan trực tiếp đến câu hỏi
- Trả lời ngắn gọn, rõ ràng bằng tiếng Việt
- Trích dẫn chính xác từ tài liệu nếu có
- Nếu câu hỏi không liên quan đến tài liệu, hãy nói rõ
- Sử dụng bullet points để liệt kê thông tin nếu cần

TRẢ LỜI (BẮT BUỘC BẰNG TIẾNG VIỆT):
"""
    
    def __init__(self, index: Optional[VectorStoreIndex] = None):
        self.config = Config
        self.index = index
        self.query_engine = None
        
        # Initialize LLM
        self.llm_config = LLMConfigurator()
        
        # Setup query engine if index provided
        if self.index:
            self._setup_query_engine()
    
    def load_or_create_index(self) -> bool:
        """Load existing index or return False if not found"""
        try:
            vector_manager = VectorStoreManager()
            
            # Try to load existing index
            index = vector_manager.load_index()
            
            if index is None:
                print("\n⚠ No existing index found!")
                print("💡 Please add documents to the data directory")
                print("💡 Then run: python scripts/vector_store.py")
                return False
            
            self.index = index
            self._setup_query_engine()
            return True
            
        except Exception as e:
            print(f"❌ Error loading index: {e}")
            return False
    
    def _setup_query_engine(self):
        """Setup query engine with retriever and response synthesizer"""
        print("\n🔧 Setting up query engine...")
        
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=5  # Increased from 3 to 5 for better context
        )
        
        # Create custom prompt
        qa_prompt = PromptTemplate(self.QA_PROMPT_TEMPLATE)
        
        response_synthesizer = get_response_synthesizer(
            text_qa_template=qa_prompt,
            response_mode="refine"  # Better quality than 'compact'
        )
        
        # Create query engine
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
        
        print("✓ Query engine configured successfully")
        print("  - Retrieval: Top 5 most relevant chunks")
        print("  - Response mode: Refine (high quality)")
    
    def query(self, question: str) -> Dict:
        """
        Query the RAG system with a question
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.query_engine:
            if not self.index:
                success = self.load_or_create_index()
                if not success:
                    raise RuntimeError("Cannot query: No vector index available")
            else:
                self._setup_query_engine()
        
        print(f"\n❓ Question: {question}")
        
        try:
            print("⏳ Đang xử lý câu hỏi... (có thể mất 30-60 giây)")
            
            # Execute query with timeout handling
            response = self.query_engine.query(question)
            
            # Extract source information
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        'text': node.text[:200] + "...",
                        'score': node.score,
                        'metadata': node.metadata
                    })
            
            result = {
                'answer': str(response),
                'sources': sources,
                'question': question
            }
            
            print(f"\n💡 Answer: {result['answer'][:200]}...")
            
            return result
            
        except TimeoutError as e:
            print("\n❌ Timeout Error: LLM không phản hồi trong thời gian cho phép")
            print("\n🔧 Các bước khắc phục:")
            print("1. Kiểm tra Ollama đang chạy: ollama list")
            print("2. Khởi động Ollama nếu chưa chạy: ollama serve")
            print("3. Kiểm tra model đã tải: ollama list")
            print(f"4. Tải model nếu chưa có: ollama pull {self.config.OLLAMA_MODEL}")
            print("5. Thử model nhẹ hơn: ollama pull llama3.2:1b")
            raise
        except Exception as e:
            print(f"\n❌ Error during query: {e}")
            print("\n🔧 Kiểm tra:")
            print("1. Ollama đang chạy: ollama serve")
            print(f"2. Model đã tải: ollama pull {self.config.OLLAMA_MODEL}")
            print("3. Kết nối mạng ổn định")
            raise

    def chat(self):
        """Interactive chat mode"""
        print("\n" + "=" * 60)
        print("🤖 RAG Educational Chatbot")
        print("=" * 60)
        print("Nhập câu hỏi của bạn (hoặc 'exit' để thoát)")
        print("=" * 60 + "\n")
        
        # Ensure index is loaded
        if not self.index:
            success = self.load_or_create_index()
            if not success:
                print("\n❌ Cannot start chat: No documents indexed")
                print("💡 Please add documents and build the index first")
                return
        
        while True:
            try:
                question = input("\n👤 Bạn: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['exit', 'quit', 'thoát']:
                    print("\n👋 Tạm biệt!")
                    break
                
                # Get response
                result = self.query(question)
                
                print(f"\n🤖 Bot: {result['answer']}")
                
                # Show sources if available
                if result['sources']:
                    print(f"\n📚 Nguồn tham khảo ({len(result['sources'])} tài liệu):")
                    for i, source in enumerate(result['sources'][:3], 1):
                        print(f"\n  {i}. {source['metadata'].get('filename', 'Unknown')}")
                        print(f"     Độ liên quan: {source['score']:.2f}")
                        print(f"     Trích dẫn: {source['text'][:150]}...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")

def main():
    """Main function to run query engine"""
    try:
        # Initialize query engine
        engine = RAGQueryEngine()
        
        # Start interactive chat
        engine.chat()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
