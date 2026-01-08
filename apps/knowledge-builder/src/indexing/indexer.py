"""
Document Indexer - Category-based indexing for ChromaDB.

This module provides tools for building ChromaDB vector stores from processed documents,
with separate collections per category (regulation, curriculum, etc.).

REFACTORED: Now uses IndexingPipeline (chunk -> embed-index stages).
Legacy methods maintained for backward compatibility.
"""

import chromadb
import json
import unicodedata
from typing import List, Optional, Dict
from pathlib import Path

# --- Centralized Config Import ---
from config.settings import settings

# --- New Pipeline Import ---
from pipeline import IndexingPipeline

# --- LlamaIndex v0.10+ Imports (kept for legacy methods) ---
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
    Settings as LlamaSettings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from indexing.splitters.regulation_node_splitter import RegulationNodeSplitter
from llama_index.embeddings.openai import OpenAIEmbedding


def normalize_vietnamese_text(text: str) -> str:
    """
    Normalize Vietnamese text to NFC form.

    Vietnamese diacritics can be represented in two Unicode forms:
    - NFC (composed): 'ó' = U+00F3 (single character)
    - NFD (decomposed): 'ó' = U+006F + U+0301 (base + combining mark)

    Example: 'Khóa' (NFC) vs 'Khoá' (NFD) - visually identical but different bytes.
    This causes vector search failures as embeddings differ.

    Normalization ensures consistent representation for both queries and documents.

    Args:
        text: Raw Vietnamese text

    Returns:
        NFC-normalized text
    """
    return unicodedata.normalize('NFC', text)


class DocumentIndexer:
    """
    Document Indexer - Category-based indexing for ChromaDB.

    Creates separate ChromaDB collections for each category:
    - regulation
    - curriculum
    - (future: announcement, other)

    Works with flat processed structure:
        processed/{category}/{document_id}.md
        processed/{category}/{document_id}.json
    """

    def __init__(self):
        """
        Initialize document indexer.
        """
        print(f"[INFO] Initializing DocumentIndexer")

        # Configure global LlamaIndex Settings
        if not settings.credentials.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please configure it in your .env file.")

        embed_model = OpenAIEmbedding(
            model=settings.indexing.EMBED_MODEL,
            api_key=settings.credentials.OPENAI_API_KEY
        )

        # Use RegulationNodeSplitter for intelligent chunking
        # 1. Pattern detection (Điều X, CHƯƠNG X) for Vietnamese regulation documents
        # 2. Title chunk merging for cleaner document structure
        # 3. Malformed markdown cleanup
        # 4. Token-aware sub-chunking with context preservation
        node_parser = RegulationNodeSplitter(
            max_tokens=settings.indexing.MAX_TOKENS,
            sub_chunk_size=settings.indexing.CHUNK_SIZE,
            sub_chunk_overlap=settings.indexing.CHUNK_OVERLAP
        )

        LlamaSettings.embed_model = embed_model
        LlamaSettings.node_parser = node_parser

        # Initialize ChromaDB client (collections created per-category)
        self.chroma_client = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))

        # Track stats
        self.stats = {
            "collections_built": 0,
            "documents_indexed": 0,
            "errors": []
        }

    def build_collection(self, category: str) -> bool:
        """
        Build a specific collection using IndexingPipeline.

        Iterates through all documents in stages/{category}/ and runs
        indexing pipeline (chunk -> embed-index) for each.

        Args:
            category: Category name (e.g., "regulation", "curriculum")

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"🔨 BUILDING COLLECTION: {category}")
        print(f"{'='*70}\n")

        # Get category directory from stages/
        category_dir = settings.paths.STAGES_DIR / category

        if not category_dir.exists():
            print(f"[WARNING] Category directory not found: {category_dir}")
            print(f"[INFO] Run processing pipeline first to create documents")
            return False

        # Get all document directories
        doc_dirs = [d for d in category_dir.iterdir() if d.is_dir()]

        if not doc_dirs:
            print(f"[INFO] No documents found in category: {category}")
            return False

        print(f"[INFO] Found {len(doc_dirs)} documents in {category}")

        # Index each document
        indexed_count = 0
        failed_count = 0

        for doc_dir in doc_dirs:
            document_id = doc_dir.name

            try:
                print(f"\n[INFO] Indexing {document_id}...")

                # Run indexing pipeline
                pipeline = IndexingPipeline(category, document_id)
                result = pipeline.run(force=False)

                if result['stages_run']:
                    print(f"[SUCCESS] Indexed {document_id}: {len(result['stages_run'])} stages run")
                    indexed_count += 1
                else:
                    print(f"[INFO] Skipped {document_id}: already indexed")
                    indexed_count += 1

            except Exception as e:
                print(f"[ERROR] Failed to index {document_id}: {e}")
                failed_count += 1
                self.stats["errors"].append({
                    "category": category,
                    "document_id": document_id,
                    "error": str(e)
                })

        # Update stats
        self.stats["collections_built"] += 1
        self.stats["documents_indexed"] += indexed_count

        print(f"\n[SUCCESS] Built collection '{category}': {indexed_count} indexed, {failed_count} failed")
        return failed_count == 0

    def build_all_collections(self, categories: Optional[List[str]] = None) -> Dict:
        """
        Build all collections for specified categories.

        Args:
            categories: List of categories to build (None = use settings)

        Returns:
            Statistics dict with build results
        """
        if categories is None:
            categories = settings.processing.PROCESS_CATEGORIES

        print("\n" + "="*70)
        print(f" DOCUMENT INDEXER - MULTI-COLLECTION BUILD")
        print(f"   Categories: {', '.join(categories)}")
        print("="*70 + "\n")

        # Build each collection
        for category in categories:
            self.build_collection(category)

        # Print final stats
        self._print_stats()

        return self.stats

    def index_single_file(self, file_path) -> bool:
        """
        Index a single document using IndexingPipeline.

        DEPRECATED: Use IndexingPipeline directly instead:
            >>> from src.pipeline import IndexingPipeline
            >>> pipeline = IndexingPipeline(category, document_id)
            >>> pipeline.run()

        Args:
            file_path: Path to document directory (e.g., data/stages/regulation/790-qd-dhcntt)

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)

        print(f"\n{'='*70}")
        print(f"🔨 INDEXING SINGLE DOCUMENT")
        print(f"   Path: {file_path}")
        print(f"{'='*70}\n")

        # Infer category and document_id from path
        # Expected: data/stages/{category}/{document_id}/
        try:
            if file_path.is_dir():
                # Already a document directory
                document_id = file_path.name
                category = file_path.parent.name
            else:
                # Legacy: data/processed/{category}/{file}.md
                print(f"[WARNING] Legacy file path detected. Please use stage-based structure.")
                print(f"[INFO] Use IndexingPipeline directly for stage-based indexing.")
                return False

            print(f"[INFO] Category: {category}, Document ID: {document_id}")

        except Exception as e:
            print(f"[ERROR] Could not infer category/document_id from path: {e}")
            return False

        # Run indexing pipeline
        try:
            pipeline = IndexingPipeline(category, document_id)
            result = pipeline.run(force=False)

            if result['stages_run']:
                print(f"[SUCCESS] Indexed {document_id}: {len(result['stages_run'])} stages run")
            else:
                print(f"[INFO] Skipped {document_id}: already indexed")

            return True

        except Exception as e:
            print(f"[ERROR] Failed to index document: {e}")
            return False

    def _load_documents_from_category(self, category: str) -> List[Document]:
        """
        Load all documents from a category directory.

        For each {document_id}.md file:
        - Read markdown content
        - Load metadata_generator from {document_id}.json
        - Create Document with metadata_generator

        Args:
            category: Category name

        Returns:
            List of Document objects
        """
        category_dir = settings.paths.PROCESSED_DATA_DIR / category

        if not category_dir.exists():
            return []

        documents = []
        md_files = list(category_dir.glob("*.md"))

        print(f"[INFO] Found {len(md_files)} markdown files in {category}")

        for md_file in md_files:
            try:
                # Read markdown content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Normalize Unicode (fix 'Khóa' NFC vs 'Khoá' NFD mismatch)
                content = normalize_vietnamese_text(content)

                if not content.strip():
                    print(f"[WARNING] Empty content in {md_file.name}, skipping")
                    continue

                # Load metadata_generator from corresponding JSON file
                json_file = md_file.with_suffix('.json')
                metadata = {}

                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        print(f"[WARNING] Failed to load metadata_generator for {md_file.name}: {e}")

                # Create Document
                doc = Document(
                    text=content,
                    metadata=metadata,
                    id_=metadata.get("document_id", md_file.stem)
                )
                documents.append(doc)

            except Exception as e:
                print(f"[ERROR] Failed to load {md_file.name}: {e}")
                continue

        return documents

    def _clean_metadata(self, metadata: Dict) -> Dict:
        """
        Clean metadata_generator to only include ChromaDB-compatible types.

        ChromaDB only accepts: str, int, float, None
        Removes: list, dict, tuple, etc.

        Args:
            metadata: Original metadata_generator dict

        Returns:
            Cleaned metadata_generator dict
        """
        cleaned = {}
        for key, value in metadata.items():
            # Keep only primitive types
            if isinstance(value, (str, int, float)) or value is None:
                cleaned[key] = value
            elif isinstance(value, list):
                # Convert list to comma-separated string
                if value and isinstance(value[0], str):
                    cleaned[key] = ", ".join(value)
                # Ignore non-string lists
            # Ignore dict, tuple, and other complex types

        return cleaned

    def _print_stats(self):
        """Print build statistics."""
        print("\n" + "="*70)
        print(" BUILD COMPLETE - STATISTICS")
        print("="*70)
        print(f"   Collections built:   {self.stats['collections_built']}")
        print(f"   Documents indexed:   {self.stats['documents_indexed']}")
        print(f"   Errors:              {len(self.stats['errors'])}")

        if self.stats["errors"]:
            print(f"\n     ERRORS:")
            for err in self.stats["errors"]:
                print(f"      • {err['category']}: {err['error']}")

        print(f"\n   Vector store location: {settings.paths.VECTOR_STORE_DIR}")
        print("="*70 + "\n")
