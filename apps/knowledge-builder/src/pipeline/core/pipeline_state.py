"""
Pipeline State Tracking - Manage document processing state.

Tracks which stages have been completed, stores metadata about each stage execution,
and provides incremental execution capabilities.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class StageInfo:
    """Information about a single stage execution."""

    def __init__(
        self,
        name: str,
        status: str,
        timestamp: Optional[str] = None,
        input_hash: Optional[str] = None,
        output_file: Optional[str] = None,
        cost: float = 0.0,
        manually_edited: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize stage info.

        Args:
            name: Stage name (parse, clean, normalize, etc.)
            status: Stage status (pending, in_progress, completed, failed, skipped, rejected)
            timestamp: ISO format timestamp of completion
            input_hash: Hash of input content (for change detection)
            output_file: Output filename (e.g., "02-cleaned.md")
            cost: Cost in USD for this stage
            manually_edited: If True, prevent overwrite
            metadata: Additional stage-specific metadata
        """
        self.name = name
        self.status = status
        self.timestamp = timestamp or datetime.now().isoformat()
        self.input_hash = input_hash
        self.output_file = output_file
        self.cost = cost
        self.manually_edited = manually_edited
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "name": self.name,
            "status": self.status,
            "timestamp": self.timestamp,
            "input_hash": self.input_hash,
            "output_file": self.output_file,
            "cost": self.cost,
            "manually_edited": self.manually_edited,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageInfo":
        """Deserialize from dict."""
        return cls(
            name=data["name"],
            status=data["status"],
            timestamp=data.get("timestamp"),
            input_hash=data.get("input_hash"),
            output_file=data.get("output_file"),
            cost=data.get("cost", 0.0),
            manually_edited=data.get("manually_edited", False),
            metadata=data.get("metadata", {})
        )


class PipelineState:
    """
    Pipeline state tracker for a single document.

    Manages:
    - Stage completion tracking
    - Input/output file paths
    - Change detection (via hashing)
    - Manual edit protection (locking)
    - Cost tracking

    Usage:
        >>> state = PipelineState.load("regulation", "790-qd-dhcntt")
        >>> state.add_stage("parse", "completed", output_file="01-parsed.md", cost=0.05)
        >>> state.save()
        >>>
        >>> if state.is_completed("parse"):
        ...     print("Parse already done!")
    """

    # Valid stage statuses
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_SKIPPED = "skipped"
    STATUS_REJECTED = "rejected"

    def __init__(
        self,
        document_id: str,
        category: str,
        source_file: Optional[str] = None,
        stages_dir: Optional[Path] = None
    ):
        """
        Initialize pipeline state.

        Args:
            document_id: Document ID (e.g., "790-qd-dhcntt")
            category: Category (e.g., "regulation")
            source_file: Original source file path
            stages_dir: Base stages directory (default: data/stages)
        """
        self.document_id = document_id
        self.category = category
        self.source_file = source_file

        # Determine stages directory
        if stages_dir is None:
            from ...config.settings import settings
            stages_dir = settings.paths.STAGES_DIR

        self.stages_dir = Path(stages_dir)
        self.doc_dir = self.stages_dir / category / document_id
        self.state_file = self.doc_dir / ".pipeline.json"

        # State data
        self.stages: List[StageInfo] = []
        self.current_stage: Optional[str] = None
        self.final_output: Optional[str] = None
        self.migrated_from_legacy: bool = False
        self.metadata: Dict[str, Any] = {}

    def add_stage(
        self,
        name: str,
        status: str,
        output_file: Optional[str] = None,
        input_hash: Optional[str] = None,
        cost: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add or update a stage.

        Args:
            name: Stage name
            status: Stage status
            output_file: Output filename
            input_hash: Hash of input content
            cost: Cost in USD
            metadata: Additional metadata
        """
        # Check if stage already exists
        existing = self.get_stage(name)
        if existing:
            # Update existing stage
            existing.status = status
            existing.timestamp = datetime.now().isoformat()
            existing.output_file = output_file or existing.output_file
            existing.input_hash = input_hash or existing.input_hash
            existing.cost = cost
            if metadata:
                existing.metadata.update(metadata)
        else:
            # Add new stage
            stage_info = StageInfo(
                name=name,
                status=status,
                timestamp=datetime.now().isoformat(),
                input_hash=input_hash,
                output_file=output_file,
                cost=cost,
                metadata=metadata
            )
            self.stages.append(stage_info)

        # Update current stage if completed
        if status == self.STATUS_COMPLETED:
            self.current_stage = name
            if output_file:
                self.final_output = output_file

    def get_stage(self, name: str) -> Optional[StageInfo]:
        """Get stage info by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def is_completed(self, name: str) -> bool:
        """Check if stage is completed."""
        stage = self.get_stage(name)
        return stage is not None and stage.status == self.STATUS_COMPLETED

    def is_locked(self, name: str) -> bool:
        """Check if stage is locked (manually edited)."""
        stage = self.get_stage(name)
        return stage is not None and stage.manually_edited

    def lock_stage(self, name: str) -> None:
        """Lock a stage to prevent overwrite."""
        stage = self.get_stage(name)
        if stage:
            stage.manually_edited = True

    def unlock_stage(self, name: str) -> None:
        """Unlock a stage to allow overwrite."""
        stage = self.get_stage(name)
        if stage:
            stage.manually_edited = False

    def get_output_path(self, stage_name: str) -> Optional[Path]:
        """Get output file path for a stage."""
        stage = self.get_stage(stage_name)
        if stage and stage.output_file:
            return self.doc_dir / stage.output_file
        return None

    def get_total_cost(self) -> float:
        """Calculate total cost across all stages."""
        return sum(stage.cost for stage in self.stages)

    def needs_rerun(self, stage_name: str, input_content: str) -> bool:
        """
        Check if stage needs to be rerun based on input hash.

        Args:
            stage_name: Stage to check
            input_content: Current input content

        Returns:
            True if stage needs rerun
        """
        stage = self.get_stage(stage_name)
        if not stage:
            return True  # Not run yet

        if stage.status != self.STATUS_COMPLETED:
            return True  # Not completed

        if stage.manually_edited:
            return False  # Locked, don't rerun

        # Check input hash
        if stage.input_hash:
            current_hash = self._compute_hash(input_content)
            return current_hash != stage.input_hash

        return False  # No hash, assume no change

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def save(self) -> None:
        """Save state to .pipeline.json."""
        self.doc_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "document_id": self.document_id,
            "category": self.category,
            "source_file": self.source_file,
            "stages": [stage.to_dict() for stage in self.stages],
            "current_stage": self.current_stage,
            "final_output": self.final_output,
            "migrated_from_legacy": self.migrated_from_legacy,
            "metadata": self.metadata
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(
        cls,
        category: str,
        document_id: str,
        stages_dir: Optional[Path] = None
    ) -> "PipelineState":
        """
        Load state from .pipeline.json.

        Args:
            category: Document category
            document_id: Document ID
            stages_dir: Base stages directory

        Returns:
            PipelineState instance
        """
        state = cls(document_id, category, stages_dir=stages_dir)

        if not state.state_file.exists():
            return state  # Return empty state

        with open(state.state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        state.source_file = data.get("source_file")
        state.stages = [StageInfo.from_dict(s) for s in data.get("stages", [])]
        state.current_stage = data.get("current_stage")
        state.final_output = data.get("final_output")
        state.migrated_from_legacy = data.get("migrated_from_legacy", False)
        state.metadata = data.get("metadata", {})

        return state

    @classmethod
    def exists(cls, category: str, document_id: str, stages_dir: Optional[Path] = None) -> bool:
        """Check if pipeline state exists for document."""
        state = cls(document_id, category, stages_dir=stages_dir)
        return state.state_file.exists()

    def get_status_summary(self) -> str:
        """
        Get human-readable status summary.

        Returns:
            String like "[x] parse -> [x] clean -> [FAIL] normalize -> [FAIL] filter"
        """
        stage_names = ["parse", "clean", "normalize", "filter", "fix-markdown", "metadata"]
        parts = []

        for name in stage_names:
            stage = self.get_stage(name)
            if not stage:
                symbol = "[ ]"  # Not started
            elif stage.status == self.STATUS_COMPLETED:
                symbol = "[x]"
            elif stage.status == self.STATUS_FAILED:
                symbol = "[FAIL]"
            elif stage.status == self.STATUS_SKIPPED:
                symbol = "[SKIP]"
            elif stage.status == self.STATUS_REJECTED:
                symbol = "[REJ]"
            elif stage.status == self.STATUS_IN_PROGRESS:
                symbol = "[...]"
            else:
                symbol = "[ ]"

            parts.append(f"{symbol} {name}")

        return " -> ".join(parts)
