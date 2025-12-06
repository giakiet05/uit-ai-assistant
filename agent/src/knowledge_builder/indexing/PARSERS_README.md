# Node Splitters Documentation

Thư mục này chứa các node splitters để chunk documents thành nodes cho indexing.

**⚠️ IMPORTANT:** Tất cả splitters đã được refactored và moved vào `src/indexing/splitters/`.

## 📁 New Structure

```
src/indexing/
├── splitters/
│   ├── __init__.py
│   ├── base_node_splitter.py          # Abstract base class
│   ├── simple_node_splitter.py        # Simple header-based splitting
│   ├── smart_node_splitter.py         # Enhanced splitting (RECOMMENDED)
│   ├── hierarchical_node_splitter.py  # Legacy with hierarchy tracking
│   └── hierarchical_node_splitter_v1.py  # Deprecated (has bugs)
├── builder.py                          # DocumentIndexer (uses SmartNodeSplitter)
└── PARSERS_README.md                   # This file
```

## 📦 Import Examples

```python
# New imports (correct)
from src.knowledge_builder.indexing.splitters import SmartNodeSplitter, SimpleNodeSplitter
from src.knowledge_builder.indexing.indexer import DocumentIndexer

# Old imports (DEPRECATED - will not work)
from src.knowledge_builder.indexing import SmartHeaderParser  # ❌
from src.knowledge_builder.indexing import HierarchicalMarkdownParserV2  # ❌
```

---

## 📋 Available Splitters

### 1. **BaseNodeSplitter** (Abstract Base Class)

**File:** `splitters/base_node_splitter.py`

Abstract base class providing shared functionality for all splitters:
- Token counting (tiktoken)
- Context prepending (document metadata + section info)
- Sub-chunking logic for large chunks
- Stats tracking

**Usage:** Extend this class when creating new splitters.

```python
from src.knowledge_builder.indexing.splitters import BaseNodeSplitter


class MyCustomSplitter(BaseNodeSplitter):
    def _parse_by_headers(self, text: str) -> List[Dict]:
        # Implement your parsing logic
        pass
```

---

### 2. **SimpleNodeSplitter** ⭐ (Good baseline)

**File:** `splitters/simple_node_splitter.py`

- ✅ Parse by headers (preserve section boundaries)
- ✅ Track ONLY current header (no hierarchy)
- ✅ Robust against LlamaParse hierarchy errors
- ✅ Simpler, more reliable

**When to use:**
- Good baseline cho production
- Documents parsed từ PDF (OCR, LlamaParse)
- Curriculum documents (không cần special handling)

**Trade-off:**
- ❌ Không biết "Điều X thuộc Chương Y"
- ❌ Title có thể bị split thành nhiều chunks
- Nhưng: Vẫn work tốt cho retrieval

**Example context:**
```
Tài liệu: Quy Chế Đào Tạo
Tiêu đề: Quy chế đào tạo theo học chế tín chỉ
Phần: Điều 10. Chế độ học tập
Ngày hiệu lực: 2022-09-28
---
## Điều 10. Chế độ học tập
...
```

**Usage:**

```python
from src.knowledge_builder.indexing.splitters import SimpleNodeSplitter

splitter = SimpleNodeSplitter(
    max_tokens=7000,
    sub_chunk_size=1024,
    sub_chunk_overlap=200
)
nodes = splitter.get_nodes_from_documents(documents)
```

---

### 3. **SmartNodeSplitter** ⭐⭐⭐ (RECOMMENDED)

**File:** `splitters/smart_node_splitter.py`

- ✅ All benefits of SimpleNodeSplitter
- ✅ **Title chunk merging** (regulation: first 3-4 short chunks → 1)
- ✅ **Pattern detection** (Điều X, CHƯƠNG X)
- ✅ **Malformed markdown cleanup** (empty headers)
- ✅ Optimized cho Vietnamese regulation documents

**When to use:**
- **DEFAULT choice cho regulation documents** 📋
- PDF-based documents với title split issues
- Documents với Điều/CHƯƠNG patterns

**Improvements over SimpleNodeSplitter:**

1. **Title merging**:
   ```
   Before: Chunk 1: "QUY CHẾ"
           Chunk 2: "ĐÀO TẠO..."
           Chunk 3: "CỦA TRƯỜNG..."

   After:  Chunk 1: "QUY CHẾ ĐÀO TẠO..." (merged)
           Chunk 2: "MỤC LỤC"
           Chunk 3: "Điều 1..."
   ```

2. **Pattern detection**:
   - Detects **Điều X.** (even without markdown headers)
   - Detects **CHƯƠNG X** (Roman/Arabic numerals)
   - Handles malformed markdown from LlamaParse

3. **Markdown cleanup**:
   - Removes empty headers (`##\n`)
   - Fixes standalone separators

**Example context:**
```
Tài liệu: 790 Qd Dhcntt 28 9 22 Quy Che Dao Tao
Tiêu đề: QUY CHẾ ĐÀO TẠO THEO HỌC CHẾ TÍN CHỈ...
Phần: Điều 10. Chế độ học tập
Loại: Văn bản gốc
---
## Điều 10. Chế độ học tập
...
```

**Usage:**

```python
from src.knowledge_builder.indexing.splitters import SmartNodeSplitter

splitter = SmartNodeSplitter(
    max_tokens=7000,
    sub_chunk_size=1024,
    sub_chunk_overlap=200,
    enable_title_merging=True,  # Merge title chunks
    enable_pattern_detection=True  # Detect Điều/CHƯƠNG patterns
)
nodes = splitter.get_nodes_from_documents(documents)

# Get stats
stats = splitter.get_stats()
print(f"Title chunks merged: {stats['title_chunks_merged']}")
print(f"Patterns detected: {stats['patterns_detected']}")
```

---

### 4. **HierarchicalNodeSplitter** (Legacy)

**File:** `splitters/hierarchical_node_splitter.py`

- ✅ Parse by headers, track hierarchy (fixed duplicate issue from V1)
- ✅ Prepend full context: `Cấu trúc: Parent > Child > Current`
- ✅ Token-aware sub-chunking
- ⚠️  **Vulnerable to hierarchy errors from LlamaParse**

**When to use:**
- Document có markdown structure tốt (headers chính xác)
- Muốn giữ full hierarchy info
- Tin tưởng LlamaParse output

**Known issue:**
- LlamaParse có thể tạo sai header levels (e.g., Điều 33 là ##, Điều 34 là ###)
- Dẫn đến hierarchy path sai → context misleading

**Example context:**
```
Tài liệu: Quy Chế Đào Tạo
Tiêu đề: Quy chế đào tạo theo học chế tín chỉ
Cấu trúc: CHƯƠNG 2 > Điều 10 > Khoản 1
Ngày hiệu lực: 2022-09-28
---
## Điều 10. Chế độ học tập
...
```

**Usage:**

```python
from src.knowledge_builder.indexing.splitters import HierarchicalNodeSplitter

splitter = HierarchicalNodeSplitter(
    max_tokens=7000,
    sub_chunk_size=1024,
    sub_chunk_overlap=200
)
nodes = splitter.get_nodes_from_documents(documents)
```

---

### 5. **HierarchicalNodeSplitterV1** ❌ (Deprecated)

**File:** `splitters/hierarchical_node_splitter_v1.py`

- ❌ **DEPRECATED** - Has duplicate header bug
- ❌ Do not use

**Status:** Kept for backwards compatibility only. Use `SmartNodeSplitter` or `HierarchicalNodeSplitter` instead.

---

## 🏆 Recommendation Table

| Document Type | Recommended Splitter | Reason |
|---------------|---------------------|--------|
| **Regulation** | `SmartNodeSplitter` | Title merging + pattern detection |
| **Curriculum** | `SimpleNodeSplitter` | No special handling needed |
| **Clean markdown** | `HierarchicalNodeSplitter` | If you trust header levels |
| **PDF documents** | `SmartNodeSplitter` | Robust against parsing errors |

---

## 🔧 Configuration

All splitters use centralized settings from `src/config/settings.py`:

```python
# settings.py (example)
class RetrievalConfig:
    MAX_TOKENS = 7000           # Max tokens before sub-chunking
    CHUNK_SIZE = 1024           # Sub-chunk target size
    CHUNK_OVERLAP = 200         # Sub-chunk overlap
    EMBED_MODEL = "text-embedding-3-small"
```

Override in splitter initialization:
```python
splitter = SmartNodeSplitter(
    max_tokens=5000,            # Override
    sub_chunk_size=512,         # Override
    sub_chunk_overlap=100       # Override
)
```

---

## 📊 Stats Tracking

All splitters track statistics:

```python
splitter = SmartNodeSplitter()
nodes = splitter.get_nodes_from_documents(documents)

stats = splitter.get_stats()
print(stats)
# {
#     'total_chunks': 142,
#     'large_chunks_split': 3,
#     'final_nodes': 148,
#     'title_chunks_merged': 3,    # SmartNodeSplitter only
#     'patterns_detected': 12      # SmartNodeSplitter only
# }
```

---

## 🧪 Testing

Test files updated with new imports:
- `test/test_simple_header_parser.py` → uses `SimpleNodeSplitter`
- `test/test_smart_header_parser.py` → uses `SmartNodeSplitter`
- `test/test_smart_parser_simple.py` → standalone test

Run tests:
```bash
python test/test_smart_header_parser.py
```

---

## 🚀 Migration Guide

### Old Code (before refactor):

```python
from src.knowledge_builder.indexing import SmartHeaderParser
from src.knowledge_builder.indexing.indexer import RagBuilder

parser = SmartHeaderParser()
builder = RagBuilder(domain="daa.uit.edu.vn")
builder.build_all_collections()
```

### New Code (after refactor):

```python
from src.knowledge_builder.indexing.splitters import SmartNodeSplitter
from src.knowledge_builder.indexing.indexer import DocumentIndexer

# Splitter is automatically used by DocumentIndexer
indexer = DocumentIndexer()  # No domain needed
indexer.build_all_collections(categories=["regulation", "curriculum"])
```

**Key changes:**
1. ✅ `SmartHeaderParser` → `SmartNodeSplitter`
2. ✅ `RagBuilder` → `DocumentIndexer`
3. ✅ No more `domain` parameter (flat structure: `processed/{category}/`)
4. ✅ Import from `src.indexing.splitters`

---

## 📝 Architecture

```
BaseNodeSplitter (abstract)
    ├── count_tokens()
    ├── _prepend_context()
    ├── _process_chunks_with_token_check()
    ├── get_nodes_from_documents()
    └── _parse_by_headers() [ABSTRACT]
         │
         ├── SimpleNodeSplitter
         │   └── Simple header parsing
         │
         ├── SmartNodeSplitter
         │   ├── _preprocess_markdown()
         │   ├── _merge_title_chunks()
         │   ├── _is_section_marker()
         │   └── _post_process_chunks()
         │
         └── HierarchicalNodeSplitter
             └── Hierarchy tracking logic
```

**Benefits of OOP design:**
- ✅ Code reuse (no duplication)
- ✅ Easy to extend (add new splitters)
- ✅ Consistent interface
- ✅ Centralized token counting & context logic

---

## ❓ FAQ

**Q: Which splitter should I use?**
A: Use `SmartNodeSplitter` for regulations, `SimpleNodeSplitter` for curriculum.

**Q: Why did you rename parsers to splitters?**
A: Avoid confusion with PDF parsers (LlamaParse). "Splitter" follows LlamaIndex convention.

**Q: Can I use the old imports?**
A: No, old files have been deleted. Update your imports to `src.indexing.splitters`.

**Q: How do I create a custom splitter?**
A: Extend `BaseNodeSplitter` and implement `_parse_by_headers()`.

**Q: Where is the CLI?**
A: CLI code removed from `builder.py` (handled by `cli.py` now).

---

## 📚 References

- **LlamaIndex Docs:** https://docs.llamaindex.ai/
- **Tiktoken:** https://github.com/openai/tiktoken
- **ChromaDB:** https://www.trychroma.com/
