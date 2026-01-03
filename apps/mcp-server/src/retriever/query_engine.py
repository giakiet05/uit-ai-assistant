"""
QueryEngine - Orchestrates blended retrieval and re-ranking.

This engine uses a blended retrieval approach:
1. Retrieves from multiple indexes (dense vector, BM25, sparse vector)
2. Merges and deduplicates results
3. Re-ranks with a reranker model
4. Returns top-k most relevant documents

Design Philosophy:
- Blended: Always query all available indexes and merge results
- Modular: Easy to add new retrieval methods
- Composable: Can be used as MCP tool or standalone
- Configurable: All parameters tunable via settings
"""

import unicodedata
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

from .program_filter import apply_program_filter
from .schemas import (
    RegulationDocument,
    CurriculumDocument,
    RegulationRetrievalResult,
    CurriculumRetrievalResult
)


def normalize_vietnamese_text(text: str) -> str:
    """
    Normalize Vietnamese text to NFC form.

    This fixes Unicode normalization issues where the same Vietnamese character
    can be represented in different ways:
    - NFC (composed): 'ó' as single character U+00F3
    - NFD (decomposed): 'ó' as 'o' U+006F + combining acute U+0301

    Example:
        'Khóa' (NFC) vs 'Khoá' (NFD) - same visual, different bytes

    Args:
        text: Input text (may be in NFC or NFD form)

    Returns:
        Normalized text in NFC form (composed)
    """
    return unicodedata.normalize('NFC', text)


@dataclass
class RetrievalResult:
    """Result from retrieval + reranking."""
    nodes: List[NodeWithScore]
    retrieval_method: str
    reranked: bool
    total_retrieved: int
    final_count: int


class QueryEngine:
    """
    Main query engine that orchestrates blended retrieval.

    Blended retrieval: Always queries all available indexes and merges results.

    Current support:
    - Dense vector retrieval (OpenAI embeddings)

    Future support (will be automatically included in blended retrieval):
    - BM25 lexical search
    - Sparse vector retrieval (SPLADE)
    """

    def __init__(
        self,
        collections: Dict[str, VectorStoreIndex],
        use_reranker: bool = True,
        reranker_model: Optional[str] = None,
        top_k: int = 3,
        retrieval_top_k: int = 20,  # Retrieve more, then rerank
        rerank_score_threshold: float = 0.7,  # Filter out low-confidence results after reranking
        min_score_threshold: float = 0.25,  # Minimum score for initial retrieval
        use_modal: bool = False  # Use Modal GPU for reranking (faster)
    ):
        """
        Initialize QueryEngine.

        Args:
            collections: Dict of collection_name -> VectorStoreIndex
            use_reranker: Whether to use reranker after retrieval
            reranker_model: Reranker model name (default: "namdp-ptit/ViRanker" for Vietnamese)
            top_k: Final number of documents to return
            retrieval_top_k: Number of documents to retrieve before reranking
            rerank_score_threshold: Minimum score threshold after reranking (default: 0.4)
                                   Nodes with score < threshold will be filtered out
            min_score_threshold: Minimum score for initial retrieval (default: 0.25)
            use_modal: Use Modal GPU for reranking (default: False, use local CPU)
        """
        self.collections = collections
        self.use_reranker = use_reranker
        self.reranker_model = reranker_model or "namdp-ptit/ViRanker"
        self.top_k = top_k
        self.retrieval_top_k = retrieval_top_k
        self.rerank_score_threshold = rerank_score_threshold
        self.min_score_threshold = min_score_threshold
        self.use_modal = use_modal

        # Initialize reranker if enabled
        if self.use_reranker:
            if self.use_modal:
                self._setup_modal_reranker()
            else:
                self._setup_local_reranker()

        print(f"[QUERY ENGINE] Initialized with:")
        print(f"  - Collections: {list(collections.keys())}")
        reranker_mode = "Modal GPU" if use_modal else "Local CPU"
        print(f"  - Reranker: {self.reranker_model if use_reranker else 'disabled'} ({reranker_mode})")
        print(f"  - Retrieval top_k: {retrieval_top_k}")
        print(f"  - Final top_k: {top_k}")
        print(f"  - Min score threshold: {min_score_threshold}")
        print(f"  - Rerank score threshold: {rerank_score_threshold}")


    def _setup_local_reranker(self):
        """
        Local reranker is no longer supported (removed FlagEmbedding dependency).
        Use Modal GPU reranker instead.
        """
        raise RuntimeError(
            "Local reranker not available. FlagEmbedding dependency removed to reduce Docker image size.\n"
            "Please use Modal GPU reranker by setting use_modal=True.\n"
            "Deploy the Modal reranker with: modal deploy modal/reranker_service.py"
        )

    def _setup_modal_reranker(self):
        """Setup Modal reranker (ViRanker on GPU via HTTP endpoint)."""
        from src.config.settings import settings

        self.modal_reranker_url = settings.retrieval.MODAL_RERANKER_URL
        print(f"[RERANKER] Using Modal HTTP endpoint: {self.modal_reranker_url}")
        print(f"[RERANKER] Modal reranker configured successfully")

    def _retrieve(
        self,
        query: str,
        collection_type: Literal["regulation", "curriculum"],
        use_reranker: Optional[bool] = None
    ) -> RetrievalResult:
        """
        Blended retrieval from specified collection with reranking.

        Pipeline:
        1. Dense vector retrieval from specified collection
        2. BM25 retrieval (TODO)
        3. Sparse vector retrieval (TODO)
        4. Merge & deduplicate
        5. Rerank
        6. Return top-k

        Args:
            query: User query string
            collection_type: Collection to retrieve from ("regulation" or "curriculum")
            use_reranker: Override default reranker setting

        Returns:
            RetrievalResult with retrieved and reranked nodes
        """
        # Normalize query text (fix Unicode normalization issues)
        query = normalize_vietnamese_text(query)

        print(f"\n{'='*70}")
        print(f"[QUERY ENGINE] Blended Retrieval")
        print(f"[QUERY ENGINE] Query (normalized): {query}")
        print(f"[QUERY ENGINE] Collection: {collection_type}")
        print(f"{'='*70}\n")

        # Get specified collection
        selected_collection = self.collections[collection_type]

        # Step 1: Retrieve from collection
        all_nodes = []

        # Dense vector retrieval
        print("[QUERY ENGINE] Retrieving from dense vector index...")
        dense_nodes = self._retrieve_dense(query, selected_collection)
        all_nodes.extend(dense_nodes)
        print(f"  → Found {len(dense_nodes)} nodes")

        # BM25 retrieval (TODO)
        # Sparse vector retrieval (TODO)

        # Step 2: Deduplicate & merge
        print(f"\n[QUERY ENGINE] Merging {len(all_nodes)} nodes...")
        merged_nodes = self._deduplicate_nodes(all_nodes)
        print(f"  → After deduplication: {len(merged_nodes)} nodes")

        # Step 3: Sort by score
        merged_nodes.sort(key=lambda x: x.score, reverse=True)

        # Take top retrieval_top_k before reranking
        top_nodes = merged_nodes[:self.retrieval_top_k]
        total_retrieved = len(top_nodes)
        print(f"[QUERY ENGINE] Top {total_retrieved} nodes selected for reranking")

        # Step 4: Rerank if enabled
        should_rerank = use_reranker if use_reranker is not None else self.use_reranker

        if should_rerank and total_retrieved > 0:
            top_nodes = self._rerank(query, top_nodes)
            reranked = True
        else:
            reranked = False

        # Step 5: Final top-k
        final_nodes = top_nodes[:self.top_k]

        print(f"[QUERY ENGINE] Final result: {len(final_nodes)} nodes (reranked: {reranked})\n")

        return RetrievalResult(
            nodes=final_nodes,
            retrieval_method=f"blended_{collection_type}",
            reranked=reranked,
            total_retrieved=total_retrieved,
            final_count=len(final_nodes)
        )

    def _retrieve_dense(
        self,
        query: str,
        collection: VectorStoreIndex
    ) -> List[NodeWithScore]:
        """
        Retrieve using dense vector embeddings from specified collection.

        Args:
            query: User query
            collection: Collection index to retrieve from

        Returns:
            List of retrieved nodes
        """
        # Retrieve from collection
        print(f"[RETRIEVER] Querying dense vector index...")
        retriever = collection.as_retriever(similarity_top_k=self.retrieval_top_k)
        nodes = retriever.retrieve(query)
        print(f"[RETRIEVER] Found {len(nodes)} nodes")

        # Filter by minimum score threshold
        filtered_nodes = [
            node for node in nodes
            if node.score >= self.min_score_threshold
        ]

        if len(filtered_nodes) < len(nodes):
            print(f"[RETRIEVER] Filtered {len(nodes) - len(filtered_nodes)} nodes (score < {self.min_score_threshold})")

        return filtered_nodes

    def _retrieve_bm25(self, query: str) -> List[NodeWithScore]:
        """Retrieve using BM25 lexical search."""
        # TODO: Implement BM25 retrieval
        # return self.bm25_retriever.retrieve(query)
        return []

    def _retrieve_sparse(self, query: str) -> List[NodeWithScore]:
        """Retrieve using sparse vector (SPLADE)."""
        # TODO: Implement sparse vector retrieval
        # return self.sparse_retriever.retrieve(query)
        return []

    def _deduplicate_nodes(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """
        Deduplicate nodes by node ID.

        When the same chunk is retrieved from multiple indexes (e.g., dense + BM25),
        keep only the node with the highest score.

        Args:
            nodes: List of retrieved nodes

        Returns:
            Deduplicated list of nodes
        """
        node_map = {}

        for node in nodes:
            node_id = node.node.node_id

            if node_id not in node_map:
                node_map[node_id] = node
            else:
                # Keep node with higher score
                if node.score > node_map[node_id].score:
                    node_map[node_id] = node

        return list(node_map.values())

    def _rerank(self, query: str, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """
        Rerank nodes using ViRanker (Vietnamese reranking model).

        Supports both local CPU and Modal GPU modes.

        Args:
            query: User query
            nodes: Retrieved nodes

        Returns:
            Reranked nodes (sorted by reranker score, filtered by threshold)
        """
        if not self.use_reranker:
            return nodes

        # Check if reranker is available (local or Modal)
        if self.use_modal:
            if not hasattr(self, 'modal_reranker_url'):
                print("[WARNING] Modal reranker URL not configured, skipping reranking")
                return nodes
        else:
            if not hasattr(self, 'reranker'):
                print("[WARNING] Local reranker not initialized, skipping reranking")
                return nodes

        print(f"[RERANKER] Reranking {len(nodes)} nodes with ViRanker...")

        # Prepare texts for reranker
        texts = [node.node.get_content() for node in nodes]

        # Get reranker scores
        if self.use_modal:
            # Modal GPU reranking via HTTP endpoint
            print(f"[RERANKER] Using Modal GPU (this may take 10-60s on cold start)...")
            try:
                import requests

                # Call HTTP endpoint with longer timeout for cold start
                # Cold start: ~10-60s (first request after idle)
                # Warm: ~1-3s (subsequent requests)
                response = requests.post(
                    self.modal_reranker_url,
                    json={
                        "query": query,
                        "texts": texts,
                        "normalize": True
                    },
                    timeout=120  # 2 minutes to handle cold start
                )
                response.raise_for_status()
                scores = response.json()["scores"]
                print(f"[RERANKER] Modal GPU reranking completed")

            except requests.exceptions.Timeout:
                print(f"[WARNING] Modal reranking timed out (cold start can take 60s+)")
                print("           Skipping reranking for this query")
                return nodes
            except Exception as e:
                print(f"[WARNING] Modal reranking failed: {e}")
                print("           No local reranker available, skipping reranking")
                return nodes
        else:
            # Local CPU reranking
            print(f"[RERANKER] Using local CPU...")
            pairs = [[query, text] for text in texts]
            scores = self.reranker.compute_score(pairs, normalize=True)

            # Handle single score vs list
            if not isinstance(scores, list):
                scores = [scores]

        # Update node scores and sort
        for node, score in zip(nodes, scores):
            node.score = float(score)

        nodes.sort(key=lambda x: x.score, reverse=True)

        # Print top 3 scores for debugging
        print(f"[RERANKER] Top 3 scores:")
        for i, node in enumerate(nodes[:3]):
            doc_id = node.node.metadata.get('document_id', 'unknown')
            print(f"  {i+1}. Score: {node.score:.4f} | Doc: {doc_id[:60]}...")

        # Filter out low-confidence results based on threshold
        filtered_nodes = [node for node in nodes if node.score >= self.rerank_score_threshold]

        if len(filtered_nodes) < len(nodes):
            print(f"[RERANKER] Filtered {len(nodes) - len(filtered_nodes)} low-confidence results (score < {self.rerank_score_threshold})")

        if len(filtered_nodes) > 0:
            print(f"[RERANKER] Reranking complete. Top score: {filtered_nodes[0].score:.4f}, kept {len(filtered_nodes)}/{len(nodes)} nodes")
        else:
            print(f"[RERANKER] Warning: All results filtered out (all scores < {self.rerank_score_threshold})")

        # ========== POST-FILTERING BY PROGRAM ==========
        # Apply program-based filtering to avoid confusion between similar majors
        # e.g., "Khoa học Máy tính" vs "Kỹ thuật Máy tính"
        filtered_nodes = apply_program_filter(query, filtered_nodes)

        return filtered_nodes

    def _strip_metadata_from_content(self, content: str) -> str:
        """
        Remove prepended metadata from content.

        During indexing, metadata is prepended to content for better semantic search.
        Format:
            Tài liệu: xxx
            Tiêu đề: xxx
            Cấu trúc: xxx
            Ngày hiệu lực: xxx
            Loại: xxx
            ---
            [Actual content starts here]

        This method strips the metadata part, returning only the actual content.

        Args:
            content: Raw content with prepended metadata

        Returns:
            Clean content without metadata
        """
        # Split by separator "---"
        if "---" in content:
            parts = content.split("---", 1)
            if len(parts) == 2:
                return parts[1].strip()

        # Fallback: if no separator found, return original content
        # (handles edge cases where metadata wasn't prepended)
        return content

    def retrieve_structured(
        self,
        query: str,
        collection_type: Literal["regulation", "curriculum"]
    ) -> Dict:
        """
        Retrieve and return structured format with separated metadata fields.

        This method replaces retrieve_with_metadata() for new tools.
        It returns a structured JSON with:
        - Clean content (metadata stripped)
        - Separated metadata fields (document_id, title, hierarchy, etc.)

        Args:
            query: User query
            collection_type: Type of collection ("regulation" or "curriculum")

        Returns:
            Dict following RegulationRetrievalResult or CurriculumRetrievalResult schema
        """
        # Retrieve nodes using existing pipeline
        result = self._retrieve(query, collection_type=collection_type)

        # Build structured documents based on collection type
        documents = []

        for node in result.nodes:
            metadata = node.node.metadata
            raw_content = node.node.get_content()

            # Strip prepended metadata from content
            clean_content = self._strip_metadata_from_content(raw_content)

            if collection_type == "regulation":
                # Build RegulationDocument
                doc_dict = {
                    "content": clean_content,
                    "document_id": metadata.get("document_id", ""),
                    "title": metadata.get("title", ""),
                    "regulation_code": metadata.get("regulation_code"),
                    "hierarchy": metadata.get("hierarchy", ""),
                    "effective_date": metadata.get("effective_date"),
                    "document_type": metadata.get("document_type", "Văn bản gốc"),
                    "score": round(float(node.score), 2)
                }
                # Validate with Pydantic
                doc = RegulationDocument(**doc_dict)
                documents.append(doc.model_dump())

            elif collection_type == "curriculum":
                # Build CurriculumDocument
                doc_dict = {
                    "content": clean_content,
                    "document_id": metadata.get("document_id", ""),
                    "title": metadata.get("title", ""),
                    "year": metadata.get("year"),
                    "major": metadata.get("major"),
                    "program_type": metadata.get("program_type"),
                    "program_name": metadata.get("program_name"),
                    "score": round(float(node.score), 2)
                }
                # Validate with Pydantic
                doc = CurriculumDocument(**doc_dict)
                documents.append(doc.model_dump())

        # Build result based on collection type
        if collection_type == "regulation":
            result_obj = RegulationRetrievalResult(
                query=query,
                total_retrieved=len(documents),
                documents=documents
            )
        else:  # curriculum
            result_obj = CurriculumRetrievalResult(
                query=query,
                total_retrieved=len(documents),
                documents=documents
            )

        return result_obj.model_dump()
