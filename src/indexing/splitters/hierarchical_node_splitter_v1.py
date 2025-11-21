"""
HierarchicalNodeSplitterV1 (deprecated) - Legacy splitter with hierarchy tracking.

DEPRECATED: Use HierarchicalNodeSplitter or SmartNodeSplitter instead.

Known issues:
- Duplicate header bug (fixed in V2/SmartNodeSplitter)

Combines MarkdownNodeParser (structure preservation) with token-aware sub-chunking.
Creates parent-child relationships for large nodes.
"""
import tiktoken
from typing import List, Sequence
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import BaseNode, NodeRelationship


class HierarchicalNodeSplitterV1:
    """
    Hybrid parser that:
    1. Parses markdown by structure (headers, tables) using MarkdownNodeParser
    2. Checks token counts
    3. Sub-chunks large nodes using SentenceSplitter with parent-child refs
    """

    def __init__(
        self,
        max_tokens: int = 7000,  # Conservative limit (< 8192)
        sub_chunk_size: int = 1024,
        sub_chunk_overlap: int = 128,
        encoding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize parser.

        Args:
            max_tokens: Maximum tokens per chunk (default 7000, safe for 8192 limit)
            sub_chunk_size: Chunk size for sub-chunking large nodes
            sub_chunk_overlap: Overlap for sub-chunks to preserve context
            encoding_model: Model name for tiktoken encoding
        """
        self.max_tokens = max_tokens
        self.sub_chunk_size = sub_chunk_size
        self.sub_chunk_overlap = sub_chunk_overlap

        # Initialize parsers
        self.md_parser = MarkdownNodeParser()
        self.sentence_splitter = SentenceSplitter(
            chunk_size=sub_chunk_size,
            chunk_overlap=sub_chunk_overlap,
            separator="\n\n"  # Respect paragraph boundaries
        )

        # Token counter
        try:
            self.encoding = tiktoken.encoding_for_model(encoding_model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

        # Stats
        self.stats = {
            "total_nodes": 0,
            "large_nodes_split": 0,
            "final_nodes": 0
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def get_nodes_from_documents(
        self, documents: Sequence[Document], show_progress: bool = False
    ) -> List[BaseNode]:
        """
        Parse documents to nodes with hierarchical structure.

        Args:
            documents: List of documents to parse
            show_progress: Whether to show progress

        Returns:
            List of nodes with parent-child relationships
        """
        # Step 1: Parse with MarkdownNodeParser
        md_nodes = self.md_parser.get_nodes_from_documents(documents, show_progress=show_progress)
        self.stats["total_nodes"] = len(md_nodes)

        # Step 2: Check tokens and conditionally sub-chunk
        final_nodes = []

        for node in md_nodes:
            token_count = self.count_tokens(node.text)

            if token_count <= self.max_tokens:
                # Small enough, keep as-is
                final_nodes.append(node)
            else:
                # Too large, sub-chunk it
                print(f"[INFO] Node has {token_count} tokens (> {self.max_tokens}), sub-chunking...")
                self.stats["large_nodes_split"] += 1

                # Convert node to document for sub-chunking
                temp_doc = Document(
                    text=node.text,
                    metadata=node.metadata
                )

                # Sub-chunk with SentenceSplitter
                sub_nodes = self.sentence_splitter.get_nodes_from_documents([temp_doc])

                # Set parent-child relationships
                for sub_node in sub_nodes:
                    # Merge metadata from parent
                    sub_node.metadata.update(node.metadata)

                    # Set parent relationship
                    sub_node.relationships[NodeRelationship.PARENT] = node.as_related_node_info()

                    final_nodes.append(sub_node)

                # Keep parent node with child references (optional, for AutoMergingRetriever)
                node.relationships[NodeRelationship.CHILD] = [
                    sub.as_related_node_info() for sub in sub_nodes
                ]
                # Don't add parent to final_nodes to avoid duplicate embeddings
                # final_nodes.append(node)

        self.stats["final_nodes"] = len(final_nodes)
        return final_nodes

    def get_stats(self) -> dict:
        """Get parsing statistics."""
        return self.stats.copy()
