"""
Filtering and utility functions for retrieval pipeline.

Contains:
- Text normalization (Unicode NFC)
- Program context filtering (Chính quy vs Từ xa)
- Node deduplication
"""

import unicodedata
from typing import List

from llama_index.core.schema import NodeWithScore

from ..utils.logger import logger


def normalize_vietnamese_text(text: str) -> str:
    """
    Normalize Vietnamese text to NFC form.

    This fixes Unicode normalization issues where the same Vietnamese character
    can be represented in different ways:
    - NFC (composed): 'ó' as single character U+00F3
    - NFD (decomposed): 'ó' as 'o' U+006F + combining acute U+0301

    Example:
        'Khóa' (NFC) vs 'Khoá' (NFD) - same visual, different bytes

    Args:
        text: Input text (may be in NFC or NFD form)

    Returns:
        Normalized text in NFC form (composed)
    """
    return unicodedata.normalize('NFC', text)


def filter_by_program_context(query: str, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
    """
    Filter nodes based on program context (Chính quy vs Từ xa) derived from query.

    Args:
        query: User query
        nodes: List of candidate nodes

    Returns:
        Filtered list of nodes
    """
    query_lower = query.lower()

    # Case 1: User explicitly asks for "Từ xa"
    if "từ xa" in query_lower:
        filtered = []
        for node in nodes:
            title = node.node.metadata.get("title", "").lower()
            # Keep if title mentions "từ xa"
            if "từ xa" in title:
                filtered.append(node)

        if filtered:
            logger.info(f"[FILTER] Applied 'Từ xa' filter: {len(nodes)} -> {len(filtered)} nodes")
            return filtered

    # Case 2: User explicitly asks for "Chính quy"
    if "chính quy" in query_lower:
        filtered = []
        for node in nodes:
            title = node.node.metadata.get("title", "").lower()
            # Exclude if title mentions "từ xa" (Safety net)
            if "từ xa" not in title:
                filtered.append(node)

        if len(filtered) < len(nodes):
            logger.info(f"[FILTER] Applied 'Chính quy' filter (excluded 'Từ xa'): {len(nodes)} -> {len(filtered)} nodes")
            return filtered

    return nodes


def deduplicate_nodes(nodes: List[NodeWithScore]) -> List[NodeWithScore]:
    """
    Deduplicate nodes by node ID.

    When the same chunk is retrieved from multiple indexes (e.g., dense + BM25),
    keep only the node with the highest score.

    Args:
        nodes: List of retrieved nodes

    Returns:
        Deduplicated list of nodes
    """
    node_map = {}

    for node in nodes:
        node_id = node.node.node_id

        if node_id not in node_map:
            node_map[node_id] = node
        else:
            # Keep node with higher score
            if node.score > node_map[node_id].score:
                node_map[node_id] = node

    return list(node_map.values())
