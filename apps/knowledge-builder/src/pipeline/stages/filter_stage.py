"""
Filter Stage - Quality check to filter out low-quality content.
"""

from pathlib import Path
from typing import Dict, Any
from ..core.stage import Stage
from ..core.pipeline_state import PipelineState
from ...processing.steps.content_filter import ContentFilter
from ...config.settings import settings


class FilterStage(Stage):
    """
    Filter low-quality content.

    Checks:
    - Hard rules (too short, error pages, navigation pages)
    - Heuristic scoring (word count, paragraphs, information density)

    If content fails quality check, it's saved to .rejected/ and stage is marked as rejected.
    """

    def __init__(self):
        super().__init__(
            name="filter",
            is_costly=False,
            is_idempotent=True,
            description="Quality check - filter low-quality content"
        )
        self.content_filter = ContentFilter()

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Filter content by quality.

        Args:
            input_path: Path to normalized markdown
            output_path: Path to save filtered markdown (if passes)
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict with filter results
        """
        # Read input
        content = input_path.read_text(encoding='utf-8')

        # Check quality
        is_useful, reason = self.content_filter.is_useful(content)

        if not is_useful:
            # Save to rejected folder
            rejected_dir = settings.paths.STAGES_DIR.parent / ".rejected" / state.category
            rejected_dir.mkdir(parents=True, exist_ok=True)

            rejected_file = rejected_dir / f"{state.document_id}.md"
            rejected_file.write_text(content, encoding='utf-8')

            # Save rejection metadata
            import json
            stats = self.content_filter.get_stats_summary(content)
            stats["rejection_reason"] = reason

            rejected_json = rejected_dir / f"{state.document_id}.json"
            rejected_json.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')

            # Update state to rejected
            state.add_stage(
                self.name,
                PipelineState.STATUS_REJECTED,
                metadata={"reason": reason, "rejected_to": str(rejected_file)}
            )
            state.save()

            raise ValueError(f"Content rejected: {reason}")

        # Content passed - save
        output_path.write_text(content, encoding='utf-8')

        # Return metadata
        stats = self.content_filter.get_stats_summary(content)
        return {
            "passed": True,
            "score": stats["score"],
            "word_count": stats["word_count"]
        }

    def get_output_filename(self) -> str:
        """Output filename for filter stage."""
        return "04-filtered.md"
