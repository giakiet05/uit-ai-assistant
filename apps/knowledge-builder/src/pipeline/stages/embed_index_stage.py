"""
Embed & Index Stage - Embed chunks and index to ChromaDB.
"""

from pathlib import Path
from typing import Dict, Any
import json
import chromadb

from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState
from config.settings import settings

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings as LlamaSettings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo


class EmbedIndexStage(Stage):
    """
    Embed chunks and index to ChromaDB.

    Loads chunks from chunks.json, recreates LlamaIndex nodes,
    embeds them, and indexes to ChromaDB.

    Each category has its own ChromaDB collection.
    """

    def __init__(self):
        super().__init__(
            name="embed-index",
            is_costly=True,  # Uses OpenAI embeddings
            is_idempotent=True,  # Can safely rerun
            description="Embed chunks and index to ChromaDB"
        )
        self.chroma_client = None
        self.embed_model = None

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        state: PipelineState,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Embed and index chunks.

        Args:
            input_path: Not used (reads from chunks.json)
            output_path: Not used (indexes to ChromaDB)
            state: Pipeline state
            **kwargs: Additional arguments

        Returns:
            Metadata dict with indexing stats
        """
        # Initialize ChromaDB client if needed
        # Use a fresh client for each execution to avoid lock issues
        try:
            # Close existing client if any
            if self.chroma_client is not None:
                try:
                    del self.chroma_client
                except:
                    pass
            
            # Create fresh client
            self.chroma_client = chromadb.PersistentClient(
                path=str(settings.paths.VECTOR_STORE_DIR)
            )
        except Exception as e:
            # If still locked, try to use EphemeralClient as fallback
            raise ValueError(f"Failed to initialize ChromaDB: {e}. "
                           f"Try clearing vector store or restarting.")

        # Initialize embedding model if needed
        if self.embed_model is None:
            if not settings.credentials.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found")

            self.embed_model = OpenAIEmbedding(
                model=settings.indexing.EMBED_MODEL,
                api_key=settings.credentials.OPENAI_API_KEY
            )
            LlamaSettings.embed_model = self.embed_model

        # Load chunks from chunks.json
        chunks_file = state.doc_dir / "chunks.json"
        if not chunks_file.exists():
            raise ValueError(f"chunks.json not found at {chunks_file}")

        chunks_data = json.loads(chunks_file.read_text(encoding='utf-8'))

        # Recreate LlamaIndex nodes from serialized data
        nodes = []
        for chunk in chunks_data:
            # Sanitize metadata - ChromaDB only accepts str, int, float, None
            sanitized_metadata = {}
            for key, value in chunk['metadata'].items():
                if value is None:
                    sanitized_metadata[key] = None
                elif isinstance(value, (str, int, float)):
                    sanitized_metadata[key] = value
                elif isinstance(value, bool):
                    sanitized_metadata[key] = str(value)  # Convert bool to string
                elif isinstance(value, (list, tuple)):
                    # Convert list to comma-separated string
                    sanitized_metadata[key] = ", ".join(str(v) for v in value)
                elif isinstance(value, dict):
                    # Convert dict to JSON string
                    import json as json_module
                    sanitized_metadata[key] = json_module.dumps(value)
                else:
                    # Convert other types to string
                    sanitized_metadata[key] = str(value)
            
            # Recreate node
            node = TextNode(
                id_=chunk['id'],
                text=chunk['text'],
                metadata=sanitized_metadata,
                start_char_idx=chunk.get('start_char_idx'),
                end_char_idx=chunk.get('end_char_idx')
            )
            
            # Restore relationships if any
            if chunk.get('relationships'):
                for rel_type_str, rel_data in chunk['relationships'].items():
                    if rel_data.get('node_id'):
                        # Convert string back to NodeRelationship enum
                        # This is simplified - in practice you'd need proper enum mapping
                        node.relationships[rel_type_str] = RelatedNodeInfo(
                            node_id=rel_data['node_id']
                        )
            
            nodes.append(node)

        # Create/get ChromaDB collection
        collection_name = state.category
        chroma_collection = self.chroma_client.get_or_create_collection(collection_name)

        # Delete existing document from collection (if reindexing)
        # ChromaDB uses metadata filter to find and delete
        try:
            chroma_collection.delete(
                where={"document_id": state.document_id}
            )
        except Exception:
            pass  # Document doesn't exist yet, that's fine

        # Create vector store and storage context
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Build index from nodes (this embeds and indexes)
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
        )

        # Calculate approximate cost
        # OpenAI text-embedding-3-small: $0.02 / 1M tokens
        # Rough estimate: 1 chunk ≈ 200 tokens
        estimated_tokens = len(nodes) * 200
        estimated_cost = (estimated_tokens / 1_000_000) * 0.02

        # Return metadata
        return {
            "nodes_indexed": len(nodes),
            "collection": collection_name,
            "embed_model": settings.indexing.EMBED_MODEL,
            "cost": estimated_cost
        }
    
    def cleanup(self):
        """Clean up resources after execution."""
        if self.chroma_client is not None:
            try:
                # Close/delete client to release locks
                del self.chroma_client
                self.chroma_client = None
            except:
                pass

    def get_output_filename(self) -> str:
        """
        Embed-index stage doesn't produce a file.

        Returns None since output is in ChromaDB.
        """
        return None  # No file output, indexed to vector store
