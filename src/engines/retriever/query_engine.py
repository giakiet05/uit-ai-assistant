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

from typing import List, Dict, Optional
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.config.settings import settings
from src.engines.retriever.multi_collection_retriever import MultiCollectionRetriever


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
        top_k: int = 5,
        retrieval_top_k: int = 20,  # Retrieve more, then rerank
        rerank_score_threshold: float = 0.4  # Filter out low-confidence results after reranking
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
        """
        self.collections = collections
        self.use_reranker = use_reranker
        self.reranker_model = reranker_model or "namdp-ptit/ViRanker"
        self.top_k = top_k
        self.retrieval_top_k = retrieval_top_k
        self.rerank_score_threshold = rerank_score_threshold

        # Initialize retrievers
        self._setup_retrievers()

        # Initialize reranker if enabled
        if self.use_reranker:
            self._setup_reranker()

        print(f"[QUERY ENGINE] Initialized with:")
        print(f"  - Collections: {list(collections.keys())}")
        print(f"  - Reranker: {self.reranker_model if use_reranker else 'disabled'}")
        print(f"  - Retrieval top_k: {retrieval_top_k}")
        print(f"  - Final top_k: {top_k}")
        print(f"  - Rerank score threshold: {rerank_score_threshold}")

    def _setup_retrievers(self):
        """Setup retrieval methods."""
        # Dense vector retriever (current)
        self.dense_retriever = MultiCollectionRetriever(
            collections=self.collections,
            top_k=self.retrieval_top_k,
            min_score_threshold=settings.retrieval.MINIMUM_SCORE_THRESHOLD
        )

        # TODO: Add BM25 retriever
        # self.bm25_retriever = BM25Retriever(...)

        # TODO: Add sparse vector retriever
        # self.sparse_retriever = SparseVectorRetriever(...)

    def _setup_reranker(self):
        """Setup reranker model (ViRanker for Vietnamese)."""
        try:
            from FlagEmbedding import FlagReranker

            print(f"[RERANKER] Loading ViRanker model: {self.reranker_model}")
            self.reranker = FlagReranker(
                self.reranker_model,
                use_fp16=True  # Faster inference
            )
            print(f"[RERANKER] ViRanker loaded successfully")

        except ImportError:
            print("[WARNING] FlagEmbedding not installed. Reranker disabled.")
            print("           Install with: pip install -U FlagEmbedding")
            self.use_reranker = False
        except Exception as e:
            print(f"[WARNING] Failed to load reranker: {e}")
            self.use_reranker = False

    def retrieve(
        self,
        query: str,
        use_reranker: Optional[bool] = None
    ) -> RetrievalResult:
        """
        Blended retrieval: Query all available indexes, merge and rerank.

        Pipeline:
        1. Dense vector retrieval
        2. BM25 retrieval (TODO)
        3. Sparse vector retrieval (TODO)
        4. Merge & deduplicate
        5. Rerank
        6. Return top-k

        Args:
            query: User query string
            use_reranker: Override default reranker setting

        Returns:
            RetrievalResult with retrieved and reranked nodes
        """
        print(f"\n{'='*70}")
        print(f"[QUERY ENGINE] Blended Retrieval")
        print(f"[QUERY ENGINE] Query: {query}")
        print(f"{'='*70}\n")

        # Step 1: Retrieve from all available indexes
        all_nodes = []

        # Dense vector retrieval
        print("[QUERY ENGINE] Retrieving from dense vector index...")
        dense_nodes = self._retrieve_dense(query)
        all_nodes.extend(dense_nodes)
        print(f"  → Found {len(dense_nodes)} nodes")

        # BM25 retrieval (TODO)
        if hasattr(self, 'bm25_retriever'):
            print("[QUERY ENGINE] Retrieving from BM25 index...")
            bm25_nodes = self._retrieve_bm25(query)
            all_nodes.extend(bm25_nodes)
            print(f"  → Found {len(bm25_nodes)} nodes")

        # Sparse vector retrieval (TODO)
        if hasattr(self, 'sparse_retriever'):
            print("[QUERY ENGINE] Retrieving from sparse vector index...")
            sparse_nodes = self._retrieve_sparse(query)
            all_nodes.extend(sparse_nodes)
            print(f"  → Found {len(sparse_nodes)} nodes")

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
            retrieval_method="blended",
            reranked=reranked,
            total_retrieved=total_retrieved,
            final_count=len(final_nodes)
        )

    def _retrieve_dense(self, query: str) -> List[NodeWithScore]:
        """Retrieve using dense vector embeddings."""
        query_bundle = QueryBundle(query_str=query)
        return self.dense_retriever.retrieve(query_bundle)

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

        Args:
            query: User query
            nodes: Retrieved nodes

        Returns:
            Reranked nodes (sorted by reranker score, filtered by threshold)
        """
        if not self.use_reranker or not hasattr(self, 'reranker'):
            return nodes

        print(f"[RERANKER] Reranking {len(nodes)} nodes with ViRanker...")

        # Prepare pairs for reranker (FlagReranker uses list of lists)
        pairs = [[query, node.node.get_content()] for node in nodes]

        # Get reranker scores (normalized to [0,1] range)
        scores = self.reranker.compute_score(pairs, normalize=True)

        # Handle single score vs list
        if not isinstance(scores, list):
            scores = [scores]

        # Update node scores and sort
        for node, score in zip(nodes, scores):
            node.score = float(score)

        nodes.sort(key=lambda x: x.score, reverse=True)

        # Filter out low-confidence results based on threshold
        filtered_nodes = [node for node in nodes if node.score >= self.rerank_score_threshold]

        if len(filtered_nodes) < len(nodes):
            print(f"[RERANKER] Filtered {len(nodes) - len(filtered_nodes)} low-confidence results (score < {self.rerank_score_threshold})")

        if len(filtered_nodes) > 0:
            print(f"[RERANKER] Reranking complete. Top score: {filtered_nodes[0].score:.4f}, kept {len(filtered_nodes)}/{len(nodes)} nodes")
        else:
            print(f"[RERANKER] Warning: All results filtered out (all scores < {self.rerank_score_threshold})")

        return filtered_nodes

    def retrieve_with_metadata(self, query: str) -> Dict:
        """
        Retrieve and return formatted result with metadata_generator.

        This is the method that will be exposed via MCP tool.
        Uses blended retrieval (all available indexes).

        Args:
            query: User query

        Returns:
            Dict with documents and metadata_generator
        """
        result = self.retrieve(query)

        return {
            "query": query,
            "method": "blended",
            "reranked": result.reranked,
            "total_retrieved": result.total_retrieved,
            "final_count": result.final_count,
            "documents": [
                {
                    "text": node.node.get_content(),
                    "score": node.score,
                    "metadata_generator": node.node.metadata if hasattr(node.node, 'metadata_generator') else {},
                    "hierarchy": node.node.metadata.get('hierarchy', '') if hasattr(node.node, 'metadata_generator') else ''
                }
                for node in result.nodes
            ]
        }
