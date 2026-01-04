"""
Chunk Stage - Parse markdown into chunks using RegulationNodeSplitter.
"""

from pathlib import Path
from typing import Dict, Any
import json

from ..core.stage import Stage
from ..core.pipeline_state import PipelineState
from ...indexing.splitters.regulation_node_splitter import RegulationNodeSplitter
from ...config.settings import settings
from llama_index.core import Document


class ChunkStage(Stage):
    """
    Parse markdown into chunks.

    Uses RegulationNodeSplitter to:
    - Detect Vietnamese patterns (Điều, CHƯƠNG)
    - Merge title chunks
    - Clean malformed headers
    - Sub-chunk large sections

    Output is saved as chunks.json with serialized nodes.
    """

    def __init__(self):
        super().__init__(
            name="chunk",
            is_costly=False,
            is_idempotent=True,
            description="Parse markdown into chunks"
        )
        self.node_splitter = None

    def should_skip(self, state, input_path, force):
        """
        Override: Always rerun chunk stage (chunks.json is for debugging only).

        Returns:
            (False, "always_rerun") - never skip
        """
        return False, "always_rerun"

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Parse markdown into chunks.

        Args:
            input_path: Path to final markdown (05-fixed.md)
            output_path: Path to save chunks (not used, chunks saved as chunks.json)
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict with chunk stats
        """
        # Initialize splitter if needed
        if self.node_splitter is None:
            self.node_splitter = RegulationNodeSplitter(
                max_tokens=settings.indexing.MAX_TOKENS,
                sub_chunk_size=settings.indexing.CHUNK_SIZE,
                sub_chunk_overlap=settings.indexing.CHUNK_OVERLAP
            )

        # Read markdown content
        content = input_path.read_text(encoding='utf-8')

        # Load metadata if exists
        metadata_file = state.doc_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"[WARNING] Failed to load metadata: {e}")

        # Flatten metadata for ChromaDB (only str, int, float, None allowed)
        flat_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, type(None))):
                flat_metadata[key] = value
            elif isinstance(value, list):
                # Convert list to comma-separated string
                flat_metadata[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Skip nested dicts (or flatten if needed)
                continue
            else:
                # Convert other types to string
                flat_metadata[key] = str(value)

        # Add category to metadata
        flat_metadata['category'] = state.category
        flat_metadata['document_id'] = state.document_id

        metadata = flat_metadata

        # Create LlamaIndex Document
        doc = Document(
            text=content,
            metadata=metadata,
            id_=state.document_id
        )

        # Parse to nodes
        nodes = self.node_splitter.get_nodes_from_documents([doc])

        # Serialize nodes to JSON-compatible format
        serialized_chunks = []
        for node in nodes:
            # Convert node to dict
            node_dict = node.dict()
            
            # Extract essential fields for storage
            chunk_data = {
                'id': node.node_id,
                'text': node.text,
                'metadata': node.metadata,
                'start_char_idx': node.start_char_idx,
                'end_char_idx': node.end_char_idx,
                'relationships': {}
            }
            
            # Store relationships (if any)
            if hasattr(node, 'relationships') and node.relationships:
                for rel_type, rel_node in node.relationships.items():
                    chunk_data['relationships'][str(rel_type)] = {
                        'node_id': rel_node.node_id if hasattr(rel_node, 'node_id') else None
                    }
            
            serialized_chunks.append(chunk_data)

        # Save to chunks.json
        chunks_file = state.doc_dir / "chunks.json"
        chunks_file.write_text(
            json.dumps(serialized_chunks, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Get stats from splitter
        stats = {}
        if hasattr(self.node_splitter, 'get_stats'):
            stats = self.node_splitter.get_stats()

        # Return metadata
        return {
            "chunks_generated": len(serialized_chunks),
            "chunks_file": "chunks.json",
            "splitter_stats": stats
        }

    def get_output_filename(self) -> str:
        """
        Chunk stage doesn't produce a markdown file.

        Returns None since output is chunks.json, not a markdown file.
        """
        return None  # No markdown output, only chunks.json
