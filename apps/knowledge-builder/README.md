# 📚 UIT Knowledge Builder

Build and manage knowledge base for UIT AI Assistant.

## 🚀 Quick Start

### Chạy Dashboard
```bash
cd apps/knowledge-builder
uv run python run_dashboard.py
```
→ **http://localhost:8501**

### Chạy CLI
```bash
# Xem status
uv run python main.py status --category regulation

# Chạy pipeline
uv run python main.py pipeline run --category regulation

# Help
uv run python main.py --help
```

---

## 📖 Documentation

### 🎯 Getting Started
- **[README_QUICK.md](README_QUICK.md)** - Quick start guide (2 phút đọc)
- **[DASHBOARD_CHEATSHEET.md](DASHBOARD_CHEATSHEET.md)** - Dashboard cheatsheet (1 trang)

### 📊 Dashboard
- **[DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)** - Hướng dẫn chi tiết dashboard
- **[DASHBOARD_WORKFLOW.md](DASHBOARD_WORKFLOW.md)** - Workflow diagrams & decision trees

### 🔧 Technical
- **[IMPORTS_FINAL.md](IMPORTS_FINAL.md)** - Import strategy explained

---

## 📊 Dashboard Overview

Dashboard cung cấp giao diện web để:
- ✅ Process documents (parse → clean → normalize → filter → fix-markdown → metadata)
- ✅ Index documents (chunk → embed-index)
- ✅ Monitor pipeline status
- ✅ Preview chunks
- ✅ Track costs

**4 Tabs chính:**
1. **📊 Overview** - Xem status và stages
2. **⚙️ Pipeline** - Run processing/indexing
3. **📄 Chunks** - Preview chunks
4. **📈 Stats** - Thống kê & costs

---

## 🎯 Pipeline Stages

### Processing Pipeline (6 stages)
```
parse → clean → normalize → filter → fix-markdown → metadata
```

| Stage | Function | Cost |
|-------|----------|------|
| `parse` | PDF/DOCX → markdown | 💰💰 LlamaParse |
| `clean` | Remove HTML, normalize | Free |
| `normalize` | Unicode, encoding | Free |
| `filter` | Quality check | Free |
| `fix-markdown` | Fix structure (LLM) | 💰💰 Optional |
| `metadata` | Extract metadata (LLM) | 💰 Required |

### Indexing Pipeline (2 stages)
```
chunk → embed-index
```

| Stage | Function | Cost |
|-------|----------|------|
| `chunk` | Split into semantic chunks | Free |
| `embed-index` | Embed & index to ChromaDB | 💰💰 OpenAI |

---

## 📂 Project Structure

```
knowledge-builder/
├── main.py                 # CLI entry point
├── run_dashboard.py        # Dashboard launcher
├── data/
│   ├── stages/            # Processed documents (category-based)
│   └── vector_store/      # ChromaDB vector store
└── src/
    ├── dashboard/         # Streamlit dashboard
    ├── pipeline/          # Processing & indexing pipelines
    ├── commands/          # CLI commands
    ├── config/            # Configuration
    ├── processing/        # Document processors
    ├── indexing/          # Indexing & chunking
    └── utils/             # Utilities
```

---

## 💰 Cost Management

**Stages tốn tiền:**
- `parse` - LlamaParse API
- `fix-markdown` - LLM API (optional, có thể skip)
- `metadata` - LLM API (required)
- `embed-index` - OpenAI Embeddings

**Tips:**
- ✅ Check Overview trước khi force rerun
- ✅ Skip `fix-markdown` nếu markdown đã OK
- ❌ Không spam force rerun các stage đã completed

---

## ⚙️ Installation

```bash
# Clone repo
git clone <repo-url>
cd apps/knowledge-builder

# Install dependencies
uv sync
# hoặc
pip install -e .

# Setup .env
cp .env.example .env
# Edit .env với API keys
```

**Requirements:**
- Python 3.13+
- uv hoặc pip
- API keys: OpenAI, LlamaParse

---

## 🐛 Troubleshooting

### Dashboard không load
```bash
lsof -ti:8501 | xargs kill -9
uv run python run_dashboard.py
```

### Import errors
Project dùng **absolute imports**. Đọc [IMPORTS_FINAL.md](IMPORTS_FINAL.md) để hiểu tại sao.

### Không thấy documents
```bash
# Migrate từ structure cũ
python main.py migrate --categories regulation
```

---

## 🎓 Learning Path

1. **Bắt đầu** → [README_QUICK.md](README_QUICK.md)
2. **Dùng Dashboard** → [DASHBOARD_CHEATSHEET.md](DASHBOARD_CHEATSHEET.md)
3. **Chi tiết Dashboard** → [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)
4. **Workflow & Diagrams** → [DASHBOARD_WORKFLOW.md](DASHBOARD_WORKFLOW.md)
5. **Technical Deep Dive** → [IMPORTS_FINAL.md](IMPORTS_FINAL.md)

---

## 📞 Support

- Issues: Create GitHub issue
- Docs: Đọc các file markdown trong repo
- Logs: Check terminal output khi chạy dashboard/CLI

---

## ✅ Features

- ✅ Stage-based processing pipeline
- ✅ Incremental execution (skip completed stages)
- ✅ Cost tracking per stage
- ✅ Manual edit protection (stage locking)
- ✅ Category-specific processing (regulation, curriculum, etc.)
- ✅ Web dashboard với Streamlit
- ✅ CLI for automation
- ✅ ChromaDB vector store integration
- ✅ Metadata generation với LLM
- ✅ Semantic chunking

---

Made with ❤️ for UIT AI Assistant
