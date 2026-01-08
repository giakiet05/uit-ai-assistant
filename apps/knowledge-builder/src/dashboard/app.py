"""
Streamlit Dashboard for UIT Knowledge Builder.

Run with: uv run python run_dashboard.py

NOTE: Dashboard uses absolute imports because Streamlit runs this as a script, not a module.
Rest of the project (pipeline, commands, etc.) uses relative imports normally.
"""
import streamlit as st
import json
import sys
from pathlib import Path
import shutil

# Add src to path ONLY for dashboard
# This is necessary because Streamlit cannot run files with relative imports
_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Now use absolute imports
from dashboard.utils import (
    get_categories,
    get_documents,
    get_document_status,
    format_cost,
    get_stage_emoji,
    get_chunks_count,
    get_all_documents_status
)
from config.settings import settings

# NOTE: Pipeline imports được lazy import khi cần


# Page config
st.set_page_config(
    page_title="UIT Knowledge Builder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
.stButton>button {
    width: 100%;
}
.stage-box {
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
    background-color: #f0f2f6;
}
.metric-card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)


# Title
st.title("📚 UIT Knowledge Builder Dashboard")
st.markdown("---")


# Sidebar
with st.sidebar:
    st.header("⚙️ Document Selection")

    # Category selector
    categories = get_categories()
    if not categories:
        st.error("No categories found in stages directory")
        st.stop()

    selected_category = st.selectbox(
        "Category",
        categories,
        index=0
    )

    # Document selector
    documents = get_documents(selected_category)
    if not documents:
        st.warning(f"No documents found in category: {selected_category}")
        st.stop()

    selected_document = st.selectbox(
        "Document",
        documents,
        index=0
    )

    st.markdown("---")

    # Actions
    st.header("🚀 Quick Actions")

    if st.button("🔄 Refresh Status"):
        st.rerun()

    if st.button("🗑️ Clear Vector Store"):
        vector_store_path = settings.paths.VECTOR_STORE_DIR
        if vector_store_path.exists():
            shutil.rmtree(vector_store_path)
            st.success("Vector store cleared!")
            st.rerun()
        else:
            st.info("Vector store already empty")


# Main content - ADD Batch tab
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "⚙️ Pipeline", "🔥 Batch Operations", "📄 Chunks", "📈 Stats"])

# Tab 1: Overview
with tab1:
    status = get_document_status(selected_category, selected_document)

    if not status:
        st.warning("No pipeline state found for this document")
    else:
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(f"📄 {selected_document}")
        with col2:
            st.metric("Total Cost", format_cost(status['total_cost']))
        with col3:
            chunks_count = get_chunks_count(selected_category, selected_document)
            st.metric("Chunks", chunks_count)

        st.markdown("---")

        # Status summary
        st.info(f"**Status:** {status['status']}")

        if status['migrated']:
            st.info("ℹ️ Migrated from legacy processed/ structure")

        # Stages grid
        st.subheader("🔧 Pipeline Stages")

        # Processing stages
        st.markdown("**Processing Pipeline:**")
        proc_cols = st.columns(6)
        processing_stages = ['parse', 'clean', 'normalize', 'filter', 'fix-markdown', 'metadata']

        for i, stage_name in enumerate(processing_stages):
            stage = next((s for s in status['stages'] if s['name'] == stage_name), None)
            with proc_cols[i]:
                if stage:
                    emoji = get_stage_emoji(stage['status'])
                    st.markdown(f"<div class='stage-box'>{emoji}<br><small>{stage_name}</small></div>",
                              unsafe_allow_html=True)
                    if stage['locked']:
                        st.caption("🔒 Locked")
                else:
                    st.markdown(f"<div class='stage-box'>⬜<br><small>{stage_name}</small></div>",
                              unsafe_allow_html=True)

        st.markdown("**Indexing Pipeline:**")
        idx_cols = st.columns(2)
        indexing_stages = ['chunk', 'embed-index']

        for i, stage_name in enumerate(indexing_stages):
            stage = next((s for s in status['stages'] if s['name'] == stage_name), None)
            with idx_cols[i]:
                if stage:
                    emoji = get_stage_emoji(stage['status'])
                    st.markdown(f"<div class='stage-box'>{emoji}<br><small>{stage_name}</small><br><small>{format_cost(stage['cost'])}</small></div>",
                              unsafe_allow_html=True)
                    if stage['locked']:
                        st.caption("🔒 Locked")
                else:
                    st.markdown(f"<div class='stage-box'>⬜<br><small>{stage_name}</small></div>",
                              unsafe_allow_html=True)


# Tab 2: Pipeline Actions (Single Document)
with tab2:
    st.subheader("⚙️ Run Pipeline - Single Document")
    st.info(f"📄 Working on: **{selected_document}**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Processing Pipeline")

        force_processing = st.checkbox("Force rerun processing stages", key="force_proc")

        if st.button("▶️ Run Full Processing Pipeline"):
            with st.spinner("Running processing pipeline..."):
                try:
                    from pipeline.processing_pipeline import ProcessingPipeline
                    from utils.file_finder import find_raw_file
                    
                    # Single document processing only
                    raw_file_path = find_raw_file(selected_category, selected_document)
                    if not raw_file_path:
                        st.warning("No raw file found, using dummy path")
                        raw_file_path = Path("dummy")

                    proc_pipeline = ProcessingPipeline(
                        category=selected_category,
                        document_id=selected_document,
                        raw_file_path=raw_file_path
                    )

                    result = proc_pipeline.run(force=force_processing)

                    st.success(f"✅ Processing hoàn thành!")
                    
                    with st.expander("📋 Chi tiết kết quả", expanded=True):
                        st.json(result)
                    
                    st.info("💡 Click 'Refresh Status' hoặc chuyển tab để cập nhật")

                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())

        st.markdown("### Individual Processing Stages")

        selected_proc_stage = st.selectbox(
            "Select stage",
            ['parse', 'clean', 'normalize', 'filter', 'fix-markdown', 'metadata'],
            key="proc_stage"
        )

        force_proc_stage = st.checkbox("Force rerun stage", key="force_proc_stage")

        if st.button(f"▶️ Run {selected_proc_stage}"):
            with st.spinner(f"Running {selected_proc_stage}..."):
                try:
                    # Lazy import
                    from pipeline.processing_pipeline import ProcessingPipeline
                    from utils.file_finder import find_raw_file

                    raw_file_path = find_raw_file(selected_category, selected_document)
                    if not raw_file_path:
                        raw_file_path = Path("dummy")

                    proc_pipeline = ProcessingPipeline(
                        category=selected_category,
                        document_id=selected_document,
                        raw_file_path=raw_file_path
                    )

                    result = proc_pipeline.run_stage(
                        stage_name=selected_proc_stage,
                        force=force_proc_stage
                    )

                    if result['executed']:
                        st.success(f"✅ Stage '{selected_proc_stage}' hoàn thành! (cost: {format_cost(result['cost'])})")
                    else:
                        st.info(f"⏭️ Stage '{selected_proc_stage}' skipped: {result.get('skip_reason', 'unknown')}")
                    
                    with st.expander("📋 Chi tiết kết quả"):
                        st.json(result)
                    
                    st.info("💡 Click 'Refresh Status' để cập nhật")

                except Exception as e:
                    st.error(f"❌ Stage failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())

    with col2:
        st.markdown("### Indexing Pipeline")

        force_indexing = st.checkbox("Force rerun indexing stages", key="force_idx")

        if st.button("▶️ Run Full Indexing Pipeline"):
            with st.spinner("Running indexing pipeline..."):
                try:
                    from pipeline.indexing_pipeline import IndexingPipeline
                    
                    # Single document indexing only
                    idx_pipeline = IndexingPipeline(
                        category=selected_category,
                        document_id=selected_document
                    )

                    result = idx_pipeline.run(force=force_indexing)

                    st.success(f"✅ Indexing hoàn thành!")
                    
                    with st.expander("📋 Chi tiết kết quả", expanded=True):
                        st.json(result)
                    
                    st.info("💡 Click 'Refresh Status' hoặc chuyển tab để cập nhật")

                except Exception as e:
                    st.error(f"❌ Indexing failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())

        st.markdown("### Individual Indexing Stages")

        selected_idx_stage = st.selectbox(
            "Select stage",
            ['chunk', 'embed-index'],
            key="idx_stage"
        )

        force_idx_stage = st.checkbox("Force rerun stage", key="force_idx_stage")

        if st.button(f"▶️ Run {selected_idx_stage}"):
            with st.spinner(f"Running {selected_idx_stage}..."):
                try:
                    # Lazy import
                    from pipeline.indexing_pipeline import IndexingPipeline

                    idx_pipeline = IndexingPipeline(
                        category=selected_category,
                        document_id=selected_document
                    )

                    result = idx_pipeline.run_stage(
                        stage_name=selected_idx_stage,
                        force=force_idx_stage
                    )

                    if result['executed']:
                        st.success(f"✅ Stage '{selected_idx_stage}' hoàn thành! (cost: {format_cost(result['cost'])})")
                    else:
                        st.info(f"⏭️ Stage '{selected_idx_stage}' skipped: {result.get('skip_reason', 'unknown')}")
                    
                    with st.expander("📋 Chi tiết kết quả"):
                        st.json(result)
                    
                    st.info("💡 Click 'Refresh Status' để cập nhật")

                except Exception as e:
                    st.error(f"❌ Stage failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())


# Tab 3: Batch Operations
with tab3:
    st.subheader("🔥 Batch Operations - Category Level")
    st.info(f"📁 Working on category: **{selected_category}** ({len(documents)} documents)")
    
    # Warning
    st.warning("⚠️ Batch operations sẽ xử lý **TẤT CẢ** documents trong category. Hãy cẩn thận!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Processing Pipeline")
        
        # Full pipeline
        st.markdown("#### Run Full Pipeline")
        force_batch_proc = st.checkbox("Force rerun all processing stages", key="force_batch_proc")
        
        if st.button("▶️ Batch: Full Processing Pipeline", key="batch_proc_full"):
            with st.spinner(f"Processing {len(documents)} documents..."):
                try:
                    from pipeline.processing_pipeline import ProcessingPipeline
                    from utils.file_finder import find_raw_file
                    
                    results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, doc in enumerate(documents):
                        status_text.text(f"Processing {idx+1}/{len(documents)}: {doc}")
                        progress_bar.progress((idx + 1) / len(documents))
                        
                        try:
                            raw_file_path = find_raw_file(selected_category, doc)
                            if not raw_file_path:
                                raw_file_path = Path("dummy")
                            
                            proc_pipeline = ProcessingPipeline(
                                category=selected_category,
                                document_id=doc,
                                raw_file_path=raw_file_path
                            )
                            
                            result = proc_pipeline.run(force=force_batch_proc)
                            results.append({
                                'document': doc,
                                'status': 'success',
                                'result': result
                            })
                        except Exception as e:
                            results.append({
                                'document': doc,
                                'status': 'error',
                                'error': str(e)
                            })
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show summary
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    fail_count = len(results) - success_count
                    
                    if fail_count == 0:
                        st.success(f"🎉 Hoàn thành! Đã xử lý {success_count}/{len(documents)} documents")
                    else:
                        st.warning(f"⚠️ Hoàn thành: {success_count} thành công, {fail_count} thất bại")
                    
                    # Show details
                    with st.expander("📋 Chi tiết kết quả", expanded=(fail_count > 0)):
                        for r in results:
                            if r['status'] == 'success':
                                st.success(f"✅ {r['document']}")
                            else:
                                st.error(f"❌ {r['document']}: {r['error']}")
                    
                    st.info("💡 Refresh page để cập nhật")
                
                except Exception as e:
                    st.error(f"❌ Batch processing failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())
        
        # Individual stage
        st.markdown("#### Run Individual Stage")
        batch_proc_stage = st.selectbox(
            "Select stage",
            ['parse', 'clean', 'normalize', 'filter', 'fix-markdown', 'metadata'],
            key="batch_proc_stage"
        )
        force_batch_proc_stage = st.checkbox("Force rerun stage", key="force_batch_proc_stage")
        
        if st.button(f"▶️ Batch: {batch_proc_stage}", key="batch_proc_stage_btn"):
            with st.spinner(f"Running {batch_proc_stage} on {len(documents)} documents..."):
                try:
                    from pipeline.processing_pipeline import ProcessingPipeline
                    from utils.file_finder import find_raw_file
                    
                    results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, doc in enumerate(documents):
                        status_text.text(f"{batch_proc_stage} {idx+1}/{len(documents)}: {doc}")
                        progress_bar.progress((idx + 1) / len(documents))
                        
                        try:
                            raw_file_path = find_raw_file(selected_category, doc)
                            if not raw_file_path:
                                raw_file_path = Path("dummy")
                            
                            proc_pipeline = ProcessingPipeline(
                                category=selected_category,
                                document_id=doc,
                                raw_file_path=raw_file_path
                            )
                            
                            result = proc_pipeline.run_stage(
                                stage_name=batch_proc_stage,
                                force=force_batch_proc_stage
                            )
                            results.append({
                                'document': doc,
                                'status': 'success' if result['executed'] else 'skipped',
                                'result': result
                            })
                        except Exception as e:
                            results.append({
                                'document': doc,
                                'status': 'error',
                                'error': str(e)
                            })
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show summary
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
                    fail_count = sum(1 for r in results if r['status'] == 'error')
                    
                    st.success(f"✅ {success_count} thành công, ⏭️ {skipped_count} skipped, ❌ {fail_count} lỗi")
                    
                    # Show details
                    with st.expander("📋 Chi tiết kết quả", expanded=(fail_count > 0)):
                        for r in results:
                            if r['status'] == 'success':
                                st.success(f"✅ {r['document']}")
                            elif r['status'] == 'skipped':
                                st.info(f"⏭️ {r['document']}: {r['result'].get('skip_reason', 'skipped')}")
                            else:
                                st.error(f"❌ {r['document']}: {r['error']}")
                    
                    st.info("💡 Refresh page để cập nhật")
                
                except Exception as e:
                    st.error(f"❌ Batch stage failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())
    
    with col2:
        st.markdown("### 📊 Indexing Pipeline")
        
        # Full pipeline
        st.markdown("#### Run Full Pipeline")
        force_batch_idx = st.checkbox("Force rerun all indexing stages", key="force_batch_idx")
        
        if st.button("▶️ Batch: Full Indexing Pipeline", key="batch_idx_full"):
            with st.spinner(f"Indexing {len(documents)} documents..."):
                try:
                    from pipeline.indexing_pipeline import IndexingPipeline
                    
                    results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, doc in enumerate(documents):
                        status_text.text(f"Indexing {idx+1}/{len(documents)}: {doc}")
                        progress_bar.progress((idx + 1) / len(documents))
                        
                        try:
                            idx_pipeline = IndexingPipeline(
                                category=selected_category,
                                document_id=doc
                            )
                            
                            result = idx_pipeline.run(force=force_batch_idx)
                            results.append({
                                'document': doc,
                                'status': 'success',
                                'result': result
                            })
                        except Exception as e:
                            results.append({
                                'document': doc,
                                'status': 'error',
                                'error': str(e)
                            })
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show summary
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    fail_count = len(results) - success_count
                    
                    if fail_count == 0:
                        st.success(f"🎉 Hoàn thành! Đã index {success_count}/{len(documents)} documents")
                    else:
                        st.warning(f"⚠️ Hoàn thành: {success_count} thành công, {fail_count} thất bại")
                    
                    # Show details
                    with st.expander("📋 Chi tiết kết quả", expanded=(fail_count > 0)):
                        for r in results:
                            if r['status'] == 'success':
                                st.success(f"✅ {r['document']}")
                            else:
                                st.error(f"❌ {r['document']}: {r['error']}")
                    
                    st.info("💡 Refresh page để cập nhật")
                
                except Exception as e:
                    st.error(f"❌ Batch indexing failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())
        
        # Individual stage
        st.markdown("#### Run Individual Stage")
        batch_idx_stage = st.selectbox(
            "Select stage",
            ['chunk', 'embed-index'],
            key="batch_idx_stage"
        )
        force_batch_idx_stage = st.checkbox("Force rerun stage", key="force_batch_idx_stage")
        
        if st.button(f"▶️ Batch: {batch_idx_stage}", key="batch_idx_stage_btn"):
            with st.spinner(f"Running {batch_idx_stage} on {len(documents)} documents..."):
                try:
                    from pipeline.indexing_pipeline import IndexingPipeline
                    
                    results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, doc in enumerate(documents):
                        status_text.text(f"{batch_idx_stage} {idx+1}/{len(documents)}: {doc}")
                        progress_bar.progress((idx + 1) / len(documents))
                        
                        try:
                            idx_pipeline = IndexingPipeline(
                                category=selected_category,
                                document_id=doc
                            )
                            
                            result = idx_pipeline.run_stage(
                                stage_name=batch_idx_stage,
                                force=force_batch_idx_stage
                            )
                            results.append({
                                'document': doc,
                                'status': 'success' if result['executed'] else 'skipped',
                                'result': result
                            })
                        except Exception as e:
                            results.append({
                                'document': doc,
                                'status': 'error',
                                'error': str(e)
                            })
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show summary
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
                    fail_count = sum(1 for r in results if r['status'] == 'error')
                    
                    st.success(f"✅ {success_count} thành công, ⏭️ {skipped_count} skipped, ❌ {fail_count} lỗi")
                    
                    # Show details
                    with st.expander("📋 Chi tiết kết quả", expanded=(fail_count > 0)):
                        for r in results:
                            if r['status'] == 'success':
                                st.success(f"✅ {r['document']}")
                            elif r['status'] == 'skipped':
                                st.info(f"⏭️ {r['document']}: {r['result'].get('skip_reason', 'skipped')}")
                            else:
                                st.error(f"❌ {r['document']}: {r['error']}")
                    
                    st.info("💡 Refresh page để cập nhật")
                
                except Exception as e:
                    st.error(f"❌ Batch stage failed: {e}")
                    import traceback
                    with st.expander("🐛 Error details", expanded=True):
                        st.code(traceback.format_exc())


# Tab 5: Chunks Preview
with tab4:
    st.subheader("📄 Chunks Preview")

    doc_dir = settings.paths.STAGES_DIR / selected_category / selected_document
    chunks_file = doc_dir / "chunks.json"

    if not chunks_file.exists():
        st.warning("No chunks found. Run chunk stage first.")
    else:
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        st.info(f"Total chunks: {len(chunks)}")

        # Chunk selector
        chunk_idx = st.number_input(
            "Chunk index",
            min_value=0,
            max_value=len(chunks) - 1,
            value=0
        )

        chunk = chunks[chunk_idx]

        # Display chunk
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Chunk Text")
            st.text_area(
                "Content",
                value=chunk['text'],
                height=400,
                key=f"chunk_{chunk_idx}"
            )

        with col2:
            st.markdown("### Metadata")
            st.json(chunk['metadata'])


# Tab 5: Global Stats
with tab4:
    st.subheader("📈 Global Statistics")

    all_status = get_all_documents_status()

    if not all_status:
        st.warning("No documents found")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Documents", len(all_status))

        with col2:
            total_cost = sum(s['total_cost'] for s in all_status)
            st.metric("Total Cost", format_cost(total_cost))

        with col3:
            total_chunks = sum(get_chunks_count(s['category'], s['document_id']) for s in all_status)
            st.metric("Total Chunks", total_chunks)

        with col4:
            categories_count = len(set(s['category'] for s in all_status))
            st.metric("Categories", categories_count)

        st.markdown("---")

        # Documents table
        st.subheader("All Documents")

        table_data = []
        for s in all_status:
            chunks = get_chunks_count(s['category'], s['document_id'])
            table_data.append({
                'Category': s['category'],
                'Document': s['document_id'][:50] + '...' if len(s['document_id']) > 50 else s['document_id'],
                'Status': s['status'],
                'Chunks': chunks,
                'Cost': format_cost(s['total_cost'])
            })

        st.dataframe(table_data, use_container_width=True)


# Footer
st.markdown("---")
st.caption("UIT Knowledge Builder Dashboard v1.0")
