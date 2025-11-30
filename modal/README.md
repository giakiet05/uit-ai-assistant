# Modal Reranker Service

ViRanker reranker deployed on Modal GPU for fast inference.

## 🚀 Quick Start

### 1. Deploy to Modal

```bash
# Deploy the service
modal deploy modal/reranker_service.py

# This will:
# - Build Docker image with dependencies
# - Deploy to Modal cloud
# - Give you a web endpoint URL
```

### 2. Test Locally (Before Deploy)

```bash
# Test the function locally (runs on Modal, not your machine)
modal run modal/reranker_service.py::test
```

### 3. Get Deployment Info

```bash
# List all deployed apps
modal app list

# View logs
modal app logs viranker-reranker
```

## 📋 Architecture

### Components:

1. **ViRankerReranker Class** (Modal function)
   - Loads model on container startup
   - Provides `rerank()` method
   - Auto-scales based on traffic

2. **HTTP Endpoint** (Optional)
   - REST API for external clients
   - POST `/rerank` with JSON body

### GPU Configuration:

- **GPU Type:** NVIDIA T4 (16GB VRAM)
- **Why T4?** Good balance of cost vs performance for reranking
- **Auto-scaling:** Scales to zero when idle (save cost)
- **Cold start:** ~5-10s first time, then cached

### Model Caching:

- Model weights cached in Modal Volume
- Volume name: `viranker-model-cache`
- Persists across deployments
- Faster cold starts after first load

## 🔧 Usage

### Option 1: Integrated with QueryEngine (Recommended)

The QueryEngine automatically supports both local CPU and Modal GPU reranking.

**Enable Modal GPU reranking:**

In `src/mcp/uit_mcp_server.py`:
```python
_query_engine = QueryEngine(
    collections=collections,
    router=router,
    use_reranker=True,
    use_modal=True,  # Set to True to use Modal GPU
    # ... other params
)
```

**How it works:**
- `use_modal=False` (default): Uses local CPU reranker (FlagEmbedding)
- `use_modal=True`: Uses Modal GPU reranker (faster, serverless)

**Fallback behavior:**
- If Modal connection fails, automatically falls back to local CPU
- No code changes needed, just flip the flag

### Option 2: Call from Python (Modal Client)

```python
import modal

# Connect to deployed app
app = modal.App.lookup("viranker-reranker")
ViRankerReranker = modal.Cls.lookup("viranker-reranker", "ViRankerReranker")

# Use the reranker
reranker = ViRankerReranker()
scores = reranker.rerank.remote(
    query="điều kiện tốt nghiệp",
    texts=["text1", "text2", "text3"],
    normalize=True
)

print(scores)  # [0.85, 0.62, 0.41]
```

### Option 2: Call HTTP Endpoint

```bash
# Get endpoint URL after deployment
modal app show viranker-reranker

# Call the endpoint
curl -X POST https://your-modal-url.modal.run/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "điều kiện tốt nghiệp",
    "texts": ["text1", "text2"],
    "normalize": true
  }'
```

Response:
```json
{
  "scores": [0.85, 0.62]
}
```

## 💰 Cost Estimation

Modal pricing (as of 2024):
- **T4 GPU:** ~$0.60/hour
- **Auto-scaling:** Only pay when running
- **Typical usage:** If reranking takes 0.5s per request:
  - 100 requests/day = ~14 seconds GPU time = ~$0.002/day
  - 1000 requests/day = ~2.3 minutes GPU time = ~$0.023/day

Very cheap for serverless! 🎉

## 🐛 Troubleshooting

### "App not found" error
```bash
# Make sure you deployed first
modal deploy modal/reranker_service.py
```

### Cold start is slow
- First request after idle: ~5-10s (loading model)
- Subsequent requests: <1s
- Solution: Set `container_idle_timeout` higher (already set to 120s)

### Out of memory error
- Unlikely with T4 (16GB)
- If happens, upgrade to A10G (24GB):
  ```python
  @app.cls(gpu="A10G")  # More expensive but more memory
  ```

## 📊 Monitoring

```bash
# View real-time logs
modal app logs viranker-reranker --follow

# Check GPU usage
modal app show viranker-reranker
```

## 🔄 Update Deployment

```bash
# Re-deploy after making changes
modal deploy modal/reranker_service.py

# Modal will:
# - Build new image if dependencies changed
# - Deploy new version
# - Keep old version running until new one is ready (zero downtime)
```
