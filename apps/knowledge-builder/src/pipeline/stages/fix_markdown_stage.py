"""
Fix Markdown Stage - Fix markdown structure using LLM.
"""

from pathlib import Path
from typing import Dict, Any
from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState
from processing.steps.markdown_fixer import MarkdownFixer


class FixMarkdownStage(Stage):
    """
    Fix markdown structure using Gemini LLM.

    Fixes:
    - Broken headers
    - Malformed tables
    - Inconsistent formatting
    - Missing structure

    This is an optional stage - can be skipped with --skip-fix-markdown.
    """

    def __init__(self):
        super().__init__(
            name="fix-markdown",
            is_costly=True,  # Uses Gemini API
            is_idempotent=False,  # LLM may produce different results
            description="Fix markdown structure using Gemini LLM"
        )
        self.markdown_fixer = None

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fix markdown structure.

        Args:
            input_path: Path to filtered markdown
            output_path: Path to save fixed markdown
            state: Pipeline state
            **kwargs: Additional arguments (skip=True to skip this stage)

        Returns:
            Metadata dict
        """
        # Check if should skip
        if kwargs.get('skip', False):
            # Just copy input to output
            content = input_path.read_text(encoding='utf-8')
            output_path.write_text(content, encoding='utf-8')
            return {
                "skipped": True,
                "reason": "skip_flag"
            }

        # Initialize fixer if needed
        if self.markdown_fixer is None:
            self.markdown_fixer = MarkdownFixer()

        # Read input
        content = input_path.read_text(encoding='utf-8')

        # Fix markdown
        fixed_content = self.markdown_fixer.fix_markdown(
            content,
            category=state.category
        )

        if not fixed_content or not fixed_content.strip():
            raise ValueError("Markdown fixing produced empty content")

        # Save
        output_path.write_text(fixed_content, encoding='utf-8')

        # Return metadata
        return {
            "model": "gemini-2.0-flash-exp",
            "input_size": len(content),
            "output_size": len(fixed_content),
            "cost": 0.02  # Estimate
        }

    def get_output_filename(self) -> str:
        """Output filename for fix-markdown stage."""
        return "05-fixed.md"
