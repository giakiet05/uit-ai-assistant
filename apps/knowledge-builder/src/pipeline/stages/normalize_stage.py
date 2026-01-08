"""
Normalize Stage - Unicode normalization and Vietnamese spelling modernization.
"""

import unicodedata
import re
from pathlib import Path
from typing import Dict, Any
from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState


class NormalizeStage(Stage):
    """
    Normalize Vietnamese text:
    1. Unicode normalization (NFC)
    2. Vietnamese spelling modernization (old -> new)

    Unicode normalization fixes:
    - NFC (composed): 'ó' = U+00F3 (single character)
    - NFD (decomposed): 'ó' = U+006F + U+0301 (base + combining mark)

    Spelling modernization (2008 reform):
    - khoá -> khóa
    - toá -> tóa
    - khoăn -> khoản
    - etc.
    """

    # Vietnamese spelling modernization mapping (old -> new)
    SPELLING_MODERNIZATION = {
        'khoá': 'khóa',
        'Khoá': 'Khóa',
        'KHOÁ': 'KHÓA',
        'toá': 'tóa',
        'Toá': 'Tóa',
        'TOÁ': 'TÓA',
        'khoăn': 'khoản',
        'Khoăn': 'Khoản',
        'KHOĂN': 'KHOẢN',
        'ngòai': 'ngoài',
        'Ngòai': 'Ngoài',
        'NGÒAI': 'NGOÀI',
        'giùm': 'giúm',
        'Giùm': 'Giúm',
        'GIÙM': 'GIÚM',
    }

    def __init__(self):
        super().__init__(
            name="normalize",
            is_costly=False,
            is_idempotent=True,
            description="Normalize Vietnamese Unicode and modernize spelling"
        )

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Normalize Unicode and modernize Vietnamese spelling.

        Args:
            input_path: Path to cleaned markdown
            output_path: Path to save normalized markdown
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict with Unicode changes and spelling corrections
        """
        # Read input
        content = input_path.read_text(encoding='utf-8')
        original_content = content

        # Step 1: Normalize to NFC
        content = unicodedata.normalize('NFC', content)
        unicode_changes = sum(1 for a, b in zip(original_content, content) if a != b)

        # Step 2: Modernize Vietnamese spelling
        spelling_corrections = {}
        for old_word, new_word in self.SPELLING_MODERNIZATION.items():
            # Use word boundary regex to match whole words only
            pattern = r'\b' + re.escape(old_word) + r'\b'
            matches = re.findall(pattern, content)
            if matches:
                spelling_corrections[old_word] = len(matches)
                content = re.sub(pattern, new_word, content)

        # Save
        output_path.write_text(content, encoding='utf-8')

        # Return metadata
        return {
            "unicode_form": "NFC",
            "unicode_changes": unicode_changes,
            "spelling_corrections": spelling_corrections,
            "total_corrections": sum(spelling_corrections.values()),
            "has_changes": unicode_changes > 0 or len(spelling_corrections) > 0
        }

    def get_output_filename(self) -> str:
        """Output filename for normalize stage."""
        return "03-normalized.md"
