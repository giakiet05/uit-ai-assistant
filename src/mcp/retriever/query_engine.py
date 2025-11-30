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
from llama_index.core.schema import NodeWithScore

from ...shared.agent.routing import BaseQueryRouter, QueryAllRouter
from .program_filter import apply_program_filter


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
        router: Optional[BaseQueryRouter] = None,
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
            router: Router for collection selection (default: QueryAllRouter)
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
        self.router = router or QueryAllRouter(list(collections.keys()))
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
        print(f"  - Router: {self.router.__class__.__name__}")
        reranker_mode = "Modal GPU" if use_modal else "Local CPU"
        print(f"  - Reranker: {self.reranker_model if use_reranker else 'disabled'} ({reranker_mode})")
        print(f"  - Retrieval top_k: {retrieval_top_k}")
        print(f"  - Final top_k: {top_k}")
        print(f"  - Min score threshold: {min_score_threshold}")
        print(f"  - Rerank score threshold: {rerank_score_threshold}")


    def _setup_local_reranker(self):
        """Setup local reranker model (ViRanker on CPU)."""
        try:
            from FlagEmbedding import FlagReranker

            print(f"[RERANKER] Loading ViRanker model locally (CPU): {self.reranker_model}")
            self.reranker = FlagReranker(
                self.reranker_model,
                use_fp16=True  # Faster inference
            )
            print(f"[RERANKER] ViRanker loaded successfully on CPU")

        except ImportError:
            print("[WARNING] FlagEmbedding not installed. Reranker disabled.")
            print("           Install with: pip install -U FlagEmbedding")
            self.use_reranker = False
        except Exception as e:
            print(f"[WARNING] Failed to load reranker: {e}")
            self.use_reranker = False

    def _setup_modal_reranker(self):
        """Setup Modal reranker (ViRanker on GPU via Modal SDK)."""
        try:
            import modal

            print(f"[RERANKER] Connecting to Modal GPU reranker: {self.reranker_model}")

            # Lookup deployed Modal class using correct API
            # Use modal.Cls.from_name() instead of modal.Cls.lookup()
            ViRankerReranker = modal.Cls.from_name(
                "viranker-reranker",  # App name (from modal.App("viranker-reranker"))
                "ViRankerReranker"    # Class name (from @app.cls)
            )

            # Create instance (this is a proxy to remote class)
            self.modal_reranker = ViRankerReranker()

            print(f"[RERANKER] Connected to Modal GPU reranker successfully")

        except ImportError as e:
            print(f"[WARNING] Modal SDK not installed: {e}")
            print("           Install with: pip install modal")
            print("           Falling back to local CPU reranker")
            self.use_modal = False
            self._setup_local_reranker()
        except Exception as e:
            print(f"[WARNING] Failed to connect to Modal reranker: {e}")
            print("           Make sure the app is deployed: modal deploy modal/reranker_service.py")
            print("           Falling back to local CPU reranker")
            self.use_modal = False
            self._setup_local_reranker()

    def retrieve(
        self,
        query: str,
        use_reranker: Optional[bool] = None
    ) -> RetrievalResult:
        """
        Routed blended retrieval: Route query to collections, then retrieve and rerank.

        Pipeline:
        0. Route query to select collections
        1. Dense vector retrieval from selected collections
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
        print(f"[QUERY ENGINE] Routed Blended Retrieval")
        print(f"[QUERY ENGINE] Query: {query}")
        print(f"{'='*70}\n")

        # Step 0: Route query to select collections
        routing_decision = self.router.route(query)
        print(f"[ROUTING] Strategy: {routing_decision.strategy}")
        print(f"[ROUTING] {routing_decision.reasoning}")
        print(f"[ROUTING] Selected collections: {routing_decision.collections}\n")

        # Filter collections based on routing decision
        selected_collections = {
            name: index for name, index in self.collections.items()
            if name in routing_decision.collections
        }

        if not selected_collections:
            print("[WARNING] No collections selected by router, using all collections")
            selected_collections = self.collections

        # Step 1: Retrieve from selected collections
        all_nodes = []

        # Dense vector retrieval
        print("[QUERY ENGINE] Retrieving from dense vector index...")
        dense_nodes = self._retrieve_dense(query, selected_collections)
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
            retrieval_method=f"routed_blended ({routing_decision.strategy})",
            reranked=reranked,
            total_retrieved=total_retrieved,
            final_count=len(final_nodes)
        )

    def _retrieve_dense(
        self,
        query: str,
        collections: Dict[str, VectorStoreIndex]
    ) -> List[NodeWithScore]:
        """
        Retrieve using dense vector embeddings from selected collections.

        Args:
            query: User query
            collections: Selected collections to retrieve from

        Returns:
            List of retrieved nodes
        """
        all_nodes = []

        # Retrieve from each selected collection
        for name, index in collections.items():
            print(f"[RETRIEVER] Querying collection: {name}")
            retriever = index.as_retriever(similarity_top_k=self.retrieval_top_k)
            nodes = retriever.retrieve(query)
            all_nodes.extend(nodes)
            print(f"[RETRIEVER] Found {len(nodes)} nodes in {name}")

        # Filter by minimum score threshold
        filtered_nodes = [
            node for node in all_nodes
            if node.score >= self.min_score_threshold
        ]

        if len(filtered_nodes) < len(all_nodes):
            print(f"[RETRIEVER] Filtered {len(all_nodes) - len(filtered_nodes)} nodes (score < {self.min_score_threshold})")

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
            if not hasattr(self, 'modal_reranker'):
                print("[WARNING] Modal reranker not initialized, skipping reranking")
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
            # Modal GPU reranking via Modal SDK
            print(f"[RERANKER] Using Modal GPU...")
            try:
                # Call remote method using .remote() API
                scores = self.modal_reranker.rerank.remote(
                    query=query,
                    texts=texts,
                    normalize=True
                )
                print(f"[RERANKER] Modal GPU reranking completed")

            except Exception as e:
                print(f"[WARNING] Modal reranking failed: {e}")
                print("           Falling back to local reranking for this query")
                # Fallback to local reranker
                if hasattr(self, 'reranker'):
                    pairs = [[query, text] for text in texts]
                    scores = self.reranker.compute_score(pairs, normalize=True)
                    if not isinstance(scores, list):
                        scores = [scores]
                else:
                    # No fallback available, return nodes as-is
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
