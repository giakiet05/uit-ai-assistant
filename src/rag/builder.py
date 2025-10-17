"""
Contains the core RagBuilder class and the command-line interface for it.
This module is a self-contained tool for building the RAG vector store.
"""

import chromadb
import os
import json
import argparse

# --- LlamaIndex v0.10+ Imports ---
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
    Settings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.config import PROCESSED_DATA_DIR, VECTOR_STORE_DIR

class RagBuilder:
    """
    Encapsulates the logic for building and persisting the RAG vector store.
    """

    def __init__(self):
        """
        Initializes and configures the RAG building components using the new Settings API.
        """
        print("[INFO] Initializing RagBuilder components...")
        
        # 1. Configure global Settings
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        node_parser = SemanticSplitterNodeParser.from_defaults(
            embed_model=embed_model,
            breakpoint_percentile_threshold=95
        )

        Settings.embed_model = embed_model
        Settings.node_parser = node_parser

        # 2. Configure Vector Store (ChromaDB)
        db = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        chroma_collection = db.get_or_create_collection("uit_documents")
        self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        # 3. Configure Storage Context (points to the vector store)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def _load_documents_from_folder(self, folder_path: str) -> list[Document]:
        """
        Loads all .md files from a folder and attaches metadata from metadata.json.
        """
        documents = []
        metadata = {}
        metadata_path = os.path.join(folder_path, "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                if 'source_urls' in metadata and isinstance(metadata['source_urls'], list):
                    metadata['source_urls'] = '\n'.join(metadata['source_urls'])

            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not read or parse metadata.json in {folder_path}: {e}")

        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    doc = Document(text=content, metadata=metadata.copy())
                    documents.append(doc)
                except Exception as e:
                    print(f"[ERROR] Failed to read document {file_path}: {e}")
        return documents

    def build_from_folder(self, folder_path: str):
        """
        Builds the vector store from all .md files in a single processed folder.
        """
        if not os.path.isdir(folder_path):
            print(f"[ERROR] Processed folder not found: {folder_path}")
            return

        print(f"--- Building from folder: {folder_path} ---")
        try:
            documents = self._load_documents_from_folder(folder_path)

            if not documents:
                print("[INFO] No .md documents found in this folder. Skipping.")
                return

            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context,
            )
            print(f"[SUCCESS] Successfully built and indexed {len(documents)} document(s) from folder.")

        except Exception as e:
            print(f"[ERROR] Failed to build from folder {folder_path}: {e}")

    def build_from_domain(self, domain: str):
        """
        Builds the vector store from all folders within a specific domain.
        """
        print(f"\n--- Building from domain: {domain} ---")
        domain_path = os.path.join(PROCESSED_DATA_DIR, domain)
        if not os.path.isdir(domain_path):
            print(f"[WARNING] Processed directory for domain '{domain}' not found. Skipping.")
            return

        for folder_name in os.listdir(domain_path):
            folder_path = os.path.join(domain_path, folder_name)
            if os.path.isdir(folder_path):
                self.build_from_folder(folder_path)

    def build_all(self):
        """
        Builds the vector store from all configured domains by scanning the processed directory.
        """
        print("\n" + "="*50)
        print("🛠️  STARTING FULL RAG VECTOR STORE BUILD")
        print("="*50)

        if not os.path.isdir(PROCESSED_DATA_DIR):
            print(f"[ERROR] Processed data directory not found: {PROCESSED_DATA_DIR}")
            return
            
        for domain_name in os.listdir(PROCESSED_DATA_DIR):
            domain_path = os.path.join(PROCESSED_DATA_DIR, domain_name)
            if os.path.isdir(domain_path):
                self.build_from_domain(domain_name)
        
        print("\n" + "="*50)
        print("✅ FULL RAG BUILD COMPLETED")
        print(f"Vector store persisted at: {VECTOR_STORE_DIR}")
        print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the RAG vector store building process.')
    parser.add_argument('--domain', '-d', type=str, help='Build for a specific domain (e.g., daa.uit.edu.vn).')
    parser.add_argument('--folder', '-f', type=str, help='Build for a single specific PROCESSED folder path.')

    args = parser.parse_args()
    
    builder = RagBuilder()

    if args.folder:
        builder.build_from_folder(args.folder)
    elif args.domain:
        domain_path = os.path.join(PROCESSED_DATA_DIR, args.domain)
        if not os.path.isdir(domain_path):
            print(f"[ERROR] Processed directory for domain '{args.domain}' not found.")
        else:
            builder.build_from_domain(args.domain)
    else:
        builder.build_all()
