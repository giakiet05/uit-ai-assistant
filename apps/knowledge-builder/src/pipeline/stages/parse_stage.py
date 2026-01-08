"""
Parse Stage - Convert PDF/DOCX to markdown.
"""

from pathlib import Path
from typing import Dict, Any
from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState
from processing.parser.parser_factory import ParserFactory


class ParseStage(Stage):
    """
    Parse PDF/DOCX files to markdown.

    Uses LlamaParse or Marker depending on configuration.
    For .md files, this stage is skipped.

    """

    def __init__(self):
        super().__init__(
            name="parse",
            is_costly=True,  # LlamaParse costs money
            is_idempotent=True,
            description="Parse PDF/DOCX to markdown using LlamaParse"
        )

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Parse file to markdown.

        Args:
            input_path: Path to PDF/DOCX file
            output_path: Path to save parsed markdown
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict with parsing info
        """
        # Get parser
        parser = ParserFactory.get_parser(str(input_path))

        # Parse
        parsed_content = parser.parse(str(input_path))

        if not parsed_content or not parsed_content.strip():
            raise ValueError("Parsing produced empty content")

        # Save
        output_path.write_text(parsed_content, encoding='utf-8')

        # Return metadata
        return {
            "parser": type(parser).__name__,
            "input_size": input_path.stat().st_size,
            "output_size": len(parsed_content),
            "cost": 0.05  # Estimate - actual cost varies
        }

    def get_output_filename(self) -> str:
        """Output filename for parse stage."""
        return "01-parsed.md"

    def should_skip(self, state: PipelineState, input_path: Path, force: bool = False) -> tuple[bool, str]:
        """
        Skip parse stage for .md files.

        Args:
            state: Pipeline state
            input_path: Input file path
            force: Force re-run

        Returns:
            (should_skip, reason)
        """
        # If input is already markdown, skip parse
        if input_path.suffix.lower() == '.md':
            return True, "input_already_markdown"

        # Otherwise use default skip logic
        return super().should_skip(state, input_path, force)
