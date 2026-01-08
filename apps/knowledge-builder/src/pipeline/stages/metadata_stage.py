"""
Metadata Stage - Generate document metadata using LLM.
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState
from processing.metadata_generator.metadata_generator_factory import MetadataGeneratorFactory


class MetadataStage(Stage):
    """
    Generate metadata for document.

    Uses LLM to extract:
    - Title
    - Category-specific metadata (regulation_number, major, etc.)
    - Document classification

    Output is saved as metadata.json in stage directory.
    """

    def __init__(self):
        super().__init__(
            name="metadata",
            is_costly=True,  # Uses LLM
            is_idempotent=False,  # LLM may produce different results
            description="Generate metadata using LLM"
        )

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate metadata.

        Args:
            input_path: Path to final markdown
            output_path: Path to save metadata.json (not used, metadata saved separately)
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict (also saved to metadata.json)
        """
        # Read content
        content = input_path.read_text(encoding='utf-8')

        # Generate metadata using category-specific generator
        generator = MetadataGeneratorFactory.get_generator(state.category)
        metadata_obj = generator.generate(input_path, content)

        if not metadata_obj:
            raise RuntimeError("Metadata generation failed - generator returned None")

        # Convert to dict
        metadata_dict = metadata_obj.model_dump()

        # Add generation timestamp
        metadata_dict["_generated_at"] = datetime.now().isoformat()

        # Save to metadata.json
        import json
        metadata_file = state.doc_dir / "metadata.json"
        metadata_file.write_text(
            json.dumps(metadata_dict, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Return metadata
        return {
            "metadata_generated": True,
            "metadata_file": "metadata.json",
            "cost": 0.01  # Estimate
        }

    def get_output_filename(self) -> str:
        """
        Metadata stage doesn't produce a markdown file.

        Returns None since output is metadata.json, not a markdown file.
        """
        return None  # No markdown output, only metadata.json
