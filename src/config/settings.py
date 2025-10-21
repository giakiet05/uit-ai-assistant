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
    
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    VECTOR_STORE_DIR = DATA_DIR / "vector_store"

    RAW_DAA_DIR = RAW_DATA_DIR / "daa.uit.edu.vn"
    RAW_UIT_DIR = RAW_DATA_DIR / "uit.edu.vn"
    PROCESSED_DAA_DIR = PROCESSED_DATA_DIR / "daa.uit.edu.vn"
    PROCESSED_UIT_DIR = PROCESSED_DATA_DIR / "uit.edu.vn"

# --- FIX: Create a new class for data sources/domains ---
class Domains:
    """Configuration for data sources and domains to be processed."""
    START_URLS = {
        "daa.uit.edu.vn": "https://daa.uit.edu.vn/",
        "uit.edu.vn": "https://uit.edu.vn/",
    }

class Crawler:
    """Houses all configurations related to the crawler module."""
    # START_URLS moved to Domains class
    CRAWL_DELAY = 2.0
    REQUEST_TIMEOUT = 30
    DOWNLOADABLE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']

class RAG:
    """Houses all configurations for the RAG pipeline (building and querying)."""
    CHUNK_SIZE = 1024
    SIMILARITY_TOP_K = 5
    MINIMUM_SCORE_THRESHOLD = 0.2

class Env:
    """Houses all settings loaded from environment variables."""
    def __init__(self):
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
        self.MAX_PAGES_PER_DOMAIN = int(os.getenv("MAX_PAGES_PER_DOMAIN", "1000"))

# --- Main Settings Singleton Class ---

class Settings:
    """
    The main singleton class that holds all configuration objects.
    """
    def __init__(self):
        print("[CONFIG] Initializing application settings...")
        
        self.env = Env()
        self.paths = Paths()
        self.domains = Domains() # <-- Add new Domains group
        self.crawler = Crawler()
        self.rag = RAG()

        self._ensure_directories()

    def _ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        print("[CONFIG] Ensuring all necessary directories exist...")
        directories_to_create = [
            self.paths.RAW_DATA_DIR,
            self.paths.PROCESSED_DATA_DIR,
            self.paths.VECTOR_STORE_DIR,
            self.paths.RAW_DAA_DIR,
            self.paths.RAW_UIT_DIR,
            self.paths.PROCESSED_DAA_DIR,
            self.paths.PROCESSED_UIT_DIR,
        ]
        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)

# --- Singleton Instance --- 
settings = Settings()
