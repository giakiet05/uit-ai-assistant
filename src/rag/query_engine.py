"""
Contains the core QueryEngine class for interacting with the RAG pipeline.
This version implements advanced techniques like custom prompts, manual engine setup, and a confidence score threshold.
"""

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    Settings,
    PromptTemplate
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.base.response.schema import Response
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode
from llama_index.core.node_parser import SemanticSplitterNodeParser

from src.config import VECTOR_STORE_DIR
from src.llm import create_llm

class QueryEngine:
    """
    The main entry point for querying the RAG system.
    """

    QA_PROMPT_TEMPLATE_STR = ("""
Bạn là một trợ lý AI chuyên gia về lĩnh vực giáo dục đại học. 
Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên một cách chính xác và chi tiết dựa trên thông tin từ các tài liệu được cung cấp.

QUY TẮC BẮT BUỘC:
1. TRẢ LỜI HOÀN TOÀN BẰNG TIẾNG VIỆT.
2. Chỉ sử dụng thông tin từ "Ngữ cảnh tài liệu" bên dưới. Tuyệt đối không bịa đặt thông tin hoặc dùng kiến thức bên ngoài.
3. Nếu thông tin không có trong ngữ cảnh để trả lời câu hỏi, hãy nói rõ ràng là: "Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."

Ngữ cảnh tài liệu:
---------------------
{context_str}
---------------------

Câu hỏi của sinh viên: {query_str}

Hướng dẫn trả lời:
- Đọc kỹ toàn bộ ngữ cảnh để tìm ra tất cả các thông tin liên quan đến câu hỏi.
- Nếu câu hỏi yêu cầu liệt kê, hãy đảm bảo liệt kê ĐẦY ĐỦ TẤT CẢ các mục bạn tìm thấy trong ngữ cảnh.
- Trình bày câu trả lời một cách rõ ràng, có cấu trúc, sử dụng gạch đầu dòng (-) cho các danh sách.

Câu trả lời chi tiết của bạn (bằng tiếng Việt):
""")

    MINIMUM_SCORE_THRESHOLD = 0.1

    def __init__(self, llm_provider: str = "ollama", llm_model: str = "llama3"):
        """
        Initializes the QueryEngine by loading the vector store and setting up the retriever and response synthesizer.
        """
        print("[INFO] Initializing QueryEngine...")
        
        # 1. Configure global Settings
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        node_parser = SemanticSplitterNodeParser.from_defaults(embed_model=embed_model, breakpoint_percentile_threshold=95)
        Settings.embed_model = embed_model
        Settings.node_parser = node_parser
        Settings.llm = create_llm(provider=llm_provider, model=llm_model)

        # 2. Load the existing Vector Store
        print(f"[INFO] Loading vector store from: {VECTOR_STORE_DIR}")
        db = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        chroma_collection = db.get_or_create_collection("uit_documents")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store)

        # 3. Manually create and store the retriever and response synthesizer
        print("[INFO] Manually setting up retriever and response synthesizer...")
        self.retriever = index.as_retriever(similarity_top_k=5)
        
        qa_prompt_template = PromptTemplate(self.QA_PROMPT_TEMPLATE_STR)
        self.response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode.REFINE,
            text_qa_template=qa_prompt_template,
            streaming=False
        )
        print("✅ QueryEngine initialized successfully with custom components.")

    def query(self, question: str) -> Response:
        """
        Queries the RAG system with a given question, with a confidence check.
        """
        print(f"\n--- New Query ---\nQuestion: {question}")
        try:
            # 1. Retrieve relevant nodes first
            retrieved_nodes = self.retriever.retrieve(question)

            if not retrieved_nodes:
                print("[INFO] No relevant documents found.")
                return Response(response="Tôi không tìm thấy thông tin nào liên quan đến câu hỏi của bạn trong tài liệu.")

            # 2. Check the confidence score of the most relevant node
            top_node = retrieved_nodes[0]
            print(f"[INFO] Top node score: {top_node.score:.4f}")
            if top_node.score < self.MINIMUM_SCORE_THRESHOLD:
                print(f"[INFO] Top node score is below threshold ({self.MINIMUM_SCORE_THRESHOLD}). Answering based on general knowledge is forbidden.")
                return Response(response="Tôi không tìm thấy thông tin đủ liên quan trong tài liệu để trả lời câu hỏi này một cách chính xác.")

            # 3. If confident, synthesize the response using the retrieved nodes
            print("[INFO] Confident enough to synthesize response from retrieved context.")
            response = self.response_synthesizer.synthesize(question, nodes=retrieved_nodes)
            return response

        except Exception as e:
            print(f"[ERROR] An error occurred during query: {e}")
            return Response(response="Sorry, an error occurred while processing your question.")
