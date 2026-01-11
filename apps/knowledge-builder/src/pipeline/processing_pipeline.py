"""
Processing Pipeline - Orchestrates all processing stages.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from pipeline.core.pipeline_state import PipelineState
from pipeline.core.stage import Stage
from pipeline.stages.parse_stage import ParseStage
from pipeline.stages.clean_stage import CleanStage
from pipeline.stages.normalize_stage import NormalizeStage
from pipeline.stages.filter_stage import FilterStage
from pipeline.stages.fix_markdown_stage import FixMarkdownStage
from pipeline.stages.flatten_table_stage import FlattenTableStage
from pipeline.stages.metadata_stage import MetadataStage
from config.settings import settings


logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Orchestrator for processing pipeline.

    Executes stages in order:
    1. parse -> 01-parsed.md
    2. clean -> 02-cleaned.md
    3. normalize -> 03-normalized.md
    4. filter -> 04-filtered.md (rejects bad content)
    5. fix-markdown -> 05-fixed.md (optional, costly)
    6. flatten-table -> 06-flattened.md (optional, costly)
    7. metadata -> metadata.json (costly)

    Features:
    - Incremental execution (skip completed stages)
    - Stage locking (protect manual edits)
    - Cost tracking
    - Observability (intermediate outputs)
    """

    STAGE_ORDER = [
        'parse',
        'clean',
        'normalize',
        'filter',
        'fix-markdown',
        'flatten-table',
        'metadata'
    ]

    def __init__(
        self,
        category: str,
        document_id: str,
        raw_file_path: Path
    ):
        """
        Initialize processing pipeline.

        Args:
            category: Document category (regulation, course, etc)
            document_id: Unique document ID
            raw_file_path: Path to raw input file (PDF, DOCX, or MD)
        """
        self.category = category
        self.document_id = document_id
        self.raw_file_path = Path(raw_file_path)

        # Load or create state
        self.state = PipelineState.load(category, document_id)
        if self.state is None:
            self.state = PipelineState(document_id, category)
            self.state.save()

        # Initialize stages
        self.stages: Dict[str, Stage] = {
            'parse': ParseStage(),
            'clean': CleanStage(),
            'normalize': NormalizeStage(),
            'filter': FilterStage(),
            'fix-markdown': FixMarkdownStage(),
            'flatten-table': FlattenTableStage(),
            'metadata': MetadataStage()
        }

        # Create stage directory
        self.stage_dir = settings.paths.get_stage_dir(category, document_id)
        self.stage_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        force: bool = False,
        skip_fix_markdown: bool = False,
        skip_flatten_table: bool = False
    ) -> Dict[str, Any]:
        """
        Run full processing pipeline.

        Args:
            force: Force rerun of all stages
            skip_fix_markdown: Skip fix-markdown stage (save cost)
            skip_flatten_table: Skip flatten-table stage (save cost)

        Returns:
            Summary dict with:
            - stages_run: List of stages executed
            - stages_skipped: List of stages skipped
            - total_cost: Total API cost
            - final_output: Path to final markdown
            - metadata_file: Path to metadata.json (if generated)
            - rejected: True if content was rejected by filter

        Raises:
            ValueError: If content is rejected by filter stage
        """
        logger.info(f"Running processing pipeline for {self.category}/{self.document_id}")

        summary = {
            'stages_run': [],
            'stages_skipped': [],
            'total_cost': 0.0,
            'final_output': None,
            'metadata_file': None,
            'rejected': False
        }

        try:
            for stage_name in self.STAGE_ORDER:
                # Handle skip flags
                kwargs = {}
                if stage_name == 'fix-markdown' and skip_fix_markdown:
                    kwargs['skip'] = True
                if stage_name == 'flatten-table' and skip_flatten_table:
                    kwargs['skip'] = True

                # Run stage
                try:
                    result = self.run_stage(
                        stage_name,
                        force=force,
                        **kwargs
                    )

                    if result['executed']:
                        summary['stages_run'].append(stage_name)
                        summary['total_cost'] += result.get('cost', 0.0)
                    else:
                        summary['stages_skipped'].append(stage_name)
                        summary['total_cost'] += result.get('cost', 0.0)

                except ValueError as e:
                    # Filter rejection
                    if stage_name == 'filter' and 'rejected' in str(e).lower():
                        summary['rejected'] = True
                        logger.warning(f"Content rejected: {e}")
                        raise
                    else:
                        raise

            # Get final outputs
            summary['final_output'] = settings.paths.get_final_output(
                self.category,
                self.document_id
            )

            metadata_path = settings.paths.get_metadata(
                self.category,
                self.document_id
            )
            if metadata_path and metadata_path.exists():
                summary['metadata_file'] = metadata_path

            logger.info(
                f"Pipeline completed: {len(summary['stages_run'])} stages run, "
                f"{len(summary['stages_skipped'])} skipped, "
                f"cost: ${summary['total_cost']:.4f}"
            )

            return summary

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

    def run_stage(
        self,
        stage_name: str,
        force: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a single stage.

        Args:
            stage_name: Name of stage to run
            force: Force rerun even if completed
            **kwargs: Additional arguments to pass to stage.execute()

        Returns:
            Result dict with:
            - executed: True if stage was executed
            - skipped: True if stage was skipped
            - skip_reason: Reason for skip (if skipped)
            - cost: API cost (if any)
            - metadata: Stage-specific metadata

        Raises:
            ValueError: If stage name is invalid or content is rejected
        """
        if stage_name not in self.stages:
            raise ValueError(f"Invalid stage name: {stage_name}")

        stage = self.stages[stage_name]

        # Get input file
        input_path = self._get_input_for_stage(stage_name)

        # Run stage (handles skipping internally)
        success = stage.run(
            state=self.state,
            input_path=input_path,
            force=force,
            **kwargs
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

    def run_from_to(
        self,
        from_stage: str,
        to_stage: str,
        force: bool = False,
        skip_fix_markdown: bool = False
    ) -> Dict[str, Any]:
        """
        Run pipeline from one stage to another.

        Args:
            from_stage: Starting stage name
            to_stage: Ending stage name (inclusive)
            force: Force rerun of stages
            skip_fix_markdown: Skip fix-markdown stage

        Returns:
            Summary dict (same as run())

        Raises:
            ValueError: If stage names are invalid or out of order
        """
        if from_stage not in self.STAGE_ORDER:
            raise ValueError(f"Invalid from_stage: {from_stage}")
        if to_stage not in self.STAGE_ORDER:
            raise ValueError(f"Invalid to_stage: {to_stage}")

        from_idx = self.STAGE_ORDER.index(from_stage)
        to_idx = self.STAGE_ORDER.index(to_stage)

        if from_idx > to_idx:
            raise ValueError(f"from_stage ({from_stage}) must come before to_stage ({to_stage})")

        logger.info(f"Running pipeline from {from_stage} to {to_stage}")

        summary = {
            'stages_run': [],
            'stages_skipped': [],
            'total_cost': 0.0,
            'final_output': None,
            'metadata_file': None,
            'rejected': False
        }

        try:
            for stage_name in self.STAGE_ORDER[from_idx:to_idx+1]:
                # Handle skip flags
                kwargs = {}
                if stage_name == 'fix-markdown' and skip_fix_markdown:
                    kwargs['skip'] = True

                # Run stage
                try:
                    result = self.run_stage(
                        stage_name,
                        force=force,
                        **kwargs
                    )

                    if result['executed']:
                        summary['stages_run'].append(stage_name)
                        summary['total_cost'] += result.get('cost', 0.0)
                    else:
                        summary['stages_skipped'].append(stage_name)

                except ValueError as e:
                    # Filter rejection
                    if stage_name == 'filter' and 'rejected' in str(e).lower():
                        summary['rejected'] = True
                        logger.warning(f"Content rejected: {e}")
                        raise
                    else:
                        raise

            # Get final outputs
            summary['final_output'] = settings.paths.get_final_output(
                self.category,
                self.document_id
            )

            metadata_path = settings.paths.get_metadata(
                self.category,
                self.document_id
            )
            if metadata_path and metadata_path.exists():
                summary['metadata_file'] = metadata_path

            logger.info(
                f"Pipeline range completed: {len(summary['stages_run'])} stages run, "
                f"{len(summary['stages_skipped'])} skipped"
            )

            return summary

        except Exception as e:
            logger.error(f"Pipeline range failed: {e}")
            raise

    def get_status(self) -> str:
        """
        Get human-readable pipeline status.

        Returns:
            Status string like "[x] parse -> [x] clean -> [x] normalize -> [ ] filter"
        """
        return self.state.get_status_summary()

    def _get_input_for_stage(self, stage_name: str) -> Path:
        """
        Get input file path for a stage.

        Args:
            stage_name: Name of stage

        Returns:
            Path to input file

        Logic:
        - For 'parse': Use raw_file_path
        - For other stages: Use output of previous stage
        """
        if stage_name == 'parse':
            return self.raw_file_path

        # Get previous stage
        stage_idx = self.STAGE_ORDER.index(stage_name)
        if stage_idx == 0:
            return self.raw_file_path

        # Find most recent completed stage before this one
        for i in range(stage_idx - 1, -1, -1):
            prev_stage_name = self.STAGE_ORDER[i]
            prev_stage_info = self.state.get_stage(prev_stage_name)

            if prev_stage_info and prev_stage_info.status == PipelineState.STATUS_COMPLETED:
                # Get output file
                output_file = prev_stage_info.output_file
                if output_file:
                    return self.stage_dir / output_file

        # Fallback: use raw file
        logger.warning(
            f"No previous completed stage found for {stage_name}, "
            f"falling back to raw file"
        )
        return self.raw_file_path
