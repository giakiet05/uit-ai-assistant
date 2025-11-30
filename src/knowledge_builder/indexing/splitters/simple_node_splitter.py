"""
SimpleNodeSplitter - Header text only, no hierarchy tracking.

Problem solved:
- LlamaParse creates incorrect header levels (e.g., Điều 33 as ##, Điều 34 as ###)
- Hierarchical parsers create wrong parent-child relationships
- This leads to incorrect context in retrieval

Solution:
- Parse by headers to split chunks (preserve semantic boundaries)
- Track ONLY current header text (no parent-child hierarchy)
- Context: "Phần: Điều 10" instead of "Cấu trúc: Chương 1 > Điều 10"

Trade-off:
- Lose hierarchy info (which section belongs to which chapter)
- But: More robust against parsing errors, simpler, still effective for retrieval
"""
import re
from typing import List, Dict
from .base_node_splitter import BaseNodeSplitter


class SimpleNodeSplitter(BaseNodeSplitter):
    """
    Simple splitter that parses by headers but doesn't track hierarchy.

    Key features:
    1. Parse markdown by headers (preserve section boundaries)
    2. Track only current header text (no parent-child relationships)
    3. Prepend minimal context (document info + current section)
    4. Robust against header level errors from LlamaParse

    Inherits from BaseNodeSplitter:
    - Token counting
    - Context prepending
    - Sub-chunking logic
    - Stats tracking
    """

    def _parse_by_headers(self, text: str) -> List[Dict]:
        """
        Parse markdown by headers WITHOUT tracking hierarchy.

        Returns:
            List of dicts with:
            - text: chunk content (including header line)
            - current_header: this chunk's header text (without # symbols)
            - level: header level (1-6) - kept for reference but not used for hierarchy

        Example:
            For "## Điều 10\nContent here":
            - text: "## Điều 10\nContent here"
            - current_header: "Điều 10"
            - level: 2
        """
        chunks = []
        current_header = None
        current_level = 0
        current_chunk_lines = []

        lines = text.split('\n')

        for line in lines:
            # Detect markdown headers: # Header, ## Header, etc.
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)

            if header_match:
                # ========== NEW HEADER DETECTED ==========
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()

                # Save previous chunk if exists
                if current_chunk_lines:
                    chunk_data = {
                        'text': '\n'.join(current_chunk_lines),
                        'current_header': current_header,
                        'level': current_level
                    }
                    chunks.append(chunk_data)

                # Start new chunk
                current_header = header_text
                current_level = level
                current_chunk_lines = [line]

            else:
                # Regular line
                current_chunk_lines.append(line)

        # Save last chunk
        if current_chunk_lines:
            chunk_data = {
                'text': '\n'.join(current_chunk_lines),
                'current_header': current_header,
                'level': current_level
            }
            chunks.append(chunk_data)

        return chunks
