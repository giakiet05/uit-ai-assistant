"""
Vector store module using ChromaDB
Handles document embedding and vector storage
"""

from typing import List, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    ServiceContext,
    Settings as LlamaSettings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document
from config import Config
from data_processor import DataProcessor

class VectorStoreManager:
    """Manage ChromaDB vector store for RAG system"""
    
    def __init__(self):
        self.config = Config
        self.chroma_client = None
        self.collection = None
        self.vector_store = None
        self.index = None
        
        # Initialize embedding model
        self._setup_embeddings()
        
        # Initialize ChromaDB
        self._setup_chroma()
    
    def _setup_embeddings(self):
        """Setup embedding model based on configuration"""
        print("\n🔧 Setting up embedding model...")
        
        if self.config.EMBEDDING_MODEL == "openai":
            if not self.config.OPENAI_API_KEY:
                raise ValueError("OpenAI API key required for OpenAI embeddings")
            
            embed_model = OpenAIEmbedding(
                api_key=self.config.OPENAI_API_KEY,
                model="text-embedding-ada-002"
            )
            print("✓ Using OpenAI embeddings")
        else:
            embed_model = HuggingFaceEmbedding(
                model_name="BAAI/bge-small-en-v1.5",  # Stable, works well with multilingual text
                max_length=512  # Explicit max length
            )
            print("✓ Using HuggingFace embeddings (multilingual support)")
        
        # Set global embedding model
        LlamaSettings.embed_model = embed_model
        
        LlamaSettings.text_splitter = SentenceSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP
        )
        print(f"  - Chunk size: {self.config.CHUNK_SIZE} tokens")
        print(f"  - Chunk overlap: {self.config.CHUNK_OVERLAP} tokens")
    
    def _setup_chroma(self):
        """Initialize ChromaDB client and collection"""
        print("\n🔧 Setting up ChromaDB...")
        
        try:
            # Create ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.config.CHROMA_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.config.COLLECTION_NAME
            )
            
            print(f"✓ ChromaDB initialized at: {self.config.CHROMA_DIR}")
            print(f"✓ Collection: {self.config.COLLECTION_NAME}")
            
        except Exception as e:
            error_msg = str(e)
            # Check if it's a schema error
            if "no such column" in error_msg or "collections.topic" in error_msg:
                print(f"⚠ ChromaDB schema error detected: {error_msg}")
                print("🔄 Attempting to reset ChromaDB database...")
                
                # Delete the corrupted database directory
                import shutil
                if self.config.CHROMA_DIR.exists():
                    shutil.rmtree(self.config.CHROMA_DIR)
                    print(f"✓ Deleted corrupted database at: {self.config.CHROMA_DIR}")
                
                # Recreate the client and collection
                self.chroma_client = chromadb.PersistentClient(
                    path=str(self.config.CHROMA_DIR),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                self.collection = self.chroma_client.create_collection(
                    name=self.config.COLLECTION_NAME
                )
                
                print("✓ ChromaDB reset and reinitialized successfully")
                print(f"✓ Collection: {self.config.COLLECTION_NAME}")
            else:
                # Re-raise if it's a different error
                raise

    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """Create vector index from documents"""
        print(f"\n📊 Creating vector index from {len(documents)} documents...")
        
        # Create vector store
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Create index
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        print("✓ Vector index created successfully")
        return self.index
    
    def load_index(self) -> Optional[VectorStoreIndex]:
        """Load existing vector index"""
        try:
            print("\n📂 Loading existing vector index...")
            
            count = self.collection.count()
            if count == 0:
                print("⚠ Collection is empty. No index to load.")
                return None
            
            # Create vector store
            self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
            
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            # Load index
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context
            )
            
            print(f"✓ Vector index loaded successfully ({count} documents)")
            return self.index
            
        except Exception as e:
            print(f"⚠ Could not load existing index: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Get vector store statistics"""
        count = self.collection.count()
        return {
            "collection_name": self.config.COLLECTION_NAME,
            "document_count": count,
            "chroma_path": str(self.config.CHROMA_DIR)
        }
    
    def reset(self):
        """Reset vector store (delete all data)"""
        print("\n⚠ Resetting vector store...")
        self.chroma_client.delete_collection(name=self.config.COLLECTION_NAME)
        self.collection = self.chroma_client.create_collection(
            name=self.config.COLLECTION_NAME
        )
        print("✓ Vector store reset complete")

def build_vector_store():
    """Main function to build vector store from documents"""
    print("=" * 60)
    print("🚀 Building Vector Store for RAG System")
    print("=" * 60)
    
    # Initialize components
    data_processor = DataProcessor()
    vector_manager = VectorStoreManager()
    
    # Load documents
    documents = data_processor.load_documents()
    
    if not documents:
        print("\n⚠ No documents found in data directory!")
        print(f"Please add documents to: {Config.DATA_DIR}")
        return None
    
    # Create vector index
    index = vector_manager.create_index(documents)
    
    # Show statistics
    stats = vector_manager.get_stats()
    print("\n" + "=" * 60)
    print("📊 Vector Store Statistics")
    print("=" * 60)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✅ Vector store built successfully!")
    return index

if __name__ == "__main__":
    build_vector_store()
