"""
Clean Stage - Clean markdown using category-specific cleaners.
"""

from pathlib import Path
from typing import Dict, Any
from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState
from processing.cleaner.cleaner_factory import CleanerFactory


class CleanStage(Stage):
    """
    Clean markdown content.

    Applies category-specific cleaning rules:
    - Remove letterheads
    - Clean navigation elements
    - Fix formatting issues
    """

    def __init__(self):
        super().__init__(
            name="clean",
            is_costly=False,
            is_idempotent=True,
            description="Clean markdown using regex-based rules"
        )

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Clean markdown content.

        Args:
            input_path: Path to parsed markdown
            output_path: Path to save cleaned markdown
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict
        """
        # Read input
        raw_content = input_path.read_text(encoding='utf-8')

        # Get cleaner for category
        cleaner = CleanerFactory.get_cleaner(state.category)

        # Clean
        cleaned_content = cleaner.clean(raw_content)

        if not cleaned_content or not cleaned_content.strip():
            raise ValueError("Cleaning produced empty content")

        # Save
        output_path.write_text(cleaned_content, encoding='utf-8')

        # Return metadata
        return {
            "cleaner": type(cleaner).__name__,
            "input_size": len(raw_content),
            "output_size": len(cleaned_content),
            "reduction": len(raw_content) - len(cleaned_content)
        }

    def get_output_filename(self) -> str:
        """Output filename for clean stage."""
        return "02-cleaned.md"
