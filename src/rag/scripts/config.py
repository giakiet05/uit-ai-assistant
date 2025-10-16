"""
Configuration module for RAG system
Manages environment variables and system settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for RAG system"""
    
    # Project paths
    BASE_DIR = Path(__file__).resolve().parents[3]  # thoát ra khỏi src/ 
    DATA_DIR = BASE_DIR / "data" / "test"
    CHROMA_DIR = BASE_DIR / "chroma_db"
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "openai"
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Ollama settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")  # Smaller, faster model
    
    # Embedding settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "local")  # "local" or "openai"
    
    # ChromaDB settings
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "educational_docs")
    
    # Chunk settings - smaller chunks for better precision
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "256"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Query settings
    SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))  # Lower for more focused responses
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.CHROMA_DIR.mkdir(exist_ok=True)
        print(f"✓ Directories created: {cls.DATA_DIR}, {cls.CHROMA_DIR}")
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        
        print("✓ Configuration validated successfully")
        return True

# Initialize directories on import
Config.ensure_directories()
