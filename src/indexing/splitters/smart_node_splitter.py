"""
SmartNodeSplitter - Enhanced splitter with pattern detection and cleanup.

Improvements over SimpleNodeSplitter:
1. Title chunk merging (for regulation documents)
2. Pattern-based section detection (Điều X, CHƯƠNG X)
3. Malformed markdown cleanup (empty headers)
4. Robust against LlamaParse inconsistencies

Focus: Regulation documents (curriculum support is basic)
"""
import re
from typing import List, Dict, Sequence
from llama_index.core import Document
from llama_index.core.schema import BaseNode
from src.indexing.splitters.base_node_splitter import BaseNodeSplitter


class SmartNodeSplitter(BaseNodeSplitter):
    """
    Smart splitter with pattern detection and structure cleanup.

    Features:
    1. Merge title chunks (regulation: first 3 short headers)
    2. Detect Vietnamese regulation patterns (Điều, CHƯƠNG)
    3. Remove malformed headers (empty ##, broken markdown)
    4. Fallback to simple parsing if patterns fail

    Inherits from BaseNodeSplitter:
    - Token counting
    - Context prepending
    - Sub-chunking logic
    - Stats tracking
    """

    # Regulation patterns (for pattern detection when markdown headers are missing)
    DIEU_PATTERN = re.compile(r'^\*?\*?Điều\s+\d+\.')  # Điều 10. or **Điều 10.**
    CHUONG_PATTERN = re.compile(r'^CHƯƠNG\s+[IVXLCDM0-9]+')  # CHƯƠNG 1, CHƯƠNG I
    CHUONG_PATTERN_2 = re.compile(r'^##?\s*Chương\s+\d+')  # ## Chương 1

    # NOTE: Khoản (1., 2., ...) and Mục (a), b), ...) are NOT pattern-detected
    # because they conflict with markdown lists and cause false positives.
    # They MUST have markdown headers (###) to be detected.

    # Special sections to keep as single chunks
    SPECIAL_SECTIONS = ['MỤC LỤC', 'DANH MỤC TỪ VIẾT TẮT', 'QUYẾT ĐỊNH']

    def __init__(
        self,
        max_tokens: int = None,
        sub_chunk_size: int = None,
        sub_chunk_overlap: int = None,
        encoding_model: str = "text-embedding-3-small",
        enable_title_merging: bool = True,
        enable_pattern_detection: bool = True,
        max_header_level: int = 4
    ):
        """
        Initialize smart splitter.

        Args:
            max_tokens: Maximum tokens per chunk before sub-chunking
            sub_chunk_size: Target size for sub-chunks
            sub_chunk_overlap: Overlap between sub-chunks
            encoding_model: Model for token counting
            enable_title_merging: Merge first N short title chunks
            enable_pattern_detection: Detect Vietnamese patterns (Điều, CHƯƠNG)
            max_header_level: Maximum header level to parse (1-6)
                              1 = only #, 2 = # and ##, 3 = up to ###, etc.
                              Default 4 = parse up to #### (includes Mục)
                              Set to 3 to merge Mục into Khoản chunks
        """
        super().__init__(max_tokens, sub_chunk_size, sub_chunk_overlap, encoding_model)

        self.enable_title_merging = enable_title_merging
        self.enable_pattern_detection = enable_pattern_detection
        self.max_header_level = max_header_level

        # Add extra stats
        self.stats["title_chunks_merged"] = 0
        self.stats["patterns_detected"] = 0

        print(f"  - title_merging: {self.enable_title_merging}")
        print(f"  - pattern_detection: {self.enable_pattern_detection}")
        print(f"  - max_header_level: {self.max_header_level} ({'# to ' + '#'*self.max_header_level})")

    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False
    ) -> List[BaseNode]:
        """
        Parse documents to nodes with smart handling.

        Overrides base implementation to add preprocessing step.

        Args:
            documents: List of documents to parse
            show_progress: Whether to show progress

        Returns:
            List of TextNode objects
        """
        all_nodes = []

        for doc in documents:
            # Step 1: Preprocess markdown (cleanup)
            cleaned_text = self._preprocess_markdown(doc.text, doc.metadata)

            # Step 2: Parse by headers
            chunks_data = self._parse_by_headers(cleaned_text, doc.metadata)
            self.stats["total_chunks"] += len(chunks_data)

            # Step 3: Post-process chunks (merge title, etc.)
            chunks_data = self._post_process_chunks(chunks_data, doc.metadata)

            # Step 4: Prepend context
            chunks_with_context = [
                self._prepend_context(chunk_data, doc.metadata)
                for chunk_data in chunks_data
            ]

            # Step 5: Token check and sub-chunk if needed
            nodes = self._process_chunks_with_token_check(
                chunks_with_context,
                chunks_data,
                doc.metadata
            )

            all_nodes.extend(nodes)

        self.stats["final_nodes"] = len(all_nodes)
        return all_nodes

    def _preprocess_markdown(self, text: str, metadata: Dict) -> str:
        """
        Clean and preprocess markdown before parsing.

        Args:
            text: Raw markdown text
            metadata: Document metadata_generator

        Returns:
            Cleaned markdown text
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove empty headers (##\n, ###\n, etc.)
            if re.match(r'^#{1,6}\s*$', line):
                print(f"  [CLEANUP] Removed empty header: '{line}'")
                continue

            # Fix bullet points mistakenly marked as headers
            # Pattern: "#### - Some text" → "- Some text"
            bullet_header_match = re.match(r'^(#{1,6})\s*(-|\*)\s+(.+)', line)
            if bullet_header_match:
                bullet_char = bullet_header_match.group(2)
                content = bullet_header_match.group(3)
                fixed_line = f"{bullet_char} {content}"
                print(f"  [CLEANUP] Fixed bullet point header: '{line[:60]}...' → '{fixed_line[:60]}...'")
                cleaned_lines.append(fixed_line)
                continue

            # Remove standalone separators that might confuse parser
            if re.match(r'^-{3,}$|^={3,}$', line.strip()):
                # Keep separator but don't let it become a header
                cleaned_lines.append(line)
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _parse_by_headers(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Parse markdown by headers WITH hierarchy tracking.

        Args:
            text: Markdown text to parse
            metadata: Document metadata (used for category-specific truncation)

        Returns:
            List of dicts with:
            - text: chunk content
            - header_path: list of parent headers (NOT including current)
            - current_header: this chunk's own header
            - level: header level (1-6)
        """
        chunks = []
        header_stack = []  # Stack tracking current hierarchy
        current_chunk_lines = []

        lines = text.split('\n')

        for line in lines:
            # Detect markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)

            if header_match:
                # ========== HEADER DETECTED ==========
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()

                # Skip headers deeper than max_header_level
                if level > self.max_header_level:
                    current_chunk_lines.append(line)
                    continue

                # Save previous chunk if exists
                if current_chunk_lines:
                    chunk_data = {
                        'text': '\n'.join(current_chunk_lines),
                        'header_path': [h['text'] for h in header_stack[:-1]],  # Parents only
                        'current_header': header_stack[-1]['text'] if header_stack else None,
                        'level': header_stack[-1]['level'] if header_stack else 0
                    }
                    chunks.append(chunk_data)
                    current_chunk_lines = []

                # Update header stack: remove headers at same or deeper level
                header_stack = [h for h in header_stack if h['level'] < level]

                # ✅ TRUNCATE header before adding to stack
                truncated_header = self._truncate_header(header_text, metadata)

                # Add current header
                header_stack.append({'level': level, 'text': truncated_header})

                # Start new chunk
                current_chunk_lines = [line]

            else:
                # Check for patterns even without markdown header
                if self.enable_pattern_detection and not current_chunk_lines:
                    # Line might be a section marker (Điều X, CHƯƠNG X)
                    if self._is_section_marker(line):
                        # Treat as implicit header
                        if current_chunk_lines:
                            chunk_data = {
                                'text': '\n'.join(current_chunk_lines),
                                'header_path': [h['text'] for h in header_stack[:-1]],
                                'current_header': header_stack[-1]['text'] if header_stack else None,
                                'level': header_stack[-1]['level'] if header_stack else 0
                            }
                            chunks.append(chunk_data)

                        # Update header stack for pattern-detected header
                        level = 2  # Default level for patterns
                        header_text = line.strip()

                        # ✅ TRUNCATE pattern-detected header
                        truncated_header = self._truncate_header(header_text, metadata)

                        # Remove headers at same or deeper level
                        header_stack = [h for h in header_stack if h['level'] < level]
                        header_stack.append({'level': level, 'text': truncated_header})

                        current_chunk_lines = [line]
                        self.stats["patterns_detected"] += 1
                        print(f"  [PATTERN] Detected section: {header_text[:50]}...")
                        continue

                current_chunk_lines.append(line)

        # Save last chunk
        if current_chunk_lines:
            chunk_data = {
                'text': '\n'.join(current_chunk_lines),
                'header_path': [h['text'] for h in header_stack[:-1]],  # Parents only
                'current_header': header_stack[-1]['text'] if header_stack else None,
                'level': header_stack[-1]['level'] if header_stack else 0
            }
            chunks.append(chunk_data)

        return chunks

    def _is_section_marker(self, line: str) -> bool:
        """
        Check if line matches Vietnamese regulation patterns.

        Only detects CHƯƠNG and Điều (top 2 levels).
        Khoản and Mục MUST have markdown headers to be detected.

        Hierarchy:
        - CHƯƠNG (level 1) - pattern detected
        - Điều (level 2) - pattern detected
        - Khoản: 1., 2., 3., ... (level 3) - MUST have markdown header (###)
        - Mục: a), b), c), ... (level 4) - MUST have markdown header (####)

        Args:
            line: Text line to check

        Returns:
            True if line is a section marker
        """
        line_stripped = line.strip()

        # Check CHƯƠNG patterns (highest level)
        if self.CHUONG_PATTERN.match(line_stripped):
            return True
        if self.CHUONG_PATTERN_2.match(line_stripped):
            return True

        # Check Điều pattern
        if self.DIEU_PATTERN.match(line_stripped):
            return True

        return False

    def _truncate_header(self, header: str, metadata: Dict = None, max_length: int = 80) -> str:
        """
        Truncate header to avoid duplication in hierarchy.

        Strategy depends on document category:

        REGULATION:
        - ALWAYS truncate known patterns (Điều, Khoản, Mục) regardless of length
        - For other headers: only truncate if > max_length

        CURRICULUM:
        - KEEP headers as-is (they're already short and descriptive)
        - Only truncate if > max_length

        Examples (Regulation):
        - "CHƯƠNG I" → "CHƯƠNG I" (short, keep)
        - "Điều 1. Phạm vi điều chỉnh" → "Điều 1" (always truncate)
        - "1. Văn bản này quy định..." → "Khoản 1" (always truncate)
        - "a. Short text" → "Mục a" (always truncate)

        Examples (Curriculum):
        - "# 1. GIỚI THIỆU" → "1. GIỚI THIỆU" (keep as-is)
        - "## 1.1. Mục tiêu đào tạo" → "1.1. Mục tiêu đào tạo" (keep as-is)
        - "### 1.3.1. Nhóm các môn học cơ sở nhóm ngành" → "1.3.1. Nhóm các môn học cơ sở nhóm ngành" (keep as-is)

        Args:
            header: Original header text
            metadata: Document metadata (used to determine category)
            max_length: Maximum length before truncation

        Returns:
            Truncated header
        """
        category = metadata.get('category', '') if metadata else ''

        # ========== CURRICULUM: KEEP HEADERS AS-IS ==========
        if category == 'curriculum':
            # Only truncate if extremely long
            if len(header) <= max_length:
                return header
            return header[:max_length] + "..."

        # ========== REGULATION: TRUNCATE KNOWN PATTERNS ==========

        # Pattern: "Điều X. <text>" OR "Điều X" → "Điều X"
        if match := re.match(r'^(Điều\s+\d+)', header):
            return match.group(1)

        # Pattern: "CHƯƠNG X - <text>" OR "CHƯƠNG X" → "CHƯƠNG X"
        if match := re.match(r'^(CHƯƠNG\s+[IVXLCDM0-9]+)', header):
            return match.group(1)

        # Pattern: "1. <text>" → "Khoản 1" (ALWAYS, even if short)
        if match := re.match(r'^(\d+)\.', header):
            return f"Khoản {match.group(1)}"

        # Pattern: "a)" OR "a." → "Mục a" (ALWAYS, even if short)
        if match := re.match(r'^([a-z])[\).]', header):
            return f"Mục {match.group(1)}"

        # ========== FOR OTHER HEADERS: ONLY TRUNCATE IF LONG ==========

        if len(header) <= max_length:
            return header

        # Fallback: just truncate with ellipsis
        return header[:max_length] + "..."

    def _post_process_chunks(self, chunks: List[Dict], metadata: Dict) -> List[Dict]:
        """
        Post-process chunks: merge title, etc.

        Args:
            chunks: List of chunk dicts
            metadata: Document metadata_generator

        Returns:
            Processed chunks
        """
        if not chunks:
            return chunks

        # Title merging (regulation only)
        category = metadata.get('category', '')
        if self.enable_title_merging and category == 'regulation':
            chunks = self._merge_title_chunks(chunks)

        return chunks

    def _prepend_context(self, chunk_data: Dict, metadata: Dict) -> str:
        """
        Prepend document context and FULL HIERARCHY to chunk text.

        Override BaseNodeSplitter to add hierarchy support.

        Args:
            chunk_data: Dict with text, header_path, current_header
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

        # ========== HEADER HIERARCHY (NEW!) ==========
        # header_path: Parent headers only (ALREADY TRUNCATED in parsing)
        # current_header: This chunk's header (ALREADY TRUNCATED in parsing)
        # full_path: Parents + current (e.g., ["CHƯƠNG I", "Điều 8", "Khoản 1"])

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
            separator = "\n---\n"
            return f"{context_header}{separator}{chunk_data['text']}"
        else:
            return chunk_data['text']

    def _merge_title_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Merge first N short chunks that look like title.

        Strategy:
        - First 3-5 chunks
        - All very short (<150 chars)
        - NOT special sections (MỤC LỤC, DANH MỤC, etc.)
        → Likely to be title split by LlamaParse

        Args:
            chunks: List of chunk dicts

        Returns:
            Chunks with merged title
        """
        if len(chunks) < 2:
            return chunks

        # Identify title chunks
        title_chunks = []
        for i, chunk in enumerate(chunks[:5]):  # Check first 5
            text = chunk['text'].strip()
            header = chunk.get('current_header', '')

            # Stop if we hit a special section (not part of title)
            if header and any(marker in header.upper() for marker in self.SPECIAL_SECTIONS):
                print(f"  [MERGE] Stopped at special section: {header}")
                break

            content_lines = [l for l in text.split('\n') if l.strip() and not l.startswith('#')]
            content_text = '\n'.join(content_lines)

            # Criteria for title chunk:
            # 1. Very short (<150 chars of content)
            # 2. Few lines (<3 lines of non-header content)
            # 3. Not a special section
            if len(content_text) < 150 and len(content_lines) < 3:
                title_chunks.append(chunk)
            else:
                break  # Stop at first non-title chunk

        # Merge if we found multiple title chunks
        if len(title_chunks) > 1:
            print(f"  [MERGE] Merging {len(title_chunks)} title chunks into 1")

            merged_text = '\n'.join(c['text'] for c in title_chunks)
            merged_header = ' '.join(
                c['current_header'] for c in title_chunks if c['current_header']
            )

            merged = {
                'text': merged_text,
                'current_header': merged_header or 'TITLE',
                'level': 0,
                'is_title': True
            }

            self.stats["title_chunks_merged"] = len(title_chunks)

            return [merged] + chunks[len(title_chunks):]

        return chunks
