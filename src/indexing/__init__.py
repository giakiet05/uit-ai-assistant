"""
Indexing module for building and managing vector stores.

Multi-collection, category-based indexing for RAG system.
"""
from .builder import RagBuilder, build_domain, build_all_domains

__all__ = ["RagBuilder", "build_domain", "build_all_domains"]
