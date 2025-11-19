"""
QueryEngine - Orchestrates multiple retrieval methods and re-ranking.

This engine:
1. Retrieves from multiple indexes (dense vector, BM25, sparse vector)
2. Merges and deduplicates results
3. Re-ranks with a reranker model
4. Returns top-k most relevant documents

Design Philosophy:
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
    Main query engine that orchestrates multiple retrieval methods.

    Current support:
    - Dense vector retrieval (OpenAI embeddings)

    Future support:
    - BM25 lexical search
    - Sparse vector retrieval (SPLADE)
    - Hybrid retrieval (fusion of multiple methods)
    """

    def __init__(
        self,
        collections: Dict[str, VectorStoreIndex],
        use_reranker: bool = True,
        reranker_model: Optional[str] = None,
        top_k: int = 5,
        retrieval_top_k: int = 20  # Retrieve more, then rerank
    ):
        """
        Initialize QueryEngine.

        Args:
            collections: Dict of collection_name -> VectorStoreIndex
            use_reranker: Whether to use reranker after retrieval
            reranker_model: Reranker model name (default: "cross-encoder/ms-marco-MiniLM-L-12-v2")
            top_k: Final number of documents to return
            retrieval_top_k: Number of documents to retrieve before reranking
        """
        self.collections = collections
        self.use_reranker = use_reranker
        self.reranker_model = reranker_model or "cross-encoder/ms-marco-MiniLM-L-12-v2"
        self.top_k = top_k
        self.retrieval_top_k = retrieval_top_k

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
        """Setup reranker model."""
        try:
            from sentence_transformers import CrossEncoder

            print(f"[RERANKER] Loading model: {self.reranker_model}")
            self.reranker = CrossEncoder(self.reranker_model)
            print(f"[RERANKER] Model loaded successfully")

        except ImportError:
            print("[WARNING] sentence-transformers not installed. Reranker disabled.")
            print("           Install with: pip install sentence-transformers")
            self.use_reranker = False
        except Exception as e:
            print(f"[WARNING] Failed to load reranker: {e}")
            self.use_reranker = False

    def retrieve(
        self,
        query: str,
        method: str = "dense",
        use_reranker: Optional[bool] = None
    ) -> RetrievalResult:
        """
        Main retrieval method.

        Args:
            query: User query string
            method: Retrieval method ("dense", "bm25", "hybrid")
            use_reranker: Override default reranker setting

        Returns:
            RetrievalResult with retrieved and reranked nodes
        """
        print(f"\n{'='*70}")
        print(f"[QUERY ENGINE] Query: {query}")
        print(f"[QUERY ENGINE] Method: {method}")
        print(f"{'='*70}\n")

        # Step 1: Retrieve with selected method
        if method == "dense":
            nodes = self._retrieve_dense(query)
        elif method == "bm25":
            nodes = self._retrieve_bm25(query)
        elif method == "hybrid":
            nodes = self._retrieve_hybrid(query)
        else:
            raise ValueError(f"Unknown retrieval method: {method}")

        total_retrieved = len(nodes)
        print(f"[QUERY ENGINE] Retrieved {total_retrieved} nodes")

        # Step 2: Rerank if enabled
        should_rerank = use_reranker if use_reranker is not None else self.use_reranker

        if should_rerank and total_retrieved > 0:
            nodes = self._rerank(query, nodes)
            reranked = True
        else:
            reranked = False

        # Step 3: Take top-k
        final_nodes = nodes[:self.top_k]

        print(f"[QUERY ENGINE] Final result: {len(final_nodes)} nodes (reranked: {reranked})\n")

        return RetrievalResult(
            nodes=final_nodes,
            retrieval_method=method,
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
        print("[WARNING] BM25 not implemented yet, falling back to dense retrieval")
        return self._retrieve_dense(query)

    def _retrieve_hybrid(self, query: str) -> List[NodeWithScore]:
        """Retrieve using hybrid method (fusion of dense + BM25)."""
        # TODO: Implement hybrid retrieval with score fusion
        print("[WARNING] Hybrid retrieval not implemented yet, falling back to dense retrieval")
        return self._retrieve_dense(query)

    def _rerank(self, query: str, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """
        Rerank nodes using cross-encoder model.

        Args:
            query: User query
            nodes: Retrieved nodes

        Returns:
            Reranked nodes (sorted by reranker score)
        """
        if not self.use_reranker or not hasattr(self, 'reranker'):
            return nodes

        print(f"[RERANKER] Reranking {len(nodes)} nodes...")

        # Prepare pairs for reranker
        pairs = [(query, node.node.get_content()) for node in nodes]

        # Get reranker scores
        scores = self.reranker.predict(pairs)

        # Update node scores and sort
        for node, score in zip(nodes, scores):
            node.score = float(score)

        nodes.sort(key=lambda x: x.score, reverse=True)

        print(f"[RERANKER] Reranking complete. Top score: {nodes[0].score:.4f}")

        return nodes

    def retrieve_with_metadata(
        self,
        query: str,
        method: str = "dense"
    ) -> Dict:
        """
        Retrieve and return formatted result with metadata.

        This is the method that will be exposed via MCP tool.

        Args:
            query: User query
            method: Retrieval method

        Returns:
            Dict with documents and metadata
        """
        result = self.retrieve(query, method)

        return {
            "query": query,
            "method": result.retrieval_method,
            "reranked": result.reranked,
            "total_retrieved": result.total_retrieved,
            "final_count": result.final_count,
            "documents": [
                {
                    "text": node.node.get_content(),
                    "score": node.score,
                    "metadata": node.node.metadata if hasattr(node.node, 'metadata') else {},
                    "hierarchy": node.node.metadata.get('hierarchy', '') if hasattr(node.node, 'metadata') else ''
                }
                for node in result.nodes
            ]
        }
