"""
Base cleaner interface for different content sources
"""
import os
import shutil
from abc import ABC, abstractmethod

# --- Centralized Config Import ---
from src.config import settings

class BaseCleaner(ABC):
    """Abstract base class for content cleaners"""

    def __init__(self):
        """Initialize cleaner with data directories from global settings."""
        # No need to pass directories, they are globally available via settings
        pass

    @abstractmethod
    def clean(self, content: str) -> str:
        """Clean the raw content and return processed content"""
        pass

    def process_folder(self, folder_path: str) -> bool:
        """
        Processes a single raw data folder. It cleans 'content.md' and copies all other files
        to the corresponding processed folder.
        Args:
            folder_path: Path to the raw folder.
        Returns:
            bool: Success status
        """
        try:
            # Use paths from the global settings object
            relative_path = os.path.relpath(folder_path, settings.paths.RAW_DATA_DIR)
            processed_folder_path = os.path.join(settings.paths.PROCESSED_DATA_DIR, relative_path)
            os.makedirs(processed_folder_path, exist_ok=True)

            # Loop through all files in the raw directory
            for filename in os.listdir(folder_path):
                raw_file_path = os.path.join(folder_path, filename)
                processed_file_path = os.path.join(processed_folder_path, filename)

                if filename == 'content.md':
                    with open(raw_file_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                    cleaned_content = self.clean(raw_content)
                    with open(processed_file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                elif os.path.isfile(raw_file_path):
                    shutil.copy2(raw_file_path, processed_file_path)
            
            print(f"✅ Processed: {folder_path} -> {processed_folder_path}")
            return True

        except Exception as e:
            print(f"❌ Error processing {folder_path}: {e}")
            return False

    def process_domain(self, domain: str) -> int:
        """
        Process all folders in a domain.
        Returns: Number of successfully processed folders
        """
        domain_path = os.path.join(settings.paths.RAW_DATA_DIR, domain)
        if not os.path.exists(domain_path):
            print(f"❌ Domain path not found: {domain_path}")
            return 0

        processed_count = 0
        for folder_name in os.listdir(domain_path):
            folder_path = os.path.join(domain_path, folder_name)
            if os.path.isdir(folder_path):
                if self.process_folder(folder_path):
                    processed_count += 1

        print(f"🎉 Processed {processed_count} folders in domain '{domain}'")
        return processed_count
