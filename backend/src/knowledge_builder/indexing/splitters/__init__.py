"""
Node splitters for document chunking.

Available splitters:
- BaseNodeSplitter: Abstract base class
- SimpleNodeSplitter: Basic header-based splitting, no hierarchy
- SmartNodeSplitter: Enhanced splitting with pattern detection (recommended for regulation)
- HierarchicalNodeSplitter: Legacy splitter with hierarchy tracking
- HierarchicalNodeSplitterV1: Deprecated (has duplicate header bug)
"""

from .base_node_splitter import BaseNodeSplitter
from .simple_node_splitter import SimpleNodeSplitter
from .smart_node_splitter import SmartNodeSplitter

__all__ = [
    "BaseNodeSplitter",
    "SimpleNodeSplitter",
    "SmartNodeSplitter",
]
