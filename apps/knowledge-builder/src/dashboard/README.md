# UIT Knowledge Builder Dashboard

Interactive web dashboard for managing document processing and indexing pipelines.

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run Dashboard
```bash
# From knowledge-builder directory
uv run python run_dashboard.py
```

Dashboard will open at: **http://localhost:8501**

## Alternative Launch Methods

### Option A: Using uv (recommended)
```bash
uv run python run_dashboard.py
```

### Option B: Direct Streamlit
```bash
uv run streamlit run src/dashboard/app.py
```

### Option C: Using uvx
```bash
uvx streamlit run src/dashboard/app.py
```

## Features

### 📊 Overview Tab
- View document status (stages completed, cost, chunks)
- Visual pipeline stages with emoji indicators
- Locked stages detection
- Migration status

### ⚙️ Pipeline Tab
- Run full processing pipeline (parse → metadata)
- Run full indexing pipeline (chunk → embed-index)
- Run individual stages
- Force rerun option
- Real-time progress and results

### 📄 Chunks Tab
- Preview chunks.json
- Navigate chunks by index
- View chunk text and metadata

### 📈 Stats Tab
- Global statistics (total docs, cost, chunks)
- Documents table across all categories
- Cost breakdown by document

### 🚀 Sidebar
- Select category and document
- Refresh status
- Clear vector store (one-click)

## Troubleshooting

### Import Errors
If you see import errors, make sure you're running from the `knowledge-builder` directory:
```bash
cd apps/knowledge-builder
uv run python run_dashboard.py
```

### Port Already in Use
If port 8501 is busy, specify a different port:
```bash
uv run streamlit run src/dashboard/app.py --server.port 8502
```

### Missing Dependencies
```bash
uv sync
```

## Development

### Project Structure
```
src/dashboard/
├── app.py              # Main Streamlit application
├── utils.py            # Helper functions
└── components/         # UI components (future)
```

### Adding Features
1. Add helper functions to `utils.py`
2. Add UI components to `app.py`
3. Test with `uv run streamlit run src/dashboard/app.py`

## Notes

- Dashboard requires valid `.env` file with API keys
- Changes auto-reload during development (Streamlit feature)
- Pipeline operations are executed synchronously
- Vector store path: configured in `settings.py`
