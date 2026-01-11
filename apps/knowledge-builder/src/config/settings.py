"""
Centralized configuration management for Knowledge Builder.

This service is responsible for:
- Crawling websites for raw data
- Processing and cleaning documents
- Generating metadata
- Building vector store index
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Paths:
    """Path configurations for Knowledge Builder."""

    # Navigate from settings.py to project root
    # apps/knowledge-builder/src/config/settings.py -> root
    ROOT_DIR = Path(__file__).resolve().parents[4]
    DATA_DIR = ROOT_DIR / "data"

    # Production paths
    RAW_DATA_DIR = DATA_DIR / os.getenv("RAW_DATA_DIR", "raw")
    STAGES_DIR = DATA_DIR / "stages"  # NEW: Stage-based pipeline
    VECTOR_STORE_DIR = DATA_DIR / "vector_store"

    # Deprecated (kept for backward compatibility during migration)
    PROCESSED_DATA_DIR = DATA_DIR / os.getenv("PROCESSED_DATA_DIR", "processed")

    @staticmethod
    def get_stage_dir(category: str, document_id: str) -> Path:
        """
        Get stage directory for a document.

        Args:
            category: Document category (regulation, curriculum, etc.)
            document_id: Document ID

        Returns:
            Path to stages/{category}/{document_id}/
        """
        return Paths.STAGES_DIR / category / document_id

    @staticmethod
    def get_stage_output(category: str, document_id: str, stage_output: str) -> Path:
        """
        Get output file path for a stage.

        Args:
            category: Document category
            document_id: Document ID
            stage_output: Output filename (e.g., "02-cleaned.md")

        Returns:
            Path to stages/{category}/{document_id}/{stage_output}
        """
        return Paths.get_stage_dir(category, document_id) / stage_output

    @staticmethod
    def get_final_output(category: str, document_id: str) -> Path:
        """
        Get final processed output for a document.

        Args:
            category: Document category
            document_id: Document ID

        Returns:
            Path to final output file (latest stage output)
            
        Logic:
            Check in reverse order: 06-flattened.md → 05-fixed.md
            Return the first one that exists.
        """
        stage_dir = Paths.get_stage_dir(category, document_id)
        
        # Check for 06-flattened.md first (if flatten-table was run)
        flattened = stage_dir / "06-flattened.md"
        if flattened.exists():
            return flattened
        
        # Fallback to 05-fixed.md
        fixed = stage_dir / "05-fixed.md"
        if fixed.exists():
            return fixed
        
        # If neither exists, return 05-fixed.md as default
        return fixed

    @staticmethod
    def get_metadata(category: str, document_id: str) -> Path:
        """
        Get metadata file path for a document.

        Args:
            category: Document category
            document_id: Document ID

        Returns:
            Path to metadata.json
        """
        return Paths.get_stage_dir(category, document_id) / "metadata.json"


class Domains:
    """Configuration for data sources and domains to be crawled."""

    START_URLS = {"daa.uit.edu.vn": "https://daa.uit.edu.vn/"}


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
        self.MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


class Indexing:
    """Configuration for indexing and vector store."""

    # Chunking configuration
    CHUNK_SIZE = 1024  # Target chunk size for sub-chunking
    CHUNK_OVERLAP = 200  # Overlap between chunks (20% of chunk size)
    MAX_TOKENS = 8000  # Max tokens before sub-chunking

    def __init__(self):
        """Load indexing configs from environment."""
        load_dotenv()
        self.EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
        self.COLLECTIONS = os.getenv("COLLECTIONS", "regulation,curriculum").split(",")


class Processing:
    """Configuration for document processing and parsing."""

    def __init__(self):
        """Load processing configs from environment."""
        load_dotenv()

        # LlamaParse configuration
        self.USE_LLAMAPARSE = os.getenv("USE_LLAMAPARSE", "true").lower() == "true"
        self.PARSE_MODE = os.getenv("PARSE_MODE", "parse_page_with_agent")
        self.PARSE_MODEL = os.getenv("PARSE_MODEL", "openai-gpt-4o-mini")

        # Processing behavior
        self.SKIP_ANNOUNCEMENTS = (
            os.getenv("SKIP_ANNOUNCEMENTS", "true").lower() == "true"
        )
        self.PROCESS_CATEGORIES = os.getenv(
            "PROCESS_CATEGORIES", "regulation,curriculum"
        ).split(",")

        # Content filtering
        self.ENABLE_CONTENT_FILTER = (
            os.getenv("ENABLE_CONTENT_FILTER", "true").lower() == "true"
        )
        self.MIN_CONTENT_SCORE = float(os.getenv("MIN_CONTENT_SCORE", "40.0"))

        # Metadata generation
        self.METADATA_GENERATION_MODEL = os.getenv(
            "METADATA_GENERATION_MODEL", "gpt-4o-mini"
        )


class Preprocessing:
    """Configuration for markdown preprocessing (structure fixing)."""

    def __init__(self):
        """Load preprocessing configs from environment."""
        load_dotenv()

        # Google Gemini for markdown fixing
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
        self.GEMINI_MAX_OUTPUT_TOKENS = int(
            os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "65000")
        )

        # Rate limiting (Google AI Studio free tier)
        self.GEMINI_RPM = int(os.getenv("GEMINI_RPM", "10"))  # Requests per minute
        self.GEMINI_TPM = int(os.getenv("GEMINI_TPM", "250000"))  # Tokens per minute
        self.GEMINI_RPD = int(os.getenv("GEMINI_RPD", "250"))  # Requests per day


class Crawler:
    """Configuration for web crawling."""

    def __init__(self):
        """Load crawler configs from environment."""
        load_dotenv()

        # Crawling behavior
        self.MAX_DEPTH = int(os.getenv("CRAWLER_MAX_DEPTH", "3"))
        self.DELAY_BETWEEN_REQUESTS = float(
            os.getenv("CRAWLER_DELAY", "1.0")
        )  # seconds
        self.USER_AGENT = os.getenv("CRAWLER_USER_AGENT", "UIT-AI-Assistant-Bot/1.0")


class Settings:
    """
    Main settings singleton for Knowledge Builder.

    Contains only configurations relevant to:
    - Crawling websites
    - Processing documents
    - Generating metadata
    - Building vector store
    """

    def __init__(self):
        print("[CONFIG] Initializing Knowledge Builder settings...")

        # Load credentials first (used by other modules)
        self.credentials = Credentials()
        self.llm = LLM()

        # Static configs
        self.paths = Paths()
        self.domains = Domains()

        # Dynamic configs (load from env)
        self.crawler = Crawler()
        self.indexing = Indexing()
        self.processing = Processing()
        self.preprocessing = Preprocessing()

        self._ensure_directories()

    def _ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        print("[CONFIG] Ensuring all necessary directories exist...")
        directories_to_create = [
            # Production directories
            self.paths.RAW_DATA_DIR,
            self.paths.STAGES_DIR,  # NEW: Stage-based pipeline
            self.paths.VECTOR_STORE_DIR,
            # Keep PROCESSED_DATA_DIR for backward compatibility (will be removed after migration)
            self.paths.PROCESSED_DATA_DIR,
        ]
        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)


# Singleton instance
settings = Settings()
