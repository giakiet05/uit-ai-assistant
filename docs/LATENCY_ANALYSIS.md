"""
COMPLETE FLOW ANALYSIS: User Question → Agent Response
=========================================================

Example Query: "Điểm TOEIC tốt nghiệp là bao nhiêu?"

FLOW BREAKDOWN (với timing ước tính):
======================================

┌─────────────────────────────────────────────────────────────────┐
│ 1. USER → API GATEWAY (Frontend → Backend)                     │
├─────────────────────────────────────────────────────────────────┤
│ - Frontend gửi HTTP POST /api/v1/chat                          │
│ - API Gateway nhận request, validate JWT, extract user_id      │
│ - Timing: ~50-100ms                                            │
│ - Bottleneck: NO                                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 2. API GATEWAY → AGENT (gRPC Call)                             │
├─────────────────────────────────────────────────────────────────┤
│ - API Gateway gọi AgentService.Chat() qua gRPC                 │
│ - Create/load session từ MongoDB                               │
│ - Load chat history (nếu có)                                   │
│ - Timing: ~100-200ms (local), ~200-500ms (với DB query)        │
│ - Bottleneck: SLIGHT (nếu history dài)                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 3. AGENT - LangGraph Orchestration                             │
├─────────────────────────────────────────────────────────────────┤
│ Step 3.1: Query Refinement (OPTIONAL - nếu bật)                │
│   - Gọi LLM để refine query                                    │
│   - Model: gpt-5-nano                                          │
│   - Timing: ~500ms-1s ⚠️                                       │
│   - Bottleneck: YES nếu bật                                    │
│                                                                 │
│ Step 3.2: LLM Planning (OpenAI API)                            │
│   - Agent LLM quyết định gọi tool nào                         │
│   - Model: gpt-5 (lớn, chậm)                                  │
│   - Input: System prompt + history + user query               │
│   - Timing: ~2-4s ⚠️⚠️ (SLOW!)                                │
│   - Bottleneck: YES - OpenAI API latency                      │
│                                                                 │
│ Step 3.3: Tool Call Decision                                   │
│   - Parse tool name và arguments từ LLM response              │
│   - Timing: ~10ms                                             │
│   - Bottleneck: NO                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 4. AGENT → MCP SERVER (Tool Execution)                         │
├─────────────────────────────────────────────────────────────────┤
│ - Agent gọi retrieve_regulation() qua MCP protocol             │
│ - Transport: HTTP SSE (streamable-http)                        │
│ - Timing overhead: ~50-100ms                                   │
│ - Bottleneck: SLIGHT                                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 5. MCP SERVER - Retrieval Pipeline                             │
├─────────────────────────────────────────────────────────────────┤
│ Step 5.1: HyDE (OPTIONAL - hiện tại TẮT)                       │
│   - Generate hypothetical document với LLM                     │
│   - Timing: ~500ms-1s (nếu bật)                               │
│   - Bottleneck: YES nếu bật                                    │
│                                                                 │
│ Step 5.2: Vector Search (ChromaDB)                             │
│   - Embed query với OpenAI text-embedding-3-small             │
│   - Embedding API call: ~200-300ms ⚠️                         │
│   - Vector search trong ChromaDB: ~50-100ms                   │
│   - Retrieve top-20 chunks                                     │
│   - Total: ~300-400ms                                         │
│   - Bottleneck: MODERATE (embedding API)                      │
│                                                                 │
│ Step 5.3: Reranking (Cohere API hoặc Modal)                    │
│   - Gửi 20 chunks + query tới reranker                        │
│   - Modal GPU reranker: ~500-800ms ⚠️                         │
│   - Local CPU reranker: ~2-3s ⚠️⚠️                            │
│   - Filter top-k (default: 3-5 chunks)                        │
│   - Bottleneck: YES - especially if local CPU                 │
│                                                                 │
│ Step 5.4: Context Distillation (NẾU BẬT)                       │
│   - Extract table HTML (~10ms)                                │
│   - Gọi gpt-5-nano cho distillation                           │
│   - LLM processing: ~1-2s per chunk ⚠️                        │
│   - Với 5 chunks: ~5-10s ⚠️⚠️⚠️ (VERY SLOW!)                 │
│   - Bottleneck: YES - MAJOR SLOWDOWN                          │
│                                                                 │
│ Step 5.5: Format Results                                       │
│   - Convert nodes → structured JSON                            │
│   - Timing: ~10-20ms                                          │
│   - Bottleneck: NO                                            │
│                                                                 │
│ TOTAL MCP RETRIEVAL:                                           │
│   - Without distillation: ~1-2s                               │
│   - With distillation: ~6-12s ⚠️⚠️⚠️                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 6. AGENT - Tool Response Processing                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 6.1: Receive tool result từ MCP                          │
│   - Parse JSON response                                        │
│   - Timing: ~10ms                                             │
│   - Bottleneck: NO                                            │
│                                                                 │
│ Step 6.2: LLM Final Answer (OpenAI API)                        │
│   - Agent LLM đọc tool result và sinh câu trả lời            │
│   - Model: gpt-5 (lớn)                                        │
│   - Input: System + history + tool result + query             │
│   - Với distilled_context: input ngắn hơn                     │
│   - Timing: ~2-5s ⚠️⚠️                                        │
│   - Bottleneck: YES - OpenAI API latency                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 7. AGENT → API GATEWAY → USER (Response Path)                  │
├─────────────────────────────────────────────────────────────────┤
│ - Agent trả response về API Gateway qua gRPC                   │
│ - API Gateway save message to MongoDB                          │
│ - API Gateway trả HTTP response cho frontend                   │
│ - Timing: ~100-200ms                                          │
│ - Bottleneck: NO                                               │
└─────────────────────────────────────────────────────────────────┘


SUMMARY - TOTAL LATENCY:
=========================

WITHOUT Context Distillation:
------------------------------
1. API Gateway receive          : ~100ms
2. Agent load session           : ~200ms
3. Agent LLM planning          : ~3s      ⚠️ SLOW
4. MCP transport               : ~100ms
5. MCP embedding API           : ~300ms
6. MCP reranking (Modal)       : ~700ms   ⚠️ MODERATE
7. MCP format                  : ~20ms
8. Agent LLM final answer      : ~3s      ⚠️ SLOW
9. Response path               : ~200ms

TOTAL: ~7-8 seconds
------------------------------


WITH Context Distillation (CURRENT):
-------------------------------------
1-3. Same as above             : ~3.4s
4.  MCP transport              : ~100ms
5.  MCP embedding API          : ~300ms
6.  MCP reranking (Modal)      : ~700ms
7.  Context Distillation       : ~8s     ⚠️⚠️⚠️ VERY SLOW!
8.  MCP format                 : ~20ms
9.  Agent LLM final answer     : ~2s     (nhanh hơn vì input ngắn)
10. Response path              : ~200ms

TOTAL: ~14-15 seconds ⚠️⚠️⚠️
-------------------------------------


TOP BOTTLENECKS (ranked by impact):
====================================

🔴 1. CONTEXT DISTILLATION (~8s)
   - Root cause: 
     * Gọi LLM 5 lần (1 lần/chunk) tuần tự
     * Model gpt-5-nano vẫn có latency ~1-2s/call
     * Total: 5 chunks × 1.5s = 7.5s
   
   - Solutions:
     ✅ ĐANG DÙNG: Parallel processing (đã implement)
        → Giảm từ ~7.5s xuống ~2s (fastest chunk wins)
     
     ❌ CHƯA APPLY: Thực tế có thể vẫn chậm vì:
        → Code mới chưa restart?
        → Hoặc đang distill toàn bộ context (không phải từng chunk)?
     
     🔧 RECOMMEND:
        - Tắt distillation tạm (USE_CONTEXT_DISTILLATION=false)
        - Hoặc tăng DISTILLATION_MIN_CHUNKS lên 10
          (chỉ distill khi retrieve >10 chunks, hiếm xảy ra)

🔴 2. AGENT LLM PLANNING (~3s)
   - Root cause: OpenAI API latency với gpt-5
   
   - Solutions:
     🔧 Dùng gpt-5-mini cho planning (nhẹ hơn)
     🔧 Cache system prompt
     🔧 Streaming response (user thấy thinking sớm hơn)

🔴 3. AGENT LLM FINAL ANSWER (~3s without distillation, ~2s with)
   - Root cause: OpenAI API latency
   
   - Solutions:
     🔧 Streaming response
     🔧 Với distillation: đã nhanh hơn nhờ input ngắn

🟡 4. RERANKING (~700ms Modal, ~2-3s local CPU)
   - Root cause: External API call hoặc CPU inference
   
   - Solutions:
     ✅ Đã dùng Modal GPU (tốt rồi)
     🔧 Giảm top_k từ 20 → 10 (ít chunks hơn để rerank)

🟡 5. EMBEDDING API (~300ms)
   - Root cause: OpenAI API latency
   
   - Solutions:
     🔧 Không thể tối ưu nhiều (cần API call)
     🔧 Có thể cache embeddings cho queries phổ biến


RECOMMENDATIONS - GIẢM LATENCY NGAY:
=====================================

PRIORITY 1 - TẮT/GIỚI HẠN CONTEXT DISTILLATION:
------------------------------------------------
```bash
# Option A: Tắt hoàn toàn (nhanh nhất)
USE_CONTEXT_DISTILLATION=false

# Option B: Chỉ distill khi quá nhiều chunks
USE_CONTEXT_DISTILLATION=true
DISTILLATION_MIN_CHUNKS=10  # Hiếm khi trigger

# Restart MCP server
```
Expected gain: **-7s** (14s → 7s) ⚠️ HUGE IMPACT!


PRIORITY 2 - STREAMING RESPONSE:
---------------------------------
- Agent stream từng chunk câu trả lời về frontend
- User thấy text appear từ từ thay vì đợi hết
- Không giảm total time, nhưng PERCEIVED latency giảm mạnh
- Frontend cần update để handle streaming

Expected gain: **Perceived -3s** (user thấy response sau ~4s thay vì 7s)


PRIORITY 3 - GIẢM RERANK TOP_K:
--------------------------------
```python
# In query_engine.py
retrieval_top_k = 10  # Từ 20 → 10
```
Expected gain: **-200ms**


PRIORITY 4 - AGENT MODEL OPTIMIZATION:
---------------------------------------
- Planning: gpt-5 → gpt-5-mini (nhanh hơn, rẻ hơn)
- Final answer: Streaming
Expected gain: **-1s**


TARGET LATENCY sau optimization:
==================================
1. Tắt distillation          : -7s
2. Streaming                 : Perceived -3s
3. Giảm top_k                : -200ms
4. Agent model optimization  : -1s

TOTAL: 7-8s → ~5s perceived (user thấy response sau 2-3s) ✅
"""

with open('/home/giakiet05/programming/projects/uit-ai-assistant/docs/LATENCY_ANALYSIS.md', 'w') as f:
    f.write(__doc__)

print(__doc__)


=============================================================================
UPDATE - OPTIMIZATION APPLIED (2026-01-10)
=============================================================================

CHANGES MADE:
-------------
1. ✅ Reduced retrieval_top_k: 20 → 10
   - Location: query_engine.py (default) + retrieval_tools.py (hardcoded)
   - Impact: Faster reranking (less chunks to process)
   
2. ✅ Increased MCP client timeout: 5min → 10min
   - Location: agent/src/tools/mcp_loader.py
   - Impact: Prevent timeout errors with distillation enabled

3. ✅ Context Distillation: KEEP ENABLED with parallel processing
   - Quality improvement: Extract only relevant info
   - Performance: Parallel distillation (~2s instead of ~7s)


EXPECTED NEW LATENCY:
---------------------
Previous WITH distillation (20 chunks):
  - Reranking: ~800ms (20 chunks)
  - Distillation: ~8s (sequential)
  - Total: ~14-15s

NEW WITH distillation (10 chunks):
  - Reranking: ~400ms (10 chunks, -50%)
  - Distillation: ~4s (parallel on 10 chunks, was ~8s on 20)
  - Total: ~10-11s ✅ (-30% improvement)

Further optimization if needed:
  - Distillation can be disabled: USE_CONTEXT_DISTILLATION=false
    → Back to ~7-8s total
  - Or increase DISTILLATION_MIN_CHUNKS to trigger less often


TRADE-OFFS:
-----------
✅ PROS:
  - 30% faster (~4s saved)
  - Less API cost (10 chunks vs 20)
  - Better focus (less noise for distillation)

⚠️ CONS:
  - Slightly lower recall (might miss relevant chunks in top 11-20)
  - Mitigation: Reranker is good, top-10 usually enough

MONITORING:
-----------
Watch for:
  - User reports of "không tìm thấy thông tin" tăng
  - If yes: consider increasing back to 15
  - If no: current setting is optimal ✅
