"""
Centralized configuration for MCP Server.

This service is responsible for:
- Document retrieval from vector store
- DAA portal scraping (grades, schedule)
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Paths:
    """Path configurations for MCP Server."""
    # Navigate from settings.py to project root
    # apps/mcp-server/src/config/settings.py -> root
    ROOT_DIR = Path(__file__).resolve().parents[4]
    DATA_DIR = ROOT_DIR / "data"

    # Vector store path (read-only, built by knowledge-builder)
    VECTOR_STORE_DIR = DATA_DIR / "vector_store"


class Credentials:
    """API keys and sensitive credentials."""
    def __init__(self):
        """Load credentials from environment."""
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class Retrieval:
    """Configuration for retrieval and vector search."""
    # Retrieval configuration
    SIMILARITY_TOP_K = 7
    MINIMUM_SCORE_THRESHOLD = 0.15

    def __init__(self):
        """Load retrieval configs from environment."""
        load_dotenv()
        self.EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")


class QueryRouting:
    """Configuration for query routing strategy."""
    def __init__(self):
        """Load query routing configs from environment."""
        load_dotenv()

        # "query_all" | "llm_classification"
        self.STRATEGY = os.getenv("ROUTING_STRATEGY", "query_all")
        self.AVAILABLE_COLLECTIONS = os.getenv(
            "AVAILABLE_COLLECTIONS",
            "regulation,curriculum"
        ).split(",")

        # LLM classification settings (for llm_classification strategy)
        self.CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "gpt-4o-mini")
        self.CLASSIFICATION_TEMPERATURE = float(os.getenv("CLASSIFICATION_TEMPERATURE", "0.0"))


class Settings:
    """
    Main settings singleton for MCP Server.

    Contains only configurations relevant to:
    - Reading vector store
    - Retrieving documents
    - Scraping DAA portal
    """
    def __init__(self):
        print("[CONFIG] Initializing MCP Server settings...")

        # Load credentials first (used by other modules)
        self.credentials = Credentials()

        # Static configs
        self.paths = Paths()

        # Dynamic configs (load from env)
        self.retrieval = Retrieval()
        self.query_routing = QueryRouting()

        print(f"[CONFIG] Vector store path: {self.paths.VECTOR_STORE_DIR}")
        print(f"[CONFIG] Embed model: {self.retrieval.EMBED_MODEL}")
        print(f"[CONFIG] Routing strategy: {self.query_routing.STRATEGY}")


# Singleton instance
settings = Settings()
