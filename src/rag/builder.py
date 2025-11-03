"""
Contains the core RagBuilder class and the command-line interface for it.
This module is a self-contained tool for building the RAG vector store.
"""

import chromadb
import os
import json
import argparse

# --- Centralized Config Import ---
from src.config import settings

# --- LlamaIndex v0.10+ Imports ---
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
    Settings as LlamaSettings, # Use alias to avoid confusion with our own Settings
    SimpleDirectoryReader
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding

class RagBuilder:
    """
    Encapsulates the logic for building and persisting the RAG vector store.
    """

    SUPPORTED_EXTENSIONS = [".md", ".pdf", ".docx"]

    def __init__(self):
        """
        Initializes and configures the RAG building components using the global settings object.
        """
        print("[INFO] Initializing RagBuilder components...")
        
        # 1. Configure global LlamaIndex Settings from our app settings
        if not settings.env.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please configure it in your .env file.")

        embed_model = OpenAIEmbedding(
            model_name=settings.env.EMBED_MODEL,
            api_key=settings.env.OPENAI_API_KEY
        )
        node_parser = SemanticSplitterNodeParser.from_defaults(
            breakpoint_percentile_threshold=95
        )

        LlamaSettings.embed_model = embed_model
        LlamaSettings.node_parser = node_parser

        # 2. Configure Vector Store (ChromaDB)
        db = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR)) # Use path from settings
        chroma_collection = db.get_or_create_collection("uit_documents_openai")
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
        domain_path = settings.paths.PROCESSED_DATA_DIR / domain # Use path from settings
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

        processed_dir = settings.paths.PROCESSED_DATA_DIR # Use path from settings
        if not os.path.isdir(processed_dir):
            print(f"[ERROR] Processed data directory not found: {processed_dir}")
            return
            
        for domain_name in os.listdir(processed_dir):
            domain_path = os.path.join(processed_dir, domain_name)
            if os.path.isdir(domain_path):
                self.build_from_domain(domain_name)
        
        print("\n" + "="*50)
        print("✅ FULL RAG BUILD COMPLETED")
        print(f"Vector store persisted at: {settings.paths.VECTOR_STORE_DIR}")
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
        # No need to check for domain existence here, build_from_domain will do it.
        builder.build_from_domain(args.domain)
    else:
        builder.build_all()
