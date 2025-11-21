from typing import List, Dict

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle


class MultiCollectionRetriever(BaseRetriever):
    """
    Custom retriever for multi-collection support.

    Retrieves from all specified collections and then filters and sorts the results.
    """

    def __init__(
        self,
        collections: Dict[str, VectorStoreIndex],
        top_k: int = 20,
        min_score_threshold: float = 0.25,
    ):
        """
        Initialize the retriever.

        Args:
            collections: A dictionary mapping collection names to VectorStoreIndex objects.
            top_k: The final number of nodes to return.
            min_score_threshold: The minimum score a node must have to be included.
        """
        self.collections = collections
        self.top_k = top_k
        self.min_score_threshold = min_score_threshold
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Core retrieval logic.

        1. Retrieves from all collections.
        2. Gathers all nodes.
        3. Sorts nodes by score.
        4. Filters nodes by score threshold.
        5. Returns the top_k nodes.
        """
        query = query_bundle.query_str

        all_nodes = []
        print(f"[RETRIEVER] Querying all {len(self.collections)} collections...")

        # 1. Retrieve from all collections
        for name, index in self.collections.items():
            print(f"[RETRIEVER] Querying collection: {name}")
            retriever = index.as_retriever(similarity_top_k=self.top_k)
            nodes = retriever.retrieve(query)
            all_nodes.extend(nodes)
            print(f"[RETRIEVER] Found {len(nodes)} nodes in {name}.")

        # 2. Sort and filter
        print(f"[RETRIEVER] Total nodes found: {len(all_nodes)}")
        all_nodes.sort(key=lambda x: x.score, reverse=True)

        filtered_nodes = [
            n for n in all_nodes if n.score >= self.min_score_threshold
        ]
        print(
            f"[RETRIEVER] Nodes after filtering (score >= {self.min_score_threshold}): {len(filtered_nodes)}"
        )

        return filtered_nodes[: self.top_k]

