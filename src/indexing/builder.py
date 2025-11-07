"""
RAG Vector Store Builder - Multi-collection, category-based indexing.

This module provides tools for building ChromaDB vector stores from processed documents,
with separate collections per category (regulations, curriculum, etc.).
"""

import chromadb
import os
import json
import argparse
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
from src.indexing.hierarchical_markdown_parser import HierarchicalMarkdownParser
from llama_index.embeddings.openai import OpenAIEmbedding


class RagBuilder:
    """
    RAG Builder - Multi-collection support for category-based indexing.

    Creates separate ChromaDB collections for each category:
    - regulations
    - curriculum
    - (future: announcements, other)

    Works with the new flat processed structure:
        processed/{domain}/{category}/{document_id}.md
        processed/{domain}/{category}/{document_id}.json
    """

    def __init__(self, domain: str = "daa.uit.edu.vn"):
        """
        Initialize builder for a specific domain.

        Args:
            domain: Domain name (e.g., "daa.uit.edu.vn")
        """
        print(f"[INFO] Initializing RagBuilderV2 for domain: {domain}")
        self.domain = domain

        # Configure global LlamaIndex Settings
        if not settings.credentials.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please configure it in your .env file.")

        embed_model = OpenAIEmbedding(
            model=settings.retrieval.EMBED_MODEL,
            api_key=settings.credentials.OPENAI_API_KEY
        )

        # Use custom HierarchicalMarkdownParser
        # 1. Parses markdown by structure (headers, tables)
        # 2. Token-aware: sub-chunks large nodes with parent-child relationships
        # 3. Avoids OpenAI's 8192 token limit
        node_parser = HierarchicalMarkdownParser(
            max_tokens=7000,  # Conservative limit
            sub_chunk_size=1024,  # Sub-chunk size for large nodes
            sub_chunk_overlap=128  # Preserve context
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
        Build a specific collection from processed/{domain}/{category}/ files.

        Args:
            category: Category name (e.g., "regulation", "curriculum")

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"🔨 BUILDING COLLECTION: {category}")
        print(f"{'='*70}\n")

        # Get category directory
        category_dir = settings.paths.PROCESSED_DATA_DIR / self.domain / category

        if not category_dir.exists():
            print(f"[WARNING] Category directory not found: {category_dir}")
            return False

        # Load documents
        documents = self._load_documents_from_category(category)

        if not documents:
            print(f"[INFO] No documents found in category: {category}")
            return False

        try:
            # Create/get collection (domain in metadata, no prefix needed)
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
                print(f"[INFO] Parsing stats: {stats['total_nodes']} initial nodes, {stats['large_nodes_split']} split, {stats['final_nodes']} final nodes")

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
        print(f"🚀 RAG BUILDER V2 - MULTI-COLLECTION BUILD")
        print(f"   Domain: {self.domain}")
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
        - Load metadata from {document_id}.json
        - Create Document with metadata

        Args:
            category: Category name

        Returns:
            List of Document objects
        """
        category_dir = settings.paths.PROCESSED_DATA_DIR / self.domain / category

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

                # Load metadata from corresponding JSON file
                json_file = md_file.with_suffix('.json')
                metadata = {}

                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        print(f"[WARNING] Failed to load metadata for {md_file.name}: {e}")

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


# Convenience functions for V2
def build_domain(domain: str, categories: Optional[List[str]] = None) -> Dict:
    """
    Build collections for a specific domain using V2 pipeline.

    Args:
        domain: Domain name (e.g., "daa.uit.edu.vn")
        categories: List of categories to build (None = use settings)

    Returns:
        Build statistics dict

    Example:
        >>> from src.indexing.builder import build_domain
        >>> stats = build_domain("daa.uit.edu.vn", categories=["regulation", "curriculum"])
    """
    builder = RagBuilder(domain=domain)
    return builder.build_all_collections(categories=categories)


def build_all_domains(categories: Optional[List[str]] = None) -> Dict:
    """
    Build collections for all configured domains using V2 pipeline.

    Args:
        categories: List of categories to build (None = use settings)

    Returns:
        Combined build statistics dict

    Example:
        >>> from src.indexing.builder import build_all_domains
        >>> stats = build_all_domains(categories=["regulation"])
    """
    all_stats = {
        "collections_built": 0,
        "documents_indexed": 0,
        "errors": []
    }

    for domain in settings.domains.START_URLS.keys():
        print(f"\n{'='*70}")
        print(f"Processing domain: {domain}")
        print(f"{'='*70}")

        builder = RagBuilder(domain=domain)
        stats = builder.build_all_collections(categories=categories)

        all_stats["collections_built"] += stats["collections_built"]
        all_stats["documents_indexed"] += stats["documents_indexed"]
        all_stats["errors"].extend(stats["errors"])

    return all_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Build RAG vector store with multi-collection support.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build all collections for all domains
  python -m src.indexing.builder

  # Build specific domain
  python -m src.indexing.builder --domain daa.uit.edu.vn

  # Build specific categories only
  python -m src.indexing.builder --domain daa.uit.edu.vn --categories regulation,curriculum
        """
    )
    parser.add_argument(
        '--domain', '-d',
        type=str,
        help='Build for a specific domain (e.g., daa.uit.edu.vn)'
    )
    parser.add_argument(
        '--categories', '-c',
        type=str,
        help='Comma-separated categories to build (e.g., regulation,curriculum)'
    )

    args = parser.parse_args()

    # Parse categories
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(',')]

    # Build
    if args.domain:
        if args.domain not in settings.domains.START_URLS:
            print(f"[ERROR] Domain '{args.domain}' not configured")
        else:
            build_domain(args.domain, categories)
    else:
        build_all_domains(categories)
