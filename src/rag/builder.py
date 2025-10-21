"""
Contains the core RagBuilder class and the command-line interface for it.
This module is a self-contained tool for building the RAG vector store.
"""

import chromadb
import os
import json
import argparse
from dotenv import load_dotenv

# --- LlamaIndex v0.10+ Imports ---
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
    Settings,
    SimpleDirectoryReader
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SemanticSplitterNodeParser
# --- FIX: Import OpenAIEmbedding --- 
from llama_index.embeddings.openai import OpenAIEmbedding

from src.config import PROCESSED_DATA_DIR, VECTOR_STORE_DIR

# Load environment variables from .env file
load_dotenv()

class RagBuilder:
    """
    Encapsulates the logic for building and persisting the RAG vector store.
    """

    SUPPORTED_EXTENSIONS = [".md", ".pdf", ".docx"]

    def __init__(self):
        """
        Initializes and configures the RAG building components using OpenAI services.
        """
        print("[INFO] Initializing RagBuilder components with OpenAI...")
        
        # 1. Configure global Settings
        # --- FIX: Use OpenAIEmbedding --- 
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file.")

        embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key)
        
        # Node parser does not depend on the embedding model choice
        node_parser = SemanticSplitterNodeParser.from_defaults(
            breakpoint_percentile_threshold=95
        )

        Settings.embed_model = embed_model
        Settings.node_parser = node_parser

        # 2. Configure Vector Store (ChromaDB)
        db = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        chroma_collection = db.get_or_create_collection("uit_documents_openai") # Use a new collection for OpenAI embeddings
        self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def _load_documents_from_folder(self, folder_path: str) -> list[Document]:
        """
        Loads all supported files from a folder and attaches shared metadata.
        """
        shared_metadata = {}
        metadata_path = os.path.join(folder_path, "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    shared_metadata = json.load(f)
                if 'source_urls' in shared_metadata and isinstance(shared_metadata['source_urls'], list):
                    shared_metadata['source_urls'] = '\n'.join(shared_metadata['source_urls'])
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not read or parse metadata.json in {folder_path}: {e}")

        reader = SimpleDirectoryReader(
            input_dir=folder_path,
            required_exts=self.SUPPORTED_EXTENSIONS
        )
        documents = reader.load_data()

        for doc in documents:
            doc.metadata.update(shared_metadata)
        
        return documents

    def build_from_folder(self, folder_path: str):
        """
        Builds the vector store from all supported files in a single processed folder.
        """
        if not os.path.isdir(folder_path):
            print(f"[ERROR] Processed folder not found: {folder_path}")
            return

        print(f"--- Building from folder: {folder_path} ---")
        try:
            documents = self._load_documents_from_folder(folder_path)
            if not documents:
                print("[INFO] No supported documents found in this folder. Skipping.")
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
        print("🛠️  STARTING FULL RAG VECTOR STORE BUILD (OpenAI)")
        print("="*50)

        if not os.path.isdir(PROCESSED_DATA_DIR):
            print(f"[ERROR] Processed data directory not found: {PROCESSED_DATA_DIR}")
            return
            
        for domain_name in os.listdir(PROCESSED_DATA_DIR):
            domain_path = os.path.join(PROCESSED_DATA_DIR, domain_name)
            if os.path.isdir(domain_path):
                self.build_from_domain(domain_name)
        
        print("\n" + "="*50)
        print("✅ FULL RAG BUILD COMPLETED (OpenAI)")
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
