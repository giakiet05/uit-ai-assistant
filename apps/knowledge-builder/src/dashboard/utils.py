"""
Utility functions for dashboard.

NOTE: Uses absolute imports because dashboard is run by Streamlit as a script.
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add src to path for absolute imports
_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from config.settings import settings
from pipeline.core.pipeline_state import PipelineState


def get_categories() -> List[str]:
    """Get all categories from stages directory."""
    stages_dir = settings.paths.STAGES_DIR
    if not stages_dir.exists():
        return []

    return [d.name for d in stages_dir.iterdir() if d.is_dir()]


def get_documents(category: str) -> List[str]:
    """Get all documents in a category."""
    category_dir = settings.paths.STAGES_DIR / category
    if not category_dir.exists():
        return []

    return [d.name for d in category_dir.iterdir() if d.is_dir()]


def get_document_status(category: str, document_id: str) -> Optional[Dict]:
    """Get pipeline status for a document."""
    state = PipelineState.load(category, document_id)

    if state is None or not state.stages:
        return None

    return {
        'category': category,
        'document_id': document_id,
        'status': state.get_status_summary(),
        'total_cost': state.get_total_cost(),
        'stages': [
            {
                'name': stage.name,
                'status': stage.status,
                'cost': stage.cost,
                'locked': stage.manually_edited,
                'output_file': stage.output_file
            }
            for stage in state.stages
        ],
        'migrated': state.migrated_from_legacy
    }


def format_cost(cost: float) -> str:
    """Format cost in dollars."""
    if cost == 0:
        return "-"
    return f"${cost:.4f}"


def get_stage_emoji(status: str) -> str:
    """Get emoji for stage status."""
    return {
        'completed': '✅',
        'failed': '❌',
        'skipped': '⏭️',
        'rejected': '🚫',
        'in_progress': '⏳',
        'pending': '⬜'
    }.get(status, '❓')


def get_chunks_count(category: str, document_id: str) -> int:
    """Get number of chunks for a document."""
    doc_dir = settings.paths.STAGES_DIR / category / document_id
    chunks_file = doc_dir / "chunks.json"

    if not chunks_file.exists():
        return 0

    import json
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    return len(chunks)


def get_all_documents_status() -> List[Dict]:
    """Get status for all documents across all categories."""
    all_status = []

    for category in get_categories():
        for document_id in get_documents(category):
            status = get_document_status(category, document_id)
            if status:
                all_status.append(status)

    return all_status
