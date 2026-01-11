"""
CurriculumNodeSplitter - Splitter optimized for Vietnamese curriculum documents.

Features:
1. Table-aware splitting (PLO tables, study plan tables, course tables)
2. Smart table row grouping by semantic units
3. Markdown table format resilience
4. Prepend only title (not full metadata)

Designed specifically for curriculum documents.
For regulation documents, use RegulationNodeSplitter.
"""
import re
from typing import List, Dict, Sequence, Optional, Tuple
from llama_index.core import Document
from llama_index.core.schema import BaseNode
from indexing.splitters.base_node_splitter import BaseNodeSplitter


class CurriculumNodeSplitter(BaseNodeSplitter):
    """
    Splitter optimized for Vietnamese curriculum documents.

    Features:
    1. Table-aware splitting (detect and split markdown tables)
    2. Semantic grouping (PLO groups, semesters, course groups)
    3. Hierarchy preservation
    4. Clean text (only prepend title)

    Table splitting strategies:
    - "CHUẨN ĐẦU RA" tables: split by PLO/LO/CĐR numbers
    - "KẾ HOẠCH GIẢNG DẠY" tables: split by semester
    - Course list tables: split by course group headers
    """

    # Table section markers
    TABLE_SECTIONS = {
        'CHUẨN ĐẦU RA': 'plo_table',
        'KẾ HOẠCH GIẢNG DẠY': 'study_plan_table',
        'KẾ HOẠCH HỌC TẬP': 'study_plan_table',
    }

    # Patterns for splitting tables
    PLO_PATTERN = re.compile(r'^\*\*(?:PLO|LO|CĐR)\s*\d+', re.IGNORECASE)
    SEMESTER_PATTERN = re.compile(r'^\*\*Học kỳ\s+\d+\*\*', re.IGNORECASE)
    COURSE_GROUP_PATTERN = re.compile(r'^\|?\s*\*\*[A-Z\u00C0-\u1EF9][^|]*\*\*', re.IGNORECASE)

    def __init__(
        self,
        max_tokens: int = None,
        sub_chunk_size: int = None,
        sub_chunk_overlap: int = None,
        encoding_model: str = "text-embedding-3-large",
        enable_table_splitting: bool = True,
        max_table_rows_per_chunk: int = 15
    ):
        """
        Initialize curriculum splitter.

        Args:
            max_tokens: Maximum tokens per chunk before sub-chunking
            sub_chunk_size: Target size for sub-chunks
            sub_chunk_overlap: Overlap between sub-chunks
            encoding_model: Model for token counting
            enable_table_splitting: Enable table-aware splitting
            max_table_rows_per_chunk: Max rows per table chunk (fallback)
        """
        super().__init__(max_tokens, sub_chunk_size, sub_chunk_overlap, encoding_model)

        self.enable_table_splitting = enable_table_splitting
        self.max_table_rows_per_chunk = max_table_rows_per_chunk

        # Add extra stats
        self.stats["tables_detected"] = 0
        self.stats["table_chunks_created"] = 0

        print(f"  - table_splitting: {self.enable_table_splitting}")
        print(f"  - max_table_rows_per_chunk: {self.max_table_rows_per_chunk}")

    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False
    ) -> List[BaseNode]:
        """
        Parse documents to nodes with table-aware splitting.

        Overrides base implementation to add table processing.

        Args:
            documents: List of documents to parse
            show_progress: Whether to show progress

        Returns:
            List of TextNode objects
        """
        all_nodes = []

        for doc in documents:
            # Step 1: Parse by headers AND tables
            chunks_data = self._parse_by_headers(doc.text, doc.metadata)
            self.stats["total_chunks"] += len(chunks_data)

            # Step 2: Prepend context (only title)
            chunks_with_context = [
                self._prepend_context(chunk_data, doc.metadata)
                for chunk_data in chunks_data
            ]

            # Step 3: Token check and sub-chunk if needed
            nodes = self._process_chunks_with_token_check(
                chunks_with_context,
                chunks_data,
                doc.metadata
            )

            all_nodes.extend(nodes)

        self.stats["final_nodes"] = len(all_nodes)
        return all_nodes

    def _prepend_context(self, chunk_data: Dict, metadata: Dict) -> str:
        """
        Prepend document title to chunk text.

        For curriculum documents, we want title context for better search/retrieval.
        Other metadata (major, year, etc.) are in node.metadata.

        Args:
            chunk_data: Dict with text, header_path, current_header
            metadata: Document metadata

        Returns:
            Chunk text with prepended title
        """
        # Get title from metadata
        title = metadata.get('title', '').strip()
        
        if title:
            # Prepend title as context
            return f"# {title}\n\n{chunk_data['text']}"
        else:
            # No title, return original
            return chunk_data['text']

    def _parse_by_headers(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Parse markdown by headers AND tables.

        Strategy:
        1. Parse by markdown headers (# ## ###)
        2. Detect tables within chunks
        3. If table detected → split table by semantic units
        4. Otherwise → keep chunk as-is

        Args:
            text: Markdown text to parse
            metadata: Document metadata

        Returns:
            List of dicts with:
            - text: chunk content
            - header_path: list of parent headers
            - current_header: this chunk's header
            - level: header level
        """
        chunks = []
        header_stack = []
        current_chunk_lines = []

        lines = text.split('\n')

        for line in lines:
            # Detect markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)

            if header_match:
                # ========== HEADER DETECTED ==========
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()

                # Save previous chunk if exists
                if current_chunk_lines:
                    # Check if chunk contains table
                    chunk_text = '\n'.join(current_chunk_lines)
                    parent_header = header_stack[-1]['text'] if header_stack else None

                    if self.enable_table_splitting and self._contains_table(chunk_text):
                        # Split table into multiple chunks
                        table_chunks = self._split_table_chunk(
                            chunk_text,
                            parent_header,
                            header_stack
                        )
                        chunks.extend(table_chunks)
                    else:
                        # Regular chunk
                        chunk_data = {
                            'text': chunk_text,
                            'header_path': [h['text'] for h in header_stack[:-1]],
                            'current_header': header_stack[-1]['text'] if header_stack else None,
                            'level': header_stack[-1]['level'] if header_stack else 0
                        }
                        chunks.append(chunk_data)

                    current_chunk_lines = []

                # Update header stack
                header_stack = [h for h in header_stack if h['level'] < level]
                header_stack.append({'level': level, 'text': header_text})

                # Start new chunk
                current_chunk_lines = [line]

            else:
                current_chunk_lines.append(line)

        # Save last chunk
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            parent_header = header_stack[-1]['text'] if header_stack else None

            if self.enable_table_splitting and self._contains_table(chunk_text):
                table_chunks = self._split_table_chunk(
                    chunk_text,
                    parent_header,
                    header_stack
                )
                chunks.extend(table_chunks)
            else:
                chunk_data = {
                    'text': chunk_text,
                    'header_path': [h['text'] for h in header_stack[:-1]],
                    'current_header': header_stack[-1]['text'] if header_stack else None,
                    'level': header_stack[-1]['level'] if header_stack else 0
                }
                chunks.append(chunk_data)

        return chunks

    def _contains_table(self, text: str) -> bool:
        """
        Check if text contains a markdown table.

        Args:
            text: Text to check

        Returns:
            True if contains table separator (---|---|---)
        """
        return bool(re.search(r'\|?\s*---+\s*\|', text))

    def _split_table_chunk(
        self,
        chunk_text: str,
        parent_header: Optional[str],
        header_stack: List[Dict]
    ) -> List[Dict]:
        """
        Split chunk containing table into multiple semantic chunks.

        Strategy depends on table type:
        - PLO table → split by PLO/LO/CĐR numbers
        - Study plan → split by semester
        - Course list → split by course group headers
        - Unknown → split by max rows

        Args:
            chunk_text: Chunk text containing table
            parent_header: Parent section header
            header_stack: Current header hierarchy

        Returns:
            List of chunk dicts
        """
        self.stats["tables_detected"] += 1

        # Detect table type from parent header
        table_type = self._detect_table_type(parent_header)

        # Split based on type
        if table_type == 'plo_table':
            table_chunks = self._split_plo_table(chunk_text, header_stack)
        elif table_type == 'study_plan_table':
            table_chunks = self._split_study_plan_table(chunk_text, header_stack)
        else:
            # Fallback: split by row count
            table_chunks = self._split_table_by_rows(chunk_text, header_stack)

        self.stats["table_chunks_created"] += len(table_chunks)
        print(f"  [TABLE] Split {table_type} into {len(table_chunks)} chunks")

        return table_chunks

    def _detect_table_type(self, parent_header: Optional[str]) -> str:
        """
        Detect table type from parent header.

        Args:
            parent_header: Parent section header

        Returns:
            Table type identifier
        """
        if not parent_header:
            return 'unknown'

        parent_upper = parent_header.upper()

        # Normalize Unicode to ensure consistent matching
        import unicodedata
        parent_upper_normalized = unicodedata.normalize('NFC', parent_upper)

        for keyword, table_type in self.TABLE_SECTIONS.items():
            keyword_normalized = unicodedata.normalize('NFC', keyword)
            if keyword_normalized in parent_upper_normalized:
                return table_type

        return 'unknown'

    def _split_plo_table(self, chunk_text: str, header_stack: List[Dict]) -> List[Dict]:
        """
        Split PLO/LO/CĐR table by main PLO numbers.

        Example:
        **PLO1. ...** | | ...
        1 | 1 | ...
        1 | 2 | ...
        **PLO2. ...** | | ...
        2 | 1 | ...

        → Split into 2 chunks (PLO1, PLO2)

        Args:
            chunk_text: Table text
            header_stack: Header hierarchy

        Returns:
            List of chunk dicts
        """
        lines = chunk_text.split('\n')
        chunks = []
        current_group_lines = []
        current_plo_header = None

        header_line = None
        separator_line = None

        for line in lines:
            # Detect table header and separator
            if '---|' in line or '|---' in line:
                if not separator_line:
                    separator_line = line
                    continue
            elif not separator_line and '|' in line:
                header_line = line
                continue

            # Detect PLO group header (boldtext row)
            plo_match = self.PLO_PATTERN.search(line)
            if plo_match:
                # Save previous group
                if current_group_lines and current_plo_header:
                    chunk_data = self._create_table_chunk(
                        header_line,
                        separator_line,
                        current_group_lines,
                        current_plo_header,
                        header_stack
                    )
                    chunks.append(chunk_data)

                # Start new group
                current_plo_header = line.strip()
                current_group_lines = [line]
            else:
                current_group_lines.append(line)

        # Save last group
        if current_group_lines and current_plo_header:
            chunk_data = self._create_table_chunk(
                header_line,
                separator_line,
                current_group_lines,
                current_plo_header,
                header_stack
            )
            chunks.append(chunk_data)

        return chunks if chunks else [self._create_fallback_chunk(chunk_text, header_stack)]

    def _split_study_plan_table(self, chunk_text: str, header_stack: List[Dict]) -> List[Dict]:
        """
        Split study plan table by semester.

        Example:
        **Học kỳ 1** | | | |
        IT001 | ... | 4 | 3 | 1
        MA006 | ... | 4 | 4 | 0
        **Học kỳ 2** | | | |
        IT002 | ... | 4 | 3 | 1

        → Split into 2 chunks (Học kỳ 1, Học kỳ 2)

        Args:
            chunk_text: Table text
            header_stack: Header hierarchy

        Returns:
            List of chunk dicts
        """
        lines = chunk_text.split('\n')
        chunks = []
        current_semester_lines = []
        current_semester_header = None

        header_line = None
        separator_line = None

        for line in lines:
            # Detect table header and separator
            if '---|' in line or '|---' in line:
                if not separator_line:
                    separator_line = line
                    continue
            elif not separator_line and '|' in line and 'Mã' in line:
                header_line = line
                continue

            # Detect semester header
            semester_match = self.SEMESTER_PATTERN.search(line)
            if semester_match:
                # Save previous semester
                if current_semester_lines and current_semester_header:
                    chunk_data = self._create_table_chunk(
                        header_line,
                        separator_line,
                        current_semester_lines,
                        current_semester_header,
                        header_stack
                    )
                    chunks.append(chunk_data)

                # Start new semester
                current_semester_header = line.strip()
                current_semester_lines = [line]
            else:
                current_semester_lines.append(line)

        # Save last semester
        if current_semester_lines and current_semester_header:
            chunk_data = self._create_table_chunk(
                header_line,
                separator_line,
                current_semester_lines,
                current_semester_header,
                header_stack
            )
            chunks.append(chunk_data)

        return chunks if chunks else [self._create_fallback_chunk(chunk_text, header_stack)]

    def _split_table_by_rows(self, chunk_text: str, header_stack: List[Dict]) -> List[Dict]:
        """
        Fallback: split table by max row count.

        Args:
            chunk_text: Table text
            header_stack: Header hierarchy

        Returns:
            List of chunk dicts
        """
        lines = chunk_text.split('\n')
        table_rows = [l for l in lines if '|' in l]

        if len(table_rows) <= self.max_table_rows_per_chunk:
            # Small table, keep as one chunk
            return [self._create_fallback_chunk(chunk_text, header_stack)]

        # Split into multiple chunks
        chunks = []
        header_line = table_rows[0] if table_rows else None
        separator_line = table_rows[1] if len(table_rows) > 1 else None

        data_rows = table_rows[2:] if len(table_rows) > 2 else []

        for i in range(0, len(data_rows), self.max_table_rows_per_chunk):
            chunk_rows = data_rows[i:i + self.max_table_rows_per_chunk]
            chunk_header = f"Rows {i+1}-{i+len(chunk_rows)}"

            chunk_data = self._create_table_chunk(
                header_line,
                separator_line,
                chunk_rows,
                chunk_header,
                header_stack
            )
            chunks.append(chunk_data)

        return chunks

    def _create_table_chunk(
        self,
        header_line: Optional[str],
        separator_line: Optional[str],
        data_lines: List[str],
        chunk_header: str,
        header_stack: List[Dict]
    ) -> Dict:
        """
        Create chunk dict from table parts.

        Args:
            header_line: Table column headers
            separator_line: Table separator (---|---|---)
            data_lines: Table data rows
            chunk_header: Header for this chunk (e.g., "Học kỳ 1", "PLO1")
            header_stack: Current header hierarchy

        Returns:
            Chunk dict
        """
        # Build chunk text
        chunk_lines = []

        # Add table header and separator if available
        if header_line:
            chunk_lines.append(header_line)
        if separator_line:
            chunk_lines.append(separator_line)

        # Add data rows
        chunk_lines.extend(data_lines)

        chunk_text = '\n'.join(chunk_lines)

        # Build hierarchy
        header_path = [h['text'] for h in header_stack]

        return {
            'text': chunk_text,
            'header_path': header_path,
            'current_header': chunk_header,
            'level': len(header_stack) + 1  # One level deeper than parent
        }

    def _create_fallback_chunk(self, chunk_text: str, header_stack: List[Dict]) -> Dict:
        """
        Create fallback chunk when splitting fails.

        Args:
            chunk_text: Original chunk text
            header_stack: Header hierarchy

        Returns:
            Chunk dict
        """
        return {
            'text': chunk_text,
            'header_path': [h['text'] for h in header_stack[:-1]],
            'current_header': header_stack[-1]['text'] if header_stack else None,
            'level': header_stack[-1]['level'] if header_stack else 0
        }
