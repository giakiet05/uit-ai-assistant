"""
Document Indexer - Category-based indexing for ChromaDB.

This module provides tools for building ChromaDB vector stores from processed documents,
with separate collections per category (regulations, curriculum, etc.).
"""

import chromadb
import os
import json
from pathlib import Path
from typing import List, Optional, Dict

# --- Centralized Config Import ---
from src.config import settings

# --- LlamaIndex v0.10+ Imports ---
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
    Settings as LlamaSettings, # Use alias to avoid confusion with our own Settings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from src.indexing.splitters import SmartNodeSplitter
from llama_index.embeddings.openai import OpenAIEmbedding


class DocumentIndexer:
    """
    Document Indexer - Category-based indexing for ChromaDB.

    Creates separate ChromaDB collections for each category:
    - regulations
    - curriculum
    - (future: announcements, other)

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
            model=settings.retrieval.EMBED_MODEL,
            api_key=settings.credentials.OPENAI_API_KEY
        )

        # Use SmartNodeSplitter for intelligent chunking
        # 1. Pattern detection (Điều X, CHƯƠNG X) for Vietnamese regulations
        # 2. Title chunk merging for cleaner document structure
        # 3. Malformed markdown cleanup
        # 4. Token-aware sub-chunking with context preservation
        node_parser = SmartNodeSplitter(
            max_tokens=settings.retrieval.MAX_TOKENS,
            sub_chunk_size=settings.retrieval.CHUNK_SIZE,
            sub_chunk_overlap=settings.retrieval.CHUNK_OVERLAP
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
        Build a specific collection from processed/{category}/ files.

        Args:
            category: Category name (e.g., "regulation", "curriculum")

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"🔨 BUILDING COLLECTION: {category}")
        print(f"{'='*70}\n")

        # Get category directory
        category_dir = settings.paths.PROCESSED_DATA_DIR / category

        if not category_dir.exists():
            print(f"[WARNING] Category directory not found: {category_dir}")
            return False

        # Load documents
        documents = self._load_documents_from_category(category)

        if not documents:
            print(f"[INFO] No documents found in category: {category}")
            return False

        # Clean metadata_generator (remove non-primitive types for ChromaDB)
        for doc in documents:
            doc.metadata = self._clean_metadata(doc.metadata)

        try:
            # Create/get collection (domain in metadata_generator, no prefix needed)
            collection_name = category
            print(f"[INFO] Creating ChromaDB collection: {collection_name}")
            chroma_collection = self.chroma_client.get_or_create_collection(collection_name)

            # Create vector store and storage context
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # Parse documents to nodes manually (HierarchicalMarkdownParser not callable by LlamaIndex)
            print(f"[INFO] Parsing {len(documents)} documents to nodes...")
            node_parser = LlamaSettings.node_parser
            nodes = node_parser.get_nodes_from_documents(documents)

            # Print parsing stats
            if hasattr(node_parser, 'get_stats'):
                stats = node_parser.get_stats()
                print(f"[INFO] Parsing stats: {stats['total_chunks']} initial chunks, {stats['large_chunks_split']} split, {stats['final_nodes']} final nodes")

            # Build index from parsed nodes
            print(f"[INFO] Embedding & indexing {len(nodes)} nodes...")
            index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
            )

            self.stats["collections_built"] += 1
            self.stats["documents_indexed"] += len(documents)

            print(f"[SUCCESS] Built collection '{collection_name}' with {len(documents)} documents ({len(nodes)} nodes)")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to build collection '{category}': {e}")
            self.stats["errors"].append({
                "category": category,
                "error": str(e)
            })
            return False

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
        print(f"🚀 DOCUMENT INDEXER - MULTI-COLLECTION BUILD")
        print(f"   Categories: {', '.join(categories)}")
        print("="*70 + "\n")

        # Build each collection
        for category in categories:
            self.build_collection(category)

        # Print final stats
        self._print_stats()

        return self.stats

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
        print("📊 BUILD COMPLETE - STATISTICS")
        print("="*70)
        print(f"   Collections built:   {self.stats['collections_built']}")
        print(f"   Documents indexed:   {self.stats['documents_indexed']}")
        print(f"   Errors:              {len(self.stats['errors'])}")

        if self.stats["errors"]:
            print(f"\n   ⚠️  ERRORS:")
            for err in self.stats["errors"]:
                print(f"      • {err['category']}: {err['error']}")

        print(f"\n   Vector store location: {settings.paths.VECTOR_STORE_DIR}")
        print("="*70 + "\n")
