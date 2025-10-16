"""
FastAPI server for RAG system
Provides REST API endpoints for the chatbot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
from query_engine import RAGQueryEngine
from vector_store import VectorStoreManager
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="RAG Educational Chatbot API",
    description="API for RAG-based educational chatbot system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global query engine instance
query_engine: Optional[RAGQueryEngine] = None

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None

class Source(BaseModel):
    text: str
    score: float
    metadata: Dict

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    question: str

class StatusResponse(BaseModel):
    status: str
    message: str
    stats: Optional[Dict] = None

@app.on_event("startup")
async def startup_event():
    """Initialize query engine on startup"""
    global query_engine
    try:
        print("\n🚀 Initializing RAG Query Engine...")
        query_engine = RAGQueryEngine()
        
        success = query_engine.load_or_create_index()
        
        if success:
            print("✓ Query engine ready")
        else:
            print("⚠ Query engine initialized but no documents found")
            print("💡 Add documents to the data directory and rebuild the index")
            
    except Exception as e:
        print(f"❌ Failed to initialize query engine: {e}")
        print("💡 Try deleting the chroma_db directory and rebuilding the index")
        query_engine = None

@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint - health check"""
    return StatusResponse(
        status="ok",
        message="RAG Educational Chatbot API is running"
    )

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Health check endpoint"""
    if query_engine is None:
        raise HTTPException(status_code=503, detail="Query engine not initialized")
    
    return StatusResponse(
        status="healthy",
        message="System is operational"
    )

@app.get("/stats", response_model=StatusResponse)
async def get_stats():
    """Get system statistics"""
    try:
        vector_manager = VectorStoreManager()
        stats = vector_manager.get_stats()
        
        return StatusResponse(
            status="ok",
            message="Statistics retrieved successfully",
            stats=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """
    Query the RAG chatbot
    
    Args:
        request: QueryRequest with question and optional parameters
        
    Returns:
        QueryResponse with answer and sources
    """
    if query_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Query engine not initialized. Please ensure vector store is built."
        )
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Override top_k if provided
        if request.top_k:
            original_top_k = Config.SIMILARITY_TOP_K
            Config.SIMILARITY_TOP_K = request.top_k
        
        # Execute query
        result = query_engine.query(request.question)
        
        # Restore original top_k
        if request.top_k:
            Config.SIMILARITY_TOP_K = original_top_k
        
        return QueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/rebuild-index")
async def rebuild_index():
    """Rebuild vector index from documents"""
    try:
        from vector_store import build_vector_store
        
        print("\n🔄 Rebuilding vector index...")
        index = build_vector_store()
        
        if index:
            # Reinitialize query engine with new index
            global query_engine
            query_engine = RAGQueryEngine(index=index)
            
            return StatusResponse(
                status="ok",
                message="Vector index rebuilt successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to rebuild index - no documents found"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    print("\n" + "=" * 60)
    print("🚀 Starting RAG Chatbot API Server")
    print("=" * 60)
    print(f"Server: http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
