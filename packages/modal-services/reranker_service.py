"""
Modal App for ViRanker Reranker Service.

Deploy Vietnamese reranker model on Modal GPU for fast inference.

Usage:
    # Deploy to Modal
    modal deploy modal/reranker_service.py

    # Test locally
    modal run modal/reranker_service.py::test

Architecture:
- Model: namdp-ptit/ViRanker (Vietnamese reranking model)
- GPU: T4 (good balance of cost/performance)
- Auto-scaling: Scale to zero when idle
- Cold start: ~5-10s (model cached after first load)
"""

import modal
from typing import List, Dict

# ========== MODAL APP CONFIGURATION ==========

# Create Modal app
app = modal.App("viranker-reranker")

# Define Docker image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        # Core dependencies - let pip resolve compatible versions
        "torch>=2.0.0",
        "transformers>=4.36.0",
        "FlagEmbedding==1.2.10",
        "fastapi[standard]",
    )
)

# Model cache volume (persist model weights across deployments)
model_volume = modal.Volume.from_name(
    "viranker-model-cache",
    create_if_missing=True
)

MODEL_DIR = "/cache/models"
MODEL_NAME = "namdp-ptit/ViRanker"


# ========== MODAL FUNCTION ==========

@app.cls(
    image=image,
    gpu="T4",  # NVIDIA T4 GPU (16GB VRAM, good for reranking)
    volumes={MODEL_DIR: model_volume},  # Cache model weights
    timeout=300,  # 5 minutes timeout
    scaledown_window=600,  # Keep container warm for 10 minutes (renamed from container_idle_timeout)
)
class ViRankerReranker:
    """
    ViRanker Reranker service on Modal GPU.

    Provides fast reranking using Vietnamese-optimized model.
    """

    @modal.enter()
    def load_model(self):
        """
        Load model on container startup (runs once per container).

        Model is cached in volume, so subsequent cold starts are faster.
        """
        from FlagEmbedding import FlagReranker
        import os

        print(f"[MODAL] Loading ViRanker model: {MODEL_NAME}")
        print(f"[MODAL] Cache directory: {MODEL_DIR}")

        # Load model (will download if not cached)
        self.reranker = FlagReranker(
            MODEL_NAME,
            use_fp16=True,  # Use FP16 for faster inference on GPU
            cache_dir=MODEL_DIR
        )

        print(f"[MODAL] Model loaded successfully!")

    @modal.method()
    def rerank(
        self,
        query: str,
        texts: List[str],
        normalize: bool = True
    ) -> List[float]:
        """
        Rerank texts based on query relevance.

        Args:
            query: Search query
            texts: List of text candidates to rerank
            normalize: Whether to normalize scores to [0, 1]

        Returns:
            List of relevance scores (same order as input texts)

        Example:
            >>> reranker = ViRankerReranker()
            >>> scores = reranker.rerank.remote(
            ...     query="điều kiện tốt nghiệp",
            ...     texts=["text1", "text2", "text3"]
            ... )
            >>> print(scores)
            [0.85, 0.62, 0.41]
        """
        print(f"[MODAL] Reranking {len(texts)} texts for query: '{query[:50]}...'")

        # Prepare pairs for reranker
        pairs = [[query, text] for text in texts]

        # Compute scores
        scores = self.reranker.compute_score(pairs, normalize=normalize)

        # Handle single score vs list
        if not isinstance(scores, list):
            scores = [scores]

        print(f"[MODAL] Reranking complete. Top score: {max(scores):.4f}")

        return scores


# ========== WEB ENDPOINT (OPTIONAL - FOR HTTP API) ==========

@app.function(
    image=image,
    gpu="T4",
    volumes={MODEL_DIR: model_volume},
)
@modal.fastapi_endpoint(method="POST")
def rerank_endpoint(request: Dict) -> Dict:
    """
    HTTP endpoint for reranking.

    POST /rerank
    Body: {
        "query": "search query",
        "texts": ["text1", "text2", ...],
        "normalize": true
    }

    Response: {
        "scores": [0.85, 0.62, 0.41, ...]
    }

    Example:
        curl -X POST https://your-modal-url/rerank \
            -H "Content-Type: application/json" \
            -d '{
                "query": "điều kiện tốt nghiệp",
                "texts": ["text1", "text2"],
                "normalize": true
            }'
    """
    from FlagEmbedding import FlagReranker
    import os

    # Load model (cached in volume)
    reranker = FlagReranker(
        MODEL_NAME,
        use_fp16=True,
        cache_dir=MODEL_DIR
    )

    # Extract request data
    query = request.get("query", "")
    texts = request.get("texts", [])
    normalize = request.get("normalize", True)

    if not query or not texts:
        return {"error": "Missing 'query' or 'texts' in request body"}, 400

    # Prepare pairs and compute scores
    pairs = [[query, text] for text in texts]
    scores = reranker.compute_score(pairs, normalize=normalize)

    # Handle single score
    if not isinstance(scores, list):
        scores = [scores]

    return {"scores": scores}


# ========== LOCAL TESTING ==========

@app.local_entrypoint()
def test():
    """
    Test the reranker locally.

    Run with: modal run modal/reranker_service.py::test
    """
    print("Testing ViRanker Reranker on Modal...")

    # Test data
    query = "điều kiện tốt nghiệp ngành khoa học máy tính"
    texts = [
        "Sinh viên ngành Khoa học Máy tính cần đạt 130 tín chỉ để tốt nghiệp.",
        "Học phí năm 2024 là 15 triệu đồng.",
        "Điều kiện tốt nghiệp bao gồm hoàn thành đủ tín chỉ và KLTN.",
    ]

    # Call Modal function
    reranker = ViRankerReranker()
    scores = reranker.rerank.remote(
        query=query,
        texts=texts,
        normalize=True
    )

    # Print results
    print("\nResults:")
    for i, (text, score) in enumerate(zip(texts, scores)):
        print(f"{i+1}. Score: {score:.4f} | Text: {text[:60]}...")

    print("\n✅ Test completed successfully!")
