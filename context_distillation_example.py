"""
Context Distillation Example - Prototype for UIT AI Assistant

How it works:
1. Retrieve chunks as usual (vector search + rerank)
2. Use fast/cheap LLM to extract ONLY relevant info
3. Pass distilled context to main LLM for final answer

Benefits:
- Reduce tokens sent to expensive LLM
- Faster response (less tokens to process)
- Better focus (less noise from irrelevant chunks)

Trade-offs:
- Extra LLM call (distillation step)
- May lose some context nuance
- Only worth it if context is VERY long
"""

from llama_index.llms.openai import OpenAI

# Giả sử đã retrieve 10 chunks (mỗi chunk ~500 tokens = 5000 tokens total)
retrieved_chunks = [
    "Điều 5. Điều kiện tốt nghiệp: Sinh viên phải hoàn thành 140 tín chỉ...",
    "Điều 10. Học phí: Mức học phí cho năm 2024 là 20 triệu đồng/năm...",
    "Điều 15. Ngoại ngữ tốt nghiệp: CTC cần TOEIC 450, CTTN cần 550...",
    # ... 7 chunks khác
]

user_query = "Điểm TOEIC tốt nghiệp là bao nhiêu?"


# APPROACH 1: Traditional RAG (no distillation)
def traditional_rag(query, chunks):
    """Send all chunks directly to LLM"""
    context = "\n\n".join(chunks)
    
    prompt = f"""Dựa vào thông tin sau:
{context}

Câu hỏi: {query}
Trả lời:"""
    
    llm = OpenAI(model="gpt-5")
    response = llm.complete(prompt)
    return response.text
    # Cost: ~5000 input tokens × $0.003 = $0.015


# APPROACH 2: Context Distillation
def context_distillation_rag(query, chunks):
    """Distill context first, then answer"""
    
    # Step 1: Distill với LLM rẻ
    context = "\n\n".join(chunks)
    
    distill_prompt = f"""Extract ONLY information relevant to this question: "{query}"

Context:
{context}

Output ONLY the relevant sentences/paragraphs, nothing else:"""
    
    cheap_llm = OpenAI(model="gpt-5-nano")  # Rẻ, nhanh
    distilled = cheap_llm.complete(distill_prompt)
    distilled_text = distilled.text.strip()
    
    # Cost step 1: ~5000 input tokens × $0.0001 = $0.0005
    
    # Step 2: Answer với context đã distill
    answer_prompt = f"""Dựa vào thông tin sau:
{distilled_text}

Câu hỏi: {query}
Trả lời:"""
    
    main_llm = OpenAI(model="gpt-5")  # Đắt nhưng xử lý ít token
    response = main_llm.complete(answer_prompt)
    
    # Cost step 2: ~100 input tokens × $0.003 = $0.0003
    # Total: $0.0005 + $0.0003 = $0.0008 (rẻ hơn 18x!)
    
    return response.text


# APPROACH 3: Smart Distillation (chỉ distill khi cần)
def smart_distillation_rag(query, chunks):
    """Only distill if context is very long"""
    
    total_chars = sum(len(c) for c in chunks)
    
    # Nếu context ngắn (<2000 chars), skip distillation
    if total_chars < 2000:
        return traditional_rag(query, chunks)
    
    # Nếu context dài, distill
    return context_distillation_rag(query, chunks)


# Example usage:
if __name__ == "__main__":
    print("Traditional RAG:")
    # answer1 = traditional_rag(user_query, retrieved_chunks)
    # print(answer1)
    
    print("\nContext Distillation RAG:")
    # answer2 = context_distillation_rag(user_query, retrieved_chunks)
    # print(answer2)
    
    print("\nRecommendation for UIT AI Assistant:")
    print("- Use traditional RAG for now (reranking already good)")
    print("- Consider distillation if:")
    print("  1. Users complain about slow responses")
    print("  2. Cost becomes an issue (>$100/month)")
    print("  3. You retrieve >10 chunks per query")
