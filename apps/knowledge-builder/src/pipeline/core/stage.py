"""
Stage Base Class - Abstract base for pipeline stages.

All processing and indexing stages inherit from this base class.
"""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from pipeline.core.pipeline_state import PipelineState


class Stage(ABC):
    """
    Abstract base class for pipeline stages.

    Each stage:
    - Takes input file(s)
    - Produces output file(s)
    - Updates pipeline state
    - Tracks cost
    - Supports incremental execution (skip if already done)

    Subclasses must implement:
    - execute(): Core processing logic
    - get_output_filename(): Output file naming

    Usage:
        >>> class ParseStage(Stage):
        ...     def execute(self, input_path, output_path):
        ...         # Parse PDF to markdown
        ...         content = parse_pdf(input_path)
        ...         output_path.write_text(content)
        ...         return {"pages": 10}
        ...
        ...     def get_output_filename(self):
        ...         return "01-parsed.md"
        >>>
        >>> stage = ParseStage("parse", is_costly=True)
        >>> stage.run(state, input_path="/path/to/file.pdf")
    """

    def __init__(
        self,
        name: str,
        is_costly: bool = False,
        is_idempotent: bool = True,
        description: str = ""
    ):
        """
        Initialize stage.

        Args:
            name: Stage name (parse, clean, normalize, etc.)
            is_costly: True if stage costs money (API calls)
            is_idempotent: True if safe to run multiple times
            description: Human-readable description
        """
        self.name = name
        self.is_costly = is_costly
        self.is_idempotent = is_idempotent
        self.description = description

    @abstractmethod
    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute stage processing.

        Args:
            input_path: Path to input file
            output_path: Path where output should be written
            state: Pipeline state tracker
            **kwargs: Additional stage-specific arguments

        Returns:
            Metadata dict (will be stored in pipeline state)

        Raises:
            Exception: If processing fails
        """
        pass

    @abstractmethod
    def get_output_filename(self) -> str:
        """
        Get output filename for this stage.

        Returns:
            Filename like "01-parsed.md", "02-cleaned.md", etc.
        """
        pass

    def validate_input(self, input_path: Path) -> bool:
        """
        Validate input file before processing.

        Args:
            input_path: Input file path

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if not input_path.exists():
            raise ValueError(f"Input file not found: {input_path}")

        if input_path.stat().st_size == 0:
            raise ValueError(f"Input file is empty: {input_path}")

        return True

    def should_skip(
        self,
        state: PipelineState,
        input_path: Path,
        force: bool = False
    ) -> tuple[bool, str]:
        """
        Check if stage should be skipped.

        Args:
            state: Pipeline state
            input_path: Input file path
            force: Force re-run even if completed

        Returns:
            (should_skip: bool, reason: str)
        """
        # Force flag always runs
        if force:
            return False, "force_flag"

        # Check if stage completed
        if not state.is_completed(self.name):
            return False, "not_completed"

        # Check if locked (manually edited)
        if state.is_locked(self.name):
            return True, "locked_manual_edit"

        # Check if input changed (via hash)
        if input_path.exists():
            input_content = input_path.read_text(encoding='utf-8')
            if state.needs_rerun(self.name, input_content):
                return False, "input_changed"

        # Skip - already completed and no changes
        return True, "already_completed"

    def compute_hash(self, content: str) -> str:
        """
        Compute hash of content for change detection.

        Args:
            content: Text content

        Returns:
            SHA256 hash (truncated to 16 chars)
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def run(
        self,
        state: PipelineState,
        input_path: Path,
        force: bool = False,
        **kwargs
    ) -> bool:
        """
        Run stage with state management.

        Args:
            state: Pipeline state tracker
            input_path: Input file path
            force: Force re-run
            **kwargs: Stage-specific arguments

        Returns:
            True if stage executed, False if skipped

        Raises:
            Exception: If processing fails
        """
        # Check if should skip
        should_skip, reason = self.should_skip(state, input_path, force)
        if should_skip:
            print(f"    [SKIP] {self.name}: {reason}")
            return False

        # Warn if costly and not force
        if self.is_costly and not force and state.is_completed(self.name):
            print(f"    [WARNING] Re-running costly stage: {self.name} (use --force to confirm)")

        # Validate input
        self.validate_input(input_path)

        # Prepare output path
        output_filename = self.get_output_filename()
        if output_filename:
            output_path = state.doc_dir / output_filename
        else:
            # Some stages don't produce file output (e.g., embed-index stage)
            output_path = state.doc_dir / ".dummy_output"

        # Mark as in progress
        state.add_stage(self.name, PipelineState.STATUS_IN_PROGRESS)
        state.save()

        try:
            # Compute input hash
            input_content = input_path.read_text(encoding='utf-8')
            input_hash = self.compute_hash(input_content)

            # Execute stage
            print(f"   [{self.name.upper()}] Processing...")
            metadata = self.execute(input_path, output_path, state, **kwargs)

            # Mark as completed
            state.add_stage(
                self.name,
                PipelineState.STATUS_COMPLETED,
                output_file=output_filename,
                input_hash=input_hash,
                cost=metadata.get("cost", 0.0),
                metadata=metadata
            )
            state.save()

            print(f"   [{self.name.upper()}] Completed -> {output_filename}")
            return True

        except Exception as e:
            # Mark as failed
            state.add_stage(
                self.name,
                PipelineState.STATUS_FAILED,
                metadata={"error": str(e)}
            )
            state.save()

            print(f"   [{self.name.upper()}] Failed: {e}")
            raise

    def get_input_path(self, state: PipelineState, previous_stage: Optional[str] = None) -> Path:
        """
        Get input file path for this stage.

        Args:
            state: Pipeline state
            previous_stage: Name of previous stage (to get its output)

        Returns:
            Path to input file
        """
        if previous_stage:
            # Get output of previous stage
            prev_output = state.get_output_path(previous_stage)
            if prev_output and prev_output.exists():
                return prev_output

        # Fallback: use final output or first available output
        if state.final_output:
            path = state.doc_dir / state.final_output
            if path.exists():
                return path

        # Find first completed stage output
        for stage_info in state.stages:
            if stage_info.status == PipelineState.STATUS_COMPLETED and stage_info.output_file:
                path = state.doc_dir / stage_info.output_file
                if path.exists():
                    return path

        raise FileNotFoundError(f"No input file found for stage: {self.name}")
