# RAG Evaluation Benchmark

Benchmark suite for evaluating the RAG system of UIT AI Assistant.

## Structure

```
benchmark/
├── data/              # Test datasets
│   ├── regulation_test_full.json       # 798 questions (filtered for students)
│   └── regulation_test_sample.json     # 200 questions (stratified sample)
├── scripts/           # Evaluation scripts
│   ├── prepare_testset.py              # Transform xlsx to JSON test sets
│   └── run_evaluation.py               # Run Ragas evaluation
├── results/           # Evaluation results (timestamped JSON files)
└── benchmark/         # Python package (placeholder)
```

## Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure .env:**
   - Set `API_BASE_URL` to your RAG API endpoint (default: http://localhost:8080)
   - Add at least one LLM API key (OPENAI_API_KEY or GOOGLE_API_KEY) for Ragas evaluation
   - Choose test set size (sample: 200 questions, full: 798 questions)

3. **Ensure dependencies are installed:**
   ```bash
   uv sync
   ```

## Usage

### Step 1: Prepare Test Set

Transform the regulation_test.xlsx file to JSON format:

```bash
uv run python scripts/prepare_testset.py
```

This will:
- Filter 976 questions → 798 questions (student-relevant only)
- Create `regulation_test_full.json` (798 questions)
- Create `regulation_test_sample.json` (200 stratified sample)

**Adjust filtering:** Edit `STUDENT_RELEVANT_DOCUMENTS` in `prepare_testset.py` if needed.

### Step 2: Run Evaluation

Run Ragas evaluation on your RAG system:

```bash
uv run python scripts/run_evaluation.py
```

This will:
1. Load test set (configured in .env)
2. Call RAG API for each question to get answers
3. Evaluate using Ragas metrics:
   - **Answer Correctness**: Semantic + factual correctness vs ground_truth
   - **Answer Similarity**: Cosine similarity with ground_truth
   - **Answer Relevancy**: Answer relevance to question
4. Save results to `results/evaluation_<testset>_<timestamp>.json`

**Environment variables:**
- `TEST_SET`: Which test set to use (default: regulation_test_sample.json)
- `API_BASE_URL`: RAG API endpoint

### Step 3: Analyze Results

Results are saved in `results/` with timestamp. Each result file contains:
- Overall scores for each metric
- Individual question results (question, ground_truth, answer)
- Metadata (timestamp, test set size, API endpoint)

## Cost Estimation

### Sample test set (200 questions):
- Generation: 200 × ~600 tokens = ~120K tokens
- Evaluation: 200 × ~800 tokens = ~160K tokens
- **Total: ~280K tokens**

**With Gemini 2.0 Flash:** ~$0.25
**With GPT-4o:** ~$8-12

### Full test set (798 questions):
- **Total: ~1.1M tokens**

**With Gemini 2.0 Flash:** ~$1.00
**With GPT-4o:** ~$30-40

## Tips

1. **Start with sample set** (200 questions) for quick iteration
2. **Use Gemini 2.0 Flash** for cost-effective evaluation
3. **Run baseline** before making changes to RAG system
4. **Compare results** by checking scores in results/ folder
5. **Adjust API endpoint** in .env if testing different environments

## Example Workflow

```bash
# 1. Prepare test sets (one-time)
uv run python scripts/prepare_testset.py

# 2. Configure environment
cp .env.example .env
# Edit .env: set API keys and endpoints

# 3. Run baseline evaluation (sample set)
uv run python scripts/run_evaluation.py

# 4. Make improvements to RAG system
# (improve chunking, query engine, prompts, etc.)

# 5. Run evaluation again
uv run python scripts/run_evaluation.py

# 6. Compare results
# Check results/ folder for score differences
```
