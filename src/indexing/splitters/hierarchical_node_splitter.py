"""
HierarchicalNodeSplitter - Advanced splitter with hierarchy tracking.

Key improvements over V1:
1. Tracks header hierarchy (parent-child relationships)
2. Prepends document context to each chunk for better retrieval
3. Preserves header paths in both text and metadata
4. Smart sub-chunking that preserves context
"""
import re
import tiktoken
from typing import List, Dict, Sequence
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode
from src.config.settings import settings


class HierarchicalNodeSplitter:
    """
    Advanced parser that:
    1. Parses markdown by headers, tracking full hierarchy path
    2. Prepends document context + header path to each chunk
    3. Sub-chunks large nodes while preserving all context
    4. Works with both regulation and curriculum documents
    """

    def __init__(
        self,
        max_tokens: int = None,
        sub_chunk_size: int = None,
        sub_chunk_overlap: int = None,
        encoding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize parser with configurable settings.

        Args:
            max_tokens: Maximum tokens per chunk before sub-chunking (default from settings)
            sub_chunk_size: Target size for sub-chunks (default from settings)
            sub_chunk_overlap: Overlap between sub-chunks (default from settings)
            encoding_model: Model name for tiktoken encoding
        """
        # Use settings or provided values
        self.max_tokens = max_tokens or settings.retrieval.MAX_TOKENS
        self.sub_chunk_size = sub_chunk_size or settings.retrieval.CHUNK_SIZE
        self.sub_chunk_overlap = sub_chunk_overlap or settings.retrieval.CHUNK_OVERLAP

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

        print(f"[INFO] HierarchicalNodeSplitter initialized:")
        print(f"  - max_tokens: {self.max_tokens}")
        print(f"  - sub_chunk_size: {self.sub_chunk_size}")
        print(f"  - sub_chunk_overlap: {self.sub_chunk_overlap}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False
    ) -> List[BaseNode]:
        """
        Parse documents to nodes with hierarchical structure and context.

        Args:
            documents: List of documents to parse
            show_progress: Whether to show progress (not implemented yet)

        Returns:
            List of TextNode objects with prepended context
        """
        all_nodes = []

        for doc in documents:
            # Stage 1: Parse with hierarchy tracking
            chunks_data = self._parse_with_hierarchy(doc.text)
            self.stats["total_chunks"] += len(chunks_data)

            # Stage 2: Prepend context to each chunk
            chunks_with_context = [
                self._prepend_context(chunk_data, doc.metadata)
                for chunk_data in chunks_data
            ]

            # Stage 3: Token check and sub-chunk if needed
            nodes = self._process_chunks_with_token_check(
                chunks_with_context,
                chunks_data,  # Keep original data for metadata
                doc.metadata
            )

            all_nodes.extend(nodes)

        self.stats["final_nodes"] = len(all_nodes)
        return all_nodes

    def _parse_with_hierarchy(self, text: str) -> List[Dict]:
        """
        Parse markdown and track header hierarchy.

        Returns:
            List of dicts with:
            - text: chunk content
            - header_path: list of parent headers (NOT including current header)
            - current_header: this chunk's own header
            - level: header level (1-6)

        Example:
            For content "# A\n## B\n### C\ntext":
            - Chunk for "### C": header_path=["A", "B"], current_header="C"
        """
        chunks = []
        header_stack = []  # Stack tracking current hierarchy
        current_chunk_lines = []

        lines = text.split('\n')

        for line in lines:
            # Detect markdown headers: # Header, ## Header, etc.
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)

            if header_match:
                # ========== HEADER DETECTED ==========
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()

                # Save previous chunk if exists
                if current_chunk_lines:
                    chunk_data = {
                        'text': '\n'.join(current_chunk_lines),
                        'header_path': [h['text'] for h in header_stack[:-1]],  # Parents only (exclude current)
                        'current_header': header_stack[-1]['text'] if header_stack else None,
                        'level': header_stack[-1]['level'] if header_stack else 0
                    }
                    chunks.append(chunk_data)
                    current_chunk_lines = []

                # Update header stack: remove headers at same or deeper level
                header_stack = [h for h in header_stack if h['level'] < level]

                # Add current header
                header_stack.append({'level': level, 'text': header_text})

                # Start new chunk
                current_chunk_lines = [line]

            else:
                # Regular line
                current_chunk_lines.append(line)

        # Save last chunk
        if current_chunk_lines:
            chunk_data = {
                'text': '\n'.join(current_chunk_lines),
                'header_path': [h['text'] for h in header_stack[:-1]],  # Parents only (exclude current)
                'current_header': header_stack[-1]['text'] if header_stack else None,
                'level': header_stack[-1]['level'] if header_stack else 0
            }
            chunks.append(chunk_data)

        return chunks

    def _prepend_context(self, chunk_data: Dict, metadata: Dict) -> str:
        """
        Prepend document context and header hierarchy to chunk text.

        Args:
            chunk_data: Dict with text, header_path, current_header
            metadata: Document metadata

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

        # ========== HEADER HIERARCHY ==========
        # header_path: Parent headers only (e.g., ["QUYẾT ĐỊNH", "HIỆU TRƯỞNG"])
        # current_header: This chunk's header (e.g., "Điều 1")
        # full_path: Parents + current (e.g., ["QUYẾT ĐỊNH", "HIỆU TRƯỞNG", "Điều 1"])

        header_path = chunk_data.get('header_path', [])
        current_header = chunk_data.get('current_header')

        if header_path or current_header:
            full_path = header_path.copy()
            if current_header:
                full_path.append(current_header)

            if full_path:
                path_str = " > ".join(full_path)
                context_parts.append(f"Cấu trúc: {path_str}")

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
            separator = "\n" + "─" * 60 + "\n"
            return f"{context_header}{separator}\n{chunk_data['text']}"
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
            chunks_data: Original chunk data for metadata
            metadata: Document metadata

        Returns:
            List of TextNode objects
        """
        final_nodes = []

        for idx, (chunk_text, chunk_data) in enumerate(zip(chunks_with_context, chunks_data)):
            token_count = self.count_tokens(chunk_text)

            # ========== CASE 1: Chunk is small enough ==========
            if token_count <= self.max_tokens:
                node = TextNode(
                    text=chunk_text,
                    metadata={
                        **metadata,
                        "chunk_index": idx,
                        "token_count": token_count,
                        "is_sub_chunked": False,
                        "header_path": chunk_data.get('header_path', []),
                        "current_header": chunk_data.get('current_header'),
                        "header_level": chunk_data.get('level', 0)
                    }
                )
                final_nodes.append(node)

            # ========== CASE 2: Chunk is too large ==========
            else:
                print(f"  ⚠️  Chunk {idx}: {token_count} tokens > {self.max_tokens}, sub-chunking...")
                self.stats["large_chunks_split"] += 1

                # Extract context header (before separator)
                separator = "\n" + "─" * 60 + "\n"
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
                            "header_path": chunk_data.get('header_path', []),
                            "current_header": chunk_data.get('current_header'),
                            "header_level": chunk_data.get('level', 0)
                        }
                    )
                    final_nodes.append(node)

        return final_nodes

    def get_stats(self) -> Dict:
        """Get parsing statistics."""
        return self.stats.copy()
