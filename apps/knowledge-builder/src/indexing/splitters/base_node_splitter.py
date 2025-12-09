"""
BaseNodeSplitter - Abstract base class for header-based node splitters.

Provides shared functionality:
- Token counting
- Context prepending (document metadata_generator + section info)
- Sub-chunking logic for large chunks
- Stats tracking

Subclasses must implement:
- _parse_by_headers(): Custom parsing logic to split markdown into chunks
"""
import tiktoken
from abc import ABC, abstractmethod
from typing import List, Dict, Sequence
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode
from ...config.settings import settings


class BaseNodeSplitter(ABC):
    """
    Abstract base class for header-based node splitters.

    Enforces interface and provides common functionality for all splitters.
    """

    def __init__(
        self,
        max_tokens: int = None,
        sub_chunk_size: int = None,
        sub_chunk_overlap: int = None,
        encoding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize splitter with configurable settings.

        Args:
            max_tokens: Maximum tokens per chunk before sub-chunking (default from settings)
            sub_chunk_size: Target size for sub-chunks (default from settings)
            sub_chunk_overlap: Overlap between sub-chunks (default from settings)
            encoding_model: Model name for tiktoken encoding
        """
        # Use settings or provided values
        self.max_tokens = max_tokens or settings.indexing.MAX_TOKENS
        self.sub_chunk_size = sub_chunk_size or settings.indexing.CHUNK_SIZE
        self.sub_chunk_overlap = sub_chunk_overlap or settings.indexing.CHUNK_OVERLAP

        # Initialize sentence splitter for sub-chunking
        self.sentence_splitter = SentenceSplitter(
            chunk_size=self.sub_chunk_size,
            chunk_overlap=self.sub_chunk_overlap,
            separator="\n\n"  # Respect paragraph boundaries
        )

        # Token counter
        try:
            self.encoding = tiktoken.encoding_for_model(encoding_model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

        # Stats tracking
        self.stats = {
            "total_chunks": 0,
            "large_chunks_split": 0,
            "final_nodes": 0
        }

        print(f"[INFO] {self.__class__.__name__} initialized:")
        print(f"  - max_tokens: {self.max_tokens}")
        print(f"  - sub_chunk_size: {self.sub_chunk_size}")
        print(f"  - sub_chunk_overlap: {self.sub_chunk_overlap}")

    # ========== ABSTRACT METHODS (must implement) ==========

    @abstractmethod
    def _parse_by_headers(self, text: str) -> List[Dict]:
        """
        Parse markdown text into chunks based on headers.

        Each subclass implements its own parsing logic.

        Args:
            text: Markdown text to parse

        Returns:
            List of dicts with:
            - text: chunk content (including header line)
            - current_header: this chunk's header text (without # symbols)
            - level: header level (1-6)
            - (optional) other metadata_generator specific to the splitter
        """
        pass

    # ========== CONCRETE METHODS (shared logic) ==========

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False
    ) -> List[BaseNode]:
        """
        Parse documents to nodes with header-based splitting.

        Args:
            documents: List of documents to parse
            show_progress: Whether to show progress (not implemented yet)

        Returns:
            List of TextNode objects with prepended context
        """
        all_nodes = []

        for doc in documents:
            # Stage 1: Parse by headers (polymorphic call to subclass)
            chunks_data = self._parse_by_headers(doc.text)
            self.stats["total_chunks"] += len(chunks_data)

            # Stage 2: Prepend context to each chunk
            chunks_with_context = [
                self._prepend_context(chunk_data, doc.metadata)
                for chunk_data in chunks_data
            ]

            # Stage 3: Token check and sub-chunk if needed
            nodes = self._process_chunks_with_token_check(
                chunks_with_context,
                chunks_data,  # Keep original data for metadata_generator
                doc.metadata
            )

            all_nodes.extend(nodes)

        self.stats["final_nodes"] = len(all_nodes)
        return all_nodes

    def _prepend_context(self, chunk_data: Dict, metadata: Dict) -> str:
        """
        Prepend document context to chunk text.

        Context includes:
        - Document info (title, effective_date, etc.)
        - Current section info

        Args:
            chunk_data: Dict with text, current_header
            metadata: Document metadata_generator

        Returns:
            Text with prepended context
        """
        context_parts = []

        # ========== DOCUMENT-LEVEL CONTEXT ==========

        if doc_id := metadata.get("document_id"):
            # Clean filename for display
            clean_id = doc_id.replace('.md', '').replace('-', ' ').title()
            context_parts.append(f"Tài liệu: {clean_id}")

        if title := metadata.get("title"):
            context_parts.append(f"Tiêu đề: {title}")

        # ========== CURRENT SECTION ==========

        current_header = chunk_data.get('current_header')
        if current_header and current_header != 'TITLE':
            context_parts.append(f"Phần: {current_header}")

        # ========== CATEGORY-SPECIFIC METADATA ==========

        category = metadata.get("category")

        if category == "regulation":
            if effective_date := metadata.get("effective_date"):
                context_parts.append(f"Ngày hiệu lực: {effective_date}")

            if doc_type := metadata.get("document_type"):
                type_map = {
                    "original": "Văn bản gốc",
                    "update": "Văn bản sửa đổi",
                    "supplement": "Văn bản bổ sung"
                }
                context_parts.append(f"Loại: {type_map.get(doc_type, doc_type)}")

        elif category == "curriculum":
            if major := metadata.get("major"):
                context_parts.append(f"Ngành: {major}")

            if year := metadata.get("year"):
                context_parts.append(f"Năm: {year}")

            if program_type := metadata.get("program_type"):
                context_parts.append(f"Hệ: {program_type}")

            if program_name := metadata.get("program_name"):
                context_parts.append(f"Chương trình: {program_name}")

        # ========== COMBINE CONTEXT + CONTENT ==========

        if context_parts:
            context_header = "\n".join(context_parts)
            separator = "\n---\n"
            return f"{context_header}{separator}{chunk_data['text']}"
        else:
            return chunk_data['text']

    def _process_chunks_with_token_check(
        self,
        chunks_with_context: List[str],
        chunks_data: List[Dict],
        metadata: Dict
    ) -> List[TextNode]:
        """
        Check token counts and sub-chunk if needed, preserving context.

        Args:
            chunks_with_context: List of chunks with prepended context
            chunks_data: Original chunk data for metadata_generator
            metadata: Document metadata_generator

        Returns:
            List of TextNode objects
        """
        final_nodes = []

        for idx, (chunk_text, chunk_data) in enumerate(zip(chunks_with_context, chunks_data)):
            token_count = self.count_tokens(chunk_text)

            # ========== CASE 1: Chunk is small enough ==========
            if token_count <= self.max_tokens:
                # Build hierarchy string from header_path + current_header
                header_path = chunk_data.get('header_path', [])
                current_header = chunk_data.get('current_header')
                full_hierarchy = header_path.copy()
                if current_header:
                    full_hierarchy.append(current_header)
                hierarchy_str = ' > '.join(full_hierarchy) if full_hierarchy else ''

                node = TextNode(
                    text=chunk_text,
                    metadata={
                        **metadata,
                        "chunk_index": idx,
                        "token_count": token_count,
                        "is_sub_chunked": False,
                        "current_header": chunk_data.get('current_header'),
                        "hierarchy": hierarchy_str,  # String for ChromaDB compatibility
                        "header_level": chunk_data.get('level', 0),
                        "splitter_type": self.__class__.__name__
                    }
                )
                final_nodes.append(node)

            # ========== CASE 2: Chunk is too large ==========
            else:
                print(f"  ⚠️  Chunk {idx}: {token_count} tokens > {self.max_tokens}, sub-chunking...")
                self.stats["large_chunks_split"] += 1

                # Extract context header (before separator)
                separator = "\n---\n"
                if separator in chunk_text:
                    context_header, actual_content = chunk_text.split(separator, 1)
                    context_header = context_header + separator
                else:
                    context_header = ""
                    actual_content = chunk_text

                # Sub-chunk the content only
                temp_doc = Document(text=actual_content.strip())
                sub_chunks = self.sentence_splitter.get_nodes_from_documents([temp_doc])

                print(f"     → Created {len(sub_chunks)} sub-chunks")

                # Build hierarchy string (same for all sub-chunks)
                header_path = chunk_data.get('header_path', [])
                current_header = chunk_data.get('current_header')
                full_hierarchy = header_path.copy()
                if current_header:
                    full_hierarchy.append(current_header)
                hierarchy_str = ' > '.join(full_hierarchy) if full_hierarchy else ''

                # Prepend context to EACH sub-chunk
                for sub_idx, sub_node in enumerate(sub_chunks):
                    full_text = context_header + "\n" + sub_node.text

                    node = TextNode(
                        text=full_text,
                        metadata={
                            **metadata,
                            "chunk_index": idx,
                            "sub_chunk_index": sub_idx,
                            "total_sub_chunks": len(sub_chunks),
                            "token_count": self.count_tokens(full_text),
                            "is_sub_chunked": True,
                            "parent_chunk_tokens": token_count,
                            "current_header": chunk_data.get('current_header'),
                            "hierarchy": hierarchy_str,  # String for ChromaDB compatibility
                            "header_level": chunk_data.get('level', 0),
                            "splitter_type": self.__class__.__name__
                        }
                    )
                    final_nodes.append(node)

        return final_nodes

    def get_stats(self) -> Dict:
        """Get parsing statistics."""
        return self.stats.copy()
