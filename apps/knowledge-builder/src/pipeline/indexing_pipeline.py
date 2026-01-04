"""
Indexing Pipeline - Orchestrates chunk and embed-index stages.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .core.pipeline_state import PipelineState
from .core.stage import Stage
from .stages.chunk_stage import ChunkStage
from .stages.embed_index_stage import EmbedIndexStage
from ..config.settings import settings


logger = logging.getLogger(__name__)


class IndexingPipeline:
    """
    Orchestrator for indexing pipeline.

    Executes stages in order:
    1. chunk -> chunks.json
    2. embed-index -> ChromaDB

    Features:
    - Incremental execution (skip completed stages)
    - Cost tracking
    - Works with stage-based structure
    """

    STAGE_ORDER = [
        'chunk',
        'embed-index'
    ]

    def __init__(
        self,
        category: str,
        document_id: str
    ):
        """
        Initialize indexing pipeline.

        Args:
            category: Document category (regulation, course, etc)
            document_id: Unique document ID
        """
        self.category = category
        self.document_id = document_id

        # Load or create state
        self.state = PipelineState.load(category, document_id)
        if self.state is None:
            raise ValueError(
                f"Pipeline state not found for {category}/{document_id}. "
                f"Run processing pipeline first."
            )

        # Initialize stages
        self.stages: Dict[str, Stage] = {
            'chunk': ChunkStage(),
            'embed-index': EmbedIndexStage()
        }

        self.stage_dir = settings.paths.get_stage_dir(category, document_id)

    def run(self, force: bool = False) -> Dict[str, Any]:
        """
        Run full indexing pipeline.

        Args:
            force: Force rerun of all stages

        Returns:
            Summary dict with:
            - stages_run: List of stages executed
            - stages_skipped: List of stages skipped
            - total_cost: Total API cost
            - chunks_file: Path to chunks.json
            - collection: ChromaDB collection name
        """
        logger.info(f"Running indexing pipeline for {self.category}/{self.document_id}")

        summary = {
            'stages_run': [],
            'stages_skipped': [],
            'total_cost': 0.0,
            'chunks_file': None,
            'collection': None
        }

        try:
            for stage_name in self.STAGE_ORDER:
                # Run stage
                result = self.run_stage(stage_name, force=force)

                if result['executed']:
                    summary['stages_run'].append(stage_name)
                    summary['total_cost'] += result.get('cost', 0.0)
                else:
                    summary['stages_skipped'].append(stage_name)

            # Get outputs
            chunks_file = self.stage_dir / "chunks.json"
            if chunks_file.exists():
                summary['chunks_file'] = chunks_file

            summary['collection'] = self.category

            logger.info(
                f"Indexing pipeline completed: {len(summary['stages_run'])} stages run, "
                f"{len(summary['stages_skipped'])} skipped, "
                f"cost: ${summary['total_cost']:.4f}"
            )

            return summary

        except Exception as e:
            logger.error(f"Indexing pipeline failed: {e}")
            raise

    def run_stage(
        self,
        stage_name: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Run a single stage.

        Args:
            stage_name: Name of stage to run
            force: Force rerun even if completed

        Returns:
            Result dict with execution info
        """
        if stage_name not in self.stages:
            raise ValueError(f"Invalid stage name: {stage_name}")

        stage = self.stages[stage_name]

        # Get input file
        input_path = self._get_input_for_stage(stage_name)

        # Run stage
        success = stage.run(
            state=self.state,
            input_path=input_path,
            force=force
        )

        # Get result from state
        stage_info = self.state.get_stage(stage_name)

        result = {
            'executed': success,
            'skipped': not success,
            'skip_reason': stage_info.metadata.get('skip_reason') if stage_info else None,
            'cost': stage_info.cost if stage_info else 0.0,
            'metadata': stage_info.metadata if stage_info else {}
        }

        return result

    def get_status(self) -> str:
        """
        Get human-readable pipeline status.

        Returns:
            Status string like "chunk -> embed-index"
        """
        parts = []
        for stage_name in self.STAGE_ORDER:
            stage = self.state.get_stage(stage_name)
            if not stage:
                symbol = "[ ]"
            elif stage.status == PipelineState.STATUS_COMPLETED:
                symbol = "[x]"
            elif stage.status == PipelineState.STATUS_FAILED:
                symbol = "[FAIL]"
            elif stage.status == PipelineState.STATUS_SKIPPED:
                symbol = "[SKIP]"
            elif stage.status == PipelineState.STATUS_IN_PROGRESS:
                symbol = "[...]"
            else:
                symbol = "[ ]"

            parts.append(f"{symbol} {stage_name}")

        return " -> ".join(parts)

    def _get_input_for_stage(self, stage_name: str) -> Path:
        """
        Get input file path for a stage.

        Args:
            stage_name: Name of stage

        Returns:
            Path to input file

        Logic:
        - For 'chunk': Use final markdown from processing pipeline
        - For 'embed-index': Use chunks.json
        """
        if stage_name == 'chunk':
            # Get final markdown from processing pipeline
            final_md = settings.paths.get_final_output(
                self.category,
                self.document_id
            )
            if not final_md or not final_md.exists():
                raise ValueError(
                    f"Final markdown not found for {self.category}/{self.document_id}. "
                    f"Run processing pipeline first."
                )
            return final_md

        elif stage_name == 'embed-index':
            # Use chunks.json from chunk stage
            chunks_file = self.stage_dir / "chunks.json"
            if not chunks_file.exists():
                raise ValueError(
                    f"chunks.json not found. Run chunk stage first."
                )
            return chunks_file

        else:
            raise ValueError(f"Unknown stage: {stage_name}")
