"""
Centralized configuration management for the entire application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Configuration Groups (as nested classes) ---

class Paths:
    """Houses all static path configurations for the application."""
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT_DIR / "data"

    # Production paths
    RAW_DATA_DIR = DATA_DIR / os.getenv("RAW_DATA_DIR", "raw")
    PROCESSED_DATA_DIR = DATA_DIR / os.getenv("PROCESSED_DATA_DIR", "processed")
    VECTOR_STORE_DIR = DATA_DIR / "vector_store"

    # Test paths (can override via env vars)
    RAW_TEST_DIR = DATA_DIR / "raw_test"
    PROCESSED_TEST_DIR = DATA_DIR / "processed_test"



# --- FIX: Create a new class for data sources/domains ---
class Domains:
    """Configuration for data sources and domains to be processed."""
    START_URLS = {
        "daa.uit.edu.vn": "https://daa.uit.edu.vn/"
    }

class Credentials:
    """API keys and sensitive credentials."""
    def __init__(self):
        """Load credentials from environment."""
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class LLM:
    """LLM configuration (models, providers)."""
    def __init__(self):
        """Load LLM configs from environment."""
        load_dotenv()
        self.PROVIDER = os.getenv("LLM_PROVIDER", "openai")
        self.MODEL = os.getenv("LLM_MODEL", "gpt-4.1-nano")

class Crawler:
    """Houses all configurations related to the crawler module."""
    CRAWL_DELAY = 2.0
    REQUEST_TIMEOUT = 30
    DOWNLOADABLE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']

    def __init__(self):
        """Load crawler configs from environment."""
        load_dotenv()
        self.MAX_PAGES_PER_DOMAIN = int(os.getenv("MAX_PAGES_PER_DOMAIN", "1000"))

class Retrieval:
    """Configuration for retrieval and vector search."""
    # Chunking configuration
    CHUNK_SIZE = 1024           # Target chunk size for sub-chunking
    CHUNK_OVERLAP = 200         # Overlap between chunks (20% of chunk size)
    MAX_TOKENS = 8000           # Max tokens before sub-chunking (buffer for 8191 limit)

    # Retrieval configuration
    SIMILARITY_TOP_K = 7  # Increased from 5 for better retrieval coverage
    MINIMUM_SCORE_THRESHOLD = 0.15  # Lowered from 0.2 to reduce false negatives

    def __init__(self):
        """Load retrieval configs from environment."""
        load_dotenv()
        self.EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

class Chat:
    """Houses all configurations for the Chat Engine."""
    MAX_HISTORY_MESSAGES = 10  # Number of previous messages to keep in context
    MEMORY_TOKEN_LIMIT = 3000  # Max tokens for chat history in LlamaIndex memory buffer
    MEMORY_TYPE = "in_memory"  # Options: "in_memory", "redis" (future)
    SESSION_TIMEOUT = 3600     # Session timeout in seconds (1 hour)
    CONDENSE_PROMPT_LANG = "vi" # Language for condensing prompts

class Processing:
    """Configuration for document processing and parsing."""
    def __init__(self):
        """Load processing configs from environment."""
        load_dotenv()

        # LlamaParse configuration
        self.USE_LLAMAPARSE = os.getenv("USE_LLAMAPARSE", "true").lower() == "true"
        self.PARSE_MODE = os.getenv("PARSE_MODE", "parse_page_with_agent")
        self.PARSE_MODEL = os.getenv("PARSE_MODEL", "openai-gpt-4.1-mini")

        # Processing behavior
        self.SKIP_ANNOUNCEMENTS = os.getenv("SKIP_ANNOUNCEMENTS", "true").lower() == "true"
        self.PROCESS_CATEGORIES = os.getenv("PROCESS_CATEGORIES", "regulation,curriculum").split(",")

        # Content filtering
        self.ENABLE_CONTENT_FILTER = os.getenv("ENABLE_CONTENT_FILTER", "true").lower() == "true"
        self.MIN_CONTENT_SCORE = float(os.getenv("MIN_CONTENT_SCORE", "40.0"))

        # Metadata generation
        self.METADATA_GENERATION_MODEL = os.getenv("METADATA_GENERATION_MODEL", "gpt-4.1-nano")

class QueryRouting:
    """Configuration for query routing strategy."""
    def __init__(self):
        """Load query routing configs from environment."""
        load_dotenv()

        self.STRATEGY = os.getenv("ROUTING_STRATEGY", "query_all")  # "query_all" | "llm_classification"
        self.AVAILABLE_COLLECTIONS = os.getenv("AVAILABLE_COLLECTIONS", "regulation,curriculum").split(",")

        # LLM classification settings (for llm_classification strategy)
        self.CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "gpt-4.1-nano")
        self.CLASSIFICATION_TEMPERATURE = float(os.getenv("CLASSIFICATION_TEMPERATURE", "0.0"))

class Preprocessing:
    """Configuration for markdown preprocessing (structure fixing)."""
    def __init__(self):
        """Load preprocessing configs from environment."""
        load_dotenv()

        # Google Gemini for markdown fixing
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
        self.GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "65000"))  # Gemini 2.5 Flash supports up to 65,536

        # Rate limiting (Google AI Studio free tier - Gemini 2.5 Flash)
        self.GEMINI_RPM = int(os.getenv("GEMINI_RPM", "10"))  # Requests per minute
        self.GEMINI_TPM = int(os.getenv("GEMINI_TPM", "250000"))  # Tokens per minute (input only)
        self.GEMINI_RPD = int(os.getenv("GEMINI_RPD", "250"))  # Requests per day

# --- Main Settings Singleton Class ---

class Settings:
    """
    The main singleton class that holds all configuration objects.
    """
    def __init__(self):
        print("[CONFIG] Initializing application settings...")

        # Load credentials first (used by other modules)
        self.credentials = Credentials()
        self.llm = LLM()

        # Static configs
        self.paths = Paths()
        self.domains = Domains()
        self.chat = Chat()

        # Dynamic configs (load from env)
        self.crawler = Crawler()
        self.retrieval = Retrieval()
        self.processing = Processing()
        self.query_routing = QueryRouting()
        self.preprocessing = Preprocessing()

        self._ensure_directories()

    def _ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        print("[CONFIG] Ensuring all necessary directories exist...")
        directories_to_create = [
            # Production directories
            self.paths.RAW_DATA_DIR,
            self.paths.PROCESSED_DATA_DIR,
            self.paths.VECTOR_STORE_DIR,

            # Test directories
            self.paths.RAW_TEST_DIR,
            self.paths.PROCESSED_TEST_DIR,

        ]
        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)

# --- Singleton Instance --- 
settings = Settings()
