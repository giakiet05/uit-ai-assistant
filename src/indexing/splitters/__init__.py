"""
Node splitters for document chunking.

Available splitters:
- BaseNodeSplitter: Abstract base class
- SimpleNodeSplitter: Basic header-based splitting, no hierarchy
- SmartNodeSplitter: Enhanced splitting with pattern detection (recommended for regulations)
- HierarchicalNodeSplitter: Legacy splitter with hierarchy tracking
- HierarchicalNodeSplitterV1: Deprecated (has duplicate header bug)
"""

from src.indexing.splitters.base_node_splitter import BaseNodeSplitter
from src.indexing.splitters.simple_node_splitter import SimpleNodeSplitter
from src.indexing.splitters.smart_node_splitter import SmartNodeSplitter

__all__ = [
    "BaseNodeSplitter",
    "SimpleNodeSplitter",
    "SmartNodeSplitter",
]
